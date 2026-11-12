import re
from pathlib import Path
from flask import Blueprint, jsonify, request
from db import get_db
from security import limiter

cartelera_bp = Blueprint('cartelera', __name__)
POSTER_DIR = Path(__file__).resolve().parents[2] / "frontend" / "static" / "images" / "posters"
POSTER_FILES = {
    re.sub(r"[^a-z0-9]", "", path.stem.lower()): path.name
    for path in POSTER_DIR.iterdir()
    if path.suffix.lower() in {".webp", ".png"}
}


def get_poster(title, stored_filename=None):
    filename = Path(str(stored_filename or "")).name
    if filename and filename != "." and (POSTER_DIR / filename).is_file():
        return f"/static/images/posters/{filename}"
    title_key = re.sub(r"[^a-z0-9]", "", str(title).lower())
    filename = next((name for stem, name in POSTER_FILES.items() if title_key.startswith(stem)), None)
    return f"/static/images/posters/{filename}" if filename else None

CONTENIDO_UI = {
    "soon": [],
    "promos": [
        {"title": "Martes y Miércoles 2x1", "text": "Entradas a precio especial en formatos 2D y 3D en todas las sedes."},
        {"title": "Combo Pareja CineStar", "text": "Crispetas grandes + 2 Bebidas + Doblados con 20% de descuento."}
    ],
    "faq": [
        {"q": "¿Cómo compro mis boletas?", "a": "Selecciona la película, el formato, la función y tus asientos preferidos en el mapa interactivo. Confirma la compra desde el carrito y recibe tu comprobante digital."},
        {"q": "¿Cómo funciona el acceso a las salas?", "a": "Presenta tu comprobante desde el celular o indica tu correo electrónico registrado al momento de ingresar a la sala."},
        {"q": "¿Puedo cambiar o cancelar mi reserva?", "a": "Los cambios de función se pueden realizar con mínimo 2 horas de anticipación desde tu panel de usuario o en taquilla física."},
        {"q": "¿Qué métodos de pago son aceptados?", "a": "Aceptamos tarjetas de crédito/débito, PSE, Nequi, Daviplata y pago en efectivo en las cajas presenciales."}
    ]
}

@cartelera_bp.route("/api/contenido", methods=["GET"])
def contenido():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.IdPelicula, p.Titulo, p.Duracion, p.Clasificacion,
                   ISNULL(g.Nombre, 'Sin género'), p.Poster
            FROM Peliculas p
            INNER JOIN Estados ep ON ep.IdEstado = p.IdEstado AND ep.Nombre = 'Activo'
            LEFT JOIN Generos g ON p.IdGenero = g.IdGenero
            ORDER BY p.Titulo
        """)
        films = {
            row[0]: {
                "id": row[0],
                "title": row[1],
                "duration": f"{row[2]} min",
                "rating": row[3],
                "genre": row[4],
                "format": "2D",
                "poster": get_poster(row[1], row[5]),
                "showtimes": [],
            }
            for row in cursor.fetchall()
        }

        cursor.execute("""
            SELECT f.IdFuncion, f.IdPelicula, CONVERT(VARCHAR(5), f.Hora, 108),
                   f.Formato, CAST(f.Precio AS FLOAT), c.Ciudad, c.Nombre
            FROM Funciones f
            INNER JOIN Estados ef ON ef.IdEstado = f.IdEstado AND ef.Nombre = 'Activo'
            INNER JOIN Salas s ON s.IdSala = f.IdSala
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados ec ON ec.IdEstado = c.IdEstado AND ec.Nombre = 'Activo'
                        WHERE f.FechaFuncion >= CONVERT(DATE, GETDATE())
                            AND f.FechaFuncion < DATEADD(DAY, 1, CONVERT(DATE, GETDATE()))
            ORDER BY f.Hora, f.IdFuncion
        """)
        formats = set()
        venues = {}
        for row in cursor.fetchall():
            film = films.get(row[1])
            if film is None:
                continue
            formats.add(row[3])
            venues.setdefault(row[5], set()).add(row[6])
            film["format"] = row[3]
            film["showtimes"].append({
                "id": row[0],
                "time": row[2],
                "format": row[3],
                "price": row[4],
                "city": row[5],
                "venue": row[6],
            })

        cursor.execute("""
            SELECT t.Nombre FROM TiposPago t
            INNER JOIN Estados e ON e.IdEstado = t.IdEstado AND e.Nombre = 'Activo'
            ORDER BY t.IdTipoPago
        """)
        payment_types = [row[0] for row in cursor.fetchall()]

    resp = dict(CONTENIDO_UI)
    resp["films"] = list(films.values())
    resp["cities"] = sorted(venues)
    resp["venues"] = {city: sorted(names) for city, names in venues.items()}
    resp["formats"] = ["Todos", *sorted(formats)]
    resp["paymentTypes"] = payment_types
    return jsonify(resp)

@cartelera_bp.route("/api/asientos-ocupados", methods=["GET"])
@limiter.limit("60 per minute")
def asientos_ocupados():
    try:
        function_id = int(request.args.get("funcion", ""))
    except ValueError:
        return jsonify({"error": "La función indicada no es válida."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.Fila, a.Numero,
                   CASE WHEN EXISTS (
                       SELECT 1
                       FROM DetallesBoleta d
                       INNER JOIN Boletas b ON b.IdBoleta = d.IdBoleta
                       INNER JOIN Estados ed ON ed.IdEstado = d.IdEstado AND ed.Nombre = 'Activo'
                       INNER JOIN Estados eb ON eb.IdEstado = b.IdEstado AND eb.Nombre = 'Activo'
                       WHERE d.IdAsiento = a.IdAsiento AND b.IdFuncion = f.IdFuncion
                   ) THEN 1 ELSE 0 END AS Ocupado
            FROM Funciones f
            INNER JOIN Estados ef ON ef.IdEstado = f.IdEstado AND ef.Nombre = 'Activo'
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Estados ep ON ep.IdEstado = p.IdEstado AND ep.Nombre = 'Activo'
            INNER JOIN Salas s ON s.IdSala = f.IdSala
            INNER JOIN Estados es ON es.IdEstado = s.IdEstado AND es.Nombre = 'Activo'
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados ec ON ec.IdEstado = c.IdEstado AND ec.Nombre = 'Activo'
            INNER JOIN Asientos a ON a.IdSala = f.IdSala
            INNER JOIN Estados ea ON ea.IdEstado = a.IdEstado AND ea.Nombre = 'Activo'
                        WHERE f.IdFuncion = ?
                            AND f.FechaFuncion >= CONVERT(DATE, GETDATE())
                            AND f.FechaFuncion < DATEADD(DAY, 1, CONVERT(DATE, GETDATE()))
            ORDER BY a.Fila, a.Numero
        """, (function_id,))
        seats = cursor.fetchall()
        if not seats:
            return jsonify({"error": "La función no está disponible."}), 404
        seat_codes = [f"{row[0]}{row[1]}" for row in seats]
        occupied = [f"{row[0]}{row[1]}" for row in seats if row[2]]

    return jsonify({"asientos": seat_codes, "asientos_ocupados": occupied})
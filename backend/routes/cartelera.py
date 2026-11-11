from flask import Blueprint, jsonify, request
from db import get_db

cartelera_bp = Blueprint('cartelera', __name__)

CONTENIDO_UI = {
    "cities": {
        "Bogotá": ["Andino", "Plaza Central", "Titán Plaza", "Santa Fe"],
        "Medellín": ["El Tesoro", "Oviedo", "Florida"],
        "Cali": ["Chipichape", "Unicentro", "Jardín Plaza"]
    },
    "formats": ["Todos", "2D", "3D", "IMAX", "4DX"],
    "slots": ["12:30", "15:10", "17:45", "20:20", "22:50"],
    "ticketPrices": {"default": 16000, "IMAX": 22000, "4DX": 25000, "3D": 19000},
    "soon": [
        {"title": "El Exorcista", "genre": "Terror / Suspenso", "tag": "Próximo estreno"},
        {"title": "The Whale", "genre": "Drama", "tag": "Preventa abierta"}
    ],
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
            SELECT p.IdPelicula, p.Titulo, p.Duracion, p.Clasificacion, ISNULL(g.Nombre, 'Acción') 
            FROM Peliculas p 
            LEFT JOIN Generos g ON p.IdGenero = g.IdGenero 
            WHERE p.IdEstado = 1
        """)
        films = []
        for r in cursor.fetchall():
            clean = str(r[1]).replace(" ", "")
            poster = f"/static/images/posters/{clean[0].lower() + clean[1:]}.png"
            films.append({
                "id": r[0], 
                "title": r[1], 
                "duration": f"{r[2]} min", 
                "rating": r[3], 
                "genre": r[4], 
                "format": "2D", 
                "poster": poster
            })

    resp = dict(CONTENIDO_UI)
    resp["films"] = films
    return jsonify(resp)

@cartelera_bp.route("/api/asientos-ocupados", methods=["GET"])
def asientos_ocupados():
    pelicula = request.args.get("pelicula", "").strip()
    funcion = request.args.get("funcion", "").strip()
    if not pelicula or not funcion:
        return jsonify({"error": "La película y la función son obligatorias."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT a.Fila, a.Numero
            FROM Funciones f
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Asientos a ON a.IdSala = f.IdSala
            INNER JOIN DetallesBoleta d ON d.IdAsiento = a.IdAsiento
            INNER JOIN Boletas b ON b.IdBoleta = d.IdBoleta AND b.IdFuncion = f.IdFuncion
            WHERE p.Titulo = ?
              AND CONVERT(VARCHAR(5), f.Hora, 108) = ?
              AND f.IdEstado = 1
              AND a.IdEstado = 1
              AND d.IdEstado = 1
              AND b.IdEstado = 1
        """, (pelicula, funcion))
        ocupados = [f"{fila}{numero}" for fila, numero in cursor.fetchall()]

    return jsonify({"asientos_ocupados": ocupados})
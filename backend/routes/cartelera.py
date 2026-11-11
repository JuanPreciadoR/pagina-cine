from flask import Blueprint, jsonify, request
from db import get_db

cartelera_bp = Blueprint('cartelera', __name__)

CONTENIDO_UI = {
    "cities": {"Bogotá": ["Andino", "Plaza Central"], "Medellín": ["El Tesoro"], "Cali": ["Chipichape"]},
    "formats": ["Todos", "2D", "3D", "IMAX"],
    "slots": ["12:30", "15:10", "17:45", "20:20"],
    "ticketPrices": {"default": 16000, "IMAX": 22000, "3D": 19000},
    "soon": [{"title": "El Exorcista", "genre": "Aventura", "tag": "Próximo estreno"}],
    "promos": [{"title": "Descuento Martes", "text": "2x1 en entradas."}],
    "faq": [{"q": "¿Cómo compro?", "a": "Selecciona la función y tus asientos."}]
}

@cartelera_bp.route("/api/contenido", methods=["GET"])
def contenido():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT p.IdPelicula, p.Titulo, p.Duracion, p.Clasificacion, ISNULL(g.Nombre, 'Acción') FROM Peliculas p LEFT JOIN Generos g ON p.IdGenero = g.IdGenero WHERE p.IdEstado = 1")
        films = []
        for r in cursor.fetchall():
            clean = str(r[1]).replace(" ", "")
            poster = f"/static/images/posters/{clean[0].lower() + clean[1:]}.png"
            films.append({"id": r[0], "title": r[1], "duration": f"{r[2]} min", "rating": r[3], "genre": r[4], "format": "2D", "poster": poster})

    resp = dict(CONTENIDO_UI)
    resp["films"] = films
    return jsonify(resp)
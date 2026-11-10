from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv
import json
import sqlite3
import os
import secrets

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=PROJECT_DIR / "frontend" / "static",
    template_folder=PROJECT_DIR / "frontend" / "templates",
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# --- CONEXIÓN MULTIPLATAFORMA (LINUX / WINDOWS) ---
db_env = os.environ.get("DATABASE_PATH", "backend/data/cinestar.db")
db_path = Path(db_env)
DB_PATH = db_path if db_path.is_absolute() else PROJECT_DIR / db_path
POSTER_DIR = PROJECT_DIR / "frontend" / "static" / "images" / "posters"
ALLOWED_POSTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# ============================================
# Base de Datos 
# ============================================
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as con:
        # Tabla usuarios con validaciones CHECK ampliadas a nuevos roles
        con.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL CHECK(length(nombre) > 0),
                email TEXT UNIQUE NOT NULL CHECK(email LIKE '%@%.%'),
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'cliente' CHECK(rol IN ('admin', 'cliente', 'cajero', 'gerente')),
                creado TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla compras con Foreign Key a usuarios (Cascade Delete)
        con.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                pelicula TEXT NOT NULL,
                funcion TEXT NOT NULL,
                asientos TEXT NOT NULL,
                total REAL NOT NULL CHECK(total >= 0),
                formato TEXT NOT NULL DEFAULT '2D',
                fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)
        
        con.execute("""
            CREATE TABLE IF NOT EXISTS contenido (
                seccion TEXT PRIMARY KEY,
                datos TEXT NOT NULL
            )
        """)
        con.execute("CREATE TABLE IF NOT EXISTS migraciones (nombre TEXT PRIMARY KEY)")

        # Migración de columna 'rol' si no existía
        columns = {row["name"] for row in con.execute("PRAGMA table_info(usuarios)")}
        if "rol" not in columns:
            con.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT NOT NULL DEFAULT 'cliente'")

        # Crear Admin por defecto si no hay administradores
        admin = con.execute("SELECT * FROM usuarios WHERE rol = 'admin'").fetchone()
        if not admin:
            con.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
                ("Administrador", "admin@cinestar.com", generate_password_hash("admin123"), "admin")
            )


@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def get_json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


# ============================================
# Rutas Frontend
# ============================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")


# ============================================
# Autenticación
# ============================================
@app.route("/api/registro", methods=["POST"])
def registro():
    data = get_json_object()
    if data is None:
        return jsonify({"error": "Objeto JSON inválido."}), 400
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({"error": "Escribe tu nombre."}), 400
    if not isinstance(email, str) or "@" not in email:
        return jsonify({"error": "Escribe un correo válido."}), 400
    if not isinstance(password, str) or len(password) < 6:
        return jsonify({"error": "La contraseña debe tener mínimo 6 caracteres."}), 400

    nombre = nombre.strip()
    email = email.strip().lower()
    with get_db() as con:
        try:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, 'cliente')",
                (nombre, email, generate_password_hash(password)),
            )
            user_id = cur.lastrowid
        except sqlite3.IntegrityError:
            return jsonify({"error": "Ya existe una cuenta con ese correo."}), 409

    session["user_id"] = user_id
    session["user_nombre"] = nombre
    session["user_email"] = email
    session["user_rol"] = "cliente"
    return jsonify({
        "status": "ok",
        "usuario": {"id": user_id, "nombre": nombre, "email": email, "rol": "cliente"}
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_object()
    if data is None:
        return jsonify({"error": "Objeto JSON inválido."}), 400
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Escribe tu correo y contraseña."}), 400
    email = email.strip().lower()

    with get_db() as con:
        row = con.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Correo o contraseña incorrectos."}), 401

    session["user_id"] = row["id"]
    session["user_nombre"] = row["nombre"]
    session["user_email"] = row["email"]
    session["user_rol"] = row["rol"]

    return jsonify({
        "status": "ok",
        "usuario": {"id": row["id"], "nombre": row["nombre"], "email": row["email"], "rol": row["rol"]}
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/sesion", methods=["GET"])
def sesion():
    if "user_id" not in session:
        return jsonify({"logueado": False})
    return jsonify({
        "logueado": True,
        "usuario": {
            "id": session["user_id"],
            "nombre": session.get("user_nombre", ""),
            "email": session.get("user_email", ""),
            "rol": session.get("user_rol", "cliente")
        }
    })


# ============================================
# Contenido y Asientos
# ============================================
CONTENIDO = {
    "cities": {
        "Bogotá": ["Andino", "Plaza Central", "Titán Plaza", "Santa Fe"],
        "Medellín": ["El Tesoro", "Oviedo", "Florida"],
        "Cali": ["Chipichape", "Unicentro", "Jardín Plaza"]
    },
    "formats": ["Todos", "2D", "3D", "IMAX", "4DX"],
    "slots": ["12:30", "15:10", "17:45", "20:20", "22:50"],
    "ticketPrices": {"default": 16000, "IMAX": 22000, "4DX": 25000, "3D": 19000},
    "films": [
        {"id": 1, "title": "Harry Potter", "genre": "Fantasía", "rating": "10+", "format": "2D", "duration": "2h 32m", "poster": "/static/images/posters/harryPotter.png"},
        {"id": 2, "title": "Cars", "genre": "Animación", "rating": "Todo público", "format": "2D", "duration": "1h 57m", "poster": "/static/images/posters/cars.png"},
        {"id": 3, "title": "Spiderman", "genre": "Acción", "rating": "12+", "format": "2D", "duration": "2h 01m", "poster": "/static/images/posters/spiderman.png"},
        {"id": 4, "title": "Toy Story", "genre": "Animación", "rating": "Todo público", "format": "2D", "duration": "1h 21m", "poster": "/static/images/posters/toyStory.png"}
    ],
    "soon": [
        {"title": "EL Exorcista", "genre": "Aventura", "tag": "Próximo estreno"},
        {"title": "The Whale", "genre": "Musical", "tag": "Preventa abierta"}
    ],
    "promos": [
        {"title": "Martes y miércoles de descuento", "text": "Entradas a precio especial en formatos 2D y 3D."},
        {"title": "Combos de CineStar", "text": "Descuentos en confitería al comprar desde la plataforma."}
    ],
    "faq": [
        {"q": "¿Cómo compro mis boletas?", "a": "Selecciona la película, la hora y tus asientos preferidos. Confirma tu compra desde el carrito."},
        {"q": "¿Cómo funciona el acceso al cine?", "a": "Presenta el comprobante digital o tu correo electrónico registrado al ingresar a la sala."}
    ]
}

def cargar_contenido():
    with get_db() as con:
        rows = con.execute("SELECT seccion, datos FROM contenido").fetchall()
    return {row["seccion"]: json.loads(row["datos"]) for row in rows}

def sembrar_contenido_inicial():
    with get_db() as con:
        count = con.execute("SELECT COUNT(*) FROM contenido").fetchone()[0]
        if count == 0:
            con.executemany(
                "INSERT INTO contenido (seccion, datos) VALUES (?, ?)",
                [(key, json.dumps(value, ensure_ascii=False)) for key, value in CONTENIDO.items()],
            )


def migrar_peliculas_de_ejemplo():
    migration_name = "cartelera_predeterminada_v1"
    peliculas_falsas = {
        "los hijos del páramo",
        "neón sur",
        "la casa de los mil pasos",
        "órbita 9",
        "sipderman",
    }
    with get_db() as con:
        if con.execute("SELECT 1 FROM migraciones WHERE nombre = ?", (migration_name,)).fetchone():
            return

        row = con.execute("SELECT datos FROM contenido WHERE seccion = 'films'").fetchone()
        if row:
            films = json.loads(row["datos"])
            if any(
                str(film.get("title", "")).strip().casefold() in peliculas_falsas
                for film in films
            ):
                con.execute(
                    "UPDATE contenido SET datos = ? WHERE seccion = 'films'",
                    (json.dumps(CONTENIDO["films"], ensure_ascii=False),),
                )

        con.execute("INSERT INTO migraciones (nombre) VALUES (?)", (migration_name,))


init_db()
sembrar_contenido_inicial()
migrar_peliculas_de_ejemplo()

@app.route("/api/contenido", methods=["GET"])
def contenido():
    return jsonify(cargar_contenido())

@app.route("/api/asientos-ocupados", methods=["GET"])
def asientos_ocupados():
    pelicula = request.args.get("pelicula")
    funcion = request.args.get("funcion")
    if not pelicula or not funcion:
        return jsonify({"asientos_ocupados": []})

    with get_db() as con:
        rows = con.execute("SELECT asientos FROM compras WHERE pelicula = ? AND funcion = ?", (pelicula, funcion)).fetchall()

    ocupados = []
    for r in rows:
        if r["asientos"]:
            ocupados.extend([a.strip() for a in r["asientos"].split(",") if a.strip()])
    return jsonify({"asientos_ocupados": ocupados})


# ============================================
# Compras
# ============================================
@app.route("/api/compra", methods=["POST"])
def crear_compra():
    if "user_id" not in session:
        return jsonify({"error": "Debes iniciar sesión para realizar la compra."}), 401

    data = get_json_object()
    if data is None:
        return jsonify({"error": "Datos inválidos."}), 400

    pelicula = data.get("pelicula")
    funcion = data.get("funcion")
    formato = data.get("formato", "2D")
    asientos_list = data.get("asientos", [])

    if not pelicula or not funcion or not asientos_list:
        return jsonify({"error": "Selecciona película, función y sillas."}), 400

    contenido_actual = cargar_contenido()
    precio_unitario = contenido_actual.get("ticketPrices", {}).get(formato, 16000)
    total = precio_unitario * len(asientos_list)
    asientos_str = ",".join(asientos_list)

    with get_db() as con:
        cur = con.execute(
            "INSERT INTO compras (usuario_id, pelicula, funcion, asientos, total, formato) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], pelicula, funcion, asientos_str, total, formato)
        )
        compra_id = cur.lastrowid

    return jsonify({
        "status": "ok",
        "compra_id": compra_id,
        "total": total,
        "asientos": asientos_list,
        "mensaje": f"¡Compra exitosa! Total: ${total:,.0f} COP".replace(",", "."),
    }), 201


# ============================================
# MÓDULO ADMINISTRATIVO (API Completa)
# ============================================
def es_admin():
    return session.get("user_rol") == "admin"

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as con:
        total_usuarios = con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        total_compras = con.execute("SELECT COUNT(*) FROM compras").fetchone()[0]
        total_recaudado = con.execute("SELECT SUM(total) FROM compras").fetchone()[0] or 0
        top_pelicula_row = con.execute(
            "SELECT pelicula, COUNT(*) as cant FROM compras GROUP BY pelicula ORDER BY cant DESC LIMIT 1"
        ).fetchone()
        top_pelicula = top_pelicula_row["pelicula"] if top_pelicula_row else "N/A"

    return jsonify({
        "total_usuarios": total_usuarios,
        "total_compras": total_compras,
        "total_boletas": total_compras,
        "total_recaudado": total_recaudado,
        "top_pelicula": top_pelicula
    })

@app.route("/api/admin/usuarios", methods=["GET"])
def admin_obtener_usuarios():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as con:
        rows = con.execute("SELECT id, nombre, email, rol, creado FROM usuarios ORDER BY id DESC").fetchall()
    return jsonify({"usuarios": [dict(r) for r in rows]})

@app.route("/api/admin/usuarios/cambiar-rol/<int:user_id>", methods=["POST"])
def admin_cambiar_rol(user_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    data = get_json_object()
    nuevo_rol = data.get("rol")
    roles_permitidos = ["admin", "cliente", "cajero", "gerente"]
    
    if nuevo_rol not in roles_permitidos:
        return jsonify({"error": "Rol no válido"}), 400

    with get_db() as con:
        con.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (nuevo_rol, user_id))
    return jsonify({"status": "ok", "mensaje": "Rol actualizado a " + nuevo_rol})

@app.route("/api/admin/usuarios/eliminar/<int:user_id>", methods=["DELETE"])
def admin_eliminar_usuario(user_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    if user_id == session.get("user_id"):
        return jsonify({"error": "No puedes eliminar tu propio usuario en sesión."}), 400

    try:
        with get_db() as con:
            con.execute("DELETE FROM compras WHERE usuario_id = ?", (user_id,))
            cur = con.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "El usuario no existe."}), 404
        return jsonify({"status": "ok", "mensaje": "Usuario y sus compras registradas han sido eliminados."})
    except sqlite3.IntegrityError as e:
        return jsonify({"error": f"Error de integridad: {str(e)}"}), 500

@app.route("/api/admin/ventas", methods=["GET"])
def admin_obtener_ventas():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as con:
        rows = con.execute("""
            SELECT c.id, u.nombre as cliente, u.email, c.pelicula, c.funcion, c.asientos, c.formato, c.total, c.fecha 
            FROM compras c
            JOIN usuarios u ON c.usuario_id = u.id
            ORDER BY c.id DESC
        """).fetchall()
    return jsonify({"ventas": [dict(r) for r in rows]})

@app.route("/api/admin/pelicula/agregar", methods=["POST"])
def admin_agregar_pelicula():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    data = request.form.to_dict() if request.mimetype == "multipart/form-data" else get_json_object()
    if not data or not data.get("title"):
        return jsonify({"error": "Datos de película incompletos"}), 400

    poster_file = request.files.get("poster")
    if poster_file and poster_file.filename:
        extension = Path(poster_file.filename).suffix.lower()
        if extension not in ALLOWED_POSTER_EXTENSIONS:
            return jsonify({"error": "Usa una imagen JPG, PNG o WebP."}), 400
        POSTER_DIR.mkdir(parents=True, exist_ok=True)
        poster_name = f"{secrets.token_hex(12)}{extension}"
        poster_file.save(POSTER_DIR / poster_name)
        data["poster"] = f"/static/images/posters/{poster_name}"
    else:
        data["poster"] = None

    contenido_actual = cargar_contenido()
    films = contenido_actual.get("films", [])
    nuevo_id = max([f.get("id", 0) for f in films], default=0) + 1
    data["id"] = nuevo_id
    films.append(data)

    with get_db() as con:
        con.execute("UPDATE contenido SET datos = ? WHERE seccion = 'films'", (json.dumps(films, ensure_ascii=False),))
    
    return jsonify({"status": "ok", "mensaje": "Película agregada a la cartelera"})

@app.route("/api/admin/pelicula/eliminar/<int:film_id>", methods=["DELETE"])
def admin_eliminar_pelicula(film_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    
    contenido_actual = cargar_contenido()
    films = contenido_actual.get("films", [])
    films_filtrados = [f for f in films if f.get("id") != film_id]
    
    with get_db() as con:
        con.execute("UPDATE contenido SET datos = ? WHERE seccion = 'films'", (json.dumps(films_filtrados, ensure_ascii=False),))
    return jsonify({"status": "ok", "mensaje": "Película eliminada"})


# ============================================
# Bloque de Arranque del Servidor
# ============================================
if __name__ == "__main__":
    print("Servidor CineStar iniciado en http://127.0.0.1:5000")
    app.run(
        debug=True,
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
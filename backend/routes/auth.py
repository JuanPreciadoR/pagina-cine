from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth_bp = Blueprint('auth', __name__)

def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

@auth_bp.route("/api/registro", methods=["POST"])
def registro():
    data = get_json()
    if not data:
        return jsonify({"error": "JSON inválido."}), 400

    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not nombre or "@" not in email or len(password) < 6:
        return jsonify({"error": "Datos inválidos o incompletos."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdUsuario FROM Usuarios WHERE Correo = ?", (email,))
        if cursor.fetchone():
            return jsonify({"error": "El correo ya existe."}), 409

        cursor.execute("INSERT INTO Usuarios (NombreUsuario, Clave, Correo, IdEstado) VALUES (?, ?, ?, 1)", 
                       (nombre, generate_password_hash(password), email))
        conn.commit()
        cursor.execute("SELECT IdUsuario FROM Usuarios WHERE Correo = ?", (email,))
        user_id = cursor.fetchone()[0]

    session.update({"user_id": user_id, "user_nombre": nombre, "user_email": email, "user_rol": "cliente"})
    return jsonify({"status": "ok", "usuario": {"id": user_id, "nombre": nombre, "email": email, "rol": "cliente"}}), 201

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = get_json()
    if not data:
        return jsonify({"error": "JSON inválido."}), 400

    email, password = data.get("email", "").strip().lower(), data.get("password", "")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.IdUsuario, u.NombreUsuario, u.Clave, u.Correo, ISNULL(r.Nombre, 'cliente')
            FROM Usuarios u
            LEFT JOIN UsuariosRoles ur ON u.IdUsuario = ur.IdUsuario
            LEFT JOIN Roles r ON ur.IdRol = r.IdRol
            WHERE u.Correo = ? OR u.NombreUsuario = ?
        """, (email, email))
        row = cursor.fetchone()

    if not row or not check_password_hash(row[2], password):
        return jsonify({"error": "Credenciales incorrectas."}), 401

    session.update({"user_id": row[0], "user_nombre": row[1], "user_email": row[3], "user_rol": str(row[4]).lower()})
    return jsonify({"status": "ok", "usuario": {"id": row[0], "nombre": row[1], "email": row[3], "rol": session["user_rol"]}})

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})

@auth_bp.route("/api/sesion", methods=["GET"])
def sesion():
    if "user_id" not in session:
        return jsonify({"logueado": False})
    return jsonify({"logueado": True, "usuario": {"id": session["user_id"], "nombre": session.get("user_nombre"), "email": session.get("user_email"), "rol": session.get("user_rol", "cliente")}})
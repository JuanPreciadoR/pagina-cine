import pyodbc
from flask import Blueprint, current_app, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from security import limiter

auth_bp = Blueprint('auth', __name__)

def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def verify_password(stored_password, password):
    return check_password_hash(stored_password, password)

def normalize_role(role):
    role = str(role or "cliente").strip().lower()
    return "admin" if role in {"admin", "administrador"} else role

def clear_auth_session():
    csrf_field = current_app.config.get("WTF_CSRF_FIELD_NAME", "csrf_token")
    csrf_token = session.get(csrf_field)
    session.clear()
    if csrf_token:
        session[csrf_field] = csrf_token

@auth_bp.route("/api/registro", methods=["POST"])
@limiter.limit("5 per hour")
def registro():
    data = get_json()
    if not data:
        return jsonify({"error": "JSON inválido."}), 400

    nombre = data.get("nombre", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not all(isinstance(value, str) for value in (nombre, email, password)):
        return jsonify({"error": "Datos inválidos o incompletos."}), 400

    nombre = nombre.strip()
    email = email.strip().lower()
    if not nombre or "@" not in email or len(password) < 6:
        return jsonify({"error": "Datos inválidos o incompletos."}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT IdUsuario FROM Usuarios WHERE Correo = ? OR NombreUsuario = ?",
                (email, nombre),
            )
            if cursor.fetchone():
                return jsonify({"error": "El correo o nombre de usuario ya existe."}), 409

            cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = ?", ("Activo",))
            state = cursor.fetchone()
            if state:
                state_id = state[0]
            else:
                cursor.execute(
                    "INSERT INTO Estados (Nombre, Descripcion) OUTPUT INSERTED.IdEstado VALUES (?, ?)",
                    ("Activo", "Registro activo dentro del sistema"),
                )
                state_id = cursor.fetchone()[0]

            cursor.execute("SELECT IdRol FROM Roles WHERE Nombre = ?", ("Cliente",))
            role = cursor.fetchone()
            if role:
                role_id = role[0]
            else:
                cursor.execute(
                    "INSERT INTO Roles (Nombre, Descripcion, IdEstado) "
                    "OUTPUT INSERTED.IdRol VALUES (?, ?, ?)",
                    ("Cliente", "Acceso de cliente", state_id),
                )
                role_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO Usuarios (NombreUsuario, Clave, Correo, IdEstado) "
                "OUTPUT INSERTED.IdUsuario VALUES (?, ?, ?, ?)",
                (nombre, generate_password_hash(password), email, state_id),
            )
            user_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO UsuariosRoles (IdUsuario, IdRol, IdEstado) VALUES (?, ?, ?)",
                (user_id, role_id, state_id),
            )
            conn.commit()
    except pyodbc.IntegrityError:
        return jsonify({"error": "El correo o nombre de usuario ya existe."}), 409

    session.permanent = True
    session.update({"user_id": user_id, "user_nombre": nombre, "user_email": email, "user_rol": "cliente"})
    return jsonify({"status": "ok", "usuario": {"id": user_id, "nombre": nombre, "email": email, "rol": "cliente"}}), 201

@auth_bp.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = get_json()
    if not data:
        return jsonify({"error": "JSON inválido."}), 400

    email, password = data.get("email", ""), data.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Credenciales incorrectas."}), 401
    email = email.strip().lower()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.IdUsuario, u.NombreUsuario, u.Clave, u.Correo,
                   CASE WHEN EXISTS (
                       SELECT 1
                       FROM UsuariosRoles ur
                       INNER JOIN Estados eur ON eur.IdEstado = ur.IdEstado AND eur.Nombre = 'Activo'
                       INNER JOIN Roles r ON r.IdRol = ur.IdRol
                       INNER JOIN Estados er ON er.IdEstado = r.IdEstado AND er.Nombre = 'Activo'
                       WHERE ur.IdUsuario = u.IdUsuario
                         AND LOWER(r.Nombre) IN ('admin', 'administrador')
                   ) THEN 'admin' ELSE 'cliente' END
            FROM Usuarios u
            WHERE (u.Correo = ? OR u.NombreUsuario = ?)
              AND u.IdEstado = (SELECT IdEstado FROM Estados WHERE Nombre = 'Activo')
        """, (email, email))
        row = cursor.fetchone()
        if row:
            password_ok = verify_password(row[2], password)

    if not row or not password_ok:
        return jsonify({"error": "Credenciales incorrectas."}), 401

    role = normalize_role(row[4])
    clear_auth_session()
    session.permanent = True
    session.update({"user_id": row[0], "user_nombre": row[1], "user_email": row[3], "user_rol": role})
    return jsonify({"status": "ok", "usuario": {"id": row[0], "nombre": row[1], "email": row[3], "rol": role}})

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    clear_auth_session()
    return jsonify({"status": "ok"})

@auth_bp.route("/api/sesion", methods=["GET"])
def sesion():
    if "user_id" not in session:
        return jsonify({"logueado": False})
    return jsonify({"logueado": True, "usuario": {"id": session["user_id"], "nombre": session.get("user_nombre"), "email": session.get("user_email"), "rol": session.get("user_rol", "cliente")}})
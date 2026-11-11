from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename
from db import get_db

admin_bp = Blueprint('admin', __name__)
POSTER_DIR = Path(__file__).resolve().parents[2] / "frontend" / "static" / "images" / "posters"
POSTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def es_admin():
    return session.get("user_rol") == "admin"

@admin_bp.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Usuarios u
            INNER JOIN Estados e ON e.IdEstado = u.IdEstado AND e.Nombre = 'Activo'
        """)
        total_usuarios = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), ISNULL(SUM(Cantidad), 0), ISNULL(SUM(Total), 0) FROM Boletas")
        boleta_data = cursor.fetchone()
        total_compras, total_boletas, total_recaudado = boleta_data[0], boleta_data[1], float(boleta_data[2])

        cursor.execute("""
            SELECT TOP 1 p.Titulo, SUM(b.Cantidad) as Cantidad
            FROM Boletas b
            INNER JOIN Funciones f ON b.IdFuncion = f.IdFuncion
            INNER JOIN Peliculas p ON f.IdPelicula = p.IdPelicula
            GROUP BY p.Titulo ORDER BY Cantidad DESC
        """)
        top_row = cursor.fetchone()
        top_pelicula = top_row[0] if top_row else "N/A"

    return jsonify({
        "total_usuarios": total_usuarios,
        "total_compras": total_compras,
        "total_boletas": total_boletas,
        "total_recaudado": total_recaudado,
        "top_pelicula": top_pelicula
    })

@admin_bp.route("/api/admin/usuarios", methods=["GET"])
def admin_obtener_usuarios():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.IdUsuario as id, u.NombreUsuario as nombre, u.Correo as email, 
                 CASE WHEN LOWER(ISNULL(r.Nombre, '')) IN ('admin', 'administrador')
                   THEN 'admin' ELSE 'cliente' END as rol,
                 CONVERT(VARCHAR, u.Fecha, 120) as creado
            FROM Usuarios u
             INNER JOIN Estados e ON e.IdEstado = u.IdEstado AND e.Nombre = 'Activo'
            LEFT JOIN UsuariosRoles ur ON u.IdUsuario = ur.IdUsuario
            LEFT JOIN Roles r ON ur.IdRol = r.IdRol
            ORDER BY u.IdUsuario DESC
        """)
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]

    return jsonify({"usuarios": [dict(zip(cols, row)) for row in rows]})

@admin_bp.route("/api/admin/ventas", methods=["GET"])
def admin_obtener_ventas():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.IdBoleta as id,
                   ISNULL(c.Nombre + ' ' + c.Apellido, 'Cliente') as cliente,
                   ISNULL(c.Correo, '') as email, p.Titulo as pelicula,
                   f.Formato as formato, CONVERT(VARCHAR(5), f.Hora, 108) as funcion,
                   ISNULL(STUFF((
                       SELECT ', ' + a.Fila + CAST(a.Numero AS VARCHAR(10))
                       FROM DetallesBoleta d
                       INNER JOIN Asientos a ON a.IdAsiento = d.IdAsiento
                       WHERE d.IdBoleta = b.IdBoleta
                       ORDER BY a.Fila, a.Numero
                       FOR XML PATH(''), TYPE
                   ).value('.', 'NVARCHAR(MAX)'), 1, 2, ''), '') as asientos,
                   b.Total as total, CONVERT(VARCHAR, b.FechaCompra, 120) as fecha
            FROM Boletas b
            INNER JOIN Funciones f ON b.IdFuncion = f.IdFuncion
            INNER JOIN Peliculas p ON f.IdPelicula = p.IdPelicula
            LEFT JOIN Clientes c ON b.IdCliente = c.IdCliente
            ORDER BY b.IdBoleta DESC
        """)
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]

    return jsonify({"ventas": [dict(zip(cols, row)) for row in rows]})


@admin_bp.route("/api/admin/usuarios/cambiar-rol/<int:user_id>", methods=["POST"])
def admin_cambiar_rol(user_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    if user_id == session.get("user_id"):
        return jsonify({"error": "No puedes cambiar tu propio rol."}), 409

    data = request.get_json(silent=True) or {}
    role_name = "Administrador" if data.get("rol") == "admin" else "Cliente" if data.get("rol") == "cliente" else None
    if not role_name:
        return jsonify({"error": "El rol indicado no es válido."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active_state = cursor.fetchone()[0]
        cursor.execute("""
            SELECT TOP 1 IdRol FROM Roles
            WHERE LOWER(Nombre) = LOWER(?) AND IdEstado = ?
        """, (role_name, active_state))
        role = cursor.fetchone()
        cursor.execute("SELECT IdUsuario FROM Usuarios WHERE IdUsuario = ? AND IdEstado = ?", (user_id, active_state))
        if not cursor.fetchone():
            return jsonify({"error": "El usuario no está disponible."}), 404
        if not role:
            return jsonify({"error": "El rol solicitado no existe."}), 404

        if role_name == "Cliente":
            cursor.execute("""
                SELECT COUNT(*) FROM UsuariosRoles ur
                INNER JOIN Roles r ON r.IdRol = ur.IdRol
                INNER JOIN Usuarios u ON u.IdUsuario = ur.IdUsuario AND u.IdEstado = ?
                WHERE LOWER(r.Nombre) IN ('admin', 'administrador')
            """, (active_state,))
            admin_count = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM UsuariosRoles ur
                INNER JOIN Roles r ON r.IdRol = ur.IdRol
                WHERE ur.IdUsuario = ? AND LOWER(r.Nombre) IN ('admin', 'administrador')
            """, (user_id,))
            if cursor.fetchone()[0] and admin_count <= 1:
                return jsonify({"error": "Debe permanecer al menos un administrador activo."}), 409

        cursor.execute("DELETE FROM UsuariosRoles WHERE IdUsuario = ?", (user_id,))
        cursor.execute(
            "INSERT INTO UsuariosRoles (IdUsuario, IdRol, IdEstado) VALUES (?, ?, ?)",
            (user_id, role[0], active_state),
        )
        conn.commit()
    return jsonify({"mensaje": "Rol actualizado."})


@admin_bp.route("/api/admin/usuarios/eliminar/<int:user_id>", methods=["DELETE"])
def admin_desactivar_usuario(user_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    if user_id == session.get("user_id"):
        return jsonify({"error": "No puedes desactivar tu propia cuenta."}), 409

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active_state = cursor.fetchone()[0]
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive_state = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM UsuariosRoles ur
            INNER JOIN Roles r ON r.IdRol = ur.IdRol
            INNER JOIN Usuarios u ON u.IdUsuario = ur.IdUsuario AND u.IdEstado = ?
            WHERE LOWER(r.Nombre) IN ('admin', 'administrador')
        """, (active_state,))
        admin_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM UsuariosRoles ur
            INNER JOIN Roles r ON r.IdRol = ur.IdRol
            WHERE ur.IdUsuario = ? AND LOWER(r.Nombre) IN ('admin', 'administrador')
        """, (user_id,))
        if cursor.fetchone()[0] and admin_count <= 1:
            return jsonify({"error": "Debe permanecer al menos un administrador activo."}), 409
        cursor.execute(
            "UPDATE Usuarios SET IdEstado = ? WHERE IdUsuario = ? AND IdEstado = ?",
            (inactive_state, user_id, active_state),
        )
        if not cursor.rowcount:
            return jsonify({"error": "El usuario no está disponible."}), 404
        conn.commit()
    return jsonify({"mensaje": "Usuario desactivado; sus datos y compras se conservaron."})


@admin_bp.route("/api/admin/pelicula/agregar", methods=["POST"])
def admin_agregar_pelicula():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    title = request.form.get("title", "").strip()
    genre_name = request.form.get("genre", "").strip()
    rating = request.form.get("rating", "").strip()
    try:
        duration = int(request.form.get("duration", ""))
    except ValueError:
        duration = 0
    if not title or not genre_name or not rating or duration < 1:
        return jsonify({"error": "Completa los datos de la película correctamente."}), 400

    upload = request.files.get("poster")
    poster_name = None
    poster_path = None
    if upload and upload.filename:
        extension = Path(secure_filename(upload.filename)).suffix.lower()
        if extension not in POSTER_EXTENSIONS:
            return jsonify({"error": "El póster debe ser JPG, PNG o WebP."}), 400
        poster_name = f"{uuid4().hex}{extension}"
        POSTER_DIR.mkdir(parents=True, exist_ok=True)
        poster_path = POSTER_DIR / poster_name
        upload.save(poster_path)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
            active_state = cursor.fetchone()[0]
            cursor.execute("SELECT IdPelicula FROM Peliculas WHERE LOWER(Titulo) = LOWER(?)", (title,))
            if cursor.fetchone():
                if poster_path:
                    poster_path.unlink(missing_ok=True)
                return jsonify({"error": "Ya existe una película con ese título."}), 409

            cursor.execute("SELECT TOP 1 IdCine FROM Cines WHERE IdEstado = ? ORDER BY IdCine", (active_state,))
            cinema = cursor.fetchone()
            if not cinema:
                if poster_path:
                    poster_path.unlink(missing_ok=True)
                return jsonify({"error": "Primero debe existir una sede activa."}), 409

            cursor.execute("SELECT IdGenero FROM Generos WHERE LOWER(Nombre) = LOWER(?)", (genre_name,))
            genre = cursor.fetchone()
            if genre:
                genre_id = genre[0]
            else:
                cursor.execute(
                    "INSERT INTO Generos (Nombre, Descripcion, IdEstado) OUTPUT INSERTED.IdGenero VALUES (?, ?, ?)",
                    (genre_name, f"Género {genre_name}", active_state),
                )
                genre_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO Peliculas
                    (IdGenero, IdCine, Titulo, Poster, Duracion, Clasificacion, FechaEstreno, IdEstado)
                OUTPUT INSERTED.IdPelicula
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?)
            """, (genre_id, cinema[0], title, poster_name, duration, rating, active_state))
            film_id = cursor.fetchone()[0]
            conn.commit()
    except Exception:
        if poster_path:
            poster_path.unlink(missing_ok=True)
        raise

    return jsonify({"mensaje": "Película guardada en la base de datos.", "id": film_id}), 201


@admin_bp.route("/api/admin/pelicula/eliminar/<int:film_id>", methods=["DELETE"])
def admin_desactivar_pelicula(film_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive_state = cursor.fetchone()[0]
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active_state = cursor.fetchone()[0]
        cursor.execute(
            "UPDATE Peliculas SET IdEstado = ? WHERE IdPelicula = ? AND IdEstado = ?",
            (inactive_state, film_id, active_state),
        )
        if not cursor.rowcount:
            return jsonify({"error": "La película no está disponible."}), 404
        conn.commit()
    return jsonify({"mensaje": "Película retirada de la cartelera; su historial se conservó."})
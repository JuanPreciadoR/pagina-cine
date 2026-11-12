from datetime import date, datetime
from math import isfinite
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


@admin_bp.route("/api/admin/operacion", methods=["GET"])
def admin_obtener_operacion():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    requested_date = request.args.get("fecha")
    try:
        selected_date = datetime.strptime(requested_date, "%Y-%m-%d").date() if requested_date else date.today()
    except ValueError:
        return jsonify({"error": "La fecha consultada no es válida."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.IdCine, c.Nombre, ISNULL(c.Ciudad, ''), c.Tipo, c.Documento,
                   e.Nombre
            FROM Cines c INNER JOIN Estados e ON e.IdEstado = c.IdEstado
            ORDER BY c.Ciudad, c.Nombre
        """)
        cinemas = [dict(zip(("id", "nombre", "ciudad", "tipo", "documento", "estado"), row))
                   for row in cursor.fetchall()]

        cursor.execute("""
            SELECT s.IdSala, s.IdCine, c.Nombre, ISNULL(c.Ciudad, ''), s.Nombre,
                   s.Capacidad, e.Nombre,
                   (SELECT COUNT(*) FROM Asientos a
                    INNER JOIN Estados ea ON ea.IdEstado = a.IdEstado AND ea.Nombre = 'Activo'
                    WHERE a.IdSala = s.IdSala)
            FROM Salas s
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados e ON e.IdEstado = s.IdEstado
            ORDER BY c.Nombre, s.Nombre
        """)
        rooms = [dict(zip(("id", "cinema_id", "cinema", "city", "nombre", "capacidad", "estado", "asientos"), row))
                 for row in cursor.fetchall()]

        cursor.execute("""
            SELECT IdPelicula, Titulo FROM Peliculas p
            INNER JOIN Estados e ON e.IdEstado = p.IdEstado AND e.Nombre = 'Activo'
            ORDER BY Titulo
        """)
        films = [{"id": row[0], "titulo": row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT f.IdFuncion, f.IdPelicula, p.Titulo, f.IdSala, s.Nombre,
                   c.Nombre, CONVERT(VARCHAR(10), f.FechaFuncion, 23),
                   CONVERT(VARCHAR(5), f.Hora, 108), f.Formato, CAST(f.Precio AS FLOAT), e.Nombre
            FROM Funciones f
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Salas s ON s.IdSala = f.IdSala
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados e ON e.IdEstado = f.IdEstado
            WHERE f.FechaFuncion >= ? AND f.FechaFuncion < DATEADD(DAY, 1, ?)
            ORDER BY f.FechaFuncion, f.Hora
        """, (selected_date, selected_date))
        shows = [dict(zip(("id", "film_id", "pelicula", "room_id", "sala", "sede", "fecha", "hora", "formato", "precio", "estado"), row))
                 for row in cursor.fetchall()]

    return jsonify({"sedes": cinemas, "salas": rooms, "peliculas": films, "funciones": shows})


@admin_bp.route("/api/admin/sedes", methods=["POST"])
def admin_crear_sede():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    data = request.get_json(silent=True) or {}
    name = str(data.get("nombre", "")).strip()
    city = str(data.get("ciudad", "")).strip()
    venue_type = str(data.get("tipo", "")).strip()
    document = str(data.get("documento", "")).strip()
    if not all((name, city, venue_type, document)):
        return jsonify({"error": "Completa el nombre, la ciudad, el tipo y el documento de la sede."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active = cursor.fetchone()
        if not active:
            return jsonify({"error": "No existe el estado Activo en el sistema."}), 409
        cursor.execute("""
            INSERT INTO Cines (Nombre, Ciudad, Tipo, Documento, EsExtranjero, IdEstado)
            OUTPUT INSERTED.IdCine VALUES (?, ?, ?, ?, 0, ?)
        """, (name, city, venue_type, document, active[0]))
        cinema_id = cursor.fetchone()[0]
        conn.commit()
    return jsonify({"mensaje": "Sede creada.", "id": cinema_id}), 201


@admin_bp.route("/api/admin/sedes/<int:cinema_id>", methods=["DELETE"])
def admin_desactivar_sede(cinema_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        if not inactive:
            return jsonify({"error": "No existe el estado Inactivo en el sistema."}), 409
        cursor.execute("UPDATE Cines SET IdEstado = ? WHERE IdCine = ? AND IdEstado <> ?",
                       (inactive[0], cinema_id, inactive[0]))
        if not cursor.rowcount:
            return jsonify({"error": "La sede no está disponible."}), 404
        conn.commit()
    return jsonify({"mensaje": "Sede desactivada; sus registros se conservaron."})


@admin_bp.route("/api/admin/salas", methods=["POST"])
def admin_crear_sala():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    data = request.get_json(silent=True) or {}
    name = str(data.get("nombre", "")).strip()
    try:
        cinema_id = int(data.get("sede_id"))
        rows = int(data.get("filas"))
        seats_per_row = int(data.get("asientos_por_fila"))
    except (TypeError, ValueError):
        return jsonify({"error": "Selecciona una sede y una capacidad de sala válida."}), 400
    if not name or not 1 <= rows <= 26 or not 1 <= seats_per_row <= 30:
        return jsonify({"error": "Indica el nombre y configura entre 1 y 26 filas, con 1 a 30 sillas por fila."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active = cursor.fetchone()
        if not active:
            return jsonify({"error": "No existe el estado Activo en el sistema."}), 409
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        cursor.execute("""
            SELECT 1 FROM Cines c INNER JOIN Estados e ON e.IdEstado = c.IdEstado AND e.Nombre = 'Activo'
            WHERE c.IdCine = ?
        """, (cinema_id,))
        if not cursor.fetchone():
            return jsonify({"error": "La sede seleccionada no está disponible."}), 404
        cursor.execute("SELECT TOP 1 IdTipoAsiento FROM TiposAsiento WHERE IdEstado = ? ORDER BY IdTipoAsiento", (active[0],))
        seat_type = cursor.fetchone()
        if not seat_type:
            return jsonify({"error": "No existe un tipo de asiento activo. Ejecuta la carga inicial del catálogo."}), 409
        capacity = rows * seats_per_row
        cursor.execute("""
            INSERT INTO Salas (IdCine, Nombre, Capacidad, IdEstado)
            OUTPUT INSERTED.IdSala VALUES (?, ?, ?, ?)
        """, (cinema_id, name, capacity, active[0]))
        room_id = cursor.fetchone()[0]
        for row_index in range(rows):
            row_label = chr(ord("A") + row_index)
            for number in range(1, seats_per_row + 1):
                cursor.execute("""
                    INSERT INTO Asientos (IdSala, IdTipoAsiento, Fila, Numero, IdEstado)
                    VALUES (?, ?, ?, ?, ?)
                """, (room_id, seat_type[0], row_label, number, active[0]))
        conn.commit()
    return jsonify({"mensaje": f"Sala creada con {capacity} sillas.", "id": room_id}), 201


@admin_bp.route("/api/admin/salas/<int:room_id>", methods=["DELETE"])
def admin_desactivar_sala(room_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        if not inactive:
            return jsonify({"error": "No existe el estado Inactivo en el sistema."}), 409
        cursor.execute("""
            SELECT COUNT(*) FROM Funciones f
            INNER JOIN Estados e ON e.IdEstado = f.IdEstado AND e.Nombre = 'Activo'
            WHERE f.IdSala = ? AND f.FechaFuncion >= CONVERT(DATE, GETDATE())
        """, (room_id,))
        if cursor.fetchone()[0]:
            return jsonify({"error": "Desactiva primero las funciones futuras de esta sala."}), 409
        cursor.execute("UPDATE Salas SET IdEstado = ? WHERE IdSala = ? AND IdEstado <> ?",
                       (inactive[0], room_id, inactive[0]))
        if not cursor.rowcount:
            return jsonify({"error": "La sala no está disponible."}), 404
        conn.commit()
    return jsonify({"mensaje": "Sala desactivada; sus sillas e historial se conservaron."})


@admin_bp.route("/api/admin/salas/<int:room_id>/asientos", methods=["GET", "POST"])
def admin_asientos_sala(room_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as conn:
        cursor = conn.cursor()
        if request.method == "GET":
            cursor.execute("""
                SELECT a.IdAsiento, a.Fila, a.Numero, t.Nombre, e.Nombre
                FROM Asientos a
                INNER JOIN TiposAsiento t ON t.IdTipoAsiento = a.IdTipoAsiento
                INNER JOIN Estados e ON e.IdEstado = a.IdEstado
                WHERE a.IdSala = ? ORDER BY a.Fila, a.Numero
            """, (room_id,))
            seats = [dict(zip(("id", "fila", "numero", "tipo", "estado"), row)) for row in cursor.fetchall()]
            return jsonify({"asientos": seats})

        data = request.get_json(silent=True) or {}
        row_label = str(data.get("fila", "")).strip().upper()
        try:
            number = int(data.get("numero"))
        except (TypeError, ValueError):
            return jsonify({"error": "Indica una fila y un número de silla válidos."}), 400
        if not row_label.isalpha() or len(row_label) > 2 or number < 1:
            return jsonify({"error": "Indica una fila de hasta dos letras y un número positivo."}), 400
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active = cursor.fetchone()
        if not active:
            return jsonify({"error": "No existe el estado Activo en el sistema."}), 409
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        cursor.execute("SELECT IdEstado FROM Salas WHERE IdSala = ?", (room_id,))
        room = cursor.fetchone()
        if not room or room[0] != active[0]:
            return jsonify({"error": "La sala no está disponible."}), 404
        cursor.execute("SELECT TOP 1 IdTipoAsiento FROM TiposAsiento WHERE IdEstado = ? ORDER BY IdTipoAsiento", (active[0],))
        seat_type = cursor.fetchone()
        if not seat_type:
            return jsonify({"error": "No existe un tipo de asiento activo."}), 409
        cursor.execute("SELECT 1 FROM Asientos WHERE IdSala = ? AND Fila = ? AND Numero = ?", (room_id, row_label, number))
        if cursor.fetchone():
            return jsonify({"error": "Ya existe una silla con esa fila y número en la sala."}), 409
        cursor.execute("""
            INSERT INTO Asientos (IdSala, IdTipoAsiento, Fila, Numero, IdEstado)
            OUTPUT INSERTED.IdAsiento VALUES (?, ?, ?, ?, ?)
        """, (room_id, seat_type[0], row_label, number, active[0]))
        seat_id = cursor.fetchone()[0]
        cursor.execute("UPDATE Salas SET Capacidad = Capacidad + 1 WHERE IdSala = ?", (room_id,))
        conn.commit()
    return jsonify({"mensaje": "Silla agregada.", "id": seat_id}), 201


@admin_bp.route("/api/admin/asientos/<int:seat_id>", methods=["DELETE"])
def admin_desactivar_asiento(seat_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        if not inactive:
            return jsonify({"error": "No existe el estado Inactivo en el sistema."}), 409
        cursor.execute("SELECT IdSala FROM Asientos WHERE IdAsiento = ? AND IdEstado <> ?", (seat_id, inactive[0]))
        seat = cursor.fetchone()
        if not seat:
            return jsonify({"error": "La silla no está disponible."}), 404
        cursor.execute("SELECT 1 FROM DetallesBoleta WHERE IdAsiento = ?", (seat_id,))
        if cursor.fetchone():
            return jsonify({"error": "Esta silla tiene compras asociadas y no se puede desactivar."}), 409
        cursor.execute("UPDATE Asientos SET IdEstado = ? WHERE IdAsiento = ?", (inactive[0], seat_id))
        cursor.execute("UPDATE Salas SET Capacidad = CASE WHEN Capacidad > 0 THEN Capacidad - 1 ELSE 0 END WHERE IdSala = ?", (seat[0],))
        conn.commit()
    return jsonify({"mensaje": "Silla desactivada."})


@admin_bp.route("/api/admin/funciones", methods=["POST"])
def admin_crear_funcion():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    data = request.get_json(silent=True) or {}
    try:
        film_id = int(data.get("pelicula_id"))
        room_id = int(data.get("sala_id"))
        show_date = datetime.strptime(str(data.get("fecha", "")), "%Y-%m-%d").date()
        show_time = datetime.strptime(str(data.get("hora", "")), "%H:%M").time()
        price = float(data.get("precio"))
    except (TypeError, ValueError):
        return jsonify({"error": "Completa película, sala, fecha, hora y precio correctamente."}), 400
    format_name = str(data.get("formato", "")).strip().upper()
    if not format_name or len(format_name) > 20 or not isfinite(price) or price < 0:
        return jsonify({"error": "El formato debe tener hasta 20 caracteres y el precio no puede ser negativo."}), 400
    if show_date < date.today():
        return jsonify({"error": "La fecha de la función no puede estar en el pasado."}), 400
    starts_at = datetime.combine(show_date, show_time)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'")
        active = cursor.fetchone()
        if not active:
            return jsonify({"error": "No existe el estado Activo en el sistema."}), 409
        cursor.execute("""
            SELECT p.Duracion FROM Peliculas p
            INNER JOIN Estados e ON e.IdEstado = p.IdEstado AND e.Nombre = 'Activo'
            WHERE p.IdPelicula = ?
        """, (film_id,))
        film = cursor.fetchone()
        cursor.execute("""
            SELECT 1 FROM Salas s
            INNER JOIN Estados e ON e.IdEstado = s.IdEstado AND e.Nombre = 'Activo'
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados ec ON ec.IdEstado = c.IdEstado AND ec.Nombre = 'Activo'
            WHERE s.IdSala = ?
        """, (room_id,))
        if not film or not cursor.fetchone():
            return jsonify({"error": "Selecciona una película y una sala activas."}), 404
        cursor.execute("""
            SELECT COUNT(*) FROM Funciones f
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Estados e ON e.IdEstado = f.IdEstado AND e.Nombre = 'Activo'
            WHERE f.IdSala = ? AND f.FechaFuncion = ?
              AND CAST(? AS DATETIME) < DATEADD(MINUTE, p.Duracion,
                    DATEADD(SECOND, DATEDIFF(SECOND, 0, f.Hora), CAST(f.FechaFuncion AS DATETIME)))
              AND DATEADD(MINUTE, ?, CAST(? AS DATETIME)) >
                    DATEADD(SECOND, DATEDIFF(SECOND, 0, f.Hora), CAST(f.FechaFuncion AS DATETIME))
        """, (room_id, datetime.combine(show_date, datetime.min.time()), starts_at, film[0], starts_at))
        if cursor.fetchone()[0]:
            return jsonify({"error": "La sala ya tiene una función en ese horario."}), 409
        cursor.execute("""
            INSERT INTO Funciones (IdPelicula, IdSala, FechaFuncion, Hora, Formato, Precio, IdEstado)
            OUTPUT INSERTED.IdFuncion VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (film_id, room_id, datetime.combine(show_date, datetime.min.time()), show_time, format_name, price, active[0]))
        function_id = cursor.fetchone()[0]
        conn.commit()
    return jsonify({"mensaje": "Función programada.", "id": function_id}), 201


@admin_bp.route("/api/admin/funciones/<int:function_id>", methods=["DELETE"])
def admin_desactivar_funcion(function_id):
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = 'Inactivo'")
        inactive = cursor.fetchone()
        if not inactive:
            return jsonify({"error": "No existe el estado Inactivo en el sistema."}), 409
        cursor.execute("UPDATE Funciones SET IdEstado = ? WHERE IdFuncion = ? AND IdEstado <> ?",
                       (inactive[0], function_id, inactive[0]))
        if not cursor.rowcount:
            return jsonify({"error": "La función no está disponible."}), 404
        conn.commit()
    return jsonify({"mensaje": "Función cancelada; las boletas históricas se conservaron."})
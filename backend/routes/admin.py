from flask import Blueprint, jsonify, request, session
from db import get_db

admin_bp = Blueprint('admin', __name__)

def es_admin():
    return session.get("user_rol") == "admin"

@admin_bp.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not es_admin():
        return jsonify({"error": "Acceso denegado"}), 403

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Usuarios")
        total_usuarios = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), ISNULL(SUM(Total), 0) FROM Boletas")
        boleta_data = cursor.fetchone()
        total_compras, total_recaudado = boleta_data[0], float(boleta_data[1])

        cursor.execute("""
            SELECT TOP 1 p.Titulo, COUNT(b.IdBoleta) as Cantidad
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
        "total_boletas": total_compras,
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
                   ISNULL(r.Nombre, 'cliente') as rol, CONVERT(VARCHAR, u.Fecha, 120) as creado 
            FROM Usuarios u
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
            SELECT b.IdBoleta as id, ISNULL(c.Nombre, 'Cliente') as cliente, 
                   ISNULL(c.Correo, 'c@cinestar.com') as email, p.Titulo as pelicula, 
                   '2D' as formato, '18:00' as funcion, 'A1, A2' as asientos, 
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
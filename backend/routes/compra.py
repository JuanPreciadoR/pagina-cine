import re

from flask import Blueprint, jsonify, request, session
from db import get_db
from security import limiter


compra_bp = Blueprint("compra", __name__)
SEAT_CODE = re.compile(r"^[A-Z]{1,2}[1-9][0-9]*$")


@compra_bp.route("/api/compra", methods=["POST"])
@limiter.limit("10 per minute")
def comprar():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Inicia sesión para completar tu compra."}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "La solicitud no tiene un formato válido."}), 400

    try:
        function_id = int(data.get("function_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "La función indicada no es válida."}), 400

    seats = data.get("seats")
    payment_type = data.get("payment_type")
    if (
        not isinstance(seats, list)
        or not seats
        or any(not isinstance(seat, str) or not SEAT_CODE.fullmatch(seat) for seat in seats)
        or len(set(seats)) != len(seats)
        or not isinstance(payment_type, str)
    ):
        return jsonify({"error": "Selecciona sillas y una forma de pago válidas."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cursor.execute("""
            SELECT f.IdSala, f.Precio
            FROM Funciones f WITH (UPDLOCK, HOLDLOCK)
            INNER JOIN Estados e ON e.IdEstado = f.IdEstado AND e.Nombre = 'Activo'
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Estados ep ON ep.IdEstado = p.IdEstado AND ep.Nombre = 'Activo'
            INNER JOIN Salas s ON s.IdSala = f.IdSala
            INNER JOIN Estados es ON es.IdEstado = s.IdEstado AND es.Nombre = 'Activo'
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN Estados ec ON ec.IdEstado = c.IdEstado AND ec.Nombre = 'Activo'
                        WHERE f.IdFuncion = ?
                            AND f.FechaFuncion >= CONVERT(DATE, GETDATE())
                            AND f.FechaFuncion < DATEADD(DAY, 1, CONVERT(DATE, GETDATE()))
        """, (function_id,))
        show = cursor.fetchone()
        if not show:
            return jsonify({"error": "La función ya no está disponible."}), 404

        cursor.execute("""
            SELECT a.IdAsiento, a.Fila, a.Numero
            FROM Asientos a WITH (UPDLOCK, HOLDLOCK)
            INNER JOIN Estados e ON e.IdEstado = a.IdEstado AND e.Nombre = 'Activo'
            WHERE a.IdSala = ?
        """, (show[0],))
        available_seats = {f"{row[1]}{row[2]}": row[0] for row in cursor.fetchall()}
        if any(seat not in available_seats for seat in seats):
            return jsonify({"error": "Una o más sillas no pertenecen a esta sala."}), 400

        cursor.execute("""
            SELECT d.IdAsiento
            FROM DetallesBoleta d WITH (UPDLOCK, HOLDLOCK)
            INNER JOIN Boletas b ON b.IdBoleta = d.IdBoleta
            INNER JOIN Estados ed ON ed.IdEstado = d.IdEstado AND ed.Nombre = 'Activo'
            INNER JOIN Estados eb ON eb.IdEstado = b.IdEstado AND eb.Nombre = 'Activo'
            WHERE b.IdFuncion = ?
        """, (function_id,))
        occupied = {row[0] for row in cursor.fetchall()}
        if any(available_seats[seat] in occupied for seat in seats):
            return jsonify({"error": "Una o más sillas ya fueron ocupadas. Actualiza la disponibilidad."}), 409

        cursor.execute("""
            SELECT IdTipoPago FROM TiposPago t
            INNER JOIN Estados e ON e.IdEstado = t.IdEstado AND e.Nombre = 'Activo'
            WHERE t.Nombre = ?
        """, (payment_type,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({"error": "La forma de pago seleccionada no está disponible."}), 400

        cursor.execute("""
            SELECT u.NombreUsuario, u.Correo
            FROM Usuarios u
            INNER JOIN Estados e ON e.IdEstado = u.IdEstado AND e.Nombre = 'Activo'
            WHERE u.IdUsuario = ?
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "La cuenta no está disponible."}), 401

        customer_document = f"USR-{user_id}"
        cursor.execute("SELECT IdCliente FROM Clientes WHERE Documento = ?", (customer_document,))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer[0]
        else:
            name_parts = user[0].strip().split(maxsplit=1)
            first_name = name_parts[0] if name_parts else "Cliente"
            last_name = name_parts[1] if len(name_parts) > 1 else "CineStar"
            cursor.execute("""
                INSERT INTO Clientes (Tipo, Documento, Nombre, Apellido, EsExtranjero, Correo, IdEstado)
                OUTPUT INSERTED.IdCliente
                VALUES ('Usuario', ?, ?, ?, 0, ?,
                    (SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'))
            """, (customer_document, first_name, last_name, user[1]))
            customer_id = cursor.fetchone()[0]

        total = show[1] * len(seats)
        cursor.execute("""
            INSERT INTO Boletas (IdCliente, IdFuncion, IdTipoPago, Cantidad, Total, IdEstado)
            OUTPUT INSERTED.IdBoleta
            VALUES (?, ?, ?, ?, ?, (SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'))
        """, (customer_id, function_id, payment[0], len(seats), total))
        ticket_id = cursor.fetchone()[0]
        for seat in seats:
            cursor.execute("""
                INSERT INTO DetallesBoleta (IdBoleta, IdAsiento, Precio, IdEstado)
                VALUES (?, ?, ?, (SELECT IdEstado FROM Estados WHERE Nombre = 'Activo'))
            """, (ticket_id, available_seats[seat], show[1]))
        conn.commit()

    return jsonify({"status": "ok", "boleta": ticket_id, "total": float(total)}), 201


@compra_bp.route("/api/mis-compras", methods=["GET"])
@limiter.limit("60 per minute")
def mis_compras():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Inicia sesión para consultar tus boletas."}), 401

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.IdBoleta, CONVERT(VARCHAR(16), b.FechaCompra, 120), eb.Nombre,
                   p.Titulo, c.Nombre, ISNULL(c.Ciudad, ''),
                   CONVERT(VARCHAR(10), f.FechaFuncion, 23),
                   CONVERT(VARCHAR(5), f.Hora, 108), f.Formato, b.Cantidad,
                   CAST(b.Total AS FLOAT), tp.Nombre, a.Fila, a.Numero
            FROM Boletas b
            INNER JOIN Clientes cl ON cl.IdCliente = b.IdCliente
            INNER JOIN Estados eb ON eb.IdEstado = b.IdEstado
            INNER JOIN Funciones f ON f.IdFuncion = b.IdFuncion
            INNER JOIN Peliculas p ON p.IdPelicula = f.IdPelicula
            INNER JOIN Salas s ON s.IdSala = f.IdSala
            INNER JOIN Cines c ON c.IdCine = s.IdCine
            INNER JOIN TiposPago tp ON tp.IdTipoPago = b.IdTipoPago
            LEFT JOIN DetallesBoleta d ON d.IdBoleta = b.IdBoleta
            LEFT JOIN Asientos a ON a.IdAsiento = d.IdAsiento
            WHERE cl.Documento = ?
            ORDER BY b.FechaCompra DESC, b.IdBoleta DESC, a.Fila, a.Numero
        """, (f"USR-{user_id}",))
        rows = cursor.fetchall()

    purchases = {}
    for row in rows:
        purchase = purchases.setdefault(row[0], {
            "id": row[0],
            "comprada": row[1],
            "estado": row[2],
            "pelicula": row[3],
            "sede": row[4],
            "ciudad": row[5],
            "fecha": row[6],
            "hora": row[7],
            "formato": row[8],
            "cantidad": row[9],
            "total": row[10],
            "pago": row[11],
            "asientos": [],
        })
        if row[12] is not None:
            purchase["asientos"].append(f"{row[12]}{row[13]}")

    return jsonify({"compras": list(purchases.values())})
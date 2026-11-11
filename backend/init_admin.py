import os

from db import get_db
from werkzeug.security import generate_password_hash

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@cinestar.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_INITIAL_PASSWORD", "admin123")


def get_or_create_state(cursor):
    cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = ?", ("Activo",))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO Estados (Nombre, Descripcion) OUTPUT INSERTED.IdEstado VALUES (?, ?)",
        ("Activo", "Registro activo dentro del sistema"),
    )
    return cursor.fetchone()[0]


def get_or_create_role(cursor, name, description, state_id):
    cursor.execute("SELECT IdRol FROM Roles WHERE Nombre = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO Roles (Nombre, Descripcion, IdEstado) "
        "OUTPUT INSERTED.IdRol VALUES (?, ?, ?)",
        (name, description, state_id),
    )
    return cursor.fetchone()[0]


def create_admin():
    with get_db() as conn:
        cursor = conn.cursor()
        state_id = get_or_create_state(cursor)
        admin_role_id = get_or_create_role(
            cursor, "Administrador", "Acceso completo al sistema", state_id
        )
        get_or_create_role(cursor, "Cliente", "Acceso de cliente", state_id)

        cursor.execute(
            "SELECT IdUsuario FROM Usuarios WHERE NombreUsuario = ? OR Correo = ?",
            (ADMIN_USERNAME, ADMIN_EMAIL),
        )
        rows = cursor.fetchall()
        if len(rows) > 1:
            raise RuntimeError("Hay cuentas distintas que usan el nombre o correo reservado para admin.")
        row = rows[0] if rows else None
        if row:
            user_id = row[0]
            cursor.execute(
                "UPDATE Usuarios SET Clave = ?, Correo = ?, IdEstado = ? WHERE IdUsuario = ?",
                (generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL, state_id, user_id),
            )
            cursor.execute("DELETE FROM UsuariosRoles WHERE IdUsuario = ?", (user_id,))
        else:
            cursor.execute(
                "INSERT INTO Usuarios (NombreUsuario, Clave, Correo, IdEstado) "
                "OUTPUT INSERTED.IdUsuario VALUES (?, ?, ?, ?)",
                (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL, state_id),
            )
            user_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO UsuariosRoles (IdUsuario, IdRol, IdEstado) VALUES (?, ?, ?)",
            (user_id, admin_role_id, state_id),
        )
        conn.commit()

    return ADMIN_PASSWORD


if __name__ == "__main__":
    admin_password = create_admin()
    print(f"Usuario admin: {ADMIN_USERNAME}")
    print(f"Correo admin: {ADMIN_EMAIL}")
    print(f"Contraseña nueva: {admin_password}")
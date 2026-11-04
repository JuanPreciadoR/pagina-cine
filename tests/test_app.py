import os
import tempfile
import unittest
from pathlib import Path


_database_dir = tempfile.TemporaryDirectory()
_database_path = Path(_database_dir.name) / "test.db"
_previous_database_path = os.environ.get("DATABASE_PATH")
os.environ["DATABASE_PATH"] = str(_database_path)

from backend import app as backend  # noqa: E402

if _previous_database_path is None:
    os.environ.pop("DATABASE_PATH", None)
else:
    os.environ["DATABASE_PATH"] = _previous_database_path


class CineStarApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend.DB_PATH = _database_path

    def setUp(self):
        with backend.get_db() as con:
            con.execute("DELETE FROM compras")
            con.execute("DELETE FROM usuarios")
            con.execute("DELETE FROM contenido")
        backend.init_db()
        backend.sembrar_contenido_inicial()
        self.client = backend.app.test_client()

    @classmethod
    def tearDownClass(cls):
        _database_dir.cleanup()

    def login_admin(self, client=None):
        client = client or self.client
        response = client.post(
            "/api/login",
            json={"email": "admin@cinestar.com", "password": "admin123"},
        )
        self.assertEqual(response.status_code, 200)

    def register_customer(self, client=None, email="cliente@example.com"):
        client = client or self.client
        return client.post(
            "/api/registro",
            json={"nombre": "Cliente de prueba", "email": email, "password": "secreto123"},
        )

    def test_public_pages_and_content_api(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        for path in (
            "/static/js/script.js",
            "/static/js/login.js",
            "/static/css/style.css",
            "/static/images/favicon.ico",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()
        response = self.client.get("/api/contenido")
        self.assertEqual(response.status_code, 200)
        self.assertIn("films", response.get_json())
        self.assertEqual(self.client.get("/api/sesion").get_json(), {"logueado": False})

    def test_registration_login_and_logout(self):
        response = self.register_customer()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.client.get("/api/sesion").get_json()["logueado"])
        self.assertEqual(
            self.register_customer(email="mal-correo").status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/registro",
                json={"nombre": "Otro", "email": "cliente@example.com", "password": "secreto123"},
            ).status_code,
            409,
        )
        self.assertEqual(self.client.post("/api/logout").status_code, 200)
        self.assertFalse(self.client.get("/api/sesion").get_json()["logueado"])

    def test_purchase_validates_and_reserves_seats(self):
        payload = {
            "pelicula": "Los Hijos del Páramo",
            "funcion": "12:30",
            "formato": "2D",
            "asientos": ["A1", "A2"],
        }
        self.assertEqual(self.client.post("/api/compra", json=payload).status_code, 401)
        self.login_admin()

        response = self.client.post("/api/compra", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["total"], 32000)
        self.assertEqual(self.client.get("/api/admin/stats").get_json()["total_boletas"], 2)
        self.assertEqual(
            self.client.get(
                "/api/asientos-ocupados",
                query_string={"pelicula": payload["pelicula"], "funcion": payload["funcion"]},
            ).get_json()["asientos_ocupados"],
            ["A1", "A2"],
        )
        self.assertEqual(self.client.post("/api/compra", json=payload).status_code, 409)

        invalid = {**payload, "asientos": ["Z9"]}
        self.assertEqual(self.client.post("/api/compra", json=invalid).status_code, 400)
        invalid = {**payload, "asientos": ["A1", "A1"]}
        self.assertEqual(self.client.post("/api/compra", json=invalid).status_code, 400)
        self.assertEqual(self.client.get("/api/asientos-ocupados").status_code, 400)

    def test_admin_authorization_and_input_validation(self):
        self.assertEqual(self.client.get("/api/admin/stats").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/usuarios").status_code, 403)
        self.assertEqual(self.client.get("/admin").status_code, 200)
        self.login_admin()
        with backend.get_db() as con:
            admin_id = con.execute(
                "SELECT id FROM usuarios WHERE email = ?",
                ("admin@cinestar.com",),
            ).fetchone()["id"]

        self.assertEqual(
            self.client.post(
                f"/api/admin/usuarios/cambiar-rol/{admin_id}",
                data="invalid",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                f"/api/admin/usuarios/cambiar-rol/{admin_id}",
                json={"rol": "cliente"},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/admin/pelicula/agregar",
                json={"title": "Incompleta"},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete("/api/admin/pelicula/eliminar/999").status_code,
            404,
        )

        response = self.client.post(
            "/api/admin/pelicula/agregar",
            json={"title": "Nueva", "genre": "Drama", "format": "2D", "duration": "90 min"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/admin/ventas").status_code, 200)

    def test_role_changes_are_checked_against_database(self):
        self.login_admin()
        with backend.get_db() as con:
            admin_id = con.execute(
                "SELECT id FROM usuarios WHERE email = ?",
                ("admin@cinestar.com",),
            ).fetchone()["id"]
        response = self.register_customer(email="admin-viejo@example.com")
        customer_id = response.get_json()["usuario"]["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = admin_id
            session["user_rol"] = "admin"

        self.assertEqual(
            self.client.post(
                f"/api/admin/usuarios/cambiar-rol/{customer_id}",
                json={"rol": "admin"},
            ).status_code,
            200,
        )
        former_admin = backend.app.test_client()
        with former_admin.session_transaction() as session:
            session["user_id"] = customer_id
            session["user_rol"] = "admin"
        self.assertEqual(former_admin.get("/api/admin/stats").status_code, 200)

        self.assertEqual(
            self.client.post(
                f"/api/admin/usuarios/cambiar-rol/{customer_id}",
                json={"rol": "cliente"},
            ).status_code,
            200,
        )
        self.assertEqual(former_admin.get("/api/admin/stats").status_code, 403)


if __name__ == "__main__":
    unittest.main()

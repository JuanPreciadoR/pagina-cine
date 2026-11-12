import re

import pytest

from app import create_app
from routes import compra


def csrf_token(client):
    response = client.get("/")
    match = re.search(rb'name="csrf-token" content="([^"]+)"', response.data)
    assert match
    return match.group(1).decode()


def test_mutating_api_requires_csrf_token(client):
    response = client.post("/api/logout", json={})

    assert response.status_code == 400
    assert response.is_json


def test_csrf_token_remains_valid_after_logout(client):
    token = csrf_token(client)
    headers = {"X-CSRFToken": token}

    assert client.post("/api/logout", json={}, headers=headers).status_code == 200
    assert client.post("/api/logout", json={}, headers=headers).status_code == 200


def test_login_rate_limit_returns_json(client):
    token = csrf_token(client)
    headers = {"X-CSRFToken": token}

    for _ in range(5):
        response = client.post("/api/login", json={}, headers=headers)
        assert response.status_code == 400

    limited = client.post("/api/login", json={}, headers=headers)
    assert limited.status_code == 429
    assert limited.json["error"]


def test_purchase_rate_limit_runs_before_database_access(client):
    token = csrf_token(client)
    headers = {"X-CSRFToken": token}

    for _ in range(10):
        response = client.post("/api/compra", json={}, headers=headers)
        assert response.status_code == 401

    limited = client.post("/api/compra", json={}, headers=headers)
    assert limited.status_code == 429


def test_production_requires_secret_and_shared_rate_limit_storage():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({
            "APP_ENV": "production",
            "SECRET_KEY": None,
            "RATELIMIT_STORAGE_URI": "redis://localhost",
        })

    with pytest.raises(RuntimeError, match="Redis"):
        create_app({"APP_ENV": "production", "SECRET_KEY": "production-secret"})

    app = create_app({
        "APP_ENV": "production",
        "SECRET_KEY": "production-secret",
        "RATELIMIT_STORAGE_URI": "redis://localhost",
    })
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_purchase_history_requires_login(client):
    response = client.get("/api/mis-compras")

    assert response.status_code == 401
    assert response.json["error"]


def test_customer_page_redirects_without_login(client):
    response = client.get("/mis-compras")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_customer_page_renders_for_logged_in_user(client):
    with client.session_transaction() as browser_session:
        browser_session["user_id"] = 42

    response = client.get("/mis-compras")

    assert response.status_code == 200
    assert b"Historial de compras" in response.data


def test_purchase_history_is_scoped_and_groups_seats(client, monkeypatch):
    rows = [
        (17, "2026-11-12 18:20", "Activo", "Dune", "Cine Centro", "Bogotá",
         "2026-11-12", "19:00", "2D", 2, 30000.0, "Tarjeta", "A", 1),
        (17, "2026-11-12 18:20", "Activo", "Dune", "Cine Centro", "Bogotá",
         "2026-11-12", "19:00", "2D", 2, 30000.0, "Tarjeta", "A", 2),
    ]

    class FakeCursor:
        parameters = None

        def execute(self, query, parameters):
            self.parameters = parameters

        def fetchall(self):
            return rows

    cursor = FakeCursor()

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def cursor(self):
            return cursor

    monkeypatch.setattr(compra, "get_db", FakeConnection)
    with client.session_transaction() as browser_session:
        browser_session["user_id"] = 42

    response = client.get("/api/mis-compras")

    assert response.status_code == 200
    assert cursor.parameters == ("USR-42",)
    assert response.json["compras"] == [{
        "id": 17,
        "comprada": "2026-11-12 18:20",
        "estado": "Activo",
        "pelicula": "Dune",
        "sede": "Cine Centro",
        "ciudad": "Bogotá",
        "fecha": "2026-11-12",
        "hora": "19:00",
        "formato": "2D",
        "cantidad": 2,
        "total": 30000.0,
        "pago": "Tarjeta",
        "asientos": ["A1", "A2"],
    }]
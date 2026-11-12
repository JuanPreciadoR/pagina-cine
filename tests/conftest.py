import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


@pytest.fixture
def app():
    return create_app({
        "APP_ENV": "testing",
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "RATELIMIT_STORAGE_URI": "memory://",
    })


@pytest.fixture
def client(app):
    return app.test_client()
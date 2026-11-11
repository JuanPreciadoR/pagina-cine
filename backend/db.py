import os
import pyodbc
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

@contextmanager
def get_db():
    """Abre una conexión a SQL Server configurada mediante variables de entorno."""
    required = ("DB_SERVER", "DB_NAME", "DB_USER", "DB_PASS")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Faltan variables de configuración SQL Server: {', '.join(missing)}")

    server = os.environ["DB_SERVER"]
    port = os.environ.get("DB_PORT", "1433")
    database = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASS"]
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()
            
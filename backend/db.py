import os
import sqlite3
import pyodbc
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

DB_ENGINE = os.environ.get("DB_ENGINE", "mssql").lower()

@contextmanager
def get_db():
    """Conector híbrido: detecta dinámicamente si se conecta a SQL Server o a SQLite."""
    if DB_ENGINE == "mssql":
        server = os.environ.get("DB_SERVER", "127.0.0.1")
        port = os.environ.get("DB_PORT", "1433")
        database = os.environ.get("DB_NAME", "CineDB")
        user = os.environ.get("DB_USER", "sa")
        password = os.environ.get("DB_PASS", "Passwordsql123!")

        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=5;"
        )
        conn = pyodbc.connect(conn_str)
        try:
            yield conn
        finally:
            conn.close()
    else:
        db_env = os.environ.get("DATABASE_PATH", "backend/data/cinestar.db")
        db_path = Path(db_env)
        DB_PATH = db_path if db_path.is_absolute() else PROJECT_DIR / db_path
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        con = sqlite3.connect(DB_PATH, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            with con:
                yield con
        finally:
            con.close()
            
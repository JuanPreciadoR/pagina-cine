import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template

from routes.auth import auth_bp
from routes.cartelera import cartelera_bp
from routes.admin import admin_bp

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=PROJECT_DIR / "frontend" / "static",
    template_folder=PROJECT_DIR / "frontend" / "templates",
)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Registro de Módulos (Blueprints)
app.register_blueprint(auth_bp)
app.register_blueprint(cartelera_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, host=host, port=port)
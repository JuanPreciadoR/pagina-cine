import os
import secrets
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

from routes.auth import auth_bp
from routes.cartelera import cartelera_bp
from routes.admin import admin_bp
from routes.compra import compra_bp
from security import csrf, limiter

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

def create_app(test_config=None):
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder=PROJECT_DIR / "frontend" / "static",
        template_folder=PROJECT_DIR / "frontend" / "templates",
    )
    app_env = os.environ.get("APP_ENV", "development").lower()
    app.config.from_mapping(
        APP_ENV=app_env,
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        SEND_FILE_MAX_AGE_DEFAULT=3600,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=app_env == "production",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        RATELIMIT_HEADERS_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)

    if app.config["APP_ENV"] == "production":
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY es obligatoria en producción.")
        if not str(app.config["RATELIMIT_STORAGE_URI"]).startswith(("redis://", "rediss://")):
            raise RuntimeError("Configura RATELIMIT_STORAGE_URI con Redis en producción.")
    elif not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)

    app.config["SESSION_COOKIE_SECURE"] = app.config["APP_ENV"] == "production"
    if app.config["APP_ENV"] == "production":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.after_request
    def add_cache_headers(response):
        if request.path.startswith("/static/") and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=3600"
        else:
            response.headers["Cache-Control"] = "no-store"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if app.config["APP_ENV"] == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "La solicitud expiró o no es válida. Recarga la página e inténtalo de nuevo."}), 400
        return error.description, 400

    @app.errorhandler(429)
    def handle_rate_limit(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Demasiadas solicitudes. Espera un momento e inténtalo de nuevo."}), 429
        return error.description, 429

    app.register_blueprint(auth_bp)
    app.register_blueprint(cartelera_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(compra_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/admin")
    def admin_page():
        return render_template("admin.html")

    @app.route("/mis-compras")
    def purchases_page():
        if "user_id" not in session:
            return redirect(url_for("index"))
        return render_template("mis_compras.html")

    return app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host=host, port=port)
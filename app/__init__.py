import secrets
from flask import Flask, jsonify, request, session
from dotenv import load_dotenv
from config import Config
from .extensions import db, ensure_schema_upgrades

def create_app(config_object=Config):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    app.config.from_prefixed_env()
    app.instance_path and __import__("os").makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.settings import settings_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)

    @app.before_request
    def csrf_protect():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
            if not secrets.compare_digest(supplied or "", session["csrf_token"]):
                return jsonify(error="Ungültiges oder fehlendes CSRF-Token."), 403

    @app.after_request
    def security_headers(response):
        # Some Windows MIME registries classify .js as text/plain. Together
        # with nosniff that makes browsers reject our own JavaScript entirely.
        if request.path.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript; charset=utf-8"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.errorhandler(413)
    def too_large(_): return jsonify(error="Anfrage ist zu groß."), 413
    @app.errorhandler(404)
    def not_found(_): return jsonify(error="Nicht gefunden."), 404
    with app.app_context(): db.create_all()
    ensure_schema_upgrades(app)
    return app

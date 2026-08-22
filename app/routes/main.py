from flask import Blueprint, current_app, render_template, session
from ..models import ProviderConfiguration

main_bp = Blueprint("main", __name__)
@main_bp.get("/")
def dashboard():
    eu_available = ProviderConfiguration.query.filter_by(enabled=True, is_eu_hosted=True).first() is not None
    return render_template("dashboard.html", eu_available=eu_available, csrf_token=session.get("csrf_token"))
@main_bp.get("/privacy")
def privacy(): return render_template("privacy.html")
@main_bp.get("/info")
def info(): return render_template("info.html", version=current_app.config["APP_VERSION"])


from flask import Blueprint, current_app, render_template
from ..models import ProviderConfiguration

settings_bp = Blueprint("settings", __name__)
@settings_bp.get("/settings/providers")
def providers():
    return render_template("providers.html", providers=ProviderConfiguration.query.order_by(ProviderConfiguration.name).all(), encryption_available=bool(current_app.config["APP_ENCRYPTION_KEY"]))


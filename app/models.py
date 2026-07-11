from datetime import datetime, timezone
from .extensions import db

def now(): return datetime.now(timezone.utc)

class ProviderConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    provider_type = db.Column(db.String(40), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    encrypted_api_key = db.Column(db.Text)
    model_name = db.Column(db.String(200), nullable=False)
    hosting_region = db.Column(db.String(120), default="Unbekannt")
    is_eu_hosted = db.Column(db.Boolean, default=False)
    enabled = db.Column(db.Boolean, default=True)
    input_cost_per_million = db.Column(db.Float, default=0)
    output_cost_per_million = db.Column(db.Float, default=0)
    context_window = db.Column(db.Integer, default=8192)
    timeout_seconds = db.Column(db.Float, default=30)
    custom_headers_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime(timezone=True), default=now)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now)

class UsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now)
    prompt_hash = db.Column(db.String(64), nullable=False)
    input_tokens = db.Column(db.Integer, nullable=False)
    estimated_output_tokens = db.Column(db.Integer, nullable=False)
    provider_name = db.Column(db.String(120))
    model_name = db.Column(db.String(200))
    estimated_cost = db.Column(db.Float, default=0)
    estimated_co2_grams = db.Column(db.Float, default=0)
    compliance_score = db.Column(db.Integer)
    request_status = db.Column(db.String(40))
    latency_ms = db.Column(db.Integer)


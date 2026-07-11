import hashlib, json, time
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from ..extensions import db
from ..models import ProviderConfiguration, UsageLog
from ..services.analysis_service import analyze_with_ollama, parse_analysis
from ..services.compliance_service import inspect_prompt
from ..services.cost_service import estimate_cost
from ..services.encryption_service import EncryptionService, EncryptionUnavailable, mask_secret
from ..services.ollama_service import OllamaError, OllamaService
from ..services.recommendation_service import recommend
from ..services.sustainability_service import estimate_duration, estimate_sustainability
from ..services.token_service import estimate_tokens
from ..services.url_security import validate_provider_url
from ..providers.ollama import OllamaProvider
from ..providers.openai_compatible import OpenAICompatibleProvider
from ..providers.base import ProviderError

api_bp = Blueprint("api", __name__, url_prefix="/api")
def error(message, status=400): return jsonify(error=message), status
def prompt_from_body():
    data = request.get_json(silent=True) or {}; prompt = data.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip(): raise ValueError("Bitte einen Prompt eingeben.")
    if len(prompt) > current_app.config["MAX_PROMPT_LENGTH"]: raise ValueError("Der Prompt überschreitet die maximale Länge.")
    return data, prompt.strip()
def serialize_provider(p):
    masked = ""
    if p.encrypted_api_key:
        try: masked = mask_secret(EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).decrypt(p.encrypted_api_key))
        except EncryptionUnavailable: masked = "*** (nicht entschlüsselbar)"
    return {"id":p.id,"name":p.name,"provider_type":p.provider_type,"base_url":p.base_url,"api_key_masked":masked,"has_api_key":bool(p.encrypted_api_key),"model_name":p.model_name,"hosting_region":p.hosting_region,"is_eu_hosted":p.is_eu_hosted,"enabled":p.enabled,"input_cost_per_million":p.input_cost_per_million,"output_cost_per_million":p.output_cost_per_million,"context_window":p.context_window,"timeout_seconds":p.timeout_seconds,"custom_headers":json.loads(p.custom_headers_json or "{}")}
def analysis_payload(prompt, mode="auto"):
    analysis_timeout = current_app.config.get("OLLAMA_ANALYSIS_TIMEOUT_SECONDS", 0)
    # requests uses None for an unlimited timeout. A positive value remains
    # available for installations that prefer a bounded analysis request.
    analysis_timeout = None if analysis_timeout <= 0 else analysis_timeout
    service = OllamaService(
        current_app.config["OLLAMA_BASE_URL"],
        current_app.config["OLLAMA_MODEL"],
        analysis_timeout,
    )
    try: analysis, warning = analyze_with_ollama(prompt, service)
    except OllamaError as exc: analysis, warning = parse_analysis(None, prompt); warning = f"{exc} Sichere Standardanalyse wird verwendet."
    compliance = inspect_prompt(prompt)
    analysis["contains_personal_data"] |= compliance["contains_personal_data"]
    analysis["contains_confidential_data"] |= compliance["contains_confidential_data"]
    analysis["compliance_score"] = min(analysis["compliance_score"], compliance["score"])
    tokens = estimate_tokens(prompt); output = current_app.config["DEFAULT_EXPECTED_OUTPUT_TOKENS"]
    model, reason = recommend(analysis, compliance, tokens, mode)
    sustainable = estimate_sustainability(tokens, output, model, current_app.config["CARBON_INTENSITY_G_PER_KWH"])
    return {"analysis":analysis,"compliance":compliance,"input_tokens":tokens,"expected_output_tokens":output,"recommendation":{**model,"reason":reason},"estimated_cost":estimate_cost(tokens,output,model),"sustainability":sustainable,"duration":estimate_duration(tokens,output,analysis["complexity_score"],model),"warning":warning,"estimates_notice":"Konfigurierbare MVP-Schätzwerte; keine wissenschaftliche Messung oder Preisgarantie."}

@api_bp.post("/analyze")
def analyze():
    try: data, prompt = prompt_from_body(); return jsonify(analysis_payload(prompt, data.get("mode","auto")))
    except ValueError as exc: return error(str(exc))
@api_bp.post("/optimize")
def optimize():
    try: _, prompt=prompt_from_body(); result=analysis_payload(prompt); return jsonify(optimized_prompt=result["analysis"]["optimized_prompt"], suggestions=result["analysis"]["optimization_suggestions"], warning=result["warning"])
    except ValueError as exc: return error(str(exc))

def provider_instance(config):
    if config.provider_type == "ollama": return OllamaProvider(config.base_url, config.model_name, config.timeout_seconds)
    key = EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).decrypt(config.encrypted_api_key)
    return OpenAICompatibleProvider(config, key)
@api_bp.post("/send")
def send():
    try: data,prompt=prompt_from_body()
    except ValueError as exc: return error(str(exc))
    compliance=inspect_prompt(prompt); override=(data.get("override_reason") or "").strip()
    if compliance["level"]=="red" and len(override)<10: return error("Rote Compliance-Bewertung blockiert den Versand. Eine begründete manuelle Freigabe ist erforderlich.",403)
    provider=ProviderConfiguration.query.filter_by(id=data.get("provider_id"),enabled=True).first()
    if not provider: return error("Aktiver Provider nicht gefunden.",404)
    if data.get("eu_only") and not provider.is_eu_hosted: return error("Der gewählte Provider ist nicht als EU-gehostet markiert.",400)
    tokens=estimate_tokens(prompt)
    if tokens > provider.context_window: return error("Der Prompt überschreitet das Kontextfenster des Providers.",400)
    started=time.monotonic()
    try: answer=provider_instance(provider).generate(prompt, provider.model_name)
    except (ProviderError,OllamaError,EncryptionUnavailable) as exc: return error(str(exc),502)
    latency=int((time.monotonic()-started)*1000); output=estimate_tokens(answer)
    if current_app.config["ENABLE_PROMPT_LOGGING"]:
        db.session.add(UsageLog(prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),input_tokens=tokens,estimated_output_tokens=output,provider_name=provider.name,model_name=provider.model_name,estimated_cost=tokens/1e6*provider.input_cost_per_million+output/1e6*provider.output_cost_per_million,estimated_co2_grams=0,compliance_score=compliance["score"],request_status="success",latency_ms=latency)); db.session.commit()
    return jsonify(answer=answer, latency_ms=latency)

@api_bp.get("/providers")
def providers(): return jsonify([serialize_provider(p) for p in ProviderConfiguration.query.order_by(ProviderConfiguration.name).all()])
def apply_provider(p,data,creating=False):
    required=("name","provider_type","base_url","model_name")
    if any(not str(data.get(k,"")).strip() for k in required): raise ValueError("Name, Typ, Base-URL und Modell sind erforderlich.")
    kind=data["provider_type"]
    if kind not in {"openai_compatible","eu_openai_compatible","ollama","custom"}: raise ValueError("Unbekannter Provider-Typ.")
    p.name=str(data["name"]).strip()[:120]; p.provider_type=kind
    p.base_url=validate_provider_url(str(data["base_url"]).strip(),allow_localhost=kind=="ollama")
    p.model_name=str(data["model_name"]).strip()[:200]; p.hosting_region=str(data.get("hosting_region","Unbekannt"))[:120]
    p.is_eu_hosted=bool(data.get("is_eu_hosted",kind=="eu_openai_compatible")); p.enabled=bool(data.get("enabled",True))
    p.input_cost_per_million=max(0,float(data.get("input_cost_per_million",0))); p.output_cost_per_million=max(0,float(data.get("output_cost_per_million",0)))
    p.context_window=max(1,int(data.get("context_window",8192))); p.timeout_seconds=max(1,min(120,float(data.get("timeout_seconds",30))))
    headers=data.get("custom_headers",{}); 
    if not isinstance(headers,dict): raise ValueError("Benutzerdefinierte Header müssen ein JSON-Objekt sein.")
    p.custom_headers_json=json.dumps(headers)
    api_key=data.get("api_key")
    if api_key: p.encrypted_api_key=EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).encrypt(str(api_key))
    return p
@api_bp.post("/providers")
def create_provider():
    try: p=apply_provider(ProviderConfiguration(),request.get_json(silent=True) or {},True); db.session.add(p); db.session.commit(); return jsonify(serialize_provider(p)),201
    except (ValueError,EncryptionUnavailable) as exc: return error(str(exc))
@api_bp.put("/providers/<int:provider_id>")
def update_provider(provider_id):
    p=db.get_or_404(ProviderConfiguration,provider_id)
    try: apply_provider(p,request.get_json(silent=True) or {}); db.session.commit(); return jsonify(serialize_provider(p))
    except (ValueError,EncryptionUnavailable) as exc: return error(str(exc))
@api_bp.delete("/providers/<int:provider_id>")
def delete_provider(provider_id): p=db.get_or_404(ProviderConfiguration,provider_id); db.session.delete(p); db.session.commit(); return "",204
@api_bp.post("/providers/<int:provider_id>/test")
def test_provider(provider_id):
    try: return jsonify(provider_instance(db.get_or_404(ProviderConfiguration,provider_id)).test_connection())
    except (ProviderError,OllamaError,EncryptionUnavailable) as exc: return error(str(exc),502)
@api_bp.get("/providers/<int:provider_id>/models")
def provider_models(provider_id):
    try: return jsonify(models=provider_instance(db.get_or_404(ProviderConfiguration,provider_id)).list_models())
    except (ProviderError,OllamaError,EncryptionUnavailable) as exc: return error(str(exc),502)
@api_bp.get("/ollama/status")
def ollama_status():
    try:
        models=OllamaService(current_app.config["OLLAMA_BASE_URL"],current_app.config["OLLAMA_MODEL"]).list_models()
        configured=current_app.config["OLLAMA_MODEL"]
        available=any(name == configured or name.split(":", 1)[0] == configured for name in models)
        return jsonify(ok=True,configured_model=configured,model_available=available,models=models)
    except OllamaError as exc: return error(str(exc),503)
@api_bp.get("/ollama/models")
def ollama_models():
    try: return jsonify(models=OllamaService(current_app.config["OLLAMA_BASE_URL"],current_app.config["OLLAMA_MODEL"]).list_models())
    except OllamaError as exc: return error(str(exc),503)
@api_bp.get("/usage/summary")
def usage_summary():
    if not current_app.config["ENABLE_PROMPT_LOGGING"]: return jsonify(enabled=False,count=0)
    row=db.session.query(func.count(UsageLog.id),func.coalesce(func.sum(UsageLog.estimated_cost),0),func.coalesce(func.sum(UsageLog.estimated_co2_grams),0)).one()
    return jsonify(enabled=True,count=row[0],estimated_cost=row[1],estimated_co2_grams=row[2])

import copy, hashlib, json, time
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from ..extensions import db
from ..models import ProviderConfiguration, UsageLog
from ..services.analysis_service import analyze_with_ollama, parse_analysis
from ..services.compliance_service import inspect_chat_history, inspect_prompt, redact_sensitive
from ..services.cost_service import estimate_cost, estimate_electricity_cost
from ..services.ecologits_service import compute_impacts
from ..services.encryption_service import EncryptionService, EncryptionUnavailable, mask_secret
from ..services.guardian_service import apply_semantic_check
from ..services.ollama_service import OllamaError, OllamaService
from ..services.recommendation_service import recommend
from ..services.sustainability_service import estimate_duration, estimate_sustainability
from ..services.token_service import estimate_tokens
from ..services.url_security import validate_provider_url
from ..providers.ollama import OllamaProvider
from ..providers.openai_compatible import OpenAICompatibleProvider
from ..providers.anthropic import AnthropicProvider
from ..providers.base import ProviderError

api_bp = Blueprint("api", __name__, url_prefix="/api")
ANTHROPIC_MODELS = {
    "claude-haiku-4-5-20251001": {
        "input_cost": 1,
        "output_cost": 5,
        "context_window": 200_000,
    },
    "claude-sonnet-4-6": {
        "input_cost": 3,
        "output_cost": 15,
        "context_window": 1_000_000,
    },
}
def error(message, status=400): return jsonify(error=message), status
def optional_float(value):
    if value in (None, ""):
        return None
    return float(value)
def prompt_from_body():
    data = request.get_json(silent=True) or {}; prompt = data.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip(): raise ValueError("Bitte einen Prompt eingeben.")
    if len(prompt) > current_app.config["MAX_PROMPT_LENGTH"]: raise ValueError("Der Prompt überschreitet die maximale Länge.")
    return data, prompt.strip()


def chat_compliance(messages: list[dict[str, str]]) -> dict:
    # Stufe 1 (deterministisch, Nachricht für Nachricht) plus Stufe 2 (semantisch,
    # über den gesamten Verlauf) -- gilt für /api/send und /api/compliance/check.
    transcript = "\n".join(message["content"] for message in messages)
    return apply_semantic_check(inspect_chat_history(messages), transcript, current_app.config)


def chat_messages_from_body(data: dict, prompt: str) -> tuple[list[dict[str, str]], dict]:
    messages = data.get("messages")
    if messages is None:
        single = [{"role": "user", "content": prompt}]
        return single, chat_compliance(single)
    if not isinstance(messages, list) or not messages:
        raise ValueError("Der Chatverlauf ist ungültig.")
    cleaned = []
    total_length = 0
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}:
            raise ValueError("Der Chatverlauf enthält eine ungültige Rolle.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Der Chatverlauf enthält eine leere Nachricht.")
        content = content.strip()
        total_length += len(content)
        cleaned.append({"role": message["role"], "content": content})
    if cleaned[0]["role"] != "user" or any(
        message["role"] == cleaned[index - 1]["role"]
        for index, message in enumerate(cleaned[1:], start=1)
    ):
        raise ValueError("Der Chatverlauf muss abwechselnd Benutzer- und Assistentennachrichten enthalten.")
    if cleaned[-1] != {"role": "user", "content": prompt}:
        raise ValueError("Die letzte Chatnachricht stimmt nicht mit dem Prompt überein.")
    max_chat_length = current_app.config["MAX_CONTENT_LENGTH"] // 2
    if total_length > max_chat_length:
        raise ValueError("Der Chatverlauf ist für eine einzelne Anfrage zu groß.")
    return cleaned, chat_compliance(cleaned)
def serialize_provider(p):
    masked = ""
    if p.encrypted_api_key:
        try: masked = mask_secret(EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).decrypt(p.encrypted_api_key))
        except EncryptionUnavailable: masked = "*** (nicht entschlüsselbar)"
    return {"id":p.id,"name":p.name,"provider_type":p.provider_type,"base_url":p.base_url,"api_key_masked":masked,"has_api_key":bool(p.encrypted_api_key),"model_name":p.model_name,"hosting_region":p.hosting_region,"is_eu_hosted":p.is_eu_hosted,"enabled":p.enabled,"input_cost_per_million":p.input_cost_per_million,"output_cost_per_million":p.output_cost_per_million,"context_window":p.context_window,"timeout_seconds":p.timeout_seconds,"custom_headers":json.loads(p.custom_headers_json or "{}"),"ecologits_provider":p.ecologits_provider,"eco_active_params_b":p.eco_active_params_b,"eco_total_params_b":p.eco_total_params_b,"eco_datacenter_pue":p.eco_datacenter_pue,"eco_datacenter_wue":p.eco_datacenter_wue,"eco_electricity_mix_zone":p.eco_electricity_mix_zone}
def sustainability_for(tokens, output, model, duration, carbon_intensity):
    formula = estimate_sustainability(tokens, output, model, carbon_intensity)
    eco_result, eco_warning = compute_impacts(
        output, duration["max_seconds"], provider=None, catalog_model=model, app_config=current_app.config
    )
    merged = {**formula, **(eco_result or {})}
    # Nur fuer lokale Modelle: der Anbieterpreis ("Kosten") ist bei Cloud-/EU-Modellen der tatsaechlich
    # zu zahlende Preis (inkl. der -- meist guenstigeren -- Stromkosten des Anbieters), waehrend bei
    # lokalen Modellen "Kosten" immer 0 ist, obwohl real Strom verbraucht wird. Fuer Cloud/EU wuerde
    # eine zusaetzliche, mit dem Haushaltsstrompreis geschaetzte "Stromkosten"-Zahl einen Betrag
    # suggerieren, den der Nutzer nicht selbst zahlt.
    merged["electricity_cost_eur"] = (
        estimate_electricity_cost(merged["energy_kwh"], current_app.config["ELECTRICITY_PRICE_EUR_PER_KWH"])
        if model.get("hosting_region") == "Lokal" else None
    )
    return merged, eco_warning

def optimized_payload(optimized_prompt, analysis, compliance, tokens, output, mode, carbon_intensity):
    tokens_opt = estimate_tokens(optimized_prompt)
    # Heuristische Annahme, nicht Teil der EcoLogits-Methodik: EcoLogits' Formel haengt nur von
    # der Anzahl der Ausgabe-Token ab, nicht vom Prompt selbst -- ohne eine Annahme dazu waere
    # der CO2-Vergleich original/optimiert immer identisch. Wir nehmen an, dass ein proportional
    # kuerzerer Prompt tendenziell zu einer proportional kuerzeren Antwort fuehrt.
    output_opt = max(1, round(output * tokens_opt / tokens))
    model_opt, reason_opt = recommend(analysis, compliance, tokens_opt, mode)
    # complexity_score stammt aus der Ollama-Analyse des Original-Prompts; der optimierte
    # Prompt wird nicht erneut eigenstaendig bewertet, Dauer/Modellwahl sind also Naeherungen.
    duration_opt = estimate_duration(tokens_opt, output_opt, analysis["complexity_score"], model_opt)
    sustainability_opt, sustainability_opt_warning = sustainability_for(tokens_opt, output_opt, model_opt, duration_opt, carbon_intensity)
    return {
        "prompt_tokens": tokens_opt,
        "expected_output_tokens": output_opt,
        "recommendation": {**model_opt, "reason": reason_opt},
        "estimated_cost": estimate_cost(tokens_opt, output_opt, model_opt),
        "sustainability": sustainability_opt,
        "sustainability_warning": sustainability_opt_warning,
        "duration": duration_opt,
    }

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
    compliance = apply_semantic_check(inspect_prompt(prompt), prompt, current_app.config)
    analysis["contains_personal_data"] |= compliance["contains_personal_data"]
    analysis["contains_confidential_data"] |= compliance["contains_confidential_data"]
    analysis["compliance_score"] = min(analysis["compliance_score"], compliance["score"])
    tokens = estimate_tokens(prompt); output = current_app.config["DEFAULT_EXPECTED_OUTPUT_TOKENS"]
    model, reason = recommend(analysis, compliance, tokens, mode)
    carbon_intensity = current_app.config["CARBON_INTENSITY_G_PER_KWH"]
    duration = estimate_duration(tokens, output, analysis["complexity_score"], model)
    sustainability, sustainability_warning = sustainability_for(tokens, output, model, duration, carbon_intensity)
    payload = {"analysis":analysis,"compliance":compliance,"input_tokens":tokens,"expected_output_tokens":output,"recommendation":{**model,"reason":reason},"estimated_cost":estimate_cost(tokens,output,model),"sustainability":sustainability,"sustainability_warning":sustainability_warning,"duration":duration,"warning":warning,"estimates_notice":"Konfigurierbare MVP-Schätzwerte; keine wissenschaftliche Messung oder Preisgarantie."}
    optimized_prompt = analysis["optimized_prompt"].strip()
    # Auch das blosse Echo des maskierten Prompts ist keine Optimierung — sonst
    # entstuende ein Vergleichsblock, dessen Ersparnis nur aus der Maskierung stammt.
    if optimized_prompt and optimized_prompt not in (prompt.strip(), redact_sensitive(prompt).strip()):
        payload["optimized"] = optimized_payload(optimized_prompt, analysis, compliance, tokens, output, mode, carbon_intensity)
    return payload

@api_bp.post("/analyze")
def analyze():
    try: data, prompt = prompt_from_body(); return jsonify(analysis_payload(prompt, data.get("mode","auto")))
    except ValueError as exc: return error(str(exc))
@api_bp.post("/optimize")
def optimize():
    try: _, prompt=prompt_from_body(); result=analysis_payload(prompt); return jsonify(optimized_prompt=result["analysis"]["optimized_prompt"], suggestions=result["analysis"]["optimization_suggestions"], warning=result["warning"])
    except ValueError as exc: return error(str(exc))


@api_bp.post("/compliance/check")
def compliance_check():
    # Vorabprüfung für die Mini-Ampel im Chat: bewertet Nachricht plus Verlauf mit
    # exakt derselben Logik wie /api/send, damit UI und Server nie auseinanderlaufen.
    try:
        data, prompt = prompt_from_body()
        _, compliance = chat_messages_from_body(data, prompt)
    except ValueError as exc:
        return error(str(exc))
    return jsonify(compliance)

def provider_instance(config):
    if config.provider_type == "ollama": return OllamaProvider(config.base_url, config.model_name, config.timeout_seconds)
    key = EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).decrypt(config.encrypted_api_key)
    if config.provider_type == "anthropic":
        return AnthropicProvider(config, key)
    return OpenAICompatibleProvider(config, key)
@api_bp.post("/send")
def send():
    try: data,prompt=prompt_from_body()
    except ValueError as exc: return error(str(exc))
    try:
        messages, compliance = chat_messages_from_body(data, prompt)
    except ValueError as exc:
        return error(str(exc))
    override = (data.get("override_reason") or "").strip()
    if compliance["level"]=="red" and len(override)<10: return error("Rote Compliance-Bewertung blockiert den Versand. Eine begründete manuelle Freigabe ist erforderlich.",403)
    provider=ProviderConfiguration.query.filter_by(id=data.get("provider_id"),enabled=True).first()
    if not provider: return error("Aktiver Provider nicht gefunden.",404)
    if data.get("eu_only") and not provider.is_eu_hosted: return error("Der gewählte Provider ist nicht als EU-gehostet markiert.",400)
    selected_model = provider.model_name
    input_cost = provider.input_cost_per_million
    output_cost = provider.output_cost_per_million
    context_window = provider.context_window
    if provider.provider_type == "anthropic":
        selected_model = str(data.get("model_name") or "").strip()
        model_config = ANTHROPIC_MODELS.get(selected_model)
        if not model_config:
            return error("Unbekanntes oder nicht erlaubtes Claude-Modell.", 400)
        input_cost = model_config["input_cost"]
        output_cost = model_config["output_cost"]
        context_window = model_config["context_window"]
    tokens = sum(estimate_tokens(message["content"]) for message in messages)
    if tokens > context_window: return error("Der Chatverlauf überschreitet das Kontextfenster des Providers.",400)
    started=time.monotonic()
    try:
        provider_client = provider_instance(provider)
        if provider.provider_type == "anthropic":
            answer, usage = provider_client.generate_messages(messages, selected_model)
            tokens = usage["input_tokens"] or tokens
            output = usage["output_tokens"]
        else:
            answer = provider_client.generate(prompt, selected_model)
            output = estimate_tokens(answer)
    except (ProviderError,OllamaError,EncryptionUnavailable) as exc: return error(str(exc),502)
    latency=int((time.monotonic()-started)*1000)
    if not output:
        output = estimate_tokens(answer)
    # Reale Nutzung: kein Formel-Fallback, wenn EcoLogits nicht verfuegbar ist -- entweder eine
    # echte Zahl oder 0, nie ein erfundener Wert fuer tatsaechlich versendete Prompts.
    impact_provider = provider
    if provider.provider_type == "anthropic":
        impact_provider = copy.copy(provider)
        impact_provider.model_name = selected_model
    eco_result, eco_warning = compute_impacts(output, latency/1000, provider=impact_provider, catalog_model=None, app_config=current_app.config)
    if eco_result:
        # provider_type=="ollama" ist im Projekt bereits das etablierte Signal fuer "lokal" (siehe
        # validate_provider_url's allow_localhost). Fuer Cloud/EU-Provider bleibt der Wert None --
        # der Anbieterpreis ("estimated_cost") deckt deren tatsaechliche Kosten bereits ab.
        eco_result["electricity_cost_eur"] = (
            estimate_electricity_cost(eco_result["energy_kwh"], current_app.config["ELECTRICITY_PRICE_EUR_PER_KWH"])
            if provider.provider_type == "ollama" else None
        )
    co2_grams = eco_result["co2_grams"] if eco_result else 0
    if current_app.config["ENABLE_PROMPT_LOGGING"]:
        db.session.add(UsageLog(prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),input_tokens=tokens,estimated_output_tokens=output,provider_name=provider.name,model_name=selected_model,estimated_cost=tokens/1e6*input_cost+output/1e6*output_cost,estimated_co2_grams=co2_grams,compliance_score=compliance["score"],request_status="success",latency_ms=latency)); db.session.commit()
    actual_cost = round(
        tokens / 1_000_000 * input_cost
        + output / 1_000_000 * output_cost,
        6,
    )
    return jsonify(
        answer=answer,
        latency_ms=latency,
        model_used=selected_model,
        input_tokens=tokens,
        output_tokens=output,
        input_cost=round(tokens / 1_000_000 * input_cost, 6),
        output_cost=round(output / 1_000_000 * output_cost, 6),
        actual_cost=actual_cost,
        cost_currency="USD" if provider.provider_type == "anthropic" else "EUR",
        sustainability=eco_result,
        sustainability_warning=eco_warning,
    )

@api_bp.get("/providers")
def providers(): return jsonify([serialize_provider(p) for p in ProviderConfiguration.query.order_by(ProviderConfiguration.name).all()])
def apply_provider(p,data,creating=False):
    kind = str(data.get("provider_type", "")).strip()
    required = ("name", "provider_type", "base_url")
    if kind != "anthropic":
        required += ("model_name",)
    if any(not str(data.get(key, "")).strip() for key in required):
        raise ValueError("Name, Typ und Base-URL sind erforderlich; außer bei Anthropic wird auch ein Modell benötigt.")
    if kind not in {"openai_compatible","eu_openai_compatible","anthropic","ollama","custom"}: raise ValueError("Unbekannter Provider-Typ.")
    p.name=str(data["name"]).strip()[:120]; p.provider_type=kind
    p.base_url=validate_provider_url(str(data["base_url"]).strip(),allow_localhost=kind=="ollama")
    p.model_name = (
        "claude-haiku-4-5-20251001"
        if kind == "anthropic"
        else str(data["model_name"]).strip()[:200]
    )
    p.hosting_region=str(data.get("hosting_region","Unbekannt"))[:120]
    p.is_eu_hosted=bool(data.get("is_eu_hosted",kind=="eu_openai_compatible")); p.enabled=bool(data.get("enabled",True))
    p.input_cost_per_million=max(0,float(data.get("input_cost_per_million",0))); p.output_cost_per_million=max(0,float(data.get("output_cost_per_million",0)))
    p.context_window=max(1,int(data.get("context_window",8192))); p.timeout_seconds=max(1,min(120,float(data.get("timeout_seconds",30))))
    headers=data.get("custom_headers",{}); 
    if not isinstance(headers,dict): raise ValueError("Benutzerdefinierte Header müssen ein JSON-Objekt sein.")
    p.custom_headers_json=json.dumps(headers)
    api_key=data.get("api_key")
    if api_key: p.encrypted_api_key=EncryptionService(current_app.config["APP_ENCRYPTION_KEY"]).encrypt(str(api_key))
    eco_provider = data.get("eco_provider") or None
    if eco_provider and eco_provider not in {"openai", "anthropic", "cohere", "google_genai", "huggingface_hub", "mistralai"}:
        raise ValueError("Unbekannter EcoLogits-Anbieter.")
    p.ecologits_provider = eco_provider
    p.eco_active_params_b = optional_float(data.get("eco_active_params_b"))
    p.eco_total_params_b = optional_float(data.get("eco_total_params_b"))
    p.eco_datacenter_pue = optional_float(data.get("eco_datacenter_pue"))
    p.eco_datacenter_wue = optional_float(data.get("eco_datacenter_wue"))
    p.eco_electricity_mix_zone = str(data.get("eco_electricity_mix_zone") or "").strip().upper()[:3] or None
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

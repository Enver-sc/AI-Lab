import json
import re

from .compliance_service import redact_sensitive
from .ollama_service import OllamaError, OllamaService

# Englische Risikodefinition: Guardian-Modelle sind überwiegend auf englische
# Instruktionen trainiert; die Begründung fordern wir trotzdem auf Deutsch an.
GUARDIAN_SYSTEM_PROMPT = """You are a data-protection guardian for prompts that are about to be sent to an external AI provider. Assess ONLY privacy risk in the sense of the EU GDPR and the German church data protection law (KDG). A text is risky if it contains or implies: (1) personal or identifying information about a natural person, even without numbers or contact data (for example a name, role, department, or a combination of details that makes someone identifiable), (2) health-related information about a person (illness, sick leave, diagnosis, treatment), (3) internal confidential business information (unpublished figures, customer data, internal plans or documents marked internal). General questions, public knowledge and clearly fictional examples are not risky. Respond ONLY with one JSON object of the form {"risk": true or false, "categories": [subset of "personal_data", "health_data", "confidential_internal"], "reason": "one short sentence in German"}. No markdown, no additional text."""

CATEGORY_LABELS = {
    "personal_data": "Personenbezogene oder identifizierende Angaben (Stufe 2)",
    "health_data": "Gesundheitsdaten (Stufe 2)",
    "confidential_internal": "Interne vertrauliche Informationen (Stufe 2)",
    "generic": "Datenschutzrisiko (Stufe 2)",
}

UNAVAILABLE_NOTICE = "Stufe-2-Prüfung nicht verfügbar (Guardian-Modell nicht erreichbar); die Bewertung basiert nur auf Stufe 1."
INVALID_NOTICE = "Stufe-2-Prüfung ohne verwertbares Ergebnis (ungültige Modellantwort); die Bewertung basiert nur auf Stufe 1."
FALLBACK_REASON = "Keine Begründung vom Guardian-Modell geliefert."


def parse_guardian(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", raw or "", re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict) or not isinstance(data.get("risk"), bool):
        return None
    categories = data.get("categories")
    if not isinstance(categories, list):
        categories = []
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = FALLBACK_REASON
    return {
        "risk": data["risk"],
        "categories": [item for item in categories if item in CATEGORY_LABELS],
        "reason": reason.strip(),
    }


def check_text(text: str, service: OllamaService) -> tuple[dict | None, str | None]:
    # Wie bei der Analyse (Issue #2): erkannte sensible Werte erreichen auch das
    # Guardian-Modell nie im Klartext.
    try:
        raw = service.generate(redact_sensitive(text), GUARDIAN_SYSTEM_PROMPT)
    except OllamaError:
        return None, UNAVAILABLE_NOTICE
    result = parse_guardian(raw)
    if result is None:
        return None, INVALID_NOTICE
    return result, None


def apply_semantic_check(compliance: dict, text: str, app_config) -> dict:
    merged = dict(compliance)
    merged.setdefault("semantic_findings", [])
    model = app_config.get("OLLAMA_GUARDIAN_MODEL") or ""
    # Leerer Modellname = Stufe 2 bewusst deaktiviert (z. B. Tests, Betrieb ohne
    # Guardian-Modell) -- dann still nur Stufe 1, ohne Warnhinweis.
    if not model:
        return merged
    service = OllamaService(
        app_config["OLLAMA_BASE_URL"],
        model,
        app_config["OLLAMA_TIMEOUT_SECONDS"],
    )
    result, warning = check_text(text, service)
    if warning:
        merged["semantic_warning"] = warning
        return merged
    if not result["risk"]:
        return merged
    categories = result["categories"] or ["generic"]
    merged["semantic_findings"] = [
        {"label": CATEGORY_LABELS[category], "reason": result["reason"]}
        for category in categories
    ]
    merged["contains_personal_data"] = merged["contains_personal_data"] or bool(
        {"personal_data", "health_data"} & set(categories)
    )
    merged["contains_confidential_data"] = (
        merged["contains_confidential_data"] or "confidential_internal" in categories
    )
    # Stufe 2 ergänzt, sie ersetzt nicht: Funde heben höchstens auf Gelb an;
    # Rot und das Blockieren bleiben allein Sache der deterministischen Stufe 1.
    if merged["level"] == "green":
        merged["level"] = "yellow"
        # Score und Ampel konsistent halten: Gelb liegt unterhalb von 80.
        merged["score"] = min(merged["score"], 79)
    return merged

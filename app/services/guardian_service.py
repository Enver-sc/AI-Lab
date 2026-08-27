import re

from .compliance_service import redact_sensitive
from .ollama_service import OllamaError, OllamaService

# granite4.1-guardian ist ein IBM-Granite-Guardian-Modell: Es ignoriert freie
# Formatanweisungen (auch "antworte als JSON" -- mit format=json liefert es sogar
# nur noch Muell) und traegt den hier gesetzten Text stattdessen wortwoertlich als
# Risikokriterium in sein eigenes, festes Antwortprotokoll "<score> yes|no </score>"
# ein (siehe `ollama show granite4.1-guardian:8b --modelfile`, Sektion get_criteria).
# Deshalb rein deskriptiv formuliert, ohne Ausgabeformat-Anweisung.
GUARDIAN_RISK_DEFINITION = (
    "Personal or identifying information about a natural person (for example a name, "
    "role, department, or a combination of details that makes someone identifiable), "
    "health-related information about a person (illness, sick leave, diagnosis, treatment), "
    "or confidential internal business information (unpublished figures, customer data, "
    "internal plans or documents marked internal). Public knowledge and clearly fictional "
    "examples are not risky."
)

# Ein einzelner Guardian-Aufruf liefert nur ein gemeinsames Ja/Nein fuer die obige
# Kriterienliste, keine Aufschluesselung nach Kategorie -- daher nur ein Label statt
# einer Kategorie-Zuordnung wie frueher vorgesehen.
FINDING_LABEL = "Datenschutzrisiko (Stufe 2)"
FINDING_REASON = "Guardian-Modell (Stufe 2) hat einen moeglichen Datenschutz- oder Vertraulichkeitsbezug erkannt."

UNAVAILABLE_NOTICE = "Stufe-2-Prüfung nicht verfügbar (Guardian-Modell nicht erreichbar); die Bewertung basiert nur auf Stufe 1."
INVALID_NOTICE = "Stufe-2-Prüfung ohne verwertbares Ergebnis (ungültige Modellantwort); die Bewertung basiert nur auf Stufe 1."

SCORE_PATTERN = re.compile(r"<score>\s*(yes|no)\s*</score>", re.I)


def parse_guardian(raw: str) -> dict | None:
    match = SCORE_PATTERN.search(raw or "")
    if not match:
        return None
    return {"risk": match.group(1).lower() == "yes"}


def check_text(text: str, service: OllamaService, keep_alive: str | None = None) -> tuple[dict | None, str | None]:
    # Wie bei der Analyse (Issue #2): erkannte sensible Werte erreichen auch das
    # Guardian-Modell nie im Klartext.
    try:
        raw = service.generate(redact_sensitive(text), GUARDIAN_RISK_DEFINITION, keep_alive=keep_alive)
    except OllamaError:
        return None, UNAVAILABLE_NOTICE
    result = parse_guardian(raw)
    if result is None:
        return None, INVALID_NOTICE
    return result, None


def apply_semantic_check(compliance: dict, text: str, app_config) -> dict:
    merged = dict(compliance)
    merged.setdefault("semantic_findings", [])
    # Vollstaendig = Stufe 1 und Stufe 2 sind gelaufen; degradiert = nur Stufe 1 kam
    # zum Zuge (Guardian nicht erreichbar, Zeitlimit ueberschritten oder Antwort nicht
    # auswertbar). Die Kachel im Frontend haengt ihre Warnfarbe an diesem Feld auf,
    # damit ein Teilausfall nicht wie ein sauberer Durchlauf aussieht.
    merged["status"] = "vollständig"
    model = app_config.get("OLLAMA_GUARDIAN_MODEL") or ""
    # Leerer Modellname = Stufe 2 bewusst deaktiviert (z. B. Tests, Betrieb ohne
    # Guardian-Modell) -- das ist eine bewusste Konfiguration, kein Ausfall, daher
    # weder Warnhinweis noch degradierter Status.
    if not model:
        return merged
    service = OllamaService(
        app_config["OLLAMA_BASE_URL"],
        model,
        app_config.get("OLLAMA_GUARDIAN_TIMEOUT_SECONDS", app_config["OLLAMA_TIMEOUT_SECONDS"]),
    )
    keep_alive = app_config.get("OLLAMA_GUARDIAN_KEEP_ALIVE")
    result, warning = check_text(text, service, keep_alive)
    if warning:
        merged["semantic_warning"] = warning
        merged["status"] = "degradiert"
        return merged
    if not result["risk"]:
        return merged
    merged["semantic_findings"] = [{"label": FINDING_LABEL, "reason": FINDING_REASON}]
    # Eine einzelne kombinierte Kriterienpruefung kann nicht zwischen personenbezogenen
    # und rein vertraulichen Geschaeftsdaten unterscheiden -- konservativ als
    # personenbezogen werten, da Gesundheits- und Personendaten der Hauptfall sind.
    merged["contains_personal_data"] = True
    # Stufe 2 ergänzt, sie ersetzt nicht: Funde heben höchstens auf Gelb an;
    # Rot und das Blockieren bleiben allein Sache der deterministischen Stufe 1.
    if merged["level"] == "green":
        merged["level"] = "yellow"
        # Score und Ampel konsistent halten: Gelb liegt unterhalb von 80.
        merged["score"] = min(merged["score"], 79)
    return merged

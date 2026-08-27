import logging
import re
import time

from .compliance_service import redact_sensitive
from .ollama_service import OllamaError, OllamaService, OllamaTimeoutError

logger = logging.getLogger(__name__)

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

# Der Guardian beantwortet einen kurzen Einzelprompt mit einem einzelnen yes/no-
# Urteil -- der Modelfile-Default (num_ctx 131072) reserviert dafuer trotzdem eine
# ~29-GB-Instanz (siehe `ollama ps`) und braucht entsprechend lange zum Laden,
# vor allem wenn ein anderes Modell den GPU-Speicher zwischenzeitlich belegt hat.
# 4096 Token reichen fuer Kriterientext + Prompt + Denkprozess + Urteil bequem aus
# (im aufgezeichneten Fixture-Lauf: 320 Prompt- + 418 Antwort-Token) und halten die
# Instanz klein genug, um zwischen zwei Pruefungen zuverlaessig warm zu bleiben.
# Bewusst keine weiteren Optionen (Temperatur o. Ä.): jede zusaetzliche, zwischen
# Aufrufen variierende Option wuerde Ollama zwingen, das Modell mit den neuen
# Optionen neu zu laden statt die bereits warme Instanz zu treffen.
GUARDIAN_OPTIONS = {"num_ctx": 4096}


def parse_guardian(raw: str) -> dict | None:
    match = SCORE_PATTERN.search(raw or "")
    if not match:
        return None
    return {"risk": match.group(1).lower() == "yes"}


def check_text(text: str, service: OllamaService, keep_alive: str | None = None) -> tuple[dict | None, str | None]:
    # Wie bei der Analyse (Issue #2): erkannte sensible Werte erreichen auch das
    # Guardian-Modell nie im Klartext.
    start = time.monotonic()
    try:
        data = service.generate_raw(
            redact_sensitive(text), GUARDIAN_RISK_DEFINITION, keep_alive=keep_alive, options=GUARDIAN_OPTIONS
        )
    except OllamaTimeoutError:
        logger.info("Guardian-Timeout nach %.1fs", time.monotonic() - start)
        return None, UNAVAILABLE_NOTICE
    except OllamaError as exc:
        logger.info("Guardian-Aufruf fehlgeschlagen nach %.1fs: %s", time.monotonic() - start, exc)
        return None, UNAVAILABLE_NOTICE
    wall = time.monotonic() - start
    # total_duration/load_duration kommen als Nanosekunden von Ollama -- ein
    # load_duration nahe total_duration zeigt einen Kaltstart (Modell neu geladen),
    # ein load_duration nahe 0 eine bereits warme Instanz.
    total_s = data.get("total_duration", 0) / 1e9
    load_s = data.get("load_duration", 0) / 1e9
    logger.info("Guardian-Aufruf: %.1fs (Ollama total=%.1fs, load=%.1fs)", wall, total_s, load_s)
    result = parse_guardian(data["response"])
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
    # weder Warnhinweis noch degradierter Status. Aber auch kein "vollständig":
    # die Kachel zeigt dafür "Stufe 1 + 2 geprüft", und das wäre hier gelogen.
    if not model:
        merged["status"] = "stufe-2-deaktiviert"
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

import json, logging, re, time
from .compliance_service import redact_sensitive
from .ollama_service import OllamaError, OllamaService, OllamaTimeoutError

logger = logging.getLogger(__name__)

DEFAULT = {"prompt_category":"unbekannt","complexity_score":35,"sensitivity_score":20,"compliance_score":80,"contains_personal_data":False,"contains_confidential_data":False,"copyright_risk":"low","recommended_model_class":"cloud_small","optimization_suggestions":["Formuliere Ziel und gewünschtes Ausgabeformat präzise."],"optimized_prompt":"","short_reasoning":"Sichere regelbasierte Standardanalyse, da keine valide Modellanalyse verfügbar war."}
SYSTEM_PROMPT = """Du analysierst Prompts lokal. Antworte ausschließlich mit einem JSON-Objekt und den Schlüsseln prompt_category, complexity_score, sensitivity_score, compliance_score, contains_personal_data, contains_confidential_data, copyright_risk, recommended_model_class, optimization_suggestions, optimized_prompt, short_reasoning. Scores sind Ganzzahlen 0..100; copyright_risk ist low|medium|high. Wähle für einfache Standardanfragen cloud_small (Claude Haiku 4.5) und nur für komplexes Schlussfolgern, anspruchsvolle Programmierung oder umfangreiche Analysen cloud_large (Claude Sonnet 4.6). Verwende local_small oder local_large bei sensiblen Daten und eu_hosted, wenn EU-Hosting erforderlich ist. Keine Markdown-Codeblöcke. optimized_prompt ist ein verbesserter Nutzerprompt für ein beliebiges Zielmodell, keine Kopie deiner eigenen Antwortformat-Anweisung: optimized_prompt darf selbst keine Formatierungsvorgabe wie "antworte als JSON" oder "gib das Ergebnis strukturiert zurück" enthalten, außer der Originalprompt verlangt das ausdrücklich."""

def parse_analysis(raw, original_prompt=""):
    warning = None
    try: data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", raw or "", re.S)
        try: data = json.loads(match.group(0)) if match else None; warning = "JSON wurde aus der Modellantwort extrahiert."
        except (json.JSONDecodeError, AttributeError): data = None
    if not isinstance(data, dict):
        result = DEFAULT.copy(); result["optimized_prompt"] = original_prompt; return result, "Ollama lieferte keine valide strukturierte Analyse; sichere Standardwerte werden verwendet."
    result = DEFAULT.copy(); result.update({k:v for k,v in data.items() if k in DEFAULT})
    for key in ("complexity_score","sensitivity_score","compliance_score"):
        try: result[key] = max(0, min(100, int(result[key])))
        except (TypeError, ValueError): result[key] = DEFAULT[key]; warning = "Einige Modellwerte waren ungültig und wurden ersetzt."
    if result["copyright_risk"] not in {"low","medium","high"}: result["copyright_risk"]="medium"
    if not isinstance(result["optimization_suggestions"], list): result["optimization_suggestions"] = DEFAULT["optimization_suggestions"]
    if not isinstance(result["optimized_prompt"], str): result["optimized_prompt"] = original_prompt
    return result, warning

REDACTION_NOTICE = "Sensible Daten wurden vor der Übergabe an das Analyse-/Optimierungsmodell maskiert; Platzhalter bleiben im optimierten Prompt sichtbar."

# Explizites num_ctx statt Ollama-Default: Ohne eigene Angabe uebernimmt der Aufruf
# den globalen Context-Default der Ollama-App (Einstellung "Context length"), der sich
# mit Updates oder Nutzereingriffen unbemerkt aendern kann -- mit 256k lud gemma4 z. B.
# eine 262144er-Instanz, die entsprechend viel Speicher band und langsam startete.
# Bemessung: MAX_PROMPT_LENGTH (30000 Zeichen, ca. 8-9k Token deutscher Text) plus
# Systemprompt (~300 Token) plus Antwort, die mit optimized_prompt in etwa die Laenge
# des Prompts erreicht -- rund 18-20k Token im Extremfall; 32768 deckt das mit Reserve
# ab, waehrend uebliche Analyse-Prompts nur wenige hundert Token brauchen. Bewusst
# keine weiteren Optionen (Temperatur o. Ä.): jede zusaetzliche, zwischen Aufrufen
# variierende Option wuerde Ollama zwingen, das Modell neu zu laden statt die warme
# Instanz wiederzuverwenden (gleiches Prinzip wie GUARDIAN_OPTIONS).
ANALYSIS_OPTIONS = {"num_ctx": 32768}

def analyze_with_ollama(prompt: str, service: OllamaService, keep_alive: str | None = None) -> tuple[dict, str | None]:
    # Issue #2: erkannte sensible Werte (z. B. IBAN) duerfen das Modell nie im
    # Klartext erreichen. Anzeige und Compliance laufen weiter auf dem Original.
    # Auch der Fallback-optimized_prompt bleibt maskiert, damit die Antwort nie
    # Klartext als "optimierten" Prompt ausweist.
    redacted = redact_sensitive(prompt)
    start = time.monotonic()
    try:
        data = service.generate_raw(redacted, SYSTEM_PROMPT, json_mode=True, keep_alive=keep_alive, options=ANALYSIS_OPTIONS)
    except OllamaTimeoutError:
        logger.info("Analyse-Timeout nach %.1fs", time.monotonic() - start)
        raise
    except OllamaError as exc:
        logger.info("Analyse-Aufruf fehlgeschlagen nach %.1fs: %s", time.monotonic() - start, exc)
        raise
    wall = time.monotonic() - start
    # Beweis-Logging wie beim Guardian: load_duration nahe total_duration = Kaltstart,
    # load nahe 0 = warme Instanz getroffen. Ollama liefert Nanosekunden.
    total_s = data.get("total_duration", 0) / 1e9
    load_s = data.get("load_duration", 0) / 1e9
    logger.info("Analyse-Aufruf: %.1fs (Ollama total=%.1fs, load=%.1fs)", wall, total_s, load_s)
    result, warning = parse_analysis(data["response"], redacted)
    if redacted != prompt:
        warning = f"{warning} {REDACTION_NOTICE}" if warning else REDACTION_NOTICE
    return result, warning

import json, re
from .ollama_service import OllamaError

DEFAULT = {"prompt_category":"unbekannt","complexity_score":35,"sensitivity_score":20,"compliance_score":80,"contains_personal_data":False,"contains_confidential_data":False,"copyright_risk":"low","recommended_model_class":"local_small","optimization_suggestions":["Formuliere Ziel und gewünschtes Ausgabeformat präzise."],"optimized_prompt":"","short_reasoning":"Sichere regelbasierte Standardanalyse, da keine valide Modellanalyse verfügbar war."}
SYSTEM_PROMPT = """Du analysierst Prompts lokal. Antworte ausschließlich mit einem JSON-Objekt und den Schlüsseln prompt_category, complexity_score, sensitivity_score, compliance_score, contains_personal_data, contains_confidential_data, copyright_risk, recommended_model_class, optimization_suggestions, optimized_prompt, short_reasoning. Scores sind Ganzzahlen 0..100; copyright_risk ist low|medium|high; recommended_model_class ist local_small|local_large|cloud_small|cloud_large|eu_hosted. Keine Markdown-Codeblöcke."""

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

def analyze_with_ollama(prompt, service):
    raw = service.generate(prompt, SYSTEM_PROMPT)
    return parse_analysis(raw, prompt)

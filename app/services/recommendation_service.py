from .model_catalog import MODELS

def recommend(analysis, compliance, input_tokens, mode="auto", providers=None):
    providers = providers or []
    sensitive = compliance["contains_personal_data"] or compliance["contains_confidential_data"] or analysis.get("sensitivity_score", 0) >= 60
    complex_task = analysis.get("complexity_score", 0) >= 70
    if mode == "eu" or (sensitive and mode == "cloud"):
        target, reason = "eu_hosted", "Sensible Daten und externer Versand sprechen für EU-Hosting."
    elif mode == "local" or sensitive or compliance["level"] == "red":
        target, reason = ("local_large" if complex_task else "local_small"), "Lokale Verarbeitung reduziert das Übertragungsrisiko."
    elif mode == "cloud": target, reason = ("cloud_large" if complex_task else "cloud_small"), "Der gewählte Cloud-Modus und die Komplexität bestimmen die Modellgröße."
    else: target, reason = ("local_large" if complex_task else "local_small"), "Die lokale, passende Modellgröße minimiert Kosten und Datenübertragung."
    model = next(m.copy() for m in MODELS if m["model_class"] == target)
    if input_tokens > model["context_window"]:
        model = next(m.copy() for m in MODELS if m["model_class"] == ("eu_hosted" if sensitive else "cloud_large"))
        reason = "Der lange Kontext benötigt ein größeres Kontextfenster."
    return model, reason


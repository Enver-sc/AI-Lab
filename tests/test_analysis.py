import requests
from app.services.analysis_service import SYSTEM_PROMPT, parse_analysis
from app.services.ollama_service import OllamaService, OllamaError

def test_invalid_ollama_analysis_falls_back():
    result,warning=parse_analysis("not json","Original")
    assert result["optimized_prompt"]=="Original" and warning

def test_extracts_json():
    result,warning=parse_analysis('text {"complexity_score": 91} end')
    assert result["complexity_score"]==91 and warning

def test_system_prompt_forbids_leaking_own_format_instruction_into_optimized_prompt():
    # Regression: das Analyse-Modell antwortet selbst im JSON-Format (siehe SYSTEM_PROMPT)
    # und uebernahm diese Anweisung teils versehentlich auch in optimized_prompt -- externe
    # Provider erhielten dann beim "Optimierten Prompt verwenden" einen Prompt, der sie
    # unabsichtlich zu einer JSON-Antwort anwies, obwohl der Nutzer das nie wollte.
    assert "optimized_prompt darf selbst keine Formatierungsvorgabe" in SYSTEM_PROMPT

def test_ollama_unreachable():
    class Session:
        def get(self,*args,**kwargs):
            raise requests.ConnectionError()
    try:
        OllamaService("http://localhost", "x", session=Session()).list_models()
    except OllamaError as exc:
        assert "nicht erreichbar" in str(exc)
    else:
        assert False


import requests
from app.services.analysis_service import parse_analysis
from app.services.ollama_service import OllamaService, OllamaError

def test_invalid_ollama_analysis_falls_back():
    result,warning=parse_analysis("not json","Original")
    assert result["optimized_prompt"]=="Original" and warning

def test_extracts_json():
    result,warning=parse_analysis('text {"complexity_score": 91} end')
    assert result["complexity_score"]==91 and warning

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


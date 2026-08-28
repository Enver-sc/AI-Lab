import logging
from unittest.mock import Mock

import pytest
import requests
from app.services.analysis_service import ANALYSIS_OPTIONS, DEFAULT, SYSTEM_PROMPT, analyze_with_ollama, parse_analysis
from app.services.ollama_service import OllamaService, OllamaError, OllamaTimeoutError

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



def _raw_response(text, total_seconds=1.0, load_seconds=0.0):
    return {"response": text, "total_duration": int(total_seconds * 1e9), "load_duration": int(load_seconds * 1e9)}


def test_analyze_with_ollama_passes_minimal_options_and_keep_alive():
    service = Mock()
    service.generate_raw.return_value = _raw_response('{"complexity_score": 42}')
    result, warning = analyze_with_ollama("Hallo", service, keep_alive="30m")
    assert result["complexity_score"] == 42 and warning is None
    kwargs = service.generate_raw.call_args.kwargs
    assert kwargs["keep_alive"] == "30m"
    assert kwargs["options"] == ANALYSIS_OPTIONS == {"num_ctx": 32768}
    assert kwargs["json_mode"] is True
    assert kwargs["think"] is False


def test_json_without_known_keys_falls_back_with_warning():
    # Regression: gemma4 lieferte mit aktivem Denken nur {"thought": ...}; das ergab
    # stumm die Standardwerte ohne Warnung.
    result, warning = parse_analysis('{"thought": "The user wants an email."}', "Original")
    assert result == {**DEFAULT, "optimized_prompt": "Original"} and warning


def test_analyze_with_ollama_logs_measured_duration_and_ollama_timings(caplog):
    service = Mock()
    service.generate_raw.return_value = _raw_response("{}", total_seconds=6.3, load_seconds=0.02)
    with caplog.at_level(logging.INFO, logger="app.services.analysis_service"):
        analyze_with_ollama("Hallo", service)
    assert any(
        r.message.startswith("Analyse-Aufruf:") and "Ollama total=6.3" in r.message and "load=0.0" in r.message
        for r in caplog.records
    )


def test_analyze_with_ollama_logs_timeout_and_reraises(caplog):
    service = Mock()
    service.generate_raw.side_effect = OllamaTimeoutError("Ollama hat das Zeitlimit überschritten.")
    with caplog.at_level(logging.INFO, logger="app.services.analysis_service"):
        with pytest.raises(OllamaTimeoutError):
            analyze_with_ollama("Hallo", service)
    assert any(r.message.startswith("Analyse-Timeout nach") for r in caplog.records)

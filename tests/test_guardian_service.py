import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.guardian_service import (
    FINDING_LABEL,
    GUARDIAN_OPTIONS,
    INVALID_NOTICE,
    UNAVAILABLE_NOTICE,
    apply_semantic_check,
    check_text,
    parse_guardian,
)
from app.services.ollama_service import OllamaError, OllamaTimeoutError

FIXTURES = Path(__file__).parent / "fixtures"

GREEN_COMPLIANCE = {
    "score": 100,
    "level": "green",
    "findings": [],
    "contains_personal_data": False,
    "contains_confidential_data": False,
}


def load_fixture_response(name):
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)["response"]


def raw_response(text, total_seconds=1.2, load_seconds=0.0):
    # Nachbildung der Ollama-/api/generate-Antwort inkl. der Felder, die das
    # Beweis-Logging in check_text auswertet (total_duration/load_duration sind
    # bei Ollama Nanosekunden).
    return {"response": text, "total_duration": int(total_seconds * 1e9), "load_duration": int(load_seconds * 1e9)}


def guardian_config(model="guardian-test"):
    return {
        "OLLAMA_GUARDIAN_MODEL": model,
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_TIMEOUT_SECONDS": 0.1,
        "OLLAMA_GUARDIAN_TIMEOUT_SECONDS": 0.1,
        "OLLAMA_GUARDIAN_KEEP_ALIVE": "30m",
    }


def test_parse_guardian_accepts_real_risky_fixture():
    # Echte Antwort von granite4.1-guardian:8b (lokal aufgezeichnet), kein
    # erfundenes Beispiel -- siehe tests/fixtures/guardian_response_risky.json.
    raw = load_fixture_response("guardian_response_risky.json")
    result = parse_guardian(raw)
    assert result == {"risk": True}


def test_parse_guardian_accepts_real_safe_fixture():
    raw = load_fixture_response("guardian_response_safe.json")
    result = parse_guardian(raw)
    assert result == {"risk": False}


def test_parse_guardian_is_case_insensitive_and_tolerates_whitespace():
    assert parse_guardian("<SCORE>  Yes  </SCORE>") == {"risk": True}


def test_parse_guardian_rejects_unusable_answer():
    assert parse_guardian("keine verwertbare Antwort") is None
    assert parse_guardian("") is None
    assert parse_guardian(None) is None


def test_check_text_masks_sensitive_values_before_model_call():
    service = Mock()
    service.generate_raw.return_value = raw_response("<score> no </score>")
    check_text("Meine IBAN ist DE89370400440532013000", service)
    sent_text = service.generate_raw.call_args[0][0]
    assert "DE89370400440532013000" not in sent_text


def test_check_text_uses_minimal_num_ctx_option():
    # num_ctx 4096 statt Modelfile-Default 131072 -- kleine, warm bleibende
    # Instanz statt einer ~29-GB-Instanz mit entsprechend langer Ladezeit.
    service = Mock()
    service.generate_raw.return_value = raw_response("<score> no </score>")
    check_text("Hallo", service)
    assert service.generate_raw.call_args.kwargs["options"] == GUARDIAN_OPTIONS == {"num_ctx": 4096}


def test_check_text_logs_measured_duration_and_ollama_timings(caplog):
    service = Mock()
    service.generate_raw.return_value = raw_response("<score> no </score>", total_seconds=4.7, load_seconds=0.03)
    with caplog.at_level(logging.INFO, logger="app.services.guardian_service"):
        check_text("Hallo", service)
    assert any("Ollama total=4.7" in r.message and "load=0.0" in r.message for r in caplog.records)


def test_check_text_logs_timeout_with_measured_duration(caplog):
    service = Mock()
    service.generate_raw.side_effect = OllamaTimeoutError("Ollama hat das Zeitlimit überschritten.")
    with caplog.at_level(logging.INFO, logger="app.services.guardian_service"):
        result, warning = check_text("Hallo", service)
    assert result is None and warning == UNAVAILABLE_NOTICE
    assert any(r.message.startswith("Guardian-Timeout nach") for r in caplog.records)


def test_apply_semantic_check_disabled_without_model():
    with patch("app.services.guardian_service.OllamaService.generate_raw") as generate_raw:
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config(model=""))
    generate_raw.assert_not_called()
    assert merged["level"] == "green"
    assert merged["semantic_findings"] == []
    assert "semantic_warning" not in merged
    # Bewusst deaktivierte Stufe 2 ist kein Ausfall (kein Warnhinweis), darf sich
    # aber auch nicht als vollstaendiger 2-Stufen-Lauf ausgeben -- daran haengt
    # die Statuszeile "Stufe 1 + 2 geprüft" der Kachel.
    assert merged["status"] == "stufe-2-deaktiviert"


def test_apply_semantic_check_raises_green_to_yellow_with_flags():
    with patch(
        "app.services.guardian_service.OllamaService.generate_raw",
        return_value=raw_response("<score> yes </score>"),
    ):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Person A ist krank", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] <= 79
    assert merged["contains_personal_data"] is True
    assert merged["semantic_findings"][0]["label"] == FINDING_LABEL
    assert merged["semantic_findings"][0]["reason"]
    assert merged["status"] == "vollständig"


def test_apply_semantic_check_never_sets_red():
    yellow = {**GREEN_COMPLIANCE, "score": 64, "level": "yellow"}
    with patch(
        "app.services.guardian_service.OllamaService.generate_raw",
        return_value=raw_response("<score> yes </score>"),
    ):
        merged = apply_semantic_check(yellow, "Text", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] == 64


def test_apply_semantic_check_warns_when_model_unreachable():
    with patch("app.services.guardian_service.OllamaService.generate_raw", side_effect=OllamaError("down")):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == UNAVAILABLE_NOTICE
    assert merged["semantic_findings"] == []
    assert merged["status"] == "degradiert"


def test_apply_semantic_check_warns_on_unusable_answer():
    with patch(
        "app.services.guardian_service.OllamaService.generate_raw",
        return_value=raw_response("???"),
    ):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == INVALID_NOTICE
    assert merged["status"] == "degradiert"


def test_apply_semantic_check_falls_back_on_timeout():
    # Simuliert das Kaltstart-/Haenger-Szenario: der Ollama-Aufruf ueberschreitet
    # das Zeitlimit, apply_semantic_check darf nicht haengen bleiben, sondern muss
    # sauber in den degradierten Zustand fallen.
    with patch(
        "app.services.guardian_service.OllamaService.generate_raw",
        side_effect=OllamaTimeoutError("Ollama hat das Zeitlimit überschritten."),
    ):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["status"] == "degradiert"
    assert merged["semantic_warning"] == UNAVAILABLE_NOTICE


def test_apply_semantic_check_passes_guardian_timeout_and_keep_alive():
    config = guardian_config()
    with patch("app.services.guardian_service.OllamaService") as service_cls:
        service_cls.return_value.generate_raw.return_value = raw_response("<score> no </score>")
        apply_semantic_check(GREEN_COMPLIANCE, "Hallo", config)
    service_cls.assert_called_once_with(
        config["OLLAMA_BASE_URL"], config["OLLAMA_GUARDIAN_MODEL"], config["OLLAMA_GUARDIAN_TIMEOUT_SECONDS"]
    )
    service_cls.return_value.generate_raw.assert_called_once()
    call_kwargs = service_cls.return_value.generate_raw.call_args.kwargs
    assert call_kwargs["keep_alive"] == "30m"
    assert call_kwargs["options"] == {"num_ctx": 4096}

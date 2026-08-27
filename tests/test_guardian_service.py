import json
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.guardian_service import (
    FINDING_LABEL,
    INVALID_NOTICE,
    UNAVAILABLE_NOTICE,
    apply_semantic_check,
    check_text,
    parse_guardian,
)
from app.services.ollama_service import OllamaError

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
    service.generate.return_value = "<score> no </score>"
    check_text("Meine IBAN ist DE89370400440532013000", service)
    sent_text = service.generate.call_args[0][0]
    assert "DE89370400440532013000" not in sent_text


def test_apply_semantic_check_disabled_without_model():
    with patch("app.services.guardian_service.OllamaService.generate") as generate:
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config(model=""))
    generate.assert_not_called()
    assert merged["level"] == "green"
    assert merged["semantic_findings"] == []
    assert "semantic_warning" not in merged
    assert merged["status"] == "vollständig"


def test_apply_semantic_check_raises_green_to_yellow_with_flags():
    with patch("app.services.guardian_service.OllamaService.generate", return_value="<score> yes </score>"):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Person A ist krank", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] <= 79
    assert merged["contains_personal_data"] is True
    assert merged["semantic_findings"][0]["label"] == FINDING_LABEL
    assert merged["semantic_findings"][0]["reason"]
    assert merged["status"] == "vollständig"


def test_apply_semantic_check_never_sets_red():
    yellow = {**GREEN_COMPLIANCE, "score": 64, "level": "yellow"}
    with patch("app.services.guardian_service.OllamaService.generate", return_value="<score> yes </score>"):
        merged = apply_semantic_check(yellow, "Text", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] == 64


def test_apply_semantic_check_warns_when_model_unreachable():
    with patch("app.services.guardian_service.OllamaService.generate", side_effect=OllamaError("down")):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == UNAVAILABLE_NOTICE
    assert merged["semantic_findings"] == []
    assert merged["status"] == "degradiert"


def test_apply_semantic_check_warns_on_unusable_answer():
    with patch("app.services.guardian_service.OllamaService.generate", return_value="???"):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == INVALID_NOTICE
    assert merged["status"] == "degradiert"


def test_apply_semantic_check_falls_back_on_timeout():
    # Simuliert das Kaltstart-/Haenger-Szenario: der Ollama-Aufruf ueberschreitet
    # das Zeitlimit, apply_semantic_check darf nicht haengen bleiben, sondern muss
    # sauber in den degradierten Zustand fallen.
    with patch(
        "app.services.guardian_service.OllamaService.generate",
        side_effect=OllamaError("Ollama hat das Zeitlimit überschritten."),
    ):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["status"] == "degradiert"
    assert merged["semantic_warning"] == UNAVAILABLE_NOTICE


def test_apply_semantic_check_passes_guardian_timeout_and_keep_alive():
    config = guardian_config()
    with patch("app.services.guardian_service.OllamaService") as service_cls:
        service_cls.return_value.generate.return_value = "<score> no </score>"
        apply_semantic_check(GREEN_COMPLIANCE, "Hallo", config)
    service_cls.assert_called_once_with(
        config["OLLAMA_BASE_URL"], config["OLLAMA_GUARDIAN_MODEL"], config["OLLAMA_GUARDIAN_TIMEOUT_SECONDS"]
    )
    service_cls.return_value.generate.assert_called_once()
    assert service_cls.return_value.generate.call_args.kwargs["keep_alive"] == "30m"

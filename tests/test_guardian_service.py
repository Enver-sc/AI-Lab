from unittest.mock import Mock, patch

from app.services.guardian_service import (
    INVALID_NOTICE,
    UNAVAILABLE_NOTICE,
    apply_semantic_check,
    check_text,
    parse_guardian,
)
from app.services.ollama_service import OllamaError

GREEN_COMPLIANCE = {
    "score": 100,
    "level": "green",
    "findings": [],
    "contains_personal_data": False,
    "contains_confidential_data": False,
}

RISK_JSON = '{"risk": true, "categories": ["health_data"], "reason": "Krankmeldung einer identifizierbaren Person."}'


def guardian_config(model="guardian-test"):
    return {
        "OLLAMA_GUARDIAN_MODEL": model,
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_TIMEOUT_SECONDS": 0.1,
    }


def test_parse_guardian_accepts_plain_json():
    result = parse_guardian(RISK_JSON)
    assert result["risk"] is True
    assert result["categories"] == ["health_data"]
    assert result["reason"].startswith("Krankmeldung")


def test_parse_guardian_extracts_json_from_surrounding_text():
    raw = "Hier das Ergebnis:\n```json\n" + RISK_JSON + "\n```"
    result = parse_guardian(raw)
    assert result is not None and result["risk"] is True


def test_parse_guardian_rejects_garbage_and_wrong_types():
    assert parse_guardian("keine json antwort") is None
    assert parse_guardian('{"risk": "ja"}') is None
    result = parse_guardian('{"risk": true, "categories": ["unbekannt"], "reason": ""}')
    assert result["categories"] == []
    assert result["reason"]


def test_check_text_masks_sensitive_values_before_model_call():
    service = Mock()
    service.generate.return_value = '{"risk": false, "categories": [], "reason": "Unauffällig."}'
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


def test_apply_semantic_check_raises_green_to_yellow_with_flags():
    with patch("app.services.guardian_service.OllamaService.generate", return_value=RISK_JSON):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Person A ist krank", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] <= 79
    assert merged["contains_personal_data"] is True
    assert merged["semantic_findings"][0]["label"] == "Gesundheitsdaten (Stufe 2)"
    assert merged["semantic_findings"][0]["reason"]


def test_apply_semantic_check_never_sets_red():
    yellow = {**GREEN_COMPLIANCE, "score": 64, "level": "yellow"}
    with patch("app.services.guardian_service.OllamaService.generate", return_value=RISK_JSON):
        merged = apply_semantic_check(yellow, "Text", guardian_config())
    assert merged["level"] == "yellow"
    assert merged["score"] == 64


def test_apply_semantic_check_warns_when_model_unreachable():
    with patch("app.services.guardian_service.OllamaService.generate", side_effect=OllamaError("down")):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == UNAVAILABLE_NOTICE
    assert merged["semantic_findings"] == []


def test_apply_semantic_check_warns_on_unusable_answer():
    with patch("app.services.guardian_service.OllamaService.generate", return_value="???"):
        merged = apply_semantic_check(GREEN_COMPLIANCE, "Hallo", guardian_config())
    assert merged["level"] == "green"
    assert merged["semantic_warning"] == INVALID_NOTICE

import json
from unittest.mock import patch

from app.services.analysis_service import REDACTION_NOTICE

IBAN = "DE89370400440532013000"
IBAN_MASKED = "DE8***3000"
MODEL_REPLY = json.dumps({
    "optimized_prompt": "Bitte überweise den Betrag auf das genannte Konto.",
    "optimization_suggestions": ["Formuliere das Ziel präziser."],
})


def call_with_mocked_model(client, csrf, prompt, endpoint="/api/analyze"):
    with patch("app.routes.api.OllamaService") as service_class:
        service_class.return_value.generate.return_value = MODEL_REPLY
        response = client.post(
            endpoint,
            json={"prompt": prompt},
            headers={"X-CSRF-Token": csrf},
        )
    return response, service_class.return_value.generate


def test_optimizer_never_receives_cleartext_iban(client, csrf):
    response, generate = call_with_mocked_model(
        client, csrf, f"Meine IBAN ist {IBAN}, bitte optimiere diesen Text."
    )
    assert response.status_code == 200
    sent_prompt = generate.call_args.args[0]
    assert IBAN not in sent_prompt
    assert IBAN_MASKED in sent_prompt
    data = response.get_json()
    assert "IBAN" in data["compliance"]["findings"]
    assert REDACTION_NOTICE in data["warning"]


def test_harmless_prompt_reaches_model_unchanged(client, csrf):
    prompt = "Schreibe ein kurzes Gedicht über den Frühling."
    response, generate = call_with_mocked_model(client, csrf, prompt)
    assert response.status_code == 200
    assert generate.call_args.args[0] == prompt
    assert response.get_json()["warning"] is None


def test_fallback_keeps_masking_and_combines_warnings(client, csrf):
    with patch("app.routes.api.OllamaService") as service_class:
        service_class.return_value.generate.return_value = "keine json antwort"
        response = client.post(
            "/api/optimize",
            json={"prompt": f"Überweise 50 Euro an {IBAN}."},
            headers={"X-CSRF-Token": csrf},
        )
    assert response.status_code == 200
    data = response.get_json()
    assert IBAN not in data["optimized_prompt"]
    assert IBAN_MASKED in data["optimized_prompt"]
    assert "sichere Standardwerte" in data["warning"]
    assert REDACTION_NOTICE in data["warning"]


def test_masked_echo_creates_no_optimized_block(client, csrf):
    echo_reply = json.dumps({"optimized_prompt": f"Meine IBAN ist {IBAN_MASKED}."})
    with patch("app.routes.api.OllamaService") as service_class:
        service_class.return_value.generate.return_value = echo_reply
        response = client.post(
            "/api/analyze",
            json={"prompt": f"Meine IBAN ist {IBAN}."},
            headers={"X-CSRF-Token": csrf},
        )
    assert response.status_code == 200
    data = response.get_json()
    assert "optimized" not in data
    assert REDACTION_NOTICE in data["warning"]


def test_issue2_regression_iban_via_optimize_endpoint(client, csrf):
    response, generate = call_with_mocked_model(
        client, csrf, f"Überweise 50 Euro an {IBAN}.", endpoint="/api/optimize"
    )
    assert response.status_code == 200
    sent_prompt = generate.call_args.args[0]
    assert IBAN not in sent_prompt
    assert IBAN_MASKED in sent_prompt
    data = response.get_json()
    assert data["optimized_prompt"] == "Bitte überweise den Betrag auf das genannte Konto."
    assert REDACTION_NOTICE in data["warning"]

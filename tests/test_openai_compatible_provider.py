from types import SimpleNamespace
from unittest.mock import Mock

from app.providers.openai_compatible import OpenAICompatibleProvider


def config(**overrides):
    defaults = dict(
        name="Gateway",
        base_url="https://gateway.example.com/v1",
        model_name="gpt-4o-mini",
        timeout_seconds=30,
        input_cost_per_million=1,
        output_cost_per_million=5,
        hosting_region="Global",
        is_eu_hosted=False,
        custom_headers_json="{}",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_generate_uses_chat_completions_api():
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "Antwort"}}]}
    http = Mock()
    http.request.return_value = response
    provider = OpenAICompatibleProvider(config(), "sk-test", session=http)

    assert provider.generate("Hallo") == "Antwort"
    _, url = http.request.call_args.args
    assert url == "https://gateway.example.com/v1/chat/completions"


def test_sends_custom_headers():
    # Regression: custom_headers_json wurde gespeichert, aber beim eigentlichen
    # API-Aufruf nie gelesen -- das Formularfeld "Benutzerdefinierte Header" hatte
    # dadurch keine Wirkung.
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "Antwort"}}]}
    http = Mock()
    http.request.return_value = response
    cfg = config(custom_headers_json='{"X-Gateway-Key": "abc123"}')
    provider = OpenAICompatibleProvider(cfg, "sk-test", session=http)

    provider.generate("Hallo")

    assert http.request.call_args.kwargs["headers"]["X-Gateway-Key"] == "abc123"


def test_invalid_custom_headers_json_is_ignored():
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "Antwort"}}]}
    http = Mock()
    http.request.return_value = response
    cfg = config(custom_headers_json="not json")
    provider = OpenAICompatibleProvider(cfg, "sk-test", session=http)

    provider.generate("Hallo")

    assert http.request.call_args.kwargs["headers"]["Authorization"] == "Bearer sk-test"

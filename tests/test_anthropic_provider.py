from types import SimpleNamespace
from unittest.mock import Mock

from app.providers.anthropic import AnthropicProvider


def config():
    return SimpleNamespace(
        name="Claude Haiku",
        base_url="https://api.anthropic.com",
        model_name="claude-haiku-4-5-20251001",
        timeout_seconds=30,
        input_cost_per_million=1,
        output_cost_per_million=5,
        hosting_region="Global",
        is_eu_hosted=False,
        custom_headers_json="{}",
    )


def test_anthropic_generate_uses_messages_api():
    response = Mock(status_code=200)
    response.json.return_value = {
        "content": [{"type": "text", "text": "Antwort"}],
        "usage": {"input_tokens": 12, "output_tokens": 4},
    }
    http = Mock()
    http.request.return_value = response
    provider = AnthropicProvider(config(), "sk-ant-test", session=http)

    assert provider.generate("Hallo") == "Antwort"
    _, url = http.request.call_args.args
    kwargs = http.request.call_args.kwargs
    assert url == "https://api.anthropic.com/v1/messages"
    assert kwargs["headers"]["x-api-key"] == "sk-ant-test"
    assert kwargs["json"]["model"] == "claude-haiku-4-5-20251001"
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "Hallo"}]


def test_anthropic_chat_returns_usage():
    response = Mock(status_code=200)
    response.json.return_value = {
        "content": [{"type": "text", "text": "Folgeantwort"}],
        "usage": {"input_tokens": 30, "output_tokens": 8},
    }
    http = Mock()
    http.request.return_value = response
    provider = AnthropicProvider(config(), "sk-ant-test", session=http)
    messages = [
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Antwort"},
        {"role": "user", "content": "Mehr Details"},
    ]

    answer, usage = provider.generate_messages(messages, "claude-sonnet-4-6")

    assert answer == "Folgeantwort"
    assert usage == {"input_tokens": 30, "output_tokens": 8}
    assert http.request.call_args.kwargs["json"]["messages"] == messages


def test_anthropic_cost_uses_input_and_output_prices():
    provider = AnthropicProvider(config(), "sk-ant-test")
    assert provider.estimate_cost(1_000_000, 1_000_000) == 6


def test_anthropic_sends_custom_headers():
    # Regression: custom_headers_json wurde gespeichert, aber beim eigentlichen
    # API-Aufruf nie gelesen -- das Formularfeld "Benutzerdefinierte Header" hatte
    # dadurch keine Wirkung.
    cfg = config()
    cfg.custom_headers_json = '{"X-Gateway-Key": "abc123"}'
    response = Mock(status_code=200)
    response.json.return_value = {"content": [{"type": "text", "text": "Antwort"}], "usage": {}}
    http = Mock()
    http.request.return_value = response
    provider = AnthropicProvider(cfg, "sk-ant-test", session=http)

    provider.generate("Hallo")

    assert http.request.call_args.kwargs["headers"]["X-Gateway-Key"] == "abc123"

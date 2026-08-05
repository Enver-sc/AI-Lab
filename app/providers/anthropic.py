import requests

from .base import BaseProvider, ProviderError


class AnthropicProvider(BaseProvider):
    def __init__(self, config, api_key: str, session=None):
        self.config = config
        self.api_key = api_key
        self.http = session or requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self.http.request(
                method,
                f"{self.config.base_url.rstrip('/')}{path}",
                headers=self.headers,
                timeout=self.config.timeout_seconds,
                allow_redirects=False,
                **kwargs,
            )
            if response.status_code in (401, 403):
                raise ProviderError("Authentifizierung bei Anthropic fehlgeschlagen.")
            if response.status_code == 429:
                raise ProviderError("Rate-Limit von Anthropic erreicht.")
            if response.status_code >= 500:
                raise ProviderError("Anthropic meldet einen Serverfehler.")
            response.raise_for_status()
            return response.json()
        except requests.Timeout as exc:
            raise ProviderError("Anthropic-Timeout.") from exc
        except requests.RequestException as exc:
            raise ProviderError("Anthropic ist nicht erreichbar.") from exc
        except ValueError as exc:
            raise ProviderError("Anthropic lieferte ungültiges JSON.") from exc

    def test_connection(self) -> dict:
        return {"ok": True, "models": self.list_models()}

    def list_models(self) -> list[str]:
        data = self._request("GET", "/v1/models")
        return [model["id"] for model in data.get("data", []) if "id" in model]

    def generate_messages(
        self,
        messages: list[dict[str, str]],
        model=None,
        options=None,
    ) -> tuple[str, dict[str, int]]:
        payload = {
            "model": model or self.config.model_name,
            "max_tokens": 4096,
            "messages": messages,
            **(options or {}),
        }
        data = self._request("POST", "/v1/messages", json=payload)
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        if not text:
            raise ProviderError("Anthropic-Antwort enthält keinen Antworttext.")
        usage = data.get("usage", {})
        return text, {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
        }

    def generate(self, prompt: str, model=None, options=None) -> str:
        text, _ = self.generate_messages(
            [{"role": "user", "content": prompt}],
            model,
            options,
        )
        return text

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1_000_000 * self.config.input_cost_per_million
            + output_tokens / 1_000_000 * self.config.output_cost_per_million
        )

    def get_provider_metadata(self) -> dict:
        return {
            "name": self.config.name,
            "region": self.config.hosting_region,
            "eu": self.config.is_eu_hosted,
        }

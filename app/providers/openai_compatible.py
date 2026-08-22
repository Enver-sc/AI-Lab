import json
import requests
from .base import BaseProvider, ProviderError

class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, config, api_key, session=None):
        self.config, self.api_key, self.http = config, api_key, session or requests.Session()
    @property
    def headers(self):
        result = {"Accept":"application/json","Content-Type":"application/json"}
        if self.api_key: result["Authorization"] = f"Bearer {self.api_key}"
        try: custom = json.loads(self.config.custom_headers_json or "{}")
        except (TypeError, ValueError): custom = {}
        if isinstance(custom, dict): result.update(custom)
        return result
    def _request(self, method, path, **kwargs):
        try:
            response = self.http.request(method, f"{self.config.base_url.rstrip('/')}{path}", headers=self.headers, timeout=self.config.timeout_seconds, allow_redirects=False, **kwargs)
            if response.status_code in (401,403): raise ProviderError("Authentifizierung beim Provider fehlgeschlagen.")
            if response.status_code == 429: raise ProviderError("Rate-Limit des Providers erreicht.")
            if response.status_code >= 500: raise ProviderError("Der Provider meldet einen Serverfehler.")
            response.raise_for_status(); return response.json()
        except requests.Timeout as exc: raise ProviderError("Provider-Timeout.") from exc
        except requests.RequestException as exc: raise ProviderError("Provider ist nicht erreichbar.") from exc
        except ValueError as exc: raise ProviderError("Provider lieferte ungültiges JSON.") from exc
    def test_connection(self): return {"ok":True,"models":self.list_models()}
    def list_models(self): return [m["id"] for m in self._request("GET", "/models").get("data",[]) if "id" in m]
    def generate(self, prompt, model=None, options=None):
        data = self._request("POST", "/chat/completions", json={"model":model or self.config.model_name,"messages":[{"role":"user","content":prompt}], **(options or {})})
        try: return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc: raise ProviderError("Provider-Antwort enthält keinen Antworttext.") from exc
    def estimate_cost(self, i, o): return i/1e6*self.config.input_cost_per_million + o/1e6*self.config.output_cost_per_million
    def get_provider_metadata(self): return {"name":self.config.name,"region":self.config.hosting_region,"eu":self.config.is_eu_hosted}


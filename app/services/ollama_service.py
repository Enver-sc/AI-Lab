import requests

class OllamaError(RuntimeError): pass

class OllamaService:
    def __init__(self, base_url, model, timeout=60, session=None):
        self.base_url, self.model, self.timeout = base_url.rstrip("/"), model, timeout
        self.http = session or requests.Session()
    def list_models(self):
        try:
            response = self.http.get(f"{self.base_url}/api/tags", timeout=min(self.timeout, 10))
            response.raise_for_status(); data = response.json()
            return [item.get("name") for item in data.get("models", []) if item.get("name")]
        except (requests.RequestException, ValueError) as exc: raise OllamaError(f"Ollama ist nicht erreichbar oder antwortet ungültig: {exc}") from exc
    def generate(self, prompt: str, system: str = "", json_mode: bool = False, keep_alive: str | None = None) -> str:
        payload = {"model": self.model, "prompt": prompt, "system": system, "stream": False}
        if json_mode:
            payload["format"] = "json"
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        try:
            response = self.http.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            if response.status_code == 404: raise OllamaError(f"Ollama-Modell '{self.model}' wurde nicht gefunden.")
            response.raise_for_status(); data = response.json()
            if not isinstance(data.get("response"), str): raise OllamaError("Ollama-Antwort enthält kein gültiges Textfeld.")
            return data["response"]
        except requests.Timeout as exc: raise OllamaError("Ollama hat das Zeitlimit überschritten.") from exc
        except requests.RequestException as exc: raise OllamaError("Ollama ist nicht erreichbar.") from exc
        except ValueError as exc: raise OllamaError("Ollama lieferte ungültiges JSON.") from exc


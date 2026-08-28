import requests

class OllamaError(RuntimeError): pass

# Eigene Unterklasse fuer den Timeout-Fall, damit Aufrufer (z. B. das Guardian-
# Beweis-Logging) einen abgebrochenen Request von anderen Fehlern (Modell nicht
# gefunden, Verbindung abgelehnt, ungueltiges JSON) unterscheiden koennen.
class OllamaTimeoutError(OllamaError): pass

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
    def _generate_raw(self, prompt: str, system: str = "", json_mode: bool = False, keep_alive: str | None = None, options: dict | None = None, think: bool | None = None) -> dict:
        payload = {"model": self.model, "prompt": prompt, "system": system, "stream": False}
        if json_mode:
            payload["format"] = "json"
        if think is not None:
            payload["think"] = think
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        if options is not None:
            payload["options"] = options
        try:
            response = self.http.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            if response.status_code == 404: raise OllamaError(f"Ollama-Modell '{self.model}' wurde nicht gefunden.")
            response.raise_for_status(); data = response.json()
            if not isinstance(data.get("response"), str): raise OllamaError("Ollama-Antwort enthält kein gültiges Textfeld.")
            return data
        except requests.Timeout as exc: raise OllamaTimeoutError("Ollama hat das Zeitlimit überschritten.") from exc
        except requests.RequestException as exc: raise OllamaError("Ollama ist nicht erreichbar.") from exc
        except ValueError as exc: raise OllamaError("Ollama lieferte ungültiges JSON.") from exc
    def generate(self, prompt: str, system: str = "", json_mode: bool = False, keep_alive: str | None = None, options: dict | None = None, think: bool | None = None) -> str:
        return self._generate_raw(prompt, system, json_mode, keep_alive, options, think)["response"]
    def generate_raw(self, prompt: str, system: str = "", json_mode: bool = False, keep_alive: str | None = None, options: dict | None = None, think: bool | None = None) -> dict:
        # Wie generate(), liefert aber die volle Ollama-Antwort inkl. total_duration/
        # load_duration -- fuer Aufrufer, die diese Felder fuer Diagnose-Logging brauchen.
        return self._generate_raw(prompt, system, json_mode, keep_alive, options, think)


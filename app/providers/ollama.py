from .base import BaseProvider
from ..services.ollama_service import OllamaService

class OllamaProvider(BaseProvider):
    def __init__(self, base_url, model, timeout=60): self.service = OllamaService(base_url, model, timeout)
    def test_connection(self): return {"ok": True, "models": self.list_models()}
    def list_models(self): return self.service.list_models()
    def generate(self, prompt, model=None, options=None): return self.service.generate(prompt)
    def get_provider_metadata(self): return {"type":"ollama","base_url":self.service.base_url,"model":self.service.model}


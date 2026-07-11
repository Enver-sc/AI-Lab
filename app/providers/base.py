from abc import ABC, abstractmethod

class ProviderError(RuntimeError): pass
class BaseProvider(ABC):
    @abstractmethod
    def test_connection(self): ...
    @abstractmethod
    def list_models(self): ...
    @abstractmethod
    def generate(self, prompt, model=None, options=None): ...
    def estimate_cost(self, input_tokens, output_tokens): return 0
    @abstractmethod
    def get_provider_metadata(self): ...


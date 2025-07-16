from abc import ABC, abstractmethod

class LLMPlugin(ABC):
    @abstractmethod
    def name(self) -> str:
        """Return the name of the LLM provider/model."""
        pass

    @abstractmethod
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Call the LLM and return the generated text."""
        pass

    @abstractmethod
    def available_models(self) -> list[str]:
        """Return a list of available models for this provider."""
        pass
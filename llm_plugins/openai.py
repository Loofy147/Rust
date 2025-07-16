import os
import importlib
from .base import LLMPlugin

class OpenAIPlugin(LLMPlugin):
    def __init__(self):
        self._models = os.environ.get("OPENAI_MODELS", "text-davinci-003").split(",")
        self.rust_llm = importlib.import_module("reasoning_agent")

    def name(self) -> str:
        return "openai"

    def call(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        return self.rust_llm.call_openai(prompt, model, max_tokens, temperature)

    def available_models(self) -> list[str]:
        return [m.strip() for m in self._models if m.strip()]
import os
import requests
from .base import LLMPlugin

class HuggingFacePlugin(LLMPlugin):
    def __init__(self):
        self.api_key = os.environ.get("HF_API_KEY")
        self.api_url = "https://api-inference.huggingface.co/models/"
        self._models = os.environ.get("HF_MODELS", "gpt2,distilgpt2").split(",")

    def name(self) -> str:
        return "huggingface"

    def call(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature
            },
            "options": {"wait_for_model": True}
        }
        url = self.api_url + model
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data and "generated_text" in data[0]:
            return data[0]["generated_text"]
        elif isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"HF API error: {data['error']}")
        else:
            return str(data)

    def available_models(self) -> list[str]:
        return [m.strip() for m in self._models if m.strip()]
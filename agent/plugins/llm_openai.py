import openai
from tenacity import retry, wait_exponential, stop_after_attempt
from agent.interfaces import LLMPlugin

class OpenAILLM(LLMPlugin):
    def __init__(self, api_key):
        openai.api_key = api_key

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
    def call(self, prompt: str, **kwargs) -> str:
        response = openai.ChatCompletion.create(
            model=kwargs.get("model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            timeout=30,
            **kwargs
        )
        return response['choices'][0]['message']['content']
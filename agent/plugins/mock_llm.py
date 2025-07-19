from agent.interfaces import LLMPlugin

class MockLLM(LLMPlugin):
    def call(self, prompt: str, **kwargs) -> str:
        return f"MOCKED LLM RESPONSE for prompt: {prompt[:30]}..."
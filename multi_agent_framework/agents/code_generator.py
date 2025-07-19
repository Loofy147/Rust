from .base import Agent
import openai
import os

class CodeGeneratorAgent(Agent):
    def __init__(self, name, inbox, outboxes, config):
        super().__init__(name, inbox, outboxes, config)
        openai.api_key = os.getenv("OPENAI_API_KEY", config.get("openai_api_key", ""))

    def process(self, msg):
        # msg: {"type": "codegen", "prompt": ...}
        if msg["type"] == "codegen":
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": msg["prompt"]}],
                    max_tokens=512
                )
                code = response.choices[0].message["content"]
                self.send({"type": "code_result", "code": code, "prompt": msg["prompt"]}, "distribution")
            except Exception as e:
                self.logger.error(f"Code generation failed: {e}")
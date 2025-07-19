from transformers import pipeline


class CustomLLMAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["text_generation"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.generator = pipeline("text-generation", model="gpt2")

    def process(self, task):
        prompt = task.get("prompt", "Hello world!")
        result = self.generator(prompt, max_length=50)[0]["generated_text"]
        return {"result": result}

from transformers import pipeline

class SummarizerAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["summarization"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    def process(self, task):
        text = task.get("text", "")
        if not text:
            return {"error": "No text provided"}
        summary = self.summarizer(text, max_length=60, min_length=10, do_sample=False)[0]["summary_text"]
        return {"summary": summary}
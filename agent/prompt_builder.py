class PromptBuilder:
    def build(self, context: str, task: str) -> str:
        return f"Context: {context}\nTask: {task}\nAnswer:"
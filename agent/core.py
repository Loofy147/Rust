from agent.interfaces import LLMPlugin, KGPlugin, VectorStorePlugin, MetricsPlugin
from agent.prompt_builder import PromptBuilder

class ReasoningAgent:
    def __init__(self, llm: LLMPlugin, kg: KGPlugin, vector_store: VectorStorePlugin, metrics: MetricsPlugin, prompt_builder: PromptBuilder):
        self.llm = llm
        self.kg = kg
        self.vector_store = vector_store
        self.metrics = metrics
        self.prompt_builder = prompt_builder

    def handle_task(self, task: str):
        # 1. Query KG for context
        context = self.kg.query(task)
        # 2. Query vector store for similar vectors
        similar = self.vector_store.query([0.1, 0.2, 0.3], top_k=3)  # Example vector
        # 3. Build prompt
        prompt = self.prompt_builder.build(str(context), task)
        # 4. Call LLM
        answer = self.llm.call(prompt)
        # 5. Store answer in KG
        self.kg.store({"id": task, "type": "answer", "data": answer})
        # 6. Emit metrics
        self.metrics.emit("task_completed", 1, tags={"task": task})
        return answer
import pytest
from agent.core import ReasoningAgent
from agent.prompt_builder import PromptBuilder

class DummyLLM:
    def call(self, prompt, **kwargs):
        return "dummy answer"

class DummyKG:
    def query(self, query):
        return {"context": "dummy context"}
    def store(self, data):
        pass

class DummyVector:
    def query(self, vector, top_k):
        return ["sim1", "sim2"]
    def add(self, vector, metadata):
        pass

class DummyMetrics:
    def emit(self, metric_name, value, tags=None):
        pass

def test_reasoning_agent():
    agent = ReasoningAgent(DummyLLM(), DummyKG(), DummyVector(), DummyMetrics(), PromptBuilder())
    result = agent.handle_task("test-task")
    assert result == "dummy answer"
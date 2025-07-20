from abc import ABC, abstractmethod

class LLMPlugin(ABC):
    @abstractmethod
    def call(self, prompt: str, **kwargs) -> str:
        pass

class KGPlugin(ABC):
    @abstractmethod
    def query(self, query: str) -> dict:
        pass

    @abstractmethod
    def store(self, data: dict) -> None:
        pass

class VectorStorePlugin(ABC):
    @abstractmethod
    def add(self, vector, metadata):
        pass

    @abstractmethod
    def query(self, vector, top_k: int):
        pass

class MetricsPlugin(ABC):
    @abstractmethod
    def emit(self, metric_name: str, value, tags: dict = None):
        pass
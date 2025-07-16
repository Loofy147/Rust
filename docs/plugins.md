# Plugin System

ReasoningAgent is built around a flexible plugin system. You can swap in different implementations for:
- LLM (Language Model)
- KG (Knowledge Graph)
- Vector Store
- Metrics
- Prompt Builder

## How Plugins Work
- Plugins are loaded dynamically based on environment variables or config.
- Hot reload is supported in development mode (`DEV_MODE=1`).
- Mock plugins are available for local/dev (`MOCK_PLUGINS=1`).

## Creating a Plugin
1. Subclass the relevant interface in `agent/interfaces.py`.
2. Implement your plugin in `agent/plugins/`.
3. Update `agent/plugin_loader.py` to support your plugin.

### Example: Custom LLM Plugin
```python
from agent.interfaces import LLMPlugin

class MyLLM(LLMPlugin):
    def call(self, prompt: str, **kwargs) -> str:
        # Your LLM logic here
        return "My LLM response"
```

## Using Your Plugin
- Set the appropriate environment variable (e.g., `LLM_PLUGIN=myllm`).
- Restart the API (or use hot reload in dev mode).

## Built-in Plugins
- `OpenAILLM` (OpenAI API)
- `MockLLM` (for dev/testing)
- `SQLAlchemyKG` (SQLite/Postgres KG)
- `ChromaVectorStore` (Chroma vector DB)
- `PrintMetrics` (prints metrics to stdout)

See `agent/plugins/` for more.
from .openai import OpenAIPlugin
from .huggingface import HuggingFacePlugin

# Register all plugins here
_PLUGINS = {
    "openai": OpenAIPlugin(),
    "huggingface": HuggingFacePlugin(),
}

_DEFAULT = "openai"

def get_plugin(name: str):
    return _PLUGINS.get(name, _PLUGINS[_DEFAULT])

def list_plugins() -> list[str]:
    return list(_PLUGINS.keys())

def get_default_plugin():
    return _PLUGINS[_DEFAULT]
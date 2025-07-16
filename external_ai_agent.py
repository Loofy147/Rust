import os
import openai
import httpx
import pinecone
from abc import ABC, abstractmethod

class ExternalAIToolAdapter(ABC):
    @abstractmethod
    async def call(self, data, parameters: dict) -> dict:
        pass

class OpenAIAdapter(ExternalAIToolAdapter):
    def __init__(self, api_key: str):
        openai.api_key = api_key

    async def call(self, data, parameters: dict) -> dict:
        prompt = parameters.get('prompt', data)
        model = parameters.get('model', 'gpt-3.5-turbo')
        resp = await openai.ChatCompletion.acreate(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"result": resp['choices'][0]['message']['content']}

class HuggingFaceAdapter(ExternalAIToolAdapter):
    def __init__(self, api_key: str, model_url: str):
        self.api_key = api_key
        self.model_url = model_url

    async def call(self, data, parameters: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": data, **parameters}
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.model_url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

class PineconeAdapter(ExternalAIToolAdapter):
    def __init__(self, api_key: str, env: str, index: str):
        pinecone.init(api_key=api_key, environment=env)
        self.index = pinecone.Index(index)

    async def call(self, data, parameters: dict) -> dict:
        res = self.index.query(vector=[data], top_k=parameters.get('top_k', 5), include_metadata=True)
        return {"matches": res['matches']}

class ExternalAIToolAgent:
    def __init__(self):
        self.adapters = {}

    def register_adapter(self, name: str, adapter: ExternalAIToolAdapter):
        self.adapters[name] = adapter

    async def call_tool(self, tool_name: str, data, parameters: dict) -> dict:
        if tool_name not in self.adapters:
            raise ValueError(f"Tool {tool_name} not registered")
        return await self.adapters[tool_name].call(data, parameters)

# Registration example (to be used in app startup)
external_ai_agent = ExternalAIToolAgent()
if os.environ.get('OPENAI_API_KEY'):
    external_ai_agent.register_adapter('openai', OpenAIAdapter(api_key=os.environ['OPENAI_API_KEY']))
if os.environ.get('HUGGINGFACE_API_KEY'):
    external_ai_agent.register_adapter('huggingface', HuggingFaceAdapter(
        api_key=os.environ['HUGGINGFACE_API_KEY'],
        model_url=os.environ.get('HUGGINGFACE_MODEL_URL', 'https://api-inference.huggingface.co/models/bigscience/bloomz-560m')
    ))
if os.environ.get('PINECONE_API_KEY'):
    external_ai_agent.register_adapter('pinecone', PineconeAdapter(
        api_key=os.environ['PINECONE_API_KEY'],
        env=os.environ['PINECONE_ENV'],
        index=os.environ['PINECONE_INDEX']
    ))
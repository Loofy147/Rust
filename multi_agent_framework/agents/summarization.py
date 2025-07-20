import os
import openai
from distributed.ray_base import RayAgent
from distributed.celery_base import celery_app, CeleryAgent

openai.api_key = os.getenv("OPENAI_API_KEY", "")

class RaySummarizationAgent(RayAgent):
    def process(self, msg):
        if msg.get("type") == "summarize":
            text = msg["text"]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize: {text}"}],
                max_tokens=128
            )
            summary = response.choices[0].message["content"]
            self.logger.info(f"Summary: {summary}")

@celery_app.task(base=CeleryAgent, name="celery_summarization_task")
def celery_summarization_task(self, msg):
    if msg.get("type") == "summarize":
        text = msg["text"]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Summarize: {text}"}],
            max_tokens=128
        )
        summary = response.choices[0].message["content"]
        self.logger.info(f"Summary: {summary}")
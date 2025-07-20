import os
import openai
from distributed.ray_base import RayAgent
from distributed.celery_base import celery_app, CeleryAgent

openai.api_key = os.getenv("OPENAI_API_KEY", "")

class RayTranslationAgent(RayAgent):
    def process(self, msg):
        if msg.get("type") == "translate":
            text = msg["text"]
            target_lang = msg.get("target_lang", "fr")
            prompt = f"Translate to {target_lang}: {text}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=128
            )
            translation = response.choices[0].message["content"]
            self.logger.info(f"Translation: {translation}")

@celery_app.task(base=CeleryAgent, name="celery_translation_task")
def celery_translation_task(self, msg):
    if msg.get("type") == "translate":
        text = msg["text"]
        target_lang = msg.get("target_lang", "fr")
        prompt = f"Translate to {target_lang}: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=128
        )
        translation = response.choices[0].message["content"]
        self.logger.info(f"Translation: {translation}")
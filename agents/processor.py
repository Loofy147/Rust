import logging
from utils.retry import retry
from plugins.plugin_manager import PluginManager

class ProcessorAgent:
    def __init__(self, storage, plugin_manager: PluginManager, llm_config):
        self.storage = storage
        self.plugin_manager = plugin_manager
        self.llm_config = llm_config
        self.running = True

    @retry
    def call_llm(self, prompt):
        if self.llm_config['provider'] == 'openai':
            import openai
            openai.api_key = self.llm_config['api_key']
            response = openai.ChatCompletion.create(
                model=self.llm_config['model'],
                messages=[{"role": "user", "content": prompt}]
            )
            return response['choices'][0]['message']['content']
        # Add HuggingFace or other providers as needed
        return "[LLM response placeholder]"

    def process_task(self, task):
        text = task.get('text', '')
        # Preprocess
        tokens = self.plugin_manager.run('tokenizer', text)
        norm = self.plugin_manager.run('normalizer', text)
        vector = self.plugin_manager.run('vectorizer', norm or text)
        sentiment = self.plugin_manager.run('sentiment_analyzer', text)
        # LLM processing
        llm_result = self.call_llm(text)
        # Store result
        self.storage.save({'input': text, 'tokens': tokens, 'norm': norm, 'vector': vector, 'sentiment': sentiment, 'llm': llm_result})
        logging.info(f"Processed task: {text}")

    def run(self):
        while self.running:
            # Placeholder: get task from queue
            text = "Sample input text."
            # Preprocess with plugins
            tokens = self.plugin_manager.run('tokenizer', text)
            # LLM processing
            llm_result = self.call_llm(text)
            # Store result
            self.storage.save({'input': text, 'tokens': tokens, 'llm': llm_result})
            logging.info(f"Processed: {text}")
            break  # Remove for real queue processing
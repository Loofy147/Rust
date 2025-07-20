import logging
from collections import defaultdict
import asyncio

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def log_error(logger, error, context=None):
    logger.error(f"Error: {error} | Context: {context}")

class EventBus:
    """Simple in-process event bus for agent communication."""
    def __init__(self):
        self.subscribers = defaultdict(list)
    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)
    async def publish(self, event):
        for cb in self.subscribers[event['type']]:
            await cb(event)
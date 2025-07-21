from celery import Celery, Task
import logging
import time
from multi_agent_framework.distributed.message_broker import MessageBroker
from multi_agent_framework import message_format
import json

celery_app = Celery('agents', broker='amqp://guest:guest@rabbitmq:5672//')


class CeleryAgent(Task):
    abstract = True
    name = None
    config = None
    state = "idle"
    logger = logging.getLogger("CeleryAgent")
    last_heartbeat = time.time()

    def __init__(self):
        self.message_broker = MessageBroker()
        self.message_broker.declare_queue(self.name)
        self.message_broker.bind_queue('agent_exchange', self.name, self.name)

    def run(self):
        self.message_broker.consume(self.name, self.process_message)

    def process_message(self, ch, method, properties, body):
        self.logger.info(f"Received message: {body}")
        self.state = "busy"
        try:
            msg = message_format.parse_jsonrpc(body.decode('utf-8'))
            if "method" in msg:
                result = self.process(msg['params'])
                response = message_format.create_jsonrpc_response(result, msg['id'])
                if properties.reply_to:
                    self.message_broker.publish(exchange='', routing_key=properties.reply_to, body=json.dumps(response))
            else:
                self.logger.error(f"Invalid JSON-RPC message: {msg}")

        except Exception as e:
            self.logger.error(f"Error: {e}")
        finally:
            self.state = "idle"
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def process(self, body):
        raise NotImplementedError

    def heartbeat(self):
        self.last_heartbeat = time.time()
        return self.state
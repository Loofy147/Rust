import unittest
import time
import json
from unittest.mock import MagicMock, patch
from multi_agent_framework.distributed.message_broker import MessageBroker
from multi_agent_framework.distributed.celery_base import CeleryAgent, celery_app
from multi_agent_framework import message_format

class TestCommunication(unittest.TestCase):

    def setUp(self):
        self.broker = MessageBroker(broker_url='amqp://guest:guest@localhost:5672/')
        self.broker.connect()
        self.broker.channel.exchange_declare(exchange='test_exchange', exchange_type='direct')
        self.broker.channel.queue_declare(queue='test_queue')
        self.broker.channel.queue_bind(exchange='test_exchange', queue='test_queue', routing_key='test_key')

    def tearDown(self):
        self.broker.channel.queue_delete(queue='test_queue')
        self.broker.channel.exchange_delete(exchange='test_exchange')
        self.broker.close()

    def test_publish_consume(self):
        message_body = "Hello, RabbitMQ!"
        self.broker.publish('test_exchange', 'test_key', message_body)

        method_frame, header_frame, body = self.broker.channel.basic_get(queue='test_queue')
        self.assertIsNotNone(method_frame)
        self.assertEqual(body.decode(), message_body)
        self.broker.channel.basic_ack(method_frame.delivery_tag)

    @patch('multi_agent_framework.distributed.celery_base.CeleryAgent.process')
    def test_celery_agent_e2e(self, mock_process):
        # 1. Setup Celery Agent
        class MyTestAgent(CeleryAgent):
            name = 'my_test_agent'

            def __init__(self):
                super().__init__()

            def process(self, body):
                return {"status": "processed", "data": body}

        celery_app.register_task(MyTestAgent())

        # 2. Start consumer in a thread
        agent_instance = MyTestAgent()

        import threading
        consumer_thread = threading.Thread(target=agent_instance.run)
        consumer_thread.daemon = True
        consumer_thread.start()
        time.sleep(1) # Give it a moment to connect

        # 3. Publish a message
        request_id = "123"
        params = {"test": "data"}
        request_msg = message_format.create_jsonrpc_request("process", params, request_id)

        # Create a unique reply_to queue
        reply_queue_name = self.broker.channel.queue_declare(queue='', exclusive=True).method.queue

        self.broker.publish(
            exchange='agent_exchange',
            routing_key='my_test_agent',
            body=json.dumps(request_msg),
            reply_to=reply_queue_name
        )

        # 4. Wait for and check response
        time.sleep(1)
        method_frame, header_frame, body = self.broker.channel.basic_get(queue=reply_queue_name)

        self.assertIsNotNone(method_frame, "Should have received a response")

        response = json.loads(body.decode())

        self.assertEqual(response['id'], request_id)
        self.assertEqual(response['result']['status'], 'processed')
        self.assertEqual(response['result']['data'], params)

        # 5. Teardown
        self.broker.channel.basic_ack(method_frame.delivery_tag)
        # Stop consumer thread by closing connection
        agent_instance.message_broker.close()
        consumer_thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()

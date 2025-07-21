import pika
import os
import logging

class MessageBroker:
    def __init__(self, broker_url=None):
        self.broker_url = broker_url or os.environ.get("RABBITMQ_URL")
        if not self.broker_url:
            raise ValueError("RabbitMQ broker URL not provided.")
        self.connection = None
        self.channel = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.broker_url))
            self.channel = self.connection.channel()
            self.logger.info("Connected to RabbitMQ.")
        except pika.exceptions.AMQPConnectionError as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed.")

    def publish(self, exchange, routing_key, body, reply_to=None):
        if not self.channel:
            self.connect()
        try:
            properties = pika.BasicProperties(reply_to=reply_to)
            self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body, properties=properties)
            self.logger.info(f"Published message to exchange '{exchange}' with routing key '{routing_key}'.")
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            raise

    def consume(self, queue_name, callback):
        if not self.channel:
            self.connect()

        self.channel.basic_consume(queue=queue_name, on_message_callback=callback)
        try:
            self.logger.info(f"Starting to consume messages from queue '{queue_name}'.")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.logger.info("Stopped consuming messages.")
        finally:
            self.close()

    def declare_exchange(self, exchange, exchange_type='direct'):
        if not self.channel:
            self.connect()
        self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type)
        self.logger.info(f"Declared exchange '{exchange}' of type '{exchange_type}'.")

    def declare_queue(self, queue_name):
        if not self.channel:
            self.connect()
        self.channel.queue_declare(queue=queue_name)
        self.logger.info(f"Declared queue '{queue_name}'.")

    def bind_queue(self, exchange, queue_name, routing_key):
        if not self.channel:
            self.connect()
        self.channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)
        self.logger.info(f"Bound queue '{queue_name}' to exchange '{exchange}' with routing key '{routing_key}'.")

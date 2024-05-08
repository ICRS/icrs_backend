import json
import logging
import os
import time
import sys

import pika
import pika.channel
import pika.delivery_mode

from src.printer_farm import PrinterFarm


DEBUG = str(os.getenv('DEBUG', False)).lower() in ['true', '1']  # noqa  # pylint: disable=invalid-envvar-default
if DEBUG:
    from dotenv import load_dotenv
    load_dotenv(override=True)

__all__ = ["QueueManager"]


class QueueManager:
    def __init__(self, printer_names: list[str],
                 printer_suffix: str,
                 rabbitmq_host: str = "localhost",
                 rabbitmq_port: int = 5672,
                 rabbitmq_queue: str = "print_queue") -> None:
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_queue = rabbitmq_queue
        self.printer_farm = PrinterFarm(printer_names, printer_suffix, address=DEBUG)
        logging.info(str(self.printer_farm))
        self.running = True
        self.rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=str(self.rabbitmq_host),
                port=int(self.rabbitmq_port)
                )
            )
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        self.rabbitmq_channel.queue_declare(queue=self.rabbitmq_queue,
                                            durable=True)

        self.rabbitmq_channel.basic_qos(prefetch_count=1)
        self.rabbitmq_channel.basic_consume(queue=self.rabbitmq_queue,
                                            on_message_callback=self.rabbit_callback)

        self.rabbitmq_channel.start_consuming()

    
    def rabbit_callback(self, ch: pika.channel.Channel, method, properties, body: bytes):
        data = body.decode()
        try:
            request = dict(json.loads(data))
            logging.info(f"Received {request}")
        except json.JSONDecodeError:
            logging.error(f"Received invalid data: {data}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        gcode = request.get("gcode", None)
        filename = request.get("filename", None)
        printer_type = request.get("printer_type", None)
        if not gcode or not filename or not printer_type:
            logging.error(f"Received invalid request: {request}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        if not self.queue_printer(printer_type, filename, gcode):
            logging.error(f"Failed to queue printer: {printer_type}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def queue_printer(self, printer_type: str, filename: str, gcode: str) -> bool:
        # Find available rinter and send gcode and start
        pass
        

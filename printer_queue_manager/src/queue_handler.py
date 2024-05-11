import io
import json
import logging
import os
import time

import pika
import pika.channel
import pika.delivery_mode
import bambulabs_api as blapi

from src.printer_farm import PrinterFarm
from src.printer_gateway import PrinterGateway


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
        self.printer_farm = PrinterFarm(
            printer_names, printer_suffix, address=DEBUG)
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
        self.rabbitmq_channel.basic_consume(
            queue=self.rabbitmq_queue,
            on_message_callback=self.rabbit_callback)

        self.rabbitmq_channel.start_consuming()

    def rabbit_callback(
            self, ch: pika.channel.Channel,
            method,
            properties,
            body: bytes):
        # Decode bytes sent from rabbitmq queue
        data: str = body.decode()
        try:
            # Parse bytes to json and then to dict
            json_data = json.loads(data)
            request = dict(json_data)
        except json.JSONDecodeError as e:
            # If data is not valid json, log error and reject message without
            # requeueing (The object in the queue might be invalid)
            logging.error(f"Received invalid data: {data}: {str(e)}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Get all required fields from the request
        gcode = request.get("gcode", None)
        filename = request.get("filename", None)
        printer_type = request.get("printer_type", None)
        # Check if any of the required fields are missing. If so, log error
        # and reject message without requeueing
        if not gcode or not filename or not printer_type:
            logging.error(f"Received invalid request: {request}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Queue the job to a printer. If the job is not queued, log error and
        # reject message with requeueing. Everything was valid but couldn't
        # queue job
        if not self.queue_printer(printer_type, filename, gcode):
            logging.error(f"No available printers: {printer_type}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
            time.sleep(5)
            return

        # If everything was successful, acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    def queue_printer(
            self,
            printer_type: str,
            filename: str,
            gcode: str) -> bool:
        # Find available rinter and send gcode and start
        printers: list[str] = self.printer_farm.get_printers(
            printer_type=printer_type)
        if not printers:
            logging.error(f"Printer type {printer_type} not found")
            return False

        logging.info(f"Available printers: {printers}")

        for name in printers:
            try:
                state = self.printer_farm.get(name, "state")

                if state in [blapi.GcodeState.IDLE, blapi.GcodeState.FINISH]:
                    printer: PrinterGateway = self.printer_farm.printers.get(
                        name)
                    file = io.BytesIO(gcode.encode())
                    file.name = filename
                    logging.info(f"Uploading gcode to printer {name}")
                    printer.upload_gcode(file)
                    file.close()
                    printer.start_print(filename, 0)
                    logging.info(f"Started printer {name} with {filename}")
                    return True

            except Exception as e:
                logging.error(f"Failed to queue printer {name}: {str(e)}")
                return False

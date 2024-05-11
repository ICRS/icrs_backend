import json
import logging

from src.queue_handler import QueueManager


settings = json.load(open("endpoints.json", "r", encoding="utf-8"))
PRINTER_NAMES = list(settings["PRINTER_NAMES"])
PRINTER_GATEWAY_ENDPOINT_SUFFIX = settings["PRINTER_GATEWAY_ENDPOINT_SUFFIX"]

rabbitmq_settings = json.load(open("rabbitmq.json", "r", encoding="utf-8"))
RABBITMQ_HOST = rabbitmq_settings["ENDPOINT"]
RABBITMQ_PORT = rabbitmq_settings["PORT"]
RABBITMQ_QUEUE = rabbitmq_settings["QUEUE"]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ])

if __name__ == '__main__':
    queue_manager = QueueManager(PRINTER_NAMES,
                                 PRINTER_GATEWAY_ENDPOINT_SUFFIX,
                                 RABBITMQ_HOST,
                                 RABBITMQ_PORT,
                                 RABBITMQ_QUEUE)

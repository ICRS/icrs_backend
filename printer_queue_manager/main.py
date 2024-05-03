import json
import logging

from src.queue_handler import QueueManager


settings = json.load(open("settings.json", "r", encoding="utf-8"))
PRINTER_NAMES = list(settings["PRINTER_NAMES"])
PRINTER_GATEWAY_ENDPOINT_SUFFIX = settings["PRINTER_GATEWAY_ENDPOINT_SUFFIX"]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ])

if __name__ == '__main__':
    queue_manager = QueueManager(PRINTER_NAMES, PRINTER_GATEWAY_ENDPOINT_SUFFIX)

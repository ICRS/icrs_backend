import json
import os
import dotenv

from bambulabs_api import Printer

__all__ = ["printer",
           "PRINTER_NAME"
           ]

dotenv.load_dotenv()


def get_env_string(env_name: str) -> str:
    return str(os.getenv(env_name)).strip()


HOSTNAME = get_env_string("HOSTNAME")
ACCESS_CODE = get_env_string("ACCESS_CODE")
PRINTER_SERIAL = get_env_string("PRINTER_SERIAL")

PRINTER_NAME = get_env_string("PRINTER_NAME")
PRINTER_NAME_TITLE = PRINTER_NAME.replace("-", " ").title()

DATABASE_URL = get_env_string("DATABASE_ADAPTER_ENDPOINT")

# =============================================================================
# RabbitMQ Settings
# =============================================================================
rabbitmq_settings = json.load(open("rabbitmq.json", "r", encoding="utf-8"))
RABBITMQ_EXCHANGE = rabbitmq_settings["EXCHANGE_NAME"]

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
# =============================================================================

printer = Printer(HOSTNAME, ACCESS_CODE, PRINTER_SERIAL)

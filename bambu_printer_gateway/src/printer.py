import json
import logging
import os
import dotenv

from bambulabs_api import Printer

from src import discovery
from src.camera import RtspsCamera, RTSPS_PORT

__all__ = ["printer",
           "PRINTER_NAME",
           "PRINTER_SERIAL",
           "PRINTER_IP",
           "CAMERA_TYPE",
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

# =============================================================================
# Printer discovery
# =============================================================================
# HOSTNAME is only a hint: if the printer has moved (DHCP), it is found again
# by serial in DISCOVERY_SUBNETS (comma-separated, empty disables the search).
DISCOVERY_SUBNETS = os.getenv("DISCOVERY_SUBNETS", "").strip()

PRINTER_IP = discovery.find_printer(
    PRINTER_SERIAL, HOSTNAME if HOSTNAME not in ("", "None") else None,
    DISCOVERY_SUBNETS) or HOSTNAME
if PRINTER_IP != HOSTNAME:
    logging.warning(f"Printer {PRINTER_SERIAL} is at {PRINTER_IP}, not HOSTNAME {HOSTNAME}")  # noqa: E501

# P2S/X1/H2D serve RTSPS on 322 when LAN Only Liveview is on; P1/A1 use 6000
CAMERA_TYPE = "rtsps" if discovery.port_open(PRINTER_IP, RTSPS_PORT) else "tls6000"
logging.info(f"Printer {PRINTER_SERIAL} at {PRINTER_IP}, camera: {CAMERA_TYPE}")
# =============================================================================

printer = Printer(PRINTER_IP, ACCESS_CODE, PRINTER_SERIAL)
if CAMERA_TYPE == "rtsps":
    printer.camera_client = RtspsCamera(PRINTER_IP, ACCESS_CODE)


import logging
import os
import dotenv

from .bambulab_printer_camera import PrinterCamera
from .bambulab_printer_ftp import PrinterFTPClient
from .bambulab_printer_mqtt import PrinterMQTTClient

dotenv.load_dotenv()

def get_env_string(env_name: str) -> str:
    return str(os.getenv(env_name)).strip()


HOSTNAME = get_env_string("HOSTNAME")
ACCESS_CODE = get_env_string("ACCESS_CODE")
PRINTER_SERIAL = get_env_string("PRINTER_SERIAL")

logging.info("Connecting to printer camera...")
camera = PrinterCamera(HOSTNAME, ACCESS_CODE)

printerMQTTClient = PrinterMQTTClient(HOSTNAME, ACCESS_CODE, PRINTER_SERIAL)

printerFTPClient = PrinterFTPClient(HOSTNAME, ACCESS_CODE)
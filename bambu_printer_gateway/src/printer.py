import os
import dotenv

from bambulabs_api import Printer

__all__ = ["printer"]

dotenv.load_dotenv()


def get_env_string(env_name: str) -> str:
    return str(os.getenv(env_name)).strip()


HOSTNAME = get_env_string("HOSTNAME")
ACCESS_CODE = get_env_string("ACCESS_CODE")
PRINTER_SERIAL = get_env_string("PRINTER_SERIAL")
PRINTER_NAME = get_env_string("PRINTER_NAME")

printer = Printer(HOSTNAME, ACCESS_CODE, PRINTER_SERIAL)

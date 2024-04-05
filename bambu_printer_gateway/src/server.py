import os
import dotenv
import logging

from .bambulab_printer_mqtt import PrinterMQTTClient
from .bambulab_printer_camera import PrinterCamera

from fastapi import APIRouter

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()

hostname = str(os.getenv("HOSTNAME")).strip()
access_code = str(os.getenv("ACCESS_CODE")).strip()
printer_serial = str(os.getenv("PRINTER_SERIAL")).strip()

print("Connecting to printer camera...")
camera = PrinterCamera(hostname, access_code)

print("Connecting to printer MQTT client...")
printerMQTTClient = PrinterMQTTClient(hostname, access_code, printer_serial)
printerMQTTClient.connect()
printerMQTTClient.start()


@router.get("/printer/status/time")
async def printer_get_time() -> dict:
    print("Received Request")
    return {"time": time} if (time := printerMQTTClient
                              .get_remaining_time()) is not None else {}

@router.get("/printer/status/percentage")
async def printer_get_percentage():
    return {"percentage": percentage} if (percentage := printerMQTTClient
                                          .get_last_print_percentage()
                                          ) is not None else {}


@router.get("/printer/camera")
async def printer_get_camera():
    try:
        last_frame = camera.get_frame()
    except Exception as e:
        print(str(e))
        return {"error": str(e)}
    return {"frame": frame} if (frame := last_frame
                                ) is not None else {}


@router.get("/printer/status/state")
async def printer_get_state():
    return {"state": printerMQTTClient.get_printer_state()}


@router.get("/printer/status/print_speed")
async def get_print_speed():
    return {"print_speed": printerMQTTClient.get_print_speed()}


@router.get("/printer/status/file_name")
async def get_file_name():
    return {"file_name": printerMQTTClient.get_file_name()}


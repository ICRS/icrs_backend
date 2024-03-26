import os
import dotenv

from .bambulab_printer_mqtt import PrinterMQTTClient
from .printer_camera_ftp import PrinterCamera

from fastapi import APIRouter

dotenv.load_dotenv()

router = APIRouter()

hostname = str(os.getenv("HOSTNAME")).strip()
access_code = str(os.getenv("ACCESS_CODE")).strip()
printer_serial = str(os.getenv("PRINTER_SERIAL")).strip()

print("Connecting to printer camera...")
camera = PrinterCamera(hostname, access_code)
camera.connect()

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

import os

from .bambulab_printer_mqtt import PrinterMQTTClient
from .printer_camera_ftp import PrinterCamera

from fastapi import APIRouter


router = APIRouter()

hostname = str(os.getenv("HOSTNAME")).strip()
access_code = str(os.getenv("ACCESS_CODE")).strip()
printer_serial = str(os.getenv("PRINTER_SERIAL")).strip()

camera = PrinterCamera(hostname, access_code)
camera.connect()

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
    return {"frame": frame} if (frame := camera.get_frame()
                                ) is not None else {}

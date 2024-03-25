from fastapi import APIRouter, HTTPException
from .bambulab_printer_mqtt import PrinterMQTTClient

import os

router = APIRouter()

hostname = str(os.getenv("HOSTNAME")).strip()
access_code = str(os.getenv("ACCESS_CODE")).strip()
printer_serial = str(os.getenv("PRINTER_SERIAL")).strip()

printerMQTTClient = PrinterMQTTClient(hostname, access_code, printer_serial)
printerMQTTClient.connect()
printerMQTTClient.start()


@router.get("/printer/status/time")
async def printer_get_time() -> dict:
    print("Received Request")
    return {"time": time} if (time := printerMQTTClient.get_remaining_time()) is not None else {}


@router.get("/printer/status/percentage")
async def printer_get_percentage():
    return {"percentage": percentage} if (percentage := printerMQTTClient.get_last_print_percentage()) is not None else {}


@router.get("/printer/status/state")
async def printer_get_state():
    return {"state": printerMQTTClient.get_printer_state()}


@router.get("/printer/status/print_speed")
async def get_print_speed():
    return {"print_speed": printerMQTTClient.get_print_speed()}


@router.get("/printer/status/file_name")
async def get_file_name():
    return {"file_name": printerMQTTClient.get_file_name()}

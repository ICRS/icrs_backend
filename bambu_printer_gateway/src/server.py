import os
import dotenv
import logging

from fastapi import APIRouter

from .bambulab_printer_mqtt import PrinterMQTTClient  # noqa
from .bambulab_printer_camera import PrinterCamera

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()

HOSTNAME = str(os.getenv("HOSTNAME")).strip()
ACCESS_CODE = str(os.getenv("ACCESS_CODE")).strip()
PRINTER_SERIAL = str(os.getenv("PRINTER_SERIAL")).strip()

print("Connecting to printer camera...")
camera = PrinterCamera(HOSTNAME, ACCESS_CODE)

print("Connecting to printer MQTT client...")
printerMQTTClient = PrinterMQTTClient(HOSTNAME, ACCESS_CODE, PRINTER_SERIAL)
printerMQTTClient.connect()
printerMQTTClient.start()


@router.get("/printer/status/time")
async def printer_get_time() -> dict:
    """
    Get the remaining time for the current print

    Returns:
        dict: time
    """
    print("Received Request")
    return {"time": time} if (time := printerMQTTClient
                              .get_remaining_time()) is not None else {}


@router.get("/printer/status/percentage")
async def printer_get_percentage() -> dict:
    """
    Get the last print percentage completed

    Returns:
        dict : percentage
    """
    return {"percentage": percentage} if (percentage := printerMQTTClient
                                          .get_last_print_percentage()
                                          ) is not None else {}


@router.get("/printer/status/state")
async def printer_get_state():
    """
    Get the current state of the printer

    Returns:
        dict: printer_state
    """
    return {"state": printerMQTTClient.get_printer_state()}


@router.get("/printer/status/print_speed")
async def get_print_speed():
    """
    Get the print speed of the printer

    Returns:
        dict: print_speed
    """
    return {"print_speed": printerMQTTClient.get_print_speed()}


@router.get("/printer/status/file_name")
async def get_file_name():
    """
    Get the file name of the current/last print

    Returns:
        dict: file_name
    """
    return {"file_name": printerMQTTClient.get_file_name()}


@router.get("/printer/camera")
async def printer_get_camera():
    """
    Get the current frame from the printer camera

    Returns:
        dict: frame of the camera
    """
    try:
        last_frame = camera.get_frame()
    except Exception as e:
        print(str(e))
        return {"error": str(e)}
    return {"frame": frame} if (frame := last_frame
                                ) is not None else {}


@router.get("/printer/led/state")
async def printer_get_led_state():
    """
    Get the current state of the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": led_state} if (led_state := printerMQTTClient
                                        .get_light_state()) is not None else {}

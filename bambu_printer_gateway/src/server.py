from typing import BinaryIO
import logging
from typing import BinaryIO
from fastapi import APIRouter, HTTPException, UploadFile

from .printer_transports import camera, printerFTPClient, printerMQTTClient
from .filament import AMSFilamentSettings, Filament


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()
status_router = APIRouter(prefix="/printer/status", tags=["Printer Status"])

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])


logging.info("Connecting to printer MQTT client...")
printerMQTTClient.connect()
printerMQTTClient.start()


@status_router.get("/time")
async def printer_get_time() -> dict:
    """
    Get the remaining time for the current print

    Returns:
        dict: time
    """
    print("Received Request")
    return {"time": time} if (time := printerMQTTClient
                              .get_remaining_time()) is not None else {}


@status_router.get("/percentage")
async def printer_get_percentage() -> dict:
    """
    Get the last print percentage completed

    Returns:
        dict : percentage
    """
    return {"percentage": percentage} if (percentage := printerMQTTClient
                                          .get_last_print_percentage()
                                          ) is not None else {}


@status_router.get("/state")
async def printer_get_state():
    """
    Get the current state of the printer

    Returns:
        dict: printer_state
    """
    return {"state": printerMQTTClient.get_printer_state()}


@status_router.get("/print_speed")
async def get_print_speed():
    """
    Get the print speed of the printer

    Returns:
        dict: print_speed
    """
    return {"print_speed": printerMQTTClient.get_print_speed()}


@status_router.get("/file_name")
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


@router.post("/printer/led/on")
async def printer_led_on():
    """
    Turn on the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": printerMQTTClient.turn_light_on()}


@router.post("/printer/led/off")
async def printer_led_off():
    """
    Turn off the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": printerMQTTClient.turn_light_off()}


@router.post("/printer/upload/gcode")
async def upload_gcode_file(file: UploadFile):
    try:
        io_file: BinaryIO = file.file
        if file.filename:
            return printerFTPClient.upload_file(io_file, file.filename)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Exception occurred during file upload: {e}")
    finally:
        file.file.close()

    return


@router.post("/printer/print/start")
async def start_print(filename: str, plate_number: int):
    return printerMQTTClient.start_print_3mf(filename, plate_number=plate_number)


@router.post("/printer/print/stop")
async def stop_print():
    return printerMQTTClient.stop_print()


@router.post("/printer/print/pause")
async def pause_print():
    return printerMQTTClient.pause_print()


@router.post("/printer/print/resume")
async def resume_print():
    return printerMQTTClient.resume_print()


@router.post("/printer/bed/temperature")
async def set_bed_temperature(temperature: int):
    return printerMQTTClient.set_bed_temperature(temperature)


@router.post("/printer/calibration/home")
async def home_printer():
    return printerMQTTClient.auto_home()


@router.post("/printer/axis/z")
async def move_z_axis(distance: int):
    return printerMQTTClient.set_bed_height(distance)


@router.post("/printer/filament/printer")
async def set_filament_printer(
    color: str,
    filament: AMSFilamentSettings | str
):
    assert len(color) == 6, "Color must be a 6 character hex code"

    if isinstance(filament, str) or isinstance(filament, AMSFilamentSettings):
        filament = Filament(filament)
    else:
        raise ValueError(
            "Filament must be a string or AMSFilamentSettings object")

    return printerMQTTClient.set_printer_filament(filament, color)


@router.post("/printer/nozzle/temperature")
async def set_nozzle_temperature(temperature: int) -> bool:
    return printerMQTTClient.set_nozzle_temperature(temperature)


@router.post("/printer/print/speed_lvl")
async def set_print_speed(speed_lvl: int) -> bool:
    assert 0 <= speed_lvl <= 3, "Speed level must be between 0 and 3"
    return printerMQTTClient.set_print_speed_lvl(speed_lvl)

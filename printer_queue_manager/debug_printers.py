from typing import BinaryIO
import dotenv
import logging

from pydantic import BaseModel
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, UploadFile

import bambulabs_api as blapi
from bambulabs_api import AMSFilamentSettings

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

router = APIRouter()

state = blapi.GcodeState.IDLE


@router.get("/time")
async def printer_get_time() -> dict:
    """
    Get the remaining time for the current print

    Returns:
        dict: time
    """
    return {"time": 10}


@router.get("/percentage")
async def printer_get_percentage() -> dict:
    """
    Get the last print percentage completed

    Returns:
        dict : percentage
    """
    return {"percentage": 90}


@router.get("/state")
async def printer_get_state():
    """
    Get the current state of the printer

    Returns:
        dict: printer_state
    """
    return {"state": state}


@router.get("/print_speed")
async def get_print_speed():
    """
    Get the print speed of the printer

    Returns:
        dict: print_speed
    """
    return {"print_speed": 10}


@router.get("/file_name")
async def get_file_name():
    """
    Get the file name of the current/last print

    Returns:
        dict: file_name
    """
    return {"file_name": "test.gcode"}


@router.get("/printer/camera")
async def printer_get_camera():
    """
    Get the current frame from the printer camera

    Returns:
        dict: frame of the camera
    """
    return {"frame": ""}


@router.get("/printer/led/state")
async def printer_get_led_state():
    """
    Get the current state of the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": "on"}


@router.post("/printer/led/on")
async def printer_led_on():
    """
    Turn on the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": True}


@router.post("/printer/led/off")
async def printer_led_off():
    """
    Turn off the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": True}


@router.post("/printer/upload/gcode")
async def upload_gcode_file(file: UploadFile):
    try:
        logging.info(f"Uploaded gcode file: {file}")
        io_file: BinaryIO = file.file  # noqa: F841
        if file.filename:
            return True

    except Exception as e:
        # noqa  # pylint: disable=raise-missing-from
        raise HTTPException(status_code=500,
                            detail=f"Exception occurred during file upload: {e}")  # noqa
    finally:
        file.file.close()
    return


class StartPrintRequest(BaseModel):
    filename: str
    plate_number: int


@router.post("/printer/print/start")
async def start_print(request: StartPrintRequest):
    global state
    logging.info(
        f"Starting {request.filename} on plate {request.plate_number}")
    state = blapi.GcodeState.RUNNING


@router.post("/printer/print/stop")
async def stop_print():
    global state
    state = blapi.GcodeState.IDLE


@router.post("/printer/print/pause")
async def pause_print():
    global state
    state = blapi.GcodeState.PAUSE


@router.post("/printer/print/resume")
async def resume_print():
    global state
    state = blapi.GcodeState.RUNNING


@router.post("/printer/bed/temperature")
async def set_bed_temperature(temperature: int):
    return True


@router.post("/printer/calibration/home")
async def home_printer():
    return True


@router.post("/printer/axis/z")
async def move_z_axis(distance: int):
    return True


@router.post("/printer/filament/printer")
async def set_filament_printer(color: str,
                               filament: AMSFilamentSettings | str):
    return True


@router.post("/printer/nozzle/temperature")
async def set_nozzle_temperature(temperature: int) -> bool:
    return True


@router.post("/printer/print/speed_lvl")
async def set_print_speed(speed_lvl: int) -> bool:
    return True


@router.post("/printer/file/delete")
async def delete_file(file_path: str) -> str:
    return True


@router.post("/printer/calibration")
async def calibrate_printer(bed_level: bool = True,
                            motor_noise_calibration: bool = True,
                            vibration_compensation: bool = True):
    return True


@router.post("/printer/filament/printer/load")
async def load_filament_spool():
    return True


@router.post("/printer/filament/printer/unload")
async def unload_filament_spool():
    return True


@router.post("/printer/filament/retry")
async def retry_filament_action():
    return True


app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("debug_printers:app", host="127.0.0.1", port=6000, reload=True)

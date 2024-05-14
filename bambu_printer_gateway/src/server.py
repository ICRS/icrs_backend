import base64
from datetime import datetime
from io import BytesIO
from typing import BinaryIO
import logging

from fastapi import APIRouter, HTTPException, UploadFile, Response
from bambulabs_api import AMSFilamentSettings, GcodeState
from PIL import Image, ImageDraw, ImageFont

from .printer import printer


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()
status_router = APIRouter(prefix="/printer/status", tags=["Printer Status"])

logging.info("Connecting to printer...")
printer.connect()


@status_router.get("/time")
async def printer_get_time() -> dict:
    """
    Get the remaining time for the current print

    Returns:
        dict: time
    """
    print("Received Request")
    return {"time": time} if (time := printer
                              .get_time()) is not None else {}


@status_router.get("/percentage")
async def printer_get_percentage() -> dict:
    """
    Get the last print percentage completed

    Returns:
        dict : percentage
    """
    return {"percentage": percentage} if (percentage := printer
                                          .get_percentage()
                                          ) is not None else {}


@status_router.get("/state")
async def printer_get_state():
    """
    Get the current state of the printer

    Returns:
        dict: printer_state
    """
    return {"state": printer.get_state()}


@status_router.get("/print_speed")
async def get_print_speed():
    """
    Get the print speed of the printer

    Returns:
        dict: print_speed
    """
    return {"print_speed": printer.get_print_speed()}


@status_router.get("/file_name")
async def get_file_name():
    """
    Get the file name of the current/last print

    Returns:
        dict: file_name
    """
    return {"file_name": printer.get_file_name()}


@router.get("/printer/camera")
async def printer_get_camera():
    """
    Get the current frame from the printer camera

    Returns:
        dict: frame of the camera
    """
    try:
        frame = printer.get_camera_frame()
        im = Image.open(BytesIO(base64.b64decode(frame)))

        width, height = im.size
        draw = ImageDraw.Draw(im)
        # Create text in the form day-month-year hour:minute:second
        text = str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        FONT_SIZE = 50
        font = ImageFont.load_default(FONT_SIZE)
        textwidth = draw.textlength(text, font)
        # calculate the x,y coordinates of the text
        margin = 10
        x = width - textwidth - margin
        y = height - FONT_SIZE - margin
        # draw watermark in the bottom right corner
        draw.text((x, y), text, font=font, fill=(0, 0, 100, 255))

        with BytesIO() as buffered:
            im.save(buffered, format="JPEG")
            contents = buffered.getvalue()
            frame_b64 = base64.b64encode(contents)

            last_frame = Response(frame_b64,
                                  media_type="image/jpeg")
    except Exception as e:  # noqa  # pylint: disable=broad-exception-caught
        logging.error(f"Error occurred while getting camera frame: {e}")    # noqa  # pylint: disable=logging-fstring-interpolation
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
    return {"led_state": led_state} if (led_state := printer
                                        .get_light_state()) is not None else {}


@router.post("/printer/led/on")
async def printer_led_on():
    """
    Turn on the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": printer.turn_light_on()}


@router.post("/printer/led/off")
async def printer_led_off():
    """
    Turn off the printer LED

    Returns:
        dict : led_state
    """
    return {"led_state": printer.turn_light_off()}


@router.post("/printer/upload/gcode")
async def upload_gcode_file(file: UploadFile):
    try:
        io_file: BinaryIO = file.file
        if file.filename:
            return printer.upload_file(io_file, file.filename)

    except Exception as e:
        # noqa  # pylint: disable=raise-missing-from
        raise HTTPException(status_code=500,
                            detail=f"Exception occurred during file upload: {e}")  # noqa
    finally:
        file.file.close()
    return


@router.post("/printer/print/start")
async def start_print(filename: str, plate_number: int):
    global printer_available
    printer_available = False
    return printer.start_print(filename, plate_number)


@router.post("/printer/print/stop")
async def stop_print():
    return printer.stop_print()


@router.post("/printer/print/pause")
async def pause_print():
    return printer.pause_print()


@router.post("/printer/print/resume")
async def resume_print():
    return printer.resume_print()


@router.post("/printer/bed/temperature")
async def set_bed_temperature(temperature: int):
    return printer.set_bed_temperature(temperature)


@router.post("/printer/calibration/home")
async def home_printer():
    return printer.home_printer()


@router.post("/printer/axis/z")
async def move_z_axis(distance: int):
    return printer.move_z_axis(distance)


@router.post("/printer/filament/printer")
async def set_filament_printer(color: str,
                               filament: AMSFilamentSettings | str):
    return printer.set_filament_printer(color, filament)


@router.post("/printer/nozzle/temperature")
async def set_nozzle_temperature(temperature: int) -> bool:
    return printer.set_nozzle_temperature(temperature)


@router.post("/printer/print/speed_lvl")
async def set_print_speed(speed_lvl: int) -> bool:
    return printer.set_print_speed(speed_lvl)


@router.post("/printer/file/delete")
async def delete_file(file_path: str) -> str:
    return printer.delete_file(file_path=file_path)


@router.post("/printer/calibration")
async def calibrate_printer(bed_level: bool = True,
                            motor_noise_calibration: bool = True,
                            vibration_compensation: bool = True):
    return printer.calibrate_printer(bed_level,
                                     motor_noise_calibration,
                                     vibration_compensation)


@router.post("/printer/filament/printer/load")
async def load_filament_spool():
    return printer.load_filament_spool()


@router.post("/printer/filament/printer/unload")
async def unload_filament_spool():
    return printer.unload_filament_spool()


@router.post("/printer/filament/retry")
async def retry_filament_action():
    return printer.retry_filament_action()


printer_available = False


@router.get("/printer/available")
async def is_printer_available() -> bool:
    """
    Get the availability of the printer for printing.
    Requires that the printer is available (manual setting) and not printing.

    Returns:
        bool: whether the printer is available for printing
    """
    return printer_available and \
        printer.get_state() in [GcodeState.IDLE, 
                GcodeState.FINISH, 
                GcodeState.FAILED]


@router.post("/printer/available")
async def set_printer_available(
        available: bool = True,
        uid: str = "") -> bool:
    """
    Endpoint to set the availability of the printer for printing.
    (For card scanning system, etc.)

    Args:
        available (bool, optional): availability of the printer.
            Defaults to True.
        uid (str, optional): uid of the user's card. Defaults to "".

    Returns:
        bool: the availability of the printer set by the user
    """
    logging.info(f"User: {uid} set printer availability to {available}")
    global printer_available
    printer_available = available
    return printer_available

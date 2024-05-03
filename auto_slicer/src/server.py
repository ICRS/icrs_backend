import logging
import subprocess

from typing import BinaryIO
from fastapi import APIRouter, UploadFile

from .printer_asset_utils import AVAILABLE_LAYER_HEIGHT, AVAILABLE_PRINTERS, \
    get_machine, process_from_machine_layer, printer_pla


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()


def slice_file_bin(
    file: BinaryIO,
    filename: str,
    filament_path: str = "assets/filament/Generic PLA.json",
    machine_path: str = "assets/machine/Bambu Lab P1P 0.4 nozzle.json",
    process_path: str = "assets/process/0.28mm Extra Draft @BBL P1P.json",
) -> None:
    file.write(filename)
    subprocess.run(["./bambu-studio"])


@router.post("/slice/file")
async def slice_file(
        file: UploadFile,
        printer_type: str = AVAILABLE_PRINTERS,
        layer_height: float = AVAILABLE_LAYER_HEIGHT,):
    try:
        io_file: BinaryIO = file.file

        filament_file_name = printer_pla(printer_type)
        process_file_name = process_from_machine_layer(
            machine_type=printer_type,
            layer_height=layer_height)
        machine_file_name = get_machine(printer_type)

        if file.filename:
            slice_file_bin(io_file,
                           file.filename,
                           filament_file_name=filament_file_name,
                           process_path=process_file_name,
                           machine_path=machine_file_name)
    except Exception as e:
        logging.exception(f"Slice file failed: {e}")
        pass

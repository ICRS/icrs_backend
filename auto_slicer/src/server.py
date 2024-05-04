import os
import logging
import subprocess

from fastapi import APIRouter
import requests


from .printer_asset_utils import AVAILABLE_LAYER_HEIGHT, AVAILABLE_PRINTERS, \
    get_machine, process_from_machine_layer, printer_pla


router = APIRouter()


def slice_file_bin(
    file_url: str,
    filename: str,
    filament_path: str = "assets/filament/Generic PLA.json",
    machine_path: str = "assets/machine/Bambu Lab P1P 0.4 nozzle.json",
    process_path: str = "assets/process/0.28mm Extra Draft @BBL P1P.json",
) -> None:
    with requests.get(file_url) as f:
        with open(filename, "wb") as file:
            file.write(f.content)
    
    os.makedirs(f"tmp/{filename}", exist_ok=True)
    command = ["./bambu-studio",
            #'--curr-bed-type', 'Textured PEI Plate',
                    "--avoid-extrusion-cali-region",
                    "--allow-rotations",
                    "--avoid-extrusion-cali-region",
                    "--orient", "1",
                    "--arrange", "1",
                    "--load-settings",
                    f"{machine_path};{process_path}",
                    "--load-filaments", f"\"{filament_path}\"",
                    "--ensure-on-bed",
                    "--slice", "1",
                    "--outputdir", f"tmp/{filename}",
                    filename]

    logging.info(command)
    result = subprocess.run(command)
    return result


@router.post("/slice/file")
async def slice_file(
        file_url: str,
        file_name: str,
        printer_type: str = AVAILABLE_PRINTERS,
        layer_height: float = AVAILABLE_LAYER_HEIGHT,):
    try:
        filament_file_name = printer_pla(printer_type)
        process_file_name = process_from_machine_layer(
            machine=printer_type,
            layer_height=layer_height)
        machine_file_name = get_machine(printer_type)


        if file_url:
            logging.info(f"{filament_file_name}")
            logging.info(f"{process_file_name}")
            logging.info(f"{machine_file_name}")
            slice_file_bin(file_url,
                           file_name,
                           filament_path="assets/filament/" + filament_file_name,
                           process_path="assets/process/" + process_file_name,
                           machine_path="assets/machine/" + machine_file_name)
    except Exception as e:
        logging.exception(f"Slice file failed: {e}")
        pass

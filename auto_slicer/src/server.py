import logging
import subprocess

from fastapi import APIRouter
import requests


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
    file_url: str,
    filename: str,
    filament_path: str = "assets/filament/Generic PLA.json",
    machine_path: str = "assets/machine/Bambu Lab P1P 0.4 nozzle.json",
    process_path: str = "assets/process/0.28mm Extra Draft @BBL P1P.json",
) -> None:
    with requests.get(file_url) as f:
        with open(filename, "wb") as file:
            file.write(f.content)

    subprocess.run(["./bambu-studio",
                    "--curr-bed-type", "Textured PEI Plate",
                    "--avoid-extrusion-cali-region",
                    "--allow-rotations",
                    "--avoid-extrusion-cali-region",
                    "--orient", 1,
                    "--arrange", 1,
                    "--load-settings",
                    f"{machine_path};{process_path}",
                    "--load-filaments", filament_path,
                    "--ensure-on-bed",
                    "--slice", 1,
                    "--output-dir", f"tmp/{filename}",
                    "--load-settings", f"{process_path};{machine_path}",
                    filename])


@router.post("/slice/file")
async def slice_file(
        file_url: str,
        file_name: str,
        printer_type: str = AVAILABLE_PRINTERS,
        layer_height: float = AVAILABLE_LAYER_HEIGHT,):
    try:
        filament_file_name = printer_pla(printer_type)
        process_file_name = process_from_machine_layer(
            machine_type=printer_type,
            layer_height=layer_height)
        machine_file_name = get_machine(printer_type)

        if file_url:
            slice_file_bin(file_url,
                           file_name,
                           filament_file_name=filament_file_name,
                           process_path=process_file_name,
                           machine_path=machine_file_name)
    except Exception as e:
        logging.exception(f"Slice file failed: {e}")
        pass

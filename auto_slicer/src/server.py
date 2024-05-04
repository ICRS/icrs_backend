import os
import logging
import subprocess
import requests

import xml.etree.ElementTree as ET
from fastapi import APIRouter

from .printer_asset_utils import AVAILABLE_LAYER_HEIGHT, AVAILABLE_PRINTERS, \
    get_machine, process_from_machine_layer, printer_pla


router = APIRouter()


def gcode_time(filename: str) -> tuple[str] | None:
    with open(filename, "r") as file:
        lines = file.readlines()[:4]
        for line in lines:
            if line.startswith("; model printing time:"):
                times = line[1:].split(";")
                model_time = times[0].split(":")[-1].strip()
                estimated_time = times[-1].split(":")[-1].strip()

                return model_time, estimated_time


def weight(filename: str) -> float:
    """
    Get weight from xml file (slice_info.config)

    Args:
        filename (str): file of xml config

    Returns:
        float: weight of the file
    """
    tree = ET.parse(filename)
    tree_root = tree.getroot()
    plate_root = tree_root.find("plate")
    return float(
        next(
            (c.get("value") for c in plate_root.findall(
                "metadata") if c.get("key") == "weight"),
            0.0)
    )


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
               '--curr-bed-type', 'Textured PEI Plate',
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
               "--export-3mf", "output.3mf",
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
            result = slice_file_bin(
                file_url,
                file_name,
                filament_path="assets/filament/"+filament_file_name,
                process_path="assets/process/"+process_file_name,
                machine_path="assets/machine/"+machine_file_name)
            logging.debug(f"Slicing Result: {result}")

            model_time, estimated_time = gcode_time(
                f"tmp/{file_name}/plate_1.gcode")

            return {"slice_result": result,
                    "file_name": file_name,
                    "file_url": file_url,
                    "printer_type": printer_type,
                    "layer_height": layer_height,
                    "plates": 1,
                    "model_time": model_time,
                    "estimated_time": estimated_time,
                    }
    except Exception as e:
        logging.exception(f"Slice file failed: {e}")
        pass

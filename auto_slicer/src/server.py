from functools import cache
import logging
import os
import subprocess

from typing import BinaryIO
from fastapi import APIRouter, Query, UploadFile


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

router = APIRouter()

AVAILABLE_PRINTERS = Query(enum=["p1p", "p1s"])
AVAILABLE_LAYER_HEIGHT = Query(enum=[0.12, 0.16, 0.20, 0.24, 0.28])


def slice_file_bin(
    file: BinaryIO,
    filename: str,
    filament_path: str = "assets/filament/Generic PLA.json",
    machine_path: str = "assets/machine/Bambu Lab P1P 0.4 nozzle.json",
    process_path: str = "assets/process/0.28mm Extra Draft @BBL P1P.json",
) -> None:
    file.write(filename)
    subprocess.run(["./bambu-studio"])


@cache
def available_processes() -> list[str]:
    return os.listdir("assets/process")


@cache
def available_machine() -> list[str]:
    return os.listdir("assets/machine")


@cache
def p1p_processes() -> list[str]:
    return sorted(
        [s for s in available_processes() if "P1P" in s], reverse=True)


@cache
def x1c_processes() -> list[str]:
    return sorted(
        [s for s in available_processes() if "X1C" in s], reverse=True)


@cache
def p1p_process_from_layer_height(layer_height: float) -> str:
    layer_height = "%.2f" % layer_height
    layer_prefix = f"{layer_height}mm"
    return next((s for s in p1p_processes() if layer_prefix in s),
                p1p_processes()[0])


@cache
def x1c_process_from_layer_height(layer_height: float) -> str:
    layer_height = "%.2f" % layer_height
    layer_prefix = f"{layer_height}mm"
    return next((s for s in x1c_processes() if layer_prefix in s),
                x1c_processes()[0])


p1s_processes = x1c_processes
p1s_process_from_layer_height = x1c_process_from_layer_height


@cache
def process_from_machine_layer(machine: str, layer_height: float) -> str:
    if machine.lower() == "p1p":
        return p1p_process_from_layer_height(layer_height)
    elif machine.lower() == "p1s":
        return p1s_process_from_layer_height(layer_height)
    return x1c_process_from_layer_height(layer_height)


@cache
def get_machine(machine_type: str = AVAILABLE_PRINTERS) -> str:
    machine_type = machine_type.lower()
    return next((s for s in available_machine() if machine_type in s.lower()),
                "Bambu Lab P1P 0.4 nozzle.json")


@router.get("/processes")
async def get_processes():
    return available_processes()


@router.get("/processes/p1p")
async def get_p1p_processes():
    return p1p_processes()


@router.get("/processes/p1s")
async def get_p1s_processes():
    return p1s_processes()


@router.get("/process/p1p")
async def get_p1p_process(layer_height: float = AVAILABLE_LAYER_HEIGHT):
    return p1p_process_from_layer_height(layer_height)


@router.get("/process/p1s")
async def get_p1s_process(layer_height: float = AVAILABLE_LAYER_HEIGHT):
    return p1s_process_from_layer_height(layer_height)


@router.get("/machine")
async def machine(machine_type: str = AVAILABLE_PRINTERS):
    return get_machine(machine_type)


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


def printer_pla(printer_type: str) -> str:
    if printer_type.lower() == "p1p":
        return "Generic PLA @BBL P1P.json"
    return "Generic PLA.json"

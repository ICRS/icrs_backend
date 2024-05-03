import os
from fastapi import Query


from functools import cache

__all__ = [
    "AVAILABLE_PRINTERS",
    "AVAILABLE_LAYER_HEIGHT",
    "get_machine",
    "process_from_machine_layer",
    "printer_pla",
]

AVAILABLE_PRINTERS = Query(enum=["p1p", "p1s"])
AVAILABLE_LAYER_HEIGHT = Query(enum=[0.12, 0.16, 0.20, 0.24, 0.28])


@cache
def available_machine() -> list[str]:
    return os.listdir("assets/machine")


@cache
def get_machine(machine_type: str = AVAILABLE_PRINTERS) -> str:
    machine_type = machine_type.lower()
    return next((s for s in available_machine() if machine_type in s.lower()),
                "Bambu Lab P1P 0.4 nozzle.json")


@cache
def available_processes() -> list[str]:
    return os.listdir("assets/process")


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


def printer_pla(printer_type: str) -> str:
    if printer_type.lower() == "p1p":
        return "Generic PLA @BBL P1P.json"
    return "Generic PLA.json"

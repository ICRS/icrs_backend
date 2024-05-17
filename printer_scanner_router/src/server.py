import logging
from fastapi import APIRouter, Query
import requests
import json

router = APIRouter(
    tags=["server"],
)

# ==============================================================================
PRINTER_CONFIG = json.load(open("printer_config.json"))

PRINTER_NAMES = list(PRINTER_CONFIG["PRINTER_NAMES"])
PRINTER_GATEWAY_ENDPOINT_SUFFIX = str(
    PRINTER_CONFIG["PRINTER_GATEWAY_ENDPOINT_SUFFIX"])

# ==============================================================================


@router.post("/availability")
async def update_availability(
    uid: str = "",
    printer_name: str = Query(enum=PRINTER_NAMES),
    available: bool = False,
):
    logging.info(f"Updating availability for {uid} to {available}")
    uid = uid.strip().replace(" ", "").rjust(8, "0")
    r = requests.post(
        f"http://{printer_name}{PRINTER_GATEWAY_ENDPOINT_SUFFIX}/printer/available", # noqa
        params={"uid": uid, "available": available},
    )

    return r.status_code

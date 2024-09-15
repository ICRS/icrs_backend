import datetime
import logging
import math
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, \
    HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import requests

from src.auth import valid_login
from requests.auth import HTTPBasicAuth

# ==============================================================================
DATABASE_ADAPTER_IP = os.getenv("DATABASE_ADAPTER_IP")

# ==============================================================================


access_server_router = APIRouter()


last_set_time = datetime.datetime.fromtimestamp(0)
last_short_code = ''


@access_server_router.post("/print-window/update")
def set_print_window(
    uuid: str = Query(min_length=8, max_length=14),
    credentials: Annotated[HTTPBasicAuth |
                           None, Depends(valid_login)] = None
):
    global last_set_time, last_short_code

    logging.info(f"UUID: {uuid}, Credentials Correct")
    result = requests.get(
        DATABASE_ADAPTER_IP + "/member/permissions/uuid",
        params={"uuid": uuid},
        auth=credentials
    )

    if result.status_code == 200:
        r = result.json()
        if len(r) == 0:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"No UUID found in server {r}"
            )

        body = result.json()
        shortcode = str(body.get("shortcode", ""))
        can_print = body.get("print", False)

        if not can_print:
            raise HTTPException(
                status_code=401,
                detail="no induction"
            )

        last_set_time = datetime.datetime.now() + datetime.timedelta(
            seconds=60)
        last_short_code = shortcode

        logging.info(f"{shortcode} {last_set_time}")
        return "SUCCESS"
    else:
        error_msg = f"Error with request: {result.status_code} {result.reason}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=f"{result.reason}"
        )


@access_server_router.get("/getPrintWindow", response_class=PlainTextResponse)
async def get_print_window(request: Request):
    global last_set_time
    return str(last_set_time > datetime.datetime.now())


class PrintData(BaseModel):
    time: str
    weight: str
    name: str


@access_server_router.post("/postPrintTime")
async def post_print_time(
    print_data: PrintData
):
    global last_short_code

    def parse_to_int(s: str) -> int:
        '''Expects the time to be in in seconds (float)'''
        return math.ceil(float(s))

    print_time = parse_to_int(print_data.time.strip())
    print_weight = parse_to_int(print_data.weight.strip())
    printer_name = print_data.name.strip()

    logging.info(
        f"Print time: {print_time}, Print weight: {print_weight}, Printer name: {printer_name}, Last Shortcode: {last_short_code}"  # noqa: E501
    )

    result = requests.post(
        DATABASE_ADAPTER_IP + "/print-metrics/print",
        params={
            "printer_name": printer_name,
            "shortcode": last_short_code,
            "print_time": print_time,
            "print_weight": print_weight,
        })

    if result.status_code != 200:
        error_msg = f"Adding Print to DB failed: {result.reason}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=error_msg
        )


@access_server_router.get("/member/permissions/uuid")
async def get_member_permission_uuid(
    uuid: str = Query(min_length=8, max_length=14),
    credentials: Annotated[HTTPBasicAuth |
                           None, Depends(valid_login)] = None
):
    result = requests.get(
        DATABASE_ADAPTER_IP + "/member/permissions/uuid",
        params={"uuid": uuid},
        auth=credentials
    )

    if result.status_code != 200:
        msg = f"Error Querying the permissions with uuid: {result.reason}"
        logging.error(msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=msg
        )

    return result.json()


@access_server_router.post("/register/card/cid")
def register_card_details_cid(
    uuid: str = Query(min_length=8, max_length=14),
    cid: str = Query(regex=r"\d{8}"),
    credentials: Annotated[HTTPBasicAuth |
                           None, Depends(valid_login)] = None
):
    result = requests.get(
        DATABASE_ADAPTER_IP + "/register/card/cid",
        params={"uuid": uuid, "cid": cid},
        auth=credentials
    )

    if result.status_code != 200:
        msg = f"Error Querying the permissions with uuid: {result.reason}"
        logging.error(msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=msg
        )

    return result.json()


@access_server_router.get("/project-box/assign/uuid")
def assign_project_box(
    uuid: str = Query(min_length=8, max_length=14),
    credentials: Annotated[HTTPBasicAuth |
                           None, Depends(valid_login)] = None
):
    result = requests.get(
        DATABASE_ADAPTER_IP + "/project-box/assign/uuid",
        params={"uuid": uuid},
        auth=credentials
    )

    if result.status_code != 200:
        msg = f"Error assigning box with uuid: {result.reason}"
        logging.error(msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=msg
        )

    return result.json()


@access_server_router.get("/slicer/print/permissions")
def get_slicer_print_permissions(
        time_seconds: int | None = None,
        orcaslicer_timedelta: str | None = None
):
    if time_seconds is None and orcaslicer_timedelta is None:
        raise HTTPException(
            status_code=400,
            detail="No print time delta given!")

    global last_set_time, last_short_code
    if last_set_time < datetime.datetime.now():
        raise HTTPException(
            status_code=401,
            detail="Card not scanned!")

    if time_seconds:
        delta = datetime.timedelta(seconds=time_seconds)
    else:
        t = {
        }

        v = 0
        for c in orcaslicer_timedelta:
            if c == 'd':
                t['days'] = v
                v = 0
            elif c == 'h':
                t['hours'] = v
                v = 0
            elif c == 'm':
                t['minutes'] = v
                v = 0
            elif c == 's':
                t['seconds'] = v
                v = 0
            else:
                v *= 10
                v += int(c)

        delta = datetime.timedelta(**t)

    if last_set_time > datetime.datetime.now():
        result = requests.get(
            DATABASE_ADAPTER_IP + "/slicer/print/permissions",
            params={"shortcode": last_short_code,
                    "time_seconds": delta.seconds},
        )
        if result.status_code != 200:
            msg = f"Permission denied for slicer: {result.reason}"
            logging.error(msg)
            raise HTTPException(
                status_code=result.status_code,
                detail=msg
            )

        return result.json()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Card not tapped on reader")

import datetime
import logging
import math
import os
from typing import Annotated
import json

from fastapi import APIRouter, Depends, Query, Request, \
    HTTPException, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
import requests

from starlette.background import BackgroundTask
from src.auth import valid_login
from requests.auth import HTTPBasicAuth


import httpx

# ==============================================================================

DATABASE_ADAPTER_IP = os.getenv("DATABASE_ADAPTER_IP")
SUBPATH = os.getenv("SUBPATH", "/api/admin")

# ==============================================================================


admin_server_router = APIRouter()

@admin_server_router.get("/card-office")
def card_office_list(
    credentials: Annotated[HTTPBasicAuth |
                            None, Depends(valid_login)] = None
):
    result = requests.get(
        DATABASE_ADAPTER_IP + "/v2/summary/inducted/recent",
        params={"update": False},
        auth=credentials
    )
    if result.status_code != 200:
        msg = f"Permission denied for permissions reading: {result.reason}"
        logging.error(msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=msg
        )

    return result.json()

@admin_server_router.post("/card-office")
def card_office_update(
    shortcodes: list[str],
    credentials: Annotated[HTTPBasicAuth |
                            None, Depends(valid_login)] = None
):
    result = requests.get(
        DATABASE_ADAPTER_IP + "/v2/summary/inducted/update",
        params={"shortcodes": shortcodes},
        auth=credentials
    )
    if result.status_code != 200:
        msg = f"Permission denied for permissions reading: {result.reason}"
        logging.error(msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=msg
        )

    to_send = result.json()[0]
    csv = ["name,shortcode,cid,email"]
    for person in to_send:
        csv.append(','.join(person) + person["shortcode"] + "@ic.ac.uk")
    return '\n'.join(csv)
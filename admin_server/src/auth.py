import logging
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from typing import Annotated

import requests
from requests.auth import HTTPBasicAuth

DATABASE_ADAPTER_IP = os.getenv("DATABASE_ADAPTER_IP")

security = HTTPBasic()


def valid_login(
    credentials: Annotated[
        HTTPBasicCredentials | None, Depends(security)] = None,
):
    basic = HTTPBasicAuth(
        credentials.username.encode("utf8"),
        credentials.password.encode("utf8")
    )

    if credentials is None:
        logging.warning("No Username or Password Given!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No username or password given!",
            headers={"WWW-Authenticate": "Basic"},
        )

    result = requests.post(DATABASE_ADAPTER_IP + "/auth/login",
                           auth=basic)

    if result.status_code != 200:
        error_msg = f"Incorrect Username or Password Given! Reason: {result.reason}"  # noqa: E501
        logging.warning(error_msg)
        raise HTTPException(
            status_code=result.status_code,
            detail=error_msg,
            headers={"WWW-Authenticate": "Basic"},
        )

    return basic

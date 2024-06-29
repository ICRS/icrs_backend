import logging
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from typing import Annotated

# =============================================================================
USERNAME = os.getenv("USERNAME").encode()
PASSWORD = os.getenv("PASSWORD").encode()

# =============================================================================

security = HTTPBasic()


def get_current_username(
    credentials: Annotated[
        HTTPBasicCredentials | None, Depends(security)] = None,
):
    """
    Authenticate the user

    Args:
        credentials (
            Annotated[ HTTPBasicCredentials  |  None, Depends, optional):
            Authentication credentials. Defaults to None.

    Raises:
        HTTPException: if incorrect username or password given or not given

    Returns:
        str: username of the user if authenticated
    """
    if credentials is None:
        logging.warning("No Username or Password Given!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No username or password given!",
            headers={"WWW-Authenticate": "Basic"},
        )

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = USERNAME
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = PASSWORD
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        logging.warning("Incorrect Username or Password Given!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@auth_router.post("/login")
def login(username: str = Depends(get_current_username)):
    """
    Login handler for the API

    Args:
        username (str, optional): authentication.
            Defaults to Depends(get_current_username).

    Returns:
        dict[str, str]: username
    """
    return "Successfully logged in"

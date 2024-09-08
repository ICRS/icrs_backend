__all__ = ["slicer_router"]

import datetime
import logging

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from src.database import main_db_pool

from src.auth import get_current_username


slicer_router = APIRouter(prefix="/slicer", tags=["Slicer"])


@slicer_router.get("/print/permissions")
def print_permissions(
    username: Annotated[str, Depends(get_current_username)],
    time: datetime.timedelta
) -> str:
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                now = datetime.datetime.now()
                if 7 < now.hour < 22:
                    cur.execute(
                        "SELECT TRUE FROM public.induction i WHERE "
                        "i.canprint and i.valid and i.print_daytime_time < %s",
                        (
                            time.seconds // 60
                        )
                    )
                else:
                    cur.execute(
                        "SELECT TRUE FROM public.induction i WHERE "
                        "i.canprint and i.valid and i.print_night_time < %s",
                        (
                            time.seconds // 60
                        )
                    )
                result = cur.fetchone()

    except Exception as e:
        msg = f"Error getting permissions for printer {e}"
        logging.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )

    if not result:
        msg = "Member cannot not print at this time"
        logging.info(msg)
        raise HTTPException(status_code=status.HTTP_302_FOUND,
                            detail=msg)
    return True

__all__ = ["slicer_router"]

import datetime
import logging

from fastapi import APIRouter, HTTPException, Query, status

from src.database import main_db_pool
from src.validation import SHORTCODE_REGEX


slicer_router = APIRouter(prefix="/slicer", tags=["Slicer"])


@slicer_router.get("/print/permissions")
def print_permissions(
    # username: Annotated[str, Depends(get_current_username)],
    time: datetime.timedelta,
    shortcode: str = Query(pattern=SHORTCODE_REGEX)
) -> str:
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                now = datetime.datetime.now()
                print_minutes = time.seconds // 60
                logging.warning(print_minutes)
                if 7 < now.hour < 22:
                    cur.execute(
                        "SELECT TRUE FROM public.induction i WHERE "
                        "i.canprint and i.valid and i.print_daytime_time > %s "
                        "and i.shortcode=%s",
                        (
                            print_minutes,
                            shortcode
                        )
                    )
                else:
                    cur.execute(
                        "SELECT TRUE FROM public.induction i WHERE "
                        "i.canprint and i.valid and i.print_night_time > %s "
                        "and i.shortcode=%s",
                        (
                            time.seconds // 60,
                            shortcode
                        )
                    )
                result = cur.fetchone()
                logging.info(result)

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=msg)
    return True

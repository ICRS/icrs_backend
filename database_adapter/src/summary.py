import logging
import os

from typing import Annotated
from fastapi import APIRouter, Depends,  HTTPException, status

from src.database import main_db_pool

from src.auth import get_current_username

env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

summary = APIRouter(prefix="/summary", tags=["Summary"])


@summary.get("/inducted")
def all_inducted(
    username: Annotated[
        str, Depends(get_current_username)],
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode FROM public.induction WHERE valid")
                inducted = cur.fetchall()
                inducted = union.getShortcodesToCIDAndName(
                    [i[0] for i in inducted])
                inducted = [
                    " - ".join(c) + "@ic.ac.uk" for c in inducted
                ]

                return inducted
    except Exception as e:
        error_msg = f"Could not query database {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@summary.get("/inducted/recent")
def recently_inducted(
    username: Annotated[
        str, Depends(get_current_username)],
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT shortcode FROM public.induction A " +
                            "WHERE valid AND NOT EXISTS " +
                            "(SELECT \'X\' FROM public.sent S " +
                            "WHERE A.shortcode=S.shortcode)")

                update = [c[0] for c in cur.fetchall()]

                mapping = union.getShortcodesToCIDAndName(update)

                cur.executemany(
                    "INSERT INTO public.sent (shortcode) VALUES (%s)",
                    [(c,) for c in update])

                return mapping
    except Exception as e:
        error_msg = f"Error when querying db or inserting into  {e}"
        logging.error(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

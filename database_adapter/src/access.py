from typing import Annotated
from fastapi import APIRouter, Depends, Query

from src.auth import get_current_username
from src.database import main_db_pool


access_router = APIRouter(prefix="/access", tags=["Access"])


@access_router.post("/print-window/update")
def update_print_window(
        username: Annotated[str, Depends(get_current_username)],
        uuid: str = Query(min_length=8, max_length=14)):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO public.card_scan_log(id) "
                "VALUES (%s)",
                (uuid,),
            )

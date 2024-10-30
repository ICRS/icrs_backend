from fastapi import APIRouter, HTTPException, Query, status
from src.database import main_db_pool


printer_streamer_router = APIRouter(
    prefix="/printer-streamer",
    tags=["Printer Streamer"]
)


@printer_streamer_router.get("/message-id/latest")
def get_last_message_id(
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT message_id "
                 "FROM public.printer_streamer_message "
                 "ORDER BY created DESC LIMIT 1"
                 ),
            )
            c = cur.fetchone()
            if not c:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="No message id available"
                )

            return str(c[0])


@printer_streamer_router.post("/message-id")
def insert_message_id(
    message_id: str = Query(min_length=8, max_length=30),
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO public.printer_streamer_message (message_id) "
                    "VALUES (%s)"
                ),
                (message_id,)
            )

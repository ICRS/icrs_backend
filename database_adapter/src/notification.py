__all__ = ["notification_router"]

import logging

from fastapi import APIRouter, HTTPException, Query, status

from src.database import main_db_pool

notification_router = APIRouter(
    prefix="/printer-notification", tags=["Printer Notification"])


@notification_router.delete("/printer")
def get_printer_notification_users(
    printer_name: str
) -> list[str]:
    """
    Purge Printer Notification Table/Cache and return the discord users who are
    registered to be notified

    Args:
        printer_name (str): the printer name

    Raises:
        HTTPException: if something bad happened to the databse

    Returns:
        list[str]: list of discord id's as strings
    """
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                logging.info(f"Clearing printer cache for {printer_name}")
                cur.execute(
                    "DELETE FROM public.printer_notification "
                    "WHERE printer=%s "
                    "RETURNING discord_id",
                    (printer_name,)
                )
                return [c[0] for c in cur.fetchall()]
    except Exception as e:
        logging.error(f"Something really bad happened to the database: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding member to database: {e}",
        )


@notification_router.get("/discord-id")
def discord_printer_subscription(
    discord_id: str = Query(min_length=17, max_length=21),
):
    """
    Get which printers the discord user has subscribed to

    Args:
        discord_id (str): discord user's id

    Raises:
        HTTPException: if something bad happened to the database

    Returns:
        list[str]: list of printer's the user has registered to
    """
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                logging.info(f"Getting printers user {discord_id} has registered to")  # noqa: E501
                cur.execute(
                    "SELECT printer FROM public.printer_notification "
                    "WHERE discord_id=%s",
                    (discord_id,)
                )
                return [c[0] for c in cur.fetchall()]
    except Exception as e:
        logging.error(f"Something really bad happened to the database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding member to database: {e}",
        )


@notification_router.post("/discord-id")
def add_user_notification(
    discord_id: str = Query(min_length=17, max_length=21),
    printer_names: list[str] | None = None,
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                logging.info(f"Subscribing user {discord_id} to {printer_names}")  # noqa: E501
                cur.executemany(
                    "INSERT INTO public.printer_notification "
                    "(discord_id, printer) "
                    "VALUES(%s,%s) ON CONFLICT DO NOTHING",
                    [(discord_id, name) for name in printer_names]
                )
                return {"inserted": cur.rowcount}
    except Exception as e:
        logging.error(f"Something really bad happened to the database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding member to database: {e}",
        )

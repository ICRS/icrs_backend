import logging
import os
import pydantic

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.database import main_db_pool

from src.auth import get_current_username
from src.union import cid_to_shortcode
from src.validation import SHORTCODE_QUERY, SHORTCODE_QUERY_PYDANTIC


env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

printer_router = APIRouter(prefix="/printer", tags=["printer"])

class PrinterDetails(BaseModel):
    printer_name: str = pydantic.Field()
    serial_number: str = pydantic.Field(min_length=5, max_length=20)

@printer_router.post("/add")
def add_printer(
    username: Annotated[str, Depends(get_current_username)],
    printer_details : PrinterDetails,
) -> str:
    serial_n = printer_details.serial_number.upper()

    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.PRINTERS (PRINTER_NAME, "
                    "SERIAL_NUMBER) VALUES (%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (
                        printer_details.printer_name,
                        serial_n,
                    )
                )
                conn.commit()
                return "SUCCESS"

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding printer to database: {e}"
        )
    
@printer_router.post("/add/user")
def add_user_to_printer(
    username: Annotated[str, Depends(get_current_username)],
    serial_number: str = Query(min_length=15, max_length=15),
    shortcode: str = Query(max_length=10)
) -> str:
    shortcode = shortcode.lower()
    serial_number = serial_number.upper()
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.PRINTER_MEMBER (SERIAL_NUMBER, SHORTCODE) "
                    "VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (serial_number, shortcode)
                )

                conn.commit()
                return "SUCCESS"
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding user to printer: {e}"
        )

@printer_router.get("/details/name")
def get_allowed_from_name(
    username: Annotated[str, Depends(get_current_username)],
    name: str,
) -> tuple | str:
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pm.SHORTCODE "
                    "FROM public.PRINTER_MEMBER pm "
                    "INNER JOIN public.PRINTERS p ON pm.SERIAL_NUMBER = p.SERIAL_NUMBER "
                    "WHERE p.PRINTER_NAME = %s ",
                    (name,) 
                )

                result = cur.fetchone()

                logging.info(f"Result: {result}")
                if not result:
                    result = tuple()
                return result
    except Exception as e:
        error_msg = (
            "Could not query database/result return "
            f"in unexpected format: {e}"
        )
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )
    
@printer_router.get("/details/serial")
def get_allowed_from_name(
    username: Annotated[str, Depends(get_current_username)],
    serial_n: str = Query(min_length=15, max_length=15),
) -> tuple | str:
    serial_n = serial_n.upper()
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pm.SHORTCODE "
                    "FROM public.PRINTER_MEMBER pm "
                    "INNER JOIN public.PRINTERS p ON pm.SERIAL_NUMBER = p.SERIAL_NUMBER "
                    "WHERE p.SERIAL_NUMBER = %s ",
                    (serial_n,) 
                )

                result = cur.fetchone()

                logging.info(f"Result: {result}")
                if not result:
                    result = tuple()
                    
                return result
    except Exception as e:
        error_msg = (
            "Could not query database/result return "
            f"in unexpected format: {e}"
        )
        logging.warning(error_msg)

        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )
import datetime
from typing import Annotated
from src.database import main_db_pool
import logging
from fastapi import APIRouter, Body, Query, HTTPException, status
import json

print_metrics_router = APIRouter(prefix="/print-metrics",
                                 tags=["Print Metrics"])

# ==============================================================================
#                               Printer Config
# ==============================================================================


def printer_name_parsing(s: str) -> str:
    return s.title().replace("-", " ")


PRINTER_CONFIG = json.load(open("printer_config.json"))
PRINTER_NAMES = [
    printer_name_parsing(n) for n in PRINTER_CONFIG["PRINTER_NAMES"]]

# ==============================================================================


@print_metrics_router.post("/print")
async def add_print_entry(printer_name: str = Query(enum=PRINTER_NAMES),
                          shortcode: str = Query(min_length=3, max_length=7),
                          print_time: int = Query(ge=0),
                          print_weight: int = Query(ge=0)):
    logging.info(f"Adding entry {printer_name, print_time, print_weight} \
                 submitted by{shortcode}")
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.print_metrics (shortcode, \
                        print_duration, print_weight, printer_name) \
                            VALUES (%s,%s,%s,%s)",
                    (shortcode, print_time, print_weight, printer_name)
                )
                conn.commit()

                return f"Successfully added entry for {shortcode}"

    except Exception:
        error_msg = f"Could not add entry for {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@print_metrics_router.post("/print/update/stop")
async def stop_print_update_entry(
        printer_name: str = Query(enum=PRINTER_NAMES)):
    try:
        printer_name = printer_name.replace("-", " ").lower()
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    ("UPDATE ONLY public.print_metrics "
                     "SET print_duration=LEAST(EXTRACT("
                     "EPOCH FROM (NOW() - time_started)), print_duration) "
                     "WHERE printer_name=%s AND time_started="
                     "(SELECT MAX(time_started) FROM public.print_metrics "
                     "WHERE LOWER(printer_name)=%s)"),
                    (printer_name,)
                )
                conn.commit()
                return True
    except Exception:
        error_msg = f"Could not update printer entry: {printer_name}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@print_metrics_router.get("/member/stats/shortcode")
def member_stats(shortcode: str = Query(min_length=3, max_length=7)):
    shortcode = shortcode.lower()
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM public.print_metrics WHERE shortcode=%s", (shortcode,))  # noqa: E501
                return cur.fetchall()
    except Exception as e:
        error_msg = f"Error occurred when querying db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@print_metrics_router.get("/member/stats/discord")
def member_stats_discord(discord_id: str = Query(min_length=10)):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT T.shortcode, T.time_started, T.print_duration, " +
                    "T.print_weight, T.printer_name " +
                    "FROM public.print_metrics T INNER JOIN public.mapping " +
                    "ON public.mapping.shortcode=T.shortcode " +
                    "WHERE user_id=%s",
                    (discord_id,))  # noqa: E501
                prints = cur.fetchall()

                return prints
    except Exception as e:
        error_msg = f"Error occurred when querying db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@print_metrics_router.get("/member/stats/summary")
def member_stats_summary(
    start_time: Annotated[datetime.datetime, Body()] = datetime.datetime(
        1970, 1, 1, 0, 0),
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode, SUM(print_duration), " +
                    "SUM(print_weight) " +
                    "FROM public.print_metrics " +
                    "WHERE time_started >= %s " +
                    "GROUP BY shortcode",
                    (start_time,)
                )
                return [{"shortcode": c[0],
                         "print_duration": c[1],
                         "print_weight": c[2]} for c in cur.fetchall()]
    except Exception as e:
        error_msg = f"Error occurred when querying db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@print_metrics_router.get("/current/printer/shortcode")
async def get_current_user_printer(
    printer_name: str
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    ("SELECT t.shortcode "
                     "FROM public.print_metrics t "
                     "WHERE t.time_started + make_interval(secs => t.print_duration) > CURRENT_TIMESTAMP and LOWER(printer_name)=%s "  # noqa: E501
                     "ORDER BY t.time_started DESC "
                     "LIMIT 1"),
                    (printer_name.replace("-", ' ').lower(),)
                )

                shortcode = cur.fetchone()
    except Exception as e:
        error_msg = f"Error occurred when querying db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    if shortcode is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No entry for printer"
        )
    else:
        return shortcode[0]

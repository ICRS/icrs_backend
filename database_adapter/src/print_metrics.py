import datetime
from typing import Annotated
from src.database import DB_CONFIG
import logging
from fastapi import APIRouter, Body, Query, HTTPException, status
import psycopg2 as pg
import json

print_metrics_router = APIRouter(prefix="/print-metrics",
                                 tags=["Print Metrics"])

# ==============================================================================
#                               Printer Config
# ==============================================================================

PRINTER_CONFIG = json.load(open("printer_config.json"))
PRINTER_NAMES = list(PRINTER_CONFIG["PRINTER_NAMES"])

# ==============================================================================


@print_metrics_router.post("/print")
async def add_print_entry(printer_name: str = Query(enum=PRINTER_NAMES),
                          shortcode: str = Query(min_length=3, max_length=7),
                          print_time: int = Query(ge=0),
                          print_weight: int = Query(ge=0)):
    logging.info(f"Adding entry {printer_name, print_time, print_weight} \
                 submitted by{shortcode}")
    try:
        with pg.connect(**DB_CONFIG) as conn:
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


@print_metrics_router.get("/member/stats/shortcode")
def member_stats(shortcode: str = Query(min_length=3, max_length=7)):
    shortcode = shortcode.lower()
    try:
        with pg.connect(**DB_CONFIG) as conn:
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
        with pg.connect(**DB_CONFIG) as conn:
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
        with pg.connect(**DB_CONFIG) as conn:
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

import datetime
from src.database import DB_CONFIG
import logging
from fastapi import APIRouter, Query, HTTPException
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
                          print_time: datetime.timedelta = Query(ge=0),
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

                return
    except Exception:
        error_msg = f"Could not add entry for {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)

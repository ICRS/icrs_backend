import math
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

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
                "INSERT INTO public.card_scan_log(ID, VALID) "
                "SELECT %s as ID, COALESCE(sum(COALESCE(fiw1.canprint::INTEGER, 0)), 0) > 0 as VALID "
                "FROM public.full_induction_view fiw1 "
                "WHERE fiw1.card_id=%s  "
                "LIMIT 1 "
                "RETURNING VALID",
                (uuid, uuid),
            )
            return bool(cur.fetchone()[0])


@access_router.get("/print-window/valid")
def get_print_window_valid(
        username: Annotated[str, Depends(get_current_username)],
        time_s: int = Query(default=60, min=0, max=3600),
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT shortcode FROM public.card_scan_log l "
                "INNER JOIN public.full_induction_view sc "
                "ON l.id=sc.card_id "
                "WHERE l.scanned_time > CURRENT_TIMESTAMP - (%s ||' seconds')::interval "
                "ORDER BY l.scanned_time DESC "
                "LIMIT 1",
                (time_s,),
            )

            return bool(cur.fetchall())


class PrintData(BaseModel):
    time: str
    weight: str
    name: str


@access_router.post("/print-metric")
def post_print_time(
    print_data: PrintData
):
    def parse_to_int(s: str) -> int:
        '''Expects the time to be in in seconds (float)'''
        return math.ceil(float(s))

    print_time = parse_to_int(print_data.time.strip())
    print_weight = parse_to_int(print_data.weight.strip())
    printer_name = print_data.name.strip()

    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO public.print_metrics (shortcode, "
                "print_duration, print_weight, printer_name) "
                "SELECT shortcode, %s, %s, %s FROM ("
                "SELECT shortcode, l.valid "
                "FROM public.card_scan_log l "
                "INNER JOIN public.full_induction_view sc "
                "ON l.id=sc.card_id "
                "ORDER BY l.scanned_time DESC "
                "LIMIT 1) "
                "WHERE valid "
                "RETURNING shortcode",
                (print_time, print_weight, printer_name)
            )

            return [i[0] for i in cur.fetchall()]

@access_router.post("/ble_device_detected")
def post_ble_addr(mac_addr: str = Query(max_length=20)):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO public.ble_stats (mac_addr) "
                "VALUES (%s) "
                "RETURNING mac_addr",
                (mac_addr,)
            )

            return bool(cur.fetchall()[0])

@access_router.get("/ble_last_15")
def ble_last_15():
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT mac_addr FROM public.ble_stats as ble "
                "WHERE ble.timestamp >= date_trunc('hour', current_timestamp) "
                "+ date_part('minute', current_timestamp)::int / 15 * interval '15 minute'"
            )

            return [x[0] for x in cur.fetchall()]
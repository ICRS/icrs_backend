import logging
from database import DB_CONFIG
from fastapi import APIRouter, Query, HTTPException
import psycopg2 as pg

router = APIRouter()


@router.get("/shortcode/discord_id")
def get_discord_id_from_shortcode(
        shortcode: str = Query(min_length=3, max_length=7)
) -> str:

    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM public.mapping WHERE shortcode=%s",
                    (shortcode,)
                )

                return {"shortcode": cur.fetchone()}
    except Exception:
        error_msg = f"Discord ID not found for short code: {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@router.get("/discord_id/shortcode")
def get_shortcode_from_discord_id(
        id: str = Query(min_length=17, max_length=19)) -> str:

    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode FROM public.mapping WHERE user_id=%s",
                    (id,)
                )

                return {"discord_id": cur.fetchone()}
    except Exception:
        error_msg = f"ShortCode not found for Discord ID: {id}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@router.get("/shortcode/can_print")
def get_can_print_from_shortcode(
    shortcode: str = Query(min_length=3, max_length=7)
) -> str:
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT can_print FROM public.access WHERE shortcode=%s",
                    (shortcode,)
                )
                can_print = str(cur.fetchone()).lower() == "true"
                return {"can_print": can_print}
    except Exception:
        error_msg = f"ShortCode not found: {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)

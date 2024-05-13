import logging
from src.database import DB_CONFIG
from fastapi import APIRouter, Query, HTTPException
import psycopg2 as pg

discord_id_router = APIRouter(
    prefix="/discord-id",
    tags=["discord-id"]
)
shortcode_router = APIRouter(
    prefix="/shortcode",
    tags=["shortcode"]
)


@shortcode_router.get("/discord-id")
def get_discord_id_from_shortcode(
        shortcode: str = Query(min_length=3, max_length=7)
) -> dict:
    """
    Get the Discord ID from the shortcode

    Args:
        shortcode (str, optional): User's shortcode.
            Defaults to Query(min_length=3, max_length=7).

    Raises:
        HTTPException: Exception 500 if the shortcode is not found

    Returns:
        dict: dictionary with the discord_id
    """
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM public.mapping WHERE shortcode=%s",
                    (shortcode,)
                )

                return {"discord_id": cur.fetchone()[0]}
    except Exception:
        error_msg = f"Discord ID not found for short code: {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@discord_id_router.get("/shortcode")
def get_shortcode_from_discord_id(
        id: str = Query(min_length=17, max_length=19)) -> dict:
    """
    Get the shortcode from the Discord ID

    Args:
        id (str, optional): Get shortcode from discord id.
            Defaults to Query(min_length=17, max_length=19).

    Raises:
        HTTPException: Exception 500 if the id is not found

    Returns:
        dict: dictionary with the shortcode
    """
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode FROM public.mapping WHERE user_id=%s",
                    (id,)
                )

                return {"shortcode": cur.fetchone()[0]}
    except Exception:
        error_msg = f"ShortCode not found for Discord ID: {id}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)


@shortcode_router.get("/permissions/print")
def get_can_print_from_shortcode(
    shortcode: str = Query(min_length=3, max_length=7)
) -> dict:
    """
    Get if the user can print from the shortcode

    Args:
        shortcode (str, optional): user's shortcode.
            Defaults to Query(min_length=3, max_length=7).

    Raises:
        HTTPException: Exception 500 if the shortcode is not found

    Returns:
        dict: dictionary with the can_print value
    """
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT canprint FROM public.access WHERE shortcode=%s",
                    (shortcode,)
                )
                can_print = str(cur.fetchone()[0]).lower() == "true"
                return {"can_print": can_print}
    except Exception:
        error_msg = f"ShortCode not found: {shortcode}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg)

import logging
import os
from src.database import DB_CONFIG
from fastapi import APIRouter, Query, HTTPException, status
import psycopg2 as pg

from src.validation import SHORTCODE_REGEX
from validation import DISCORD_ID_REGEX

env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union


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
    shortcode: str = Query(min_length=3, max_length=7,
                           pattern=SHORTCODE_REGEX)
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
    id: str = Query(min_length=17, max_length=19, pattern=DISCORD_ID_REGEX)
) -> dict:
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
    shortcode: str = Query(min_length=3, max_length=7, pattern=SHORTCODE_REGEX)
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


@discord_id_router.post("/deregister")
def deregister_user(
    discord_id: str = Query(min_length=17, max_length=19,
                            DISCORD_ID_REGEX=DISCORD_ID_REGEX
                            )
) -> dict:
    valid = change_valid(discord_id, 1)
    return {
        "msg": "Membership Reverified!",
        "valid": valid,
    }


@discord_id_router.post("/register")
def register_user(
    shortcode: str = Query(min_length=3, max_length=7,
                           pattern=SHORTCODE_REGEX),
    discord_id: str = Query(min_length=17, max_length=19,
                            DISCORD_ID_REGEX=DISCORD_ID_REGEX
                            )
) -> dict:
    is_member = union.isMember(shortcode)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                f"Shortcode: {shortcode} is not a member."
            )
        )

    if shortcode_exists(shortcode):
        if valid_mapping(shortcode, discord_id):
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail={
                    "msg": (f"Shortcode {shortcode}, Discord User: "
                            f"{discord_id} already in database"),
                }
            )
        else:
            valid = change_valid(discord_id, 1)
            return {
                "msg": "Membership Reverified!",
                "valid": valid,
            }
    else:
        valid = add_mapping(shortcode, discord_id=discord_id)
        return {
            "msg": f"User: shortcode {shortcode}, discord_id {discord_id} added successfully",  # noqa: E501
            "valid": valid
        }


def add_mapping(shortcode: str, discord_id: str) -> bool:
    """
    Add user shortcode, discord id to database

    Args:
        shortcode (str): shortcode
        discord_id (str): discord user id

    Returns:
        bool: if insert operation was successful
    """
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO public.mapping VALUES (%s,%s,%s)',
                (discord_id.lower().strip(), shortcode.lower().strip(), 1)
            )
            conn.commit()
    return True


def shortcode_exists(shortcode: str) -> bool:
    """
    Check if shortcode exists in the mapping db

    Args:
        shortcode (str): shortcode

    Returns:
        bool: if shortcode exists in the mapping db
    """
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.mapping WHERE shortcode = %s',
                           (shortcode.lower().strip(),))
            return any(cursor.fetchall())


def valid_mapping(
        shortcode: str,
        discord_id: str) -> bool:
    """
    Check if the discord id, shortcode mapping is active

    Args:
        shortcode (str): shortcode of user
        discord_id (str): discord id of user

    Returns:
        bool: whether the discord id, shortcode mapping is active
    """
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT active FROM public.mapping WHERE shortcode=%s AND user_id=%s',  # noqa: E501
                (shortcode.lower().strip(), discord_id)
            )
            val = cursor.fetchall()
            if any(val):
                valid = val[0][0]
            else:
                valid = 0
    return bool(valid)


def change_valid(
    userid: str,
    valid: int
) -> bool:
    """
    change_valid changes the validity of a shortcode for a given user id

    Parameters
    ----------
    userid : String
        Discord user id
    valid : int
        Validity status, 0 for invalid, 1 for valid

    Returns
    -------
    bool
        True if the validity status was changed, False otherwise

    Raises
    ------
    KeyError
        Raised if the validity status is not 0 or 1
    """
    if (valid in {0, 1}):
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                UPDATE public.mapping
                SET active = %s
                WHERE user_id = %s
                ''', (valid, str(userid))
                )
            conn.commit()
        return True
    else:
        raise KeyError('Issue changing valid status')

import logging
import os
import pydantic
import psycopg2 as pg

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.database import DB_CONFIG

from src.auth import get_current_username
from src.union import cid_to_shortcode
from src.validation import SHORTCODE_REGEX


env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

member_router = APIRouter(prefix="/member", tags=["Member"])


class MemberDetails(BaseModel):
    id: str = pydantic.Field(min_length=8, max_length=14)
    shortcode: str = pydantic.Field(min_length=3, max_length=7)
    print: bool = pydantic.Field(True)
    laser: bool = pydantic.Field(False)


@member_router.post("/add")
def add_icrs_member(
    username: Annotated[str, Depends(get_current_username)],
    member_details: MemberDetails,
) -> str:
    """
    Add a member to the database for inductions

    Args:
        username (Annotated[ str, Depends): authentication stuff for fastapi
        member_details (MemberDetails): member details - card uuid, shortcode,
            and permissions

    Raises:
        HTTPException: internal server error if member could not be added to db

    Returns:
        str: is member
    """
    id = member_details.id.upper().strip().replace(" ", "")
    shortcode = member_details.shortcode.lower()

    is_member = union.isMember(shortcode)
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.induction (shortcode, "
                    "valid, canPrint, canLaserCut) VALUES (%s,%s,%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (
                        shortcode,
                        is_member,
                        member_details.print,
                        member_details.laser,
                    )
                )

                cur.execute(
                    "INSERT INTO public.shortcode_card_mapping "
                    "(id, shortcode) VALUES (%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (id, shortcode),
                )
                conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred when adding member to database: {e}",
        )

    return f"Is Member: {is_member}"


class MemberPermissions(BaseModel):
    shortcode: str = pydantic.Field(min_length=3, max_length=7)
    print: bool = pydantic.Field(default=False)
    laser: bool = pydantic.Field(default=False)
    inducted: bool = pydantic.Field(default=True)


@member_router.get("/permissions/shortcode")
def get_member_permissions_from_shortcode(
    username: Annotated[str, Depends(get_current_username)],
    shortcode: str = Query(min_length=3, max_length=7),
) -> MemberPermissions | dict:
    """
    Get member permissions from shortcode

    Args:
        username (Annotated[ str, Depends): authentication stuff for fastapi
        shortcode (str, optional): member shortcode.
            Defaults to Query(min_length=3, max_length=7).

    Raises:
        HTTPException: internal server error if error querying db

    Returns:
        MemberPermissions | dict: member permissions or empty dict
    """
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT canprint, canlasercut, valid "
                    "FROM public.induction WHERE shortcode=%s",
                    (shortcode,),
                )  # noqa: E501
                result = cur.fetchone()
                if not result:
                    result = {}
                else:
                    result = MemberPermissions(
                        shortcode=shortcode,
                        print=result[0],
                        laser=result[1],
                        inducted=result[2],
                    )
                return result
    except Exception as e:
        error_msg = (
            "Could not query database/result return"
            f"in unexpected format: {e}"
        )
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


@member_router.get("/permissions/uuid")
def get_member_permissions_from_uuid(
    username: Annotated[str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14),
) -> MemberPermissions | dict:
    """
    Get member permissions from uuid

    Args:
        username (Annotated[ str, Depends): authentication stuff for fastapi
        uuid (str, optional): member card uuid.
            Defaults to Query(min_length=8, max_length=14).

    Raises:
        HTTPException: internal server error if error querying db

    Returns:
        MemberPermissions | dict: member permissions or empty dict
    """
    uuid = "".join(u.zfill(2) for u in uuid.split(" "))

    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT i.shortcode, i.canprint, i.canlasercut, valid FROM "  # noqa: E501
                    "public.induction i JOIN public.shortcode_card_mapping s ON "  # noqa: E501
                    "i.shortcode=s.shortcode WHERE s.id=%s",
                    (uuid,),
                )
                result = cur.fetchone()

                if not result:
                    result = {}
                else:
                    result = MemberPermissions(
                        shortcode=result[0],
                        print=result[1],
                        laser=result[2],
                        inducted=result[3],
                    )
                return result
    except Exception as e:
        error_msg = (
            "Could not query database/result return" +
            f"in unexpected format: {e}"
        )
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


@member_router.get("/refresh/all")
def refresh_all_membership(
    username: Annotated[str, Depends(get_current_username)],
):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode From public.induction WHERE "
                    "NOT valid"
                )

                update = [c[0] for c in cur.fetchall()]
                update = union.is_member_list(update)

                set_valid_by_shortcode = (
                    "UPDATE public.induction"
                    + "SET valid='1', canprint='1' WHERE shortcode=%s"
                )

                cur.executemany(set_valid_by_shortcode, [(c,) for c in update])

                conn.commit()

                return "Successfully Registered Users"
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error Querying/Updating db or Union API: {e}")
        return "FAILURE"


@member_router.post("/permissions/update")
def update_permissions(
    username: Annotated[str, Depends(get_current_username)],
    permissions: MemberPermissions,
):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.induction SET canPrint=%s, canLaserCut=%s "
                    "WHERE shortcode=%s and valid",
                    (
                        permissions.print,
                        permissions.laser,
                        permissions.shortcode.lower(),
                    ),
                )

                return "Permissions Updated"
    except Exception as e:
        error_msg = f"Error Updating db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


@member_router.post("/register/card/cid")
def register_card_details_cid(
    username: Annotated[str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14),
    cid: str = Query(regex=r"\d{8}")
):
    shortcode = cid_to_shortcode(cid)
    if not shortcode:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,
                            detail="CID not found!")

    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.shortcode_card_mapping (id, "
                    "shortcode) VALUES (%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (
                        uuid.upper(),
                        shortcode.lower(),
                    )
                )

    except Exception as e:
        error_msg = f"Error Updating db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


@member_router.post("/register/card/shortcode")
def register_card_details_shortcode(
    username: Annotated[str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14),
    shortcode: str = Query(regex=SHORTCODE_REGEX),
):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.shortcode_card_mapping (id, "
                    "shortcode) VALUES (%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (
                        uuid.upper(),
                        shortcode.lower(),
                    )
                )

    except Exception as e:
        error_msg = f"Error Updating db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )

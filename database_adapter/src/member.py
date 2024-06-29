import logging
import os
import pydantic
import psycopg2 as pg

from typing import Annotated
from fastapi import APIRouter, Depends,  HTTPException, Query, status
from pydantic import BaseModel

from src.database import DB_CONFIG

from src.auth import get_current_username


env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

member_router = APIRouter(prefix="/member", tags=["Member"])


class MemberDetails(BaseModel):
    id: str = pydantic.Field(min_length=8, max_length=14)
    shortcode: str = pydantic.Field(min_length=3, max_length=7)
    canPrint: bool = pydantic.Field(True)
    canLaserCut: bool = pydantic.Field(False)


@member_router.post("/add")
def add_icrs_member(
    username: Annotated[
        str, Depends(get_current_username)],
    member_details: MemberDetails
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
                    "INSERT INTO public.access (id, shortcode, " +
                    "valid, canPrint, canLaserCut) VALUES (%s,%s,%s,%s,%s)",
                    (id,
                     shortcode,
                     is_member,
                     member_details.canPrint,
                     member_details.canLaserCut))

                conn.commit()
    except Exception as e:
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
    username: Annotated[
        str, Depends(get_current_username)],
    shortcode: str = Query(min_length=3, max_length=7)
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
                    "SELECT * FROM public.access WHERE shortcode=%s", (shortcode,))  # noqa: E501
                result = cur.fetchone()
                if not result:
                    result = {}
                else:
                    result = MemberPermissions(
                        shortcode=result[1],
                        print=result[2],
                        laser=result[3],
                        inducted=result[4]
                    )
                return result
    except Exception as e:
        error_msg = "Could not query database/result return" + \
            f"in unexpected format: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@member_router.get("/permissions/uuid")
def get_member_permissions_from_uuid(
    username: Annotated[
        str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14)
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
                cur.execute("SELECT * FROM public.access WHERE id=%s", (uuid,))
                result = cur.fetchone()

                if not result:
                    result = {}
                else:
                    result = MemberPermissions(
                        shortcode=result[1],
                        print=result[2],
                        laser=result[3],
                        inducted=result[4]
                    )
                return result
    except Exception as e:
        error_msg = "Could not query database/result return" + \
            f"in unexpected format: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@member_router.get("/refresh/all")
def refresh_all_membership(
    username: Annotated[
        str, Depends(get_current_username)],
):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode From public.access WHERE " +
                    "valid=\'FALSE\' OR valid=\'0\'")

                update = [c[0] for c in cur.fetchall()]
                update = union.is_member_list(update)

                set_valid_by_shortcode = "UPDATE public.access " + \
                    "SET valid=\'TRUE\', canprint=\'TRUE\' WHERE shortcode=%s"

                cur.executemany(set_valid_by_shortcode, [(c,) for c in update])

                conn.commit()

                return "Successfully Registered Users"
    except Exception as e:
        logging.error(f"Error Querying/Updating db or Union API: {e}")
        return "FAILURE"


@member_router.post("/permissions/update")
def update_permissions(
    username: Annotated[
        str, Depends(get_current_username)],
    permissions: MemberPermissions,
):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.access SET canPrint=%s, canLaserCut=%s " +
                    "WHERE shortcode=%s and valid=\'TRUE\'",
                    (str(permissions.print).upper(),
                     str(permissions.laser).upper(),
                     permissions.shortcode.lower())
                )

                conn.commit()
                return "Permissions Updated"
    except Exception as e:
        error_msg = f"Error Updating db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

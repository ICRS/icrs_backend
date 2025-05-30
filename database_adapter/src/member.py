import logging
import os
import pydantic

from typing import Annotated, Literal
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

member_router = APIRouter(prefix="/member", tags=["Member"])


class MemberDetails(BaseModel):
    id: str = pydantic.Field(min_length=8, max_length=14)
    shortcode: str = SHORTCODE_QUERY_PYDANTIC
    print: bool = pydantic.Field(True)
    laser: bool = pydantic.Field(False)


@member_router.get("")
def is_member(
    shortcode: str = SHORTCODE_QUERY,
):
    return union.isMember(shortcode)


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
        with main_db_pool.connection() as conn:
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
    shortcode: str = SHORTCODE_QUERY_PYDANTIC
    print: bool = pydantic.Field(default=False)
    laser: bool = pydantic.Field(default=False)
    inducted: bool = pydantic.Field(default=True)
    time_added: str = pydantic.Field(default="")
    card_id: str = pydantic.Field(min_length=8, max_length=14, default="")
    resin: bool = pydantic.Field(default=False)
    printer_override: bool = pydantic.Field(default=False)


@member_router.get("/permissions/shortcode")
def get_member_permissions_from_shortcode(
    username: Annotated[str, Depends(get_current_username)],
    shortcode: str = SHORTCODE_QUERY,
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
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT i.canprint, i.canlasercut, i.valid, i.time_added, m.id, i.can_resin, i.printer_override "  # noqa: E501
                    "FROM public.induction i "
                    "LEFT JOIN public.shortcode_card_mapping m ON i.shortcode=m.shortcode "  # noqa: E501
                    "WHERE i.shortcode = %s;",
                    (shortcode,)
                )

                result = cur.fetchone()

                logging.info(f"Result: {result}")
                if not result:
                    result = {}
                else:
                    datStr = result[3].strftime("%d %b %Y") if result[3] else "Unknown Date"  # noqa: E501

                    result = MemberPermissions(
                        shortcode=shortcode,
                        print=result[0],
                        laser=result[1],
                        inducted=result[2],
                        time_added=datStr,
                        card_id=result[4] if result[4] else "Not Found",
                        resin=result[5],
                        printer_override=result[6],
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
    update_log: bool = False,
    device: Literal['printer', 'gun'] = 'printer',
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
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT i.shortcode, i.canprint, i.canlasercut, valid, i.can_resin, i.printer_override FROM "  # noqa: E501
                    "public.induction i JOIN public.shortcode_card_mapping s ON "  # noqa: E501
                    "i.shortcode=s.shortcode WHERE s.id=%s",
                    (uuid,),
                )
                result = cur.fetchone()

                if not result:
                    result = {}
                    if update_log:
                        cur.execute(
                            "INSERT INTO public.card_scan_log "
                            "(id, device) VALUES (%s, %s) "
                            "ON CONFLICT DO NOTHING",
                            (uuid, device),
                        )
                else:
                    result = MemberPermissions(
                        shortcode=result[0],
                        print=result[1],
                        laser=result[2],
                        inducted=result[3],
                        resin=result[4],
                        printer_override=result[5],
                    )
                    if update_log:
                        cur.execute(
                            "INSERT INTO public.card_scan_log "
                            "(id, valid, device) VALUES (%s,%s,%s) "
                            "ON CONFLICT DO NOTHING",
                            (uuid, (result.inducted and result.print), device),
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
        with main_db_pool.connection() as conn:
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
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE public.induction SET "
                    "valid=%s, canPrint=%s, canLaserCut=%s, can_resin=%s, printer_override=%s "
                    "WHERE shortcode=%s",
                    (
                        permissions.inducted,
                        permissions.print,
                        permissions.laser,
                        permissions.resin,
                        permissions.printer_override,
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
        with main_db_pool.connection() as conn:
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


@member_router.delete("/register/card")
def remove_card_details_cid(
    username: Annotated[str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14),
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM public.shortcode_card_mapping "
                    "WHERE id=%s",
                    (
                        uuid.upper(),
                    )
                )
                v = cur.rowcount
                logging.info(f"Deleting uuid {uuid} with result {v}")
                return {"deleted": v}

    except Exception as e:
        error_msg = (f"Error Deleting Card {uuid} from shortcode mapping "
                     f"table: {e}")
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


@member_router.post("/register/card/shortcode")
def register_card_details_shortcode(
    username: Annotated[str, Depends(get_current_username)],
    uuid: str = Query(min_length=8, max_length=14),
    shortcode: str = SHORTCODE_QUERY,
):
    try:
        with main_db_pool.connection() as conn:
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

@member_router.get("/scans/last")
def get_last_scans(n : int = 5, device : Literal['printer', 'gun'] = 'gun'):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT TO_CHAR(c.scanned_time, 'yyyy-mm-ddThh24:mi:ss'), c.id, i.valid, s.shortcode, m.user_id FROM public.card_scan_log c "
                    "LEFT JOIN public.shortcode_card_mapping s ON UPPER(s.id) = UPPER(c.id) "
                    "LEFT JOIN public.mapping m ON s.shortcode=m.shortcode "
                    "LEFT JOIN public.induction i ON i.shortcode=s.shortcode "
                    "WHERE c.device=%s "
                    "ORDER BY scanned_time DESC LIMIT %s ",
                    (device, n,)
                )

                scans = cur.fetchall()

                return scans
    except Exception as e:
        error_msg = f"Error fetching from db: {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
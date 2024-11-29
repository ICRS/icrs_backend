from dataclasses import dataclass
import logging
import os

from typing import Annotated
from fastapi import APIRouter, Depends,  HTTPException, status

from src.database import main_db_pool

from src.auth import get_current_username

env = os.getenv("ENV", "dev")

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

summary = APIRouter(prefix="/summary", tags=["Summary"])
summary_v2 = APIRouter(prefix="/v2/summary", tags=["Summary"])


@summary.get("/inducted")
def all_inducted(
    username: Annotated[
        str, Depends(get_current_username)],
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT shortcode FROM public.induction WHERE valid")
                inducted = cur.fetchall()
                inducted = union.getShortcodesToCIDAndName(
                    [i[0] for i in inducted])
                inducted = [
                    " - ".join(c) + "@ic.ac.uk" for c in inducted
                ]

                return inducted
    except Exception as e:
        error_msg = f"Could not query database {e}"
        logging.warning(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@summary.get("/inducted/recent")
def recently_inducted(
    username: Annotated[
        str, Depends(get_current_username)],
):
    try:
        with main_db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT shortcode FROM public.induction A " +
                            "WHERE valid AND NOT EXISTS " +
                            "(SELECT \'X\' FROM public.sent S " +
                            "WHERE A.shortcode=S.shortcode)")
                update = [c[0] for c in cur.fetchall()]

                cur.execute("SELECT shortcode, time_added FROM public.sent S "
                            "ORDER BY time_added DESC")
                sent = {c[0]: c[1] for c in cur.fetchall()}

                mapping = union.getShortcodesToCIDAndName(update)
                sent_info = [
                    (a, b, c, sent[c]) for a, b, c in
                    union.getShortcodesToCIDAndName(list(sent))]

                cur.executemany(
                    "INSERT INTO public.sent (shortcode) VALUES (%s)",
                    [(c,) for c in update])

                return mapping, sent_info
    except Exception as e:
        error_msg = f"Error when querying db or inserting into  {e}"
        logging.error(error_msg)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@dataclass
class InductionInfo:
    shortcode: str
    cid: str
    name: str


@summary_v2.get("/inducted")
def all_inducted_v2(
    username: Annotated[
        str, Depends(get_current_username)],
) -> list[InductionInfo]:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT shortcode FROM public.induction WHERE valid")
            inducted = cur.fetchall()
            inducted = union.getShortcodesToCIDAndName(
                [i[0] for i in inducted])
            inducted = [
                InductionInfo(
                    shortcode=shortcode,
                    cid=cid,
                    name=name
                ) for name, cid, shortcode in inducted
            ]

            return inducted


@summary_v2.get("/inducted/recent")
def recently_inducted_v2(
    username: Annotated[
        str, Depends(get_current_username)],
    update: bool = False
) -> tuple[list[InductionInfo], list[InductionInfo]]:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT shortcode FROM public.induction A " +
                        "WHERE valid AND NOT EXISTS " +
                        "(SELECT \'X\' FROM public.sent S " +
                        "WHERE A.shortcode=S.shortcode)")
            update = [c[0] for c in cur.fetchall()]

            cur.execute("SELECT shortcode, time_added FROM public.sent S "
                        "ORDER BY time_added DESC")
            sent = {c[0]: c[1] for c in cur.fetchall()}

            mapping = [
                InductionInfo(
                    shortcode=shortcode,
                    cid=cid,
                    name=name
                )
                for name, cid, shortcode in
                union.getShortcodesToCIDAndName(update)]
            sent_info = [
                InductionInfo(
                    shortcode=shortcode,
                    cid=cid,
                    name=name
                )
                for name, cid, shortcode in
                union.getShortcodesToCIDAndName(list(sent))]

            if update:
                cur.executemany(
                    "INSERT INTO public.sent (shortcode) VALUES (%s)",
                    [(c,) for c in update])

            return mapping, sent_info

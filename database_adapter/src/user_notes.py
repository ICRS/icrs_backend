from dataclasses import dataclass
import datetime
import logging
from fastapi import APIRouter, HTTPException, Query, status

from src.database import main_db_pool


user_notes_router = APIRouter(
    prefix="/user/notes",
    tags=["User Notes"]
)


@dataclass
class UserNote:
    uid: int
    shortcode: str
    note: str
    created: datetime.datetime


@user_notes_router.get("")
def get_notes_by_discord_id(
    id: str = Query(min_length=17, max_length=19)
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT u.id, u.shortcode, u.note, u.created "
                 "FROM public.mapping m "
                 "LEFT JOIN public.user_notes u "
                 "ON u.shortcode=m.shortcode "
                 "WHERE m.user_id=%s AND u.id IS NOT NULL "
                 "ORDER BY u.created DESC"),
                (id,)
            )
            user_notes = cur.fetchall()
    if not user_notes:
        msg = f"No user notes available for discord {id}"
        logging.info(msg)
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=msg
        )

    user_notes = [UserNote(*r) for r in user_notes]
    return user_notes


@user_notes_router.post("")
def add_note_by_discord_id(
    id: str = Query(min_length=17, max_length=19),
    note: str = Query(default=""),
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("INSERT INTO public.user_notes (shortcode, note) "
                 "(SELECT shortcode, %s as note "
                 "FROM public.mapping m "
                 "WHERE user_id = %s LIMIT 1) "
                 "RETURNING id, shortcode, note, created"),
                (note, id)
            )
            c = cur.fetchone()
            detail = f"Not inserted: discord id not found {id}"
            if not c:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail=detail
                )
            return UserNote(*c)


@user_notes_router.delete("")
def delete_note_by_id(
    id: int,
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("DELETE FROM USER_NOTES WHERE id=%s "
                 "RETURNING id"
                 ),
                (id,)
            )
            return {"id": cur.fetchone()[0]}

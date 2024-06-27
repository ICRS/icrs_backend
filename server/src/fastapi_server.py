import datetime
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
import pydantic

from database import DB_CONFIG

import psycopg2 as pg

from fast_auth import get_current_username

env = os.getenv("ENV", "dev")

if env == "dev":
    import union_mock as union
else:
    import union as union


app = FastAPI()

last_set_time = datetime.datetime.fromtimestamp(0)
last_short_code = ''


class MemberDetails(BaseModel):
    id: str = pydantic.Field(min_length=8, max_length=14)
    shortcode: str = pydantic.Field(min_length=3, max_length=7)
    canPrint: bool = pydantic.Field(True)
    canLaserCut: bool = pydantic.Field(False)


@app.post("/member/add")
def add_icrs_member(
    username: Annotated[
        str, Depends(get_current_username)],
    member_details: MemberDetails
):
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

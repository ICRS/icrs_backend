import json
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
import psycopg2 as pg
from pydantic import BaseModel

from src.database import DB_CONFIG


induction_router = APIRouter(
    prefix="/induction",
    tags=["Induction Quiz"]
)


class QuizAsset(BaseModel):
    media: str
    type: str
    data: str


class QuizRow(BaseModel):
    question: str
    correct_options: List[str]
    incorrect_options: List[str]
    num_answers: int
    single_choice: bool = False
    assets: List[QuizAsset] = []


def get_options(s: str):
    return [c for c in s.split(';') if c]


@induction_router.get("/quiz")
def quiz() -> List[QuizRow]:
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT q.QUESTION, q.CORRECT_OPTIONS, q.INCORRECT_OPTIONS, "
                 "q.NUM_ANSWERS, q.SINGLE_CHOICE, q.ASSETS "
                 "FROM public.induction_quiz q ORDER BY q.order ASC"),
            )
            quiz = cur.fetchall()
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No Quiz available"
        )

    quiz = [QuizRow(
        question=r[0], correct_options=get_options(r[1]),
        incorrect_options=get_options(r[2]), num_answers=r[3],
        single_choice=r[4],
        assets=json.loads(r[5]) if r[5] else []) for r in quiz]

    return quiz


@induction_router.post("/induct/discord-id")
def induct(
    id: str = Query(min_length=17, max_length=19)
):
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("INSERT INTO public.induction (shortcode, "
                 "valid, canPrint) "
                 "SELECT SHORTCODE, TRUE, TRUE "
                 "FROM public.mapping WHERE user_id=%s "
                 "ON CONFLICT(shortcode) "
                 "DO UPDATE SET (valid, canPrint) = (TRUE, TRUE)"
                 ),
                (id,)
            )

    return True

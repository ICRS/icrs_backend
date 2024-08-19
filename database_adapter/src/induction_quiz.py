from typing import List
from fastapi import APIRouter, HTTPException, status
import psycopg2 as pg
from pydantic import BaseModel

from src.database import MEME_DB_CONFIG


induction_router = APIRouter(
    prefix="/induction",
    tags=["Induction Quiz"]
)


class QuizRow(BaseModel):
    question: str
    correct_options: List[str]
    incorrect_options: List[str]
    num_answers: int


@induction_router.get("/quiz")
def quiz():
    with pg.connect(**MEME_DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT QUESTION, CORRECT_OPTIONS, INCORRECT_OPTIONS, "
                 " NUM_ANSWERS FROM public.induction_quiz"),
            )
            quiz = cur.fetchall()
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No Quiz available"
        )

    quiz = [QuizRow(
        question=r[0], correct_options=r[1].split(';'),
        incorrect_options=r[2].split(';'), num_answers=r[3]) for r in quiz]

    return quiz

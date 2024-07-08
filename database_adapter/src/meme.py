import io
import psycopg2 as pg

from fastapi import APIRouter, HTTPException, Response, status
from PIL import Image

from src.database import DB_CONFIG


meme_router = APIRouter(prefix="/meme", tags=["Meme"])


@meme_router.get("/quote/random")
def get_random_quote(name: str):
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT quote FROM public.user_quote WHERE name=%s ORDER "
                 "BY RANDOM() LIMIT 1"),
                (name,))
            quote = cur.fetchone()
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No Quote for Person"
        )

    return {
        "quote": quote[0],
        "name": name
    }


@meme_router.get("/image/random")
async def get_random_image(name: str):
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                ("SELECT image FROM public.user_image WHERE name=%s ORDER "
                 "BY RANDOM() LIMIT 1"),
                (name,))
            img = cur.fetchone()

    if img is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No Image for Person"
        )

    img = Image.open(io.BytesIO(img[0]))
    img_io = io.BytesIO()
    img.save(img_io, format='png')
    img_io.seek(0)
    binary_data = img_io.read()

    return Response(
        content=binary_data,
        media_type="image/png")

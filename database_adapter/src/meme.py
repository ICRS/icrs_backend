import base64
import io
import logging
import os

from fastapi import APIRouter, HTTPException, Query, Response, status
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pydantic

from src.database import meme_db_pool


meme_router = APIRouter(prefix="/meme", tags=["Meme"])


class Quote(pydantic.BaseModel):
    name: str = pydantic.Field()
    quote: str = pydantic.Field()


@meme_router.post("/quote")
def add_quote(payload: Quote):
    with meme_db_pool.connection() as conn:
        with conn.cursor() as cur:
            logging.info(f"Insert quote: {payload}")
            cur.execute(
                ("INSERT INTO public.user_quote (name, quote) "
                 "VALUES (%s,%s)"
                 ),
                (payload.name, payload.quote)
            )
            v = cur.rowcount
            if not v:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Quote already in db"
                )


@meme_router.get("/quote/random")
def get_random_quote(name: str):
    with meme_db_pool.connection() as conn:
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
    with meme_db_pool.connection() as conn:
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


@meme_router.get("/random")
async def get_random_meme(name: str = Query("")):
    with meme_db_pool.connection() as conn:
        with conn.cursor() as cur:
            if not name:
                cur.execute(
                    ("SELECT s.name, t.quote, s.image "
                     "FROM (SELECT name, image FROM public.user_image ORDER BY RANDOM() LIMIT 1) s "  # noqa: E501
                     "LEFT JOIN public.user_quote t ON s.name=t.name "
                     "ORDER BY RANDOM() LIMIT 1"))
            else:
                cur.execute(
                    ("SELECT s.name, t.quote, s.image "
                     "FROM (SELECT name, image FROM public.user_image WHERE name=%s ORDER BY RANDOM() LIMIT 1) s "  # noqa: E501
                     "LEFT JOIN public.user_quote t ON s.name=t.name "
                     "ORDER BY RANDOM() LIMIT 1"), (name,))

            data = cur.fetchone()

            if data is None:
                msg = f"Not enough data for {name} or failed to query db"
                logging.warning(msg)
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail=msg
                )

            n, quote, image = data
            img = Image.open(io.BytesIO(image))
            image = generate(img, n, quote)

            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue())

            return {
                "name": n,
                "quote": quote,
                # "size": len(image),
                "data": img_str,
            }


@meme_router.get("/names")
async def get_names():
    with meme_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT name FROM public.user_quote")
            data = cur.fetchall()
            if data is None:
                msg = "Nothing in db"
                logging.warning(msg)
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail=msg
                )

            return [d[0] for d in data]


def generate(image: Image.Image, author: str, quote: str,
             font=("assets/fonts/Precious.ttf")) -> Image.Image:
    """
    generate a quote image from a given image and quote

    Parameters
    ----------
    IMAGE_PATH : String
        Path to the Image
    author : String
        Author of quote
    quote : String
        Quote
    font : String, optional
        Path to the font file, by default "assets/fonts/Precious.ttf"

    Returns
    -------
    PIL.Image.Image
        PIL Image Object
    """
    logging.info("Image Opened")
    grayscale = image.convert("L")
    width, height = grayscale.size
    ratio = 400/width
    grayscale = grayscale.resize((int(width*ratio), int(height*ratio)))
    logging.info("Image Resized")
    temp = io.BytesIO()

    grayscale.save(temp, format="PNG")

    logging.info("Image Temp Saved")

    img = convert(
        quote=quote,
        author=author,
        fg="white",
        image=temp,
        border_color="black",
        font_size=40,
        font_file=font,
        width=400,
        height=400)

    return img


def convert(quote, author, fg, image: Image.Image, border_color,
            font_file=None, font_size=None, width=None, height=None):
    """
    convert a quote to an image

    Parameters
    ----------
    quote : String
        Quote to be converted
    author : String
        Author of the Quote
    fg : String
        Foreground Color
    image : PIL.Image.Image
        Image to be used as background
    border_color : String
        Border Color
    font_file : String, optional
        Path to font file, by default None
    font_size : int, optional
        Font size, by default None
    width : int, optional
        Width of new image, by default None
    height : int, optional
        Height of new image, by default None

    Returns
    -------
    PIL.Image.Image
        Image with quote
    """
    x1 = width if width else 612
    y1 = height if height else 612

    sentence = f"{quote} - {author}"

    font = ImageFont.truetype(font_file if font_file
                              else os.path.relpath("assets/fonts/Coves Bold.otf"),  # noqa: E501
                              font_size if font_size else 32)

    img = Image.new("RGB", (x1, y1), color=(255, 255, 255))

    back = Image.open(image, 'r')
    img_w, img_h = back.size
    bg_w, bg_h = img.size
    offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
    bback = back.filter(ImageFilter.BLUR)
    img.paste(bback, offset)

    d = ImageDraw.Draw(img)

    sum_value = 0
    for letter in sentence:
        s = font.getbbox(letter)
        sum_value += s[2] - s[0]
    average_length_of_letter = sum_value / len(sentence)

    number_of_letters_for_each_line = (x1 / 1.618) / average_length_of_letter
    incrementer = 0
    fresh_sentence = ""

    for letter in sentence:
        if letter == "-":
            fresh_sentence += "\n\n" + letter
        elif incrementer < number_of_letters_for_each_line:
            fresh_sentence += letter
        else:
            if letter == " ":
                fresh_sentence += "\n"
                incrementer = 0
            else:
                fresh_sentence += letter
        incrementer += 1

    x2 = max([font.getbbox(line) for line in fresh_sentence.split('\n')],
             key=lambda x: x[2] - x[0])[2]
    fline = font.getbbox(fresh_sentence.split('\n')[0])
    y2 = (fline[3] - fline[1]) * len(fresh_sentence.split('\n'))

    qx = x1 / 2 - x2 / 2
    qy = y1 / 2 - y2 / 2

    d.text((qx-1, qy-1), fresh_sentence, align="center",
           font=font, fill=border_color)
    d.text((qx+1, qy-1), fresh_sentence, align="center",
           font=font, fill=border_color)
    d.text((qx-1, qy+1), fresh_sentence, align="center",
           font=font, fill=border_color)
    d.text((qx+1, qy+1), fresh_sentence, align="center",
           font=font, fill=border_color)

    d.text((qx, qy), fresh_sentence, align="center", font=font, fill=fg)

    return img

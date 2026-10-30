__all__ = [
    "SHORTCODE_REGEX",
    "DISCORD_ID_REGEX",
    "SHORTCODE_QUERY",
    "SHORTCODE_QUERY_PYDANTIC",
]

from fastapi import Query
from typing import Annotated
from pydantic import StringConstraints
import pydantic


SHORTCODE_REGEX = r'^[a-z]{2,3}[0-9]{2,5}$'
DISCORD_ID_REGEX = r'^<@[0-9]{17,21}>$'

SHORTCODE_QUERY = Query(
    pattern=SHORTCODE_REGEX,
    min_length=3,
    max_length=8)
SHORTCODE = Annotated[
    str,
    StringConstraints(
        pattern=SHORTCODE_REGEX,
        min_length=3,
        max_length=8,
    ),
]
SHORTCODE_QUERY_PYDANTIC = pydantic.Field(
    pattern=SHORTCODE_REGEX,
    min_length=3,
    max_length=8)

__all__ = [
    "CountResponse"
]

import pydantic


class CountResponse(pydantic.BaseModel):
    count: int = pydantic.Field()

from dataclasses import dataclass
import datetime
from fastapi import APIRouter
import pydantic
from src.database import main_db_pool

project_router = APIRouter(
    prefix="/occupancy",
    tags=["Occupancy"]
)


class OccupancyEvent(pydantic.BaseModel):
    time: datetime.datetime
    name: str = pydantic.Field(max_length=2048),
    occupancy: bool = False

class OccupancyResponse(pydantic.BaseModel):
    id: int

@project_router.post("/", response_model=OccupancyResponse)
def log_event(
    event: OccupancyEvent,
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO occupancy.history (timestamp, shortcode, active) "
                    "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING "
                    "RETURNING id"
                ),
                (event.time, event.name, event.occupancy)
            )

            return OccupancyResponse(cur.fetchone()[0])

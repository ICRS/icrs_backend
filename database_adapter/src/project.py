from dataclasses import dataclass
from fastapi import APIRouter
import pydantic
from src.database import main_db_pool


project_router = APIRouter(
    prefix="/project",
    tags=["Project"]
)


class Project(pydantic.BaseModel):
    title: str = pydantic.Field(max_length=50),
    description: str = pydantic.Field(max_length=2048)


@dataclass
class ProjectResponse:
    id: int


@project_router.post("")
def create_project(
    project: Project,
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO project.project_master (title, description) "
                    "VALUES (%s,%s) ON CONFLICT DO NOTHING "
                    "RETURNING id"
                ),
                (project.title, project.description)
            )

            return ProjectResponse(cur.fetchone()[0])

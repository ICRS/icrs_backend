from dataclasses import dataclass
import datetime
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


class ProjectSummary(Project):
    id: int = pydantic.Field()
    created_at: datetime.datetime = pydantic.Field()


class ProjectMembers(pydantic.BaseModel):
    shortcode: str = pydantic.Field(min_length=3, max_length=10)
    acknowledged: bool = pydantic.Field(False)
    registered_at: datetime.datetime = pydantic.Field()


class ProjectDetails(Project):
    title: str = pydantic.Field(max_length=50),
    description: str = pydantic.Field(max_length=2048)
    project_members: list[ProjectMembers] = pydantic.Field([])


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


@project_router.get("/list")
def get_project_summary(
) -> list[ProjectSummary]:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT ID, TITLE, DESCRIPTION, CREATED_AT "
                    "FROM project.project_master"
                ),
            )

            return [ProjectSummary(*p) for p in cur.fetchall()]


@project_router.get("")
def get_project(
    id: int
) -> ProjectDetails:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT m.id, m.title, m.description, m.created_at"
                    "FROM project.project_master m"
                    "WHERE m.id=%s"
                ),
                (id,)
            )

            project_detail = cur.fetch_one()

            cur.execute(
                (
                    "SELECT mem.shortcode, mem.shortcode, mem.registered_at"
                    "FROM project.project_members mem "
                    "WHERE mem.id=%s"
                ),
                (id,)
            )
            return ProjectDetails(
                title=project_detail[0],
                description=project_detail[1],
                project_members=[ProjectMembers(*c) for c in cur.fetchall()])

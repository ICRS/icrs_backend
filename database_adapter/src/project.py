from dataclasses import dataclass
import datetime
import logging
from fastapi import APIRouter, Query
import pydantic
from src.database import main_db_pool
from src.common import CountResponse

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
    priority: int = 0


class ProjectMembers(pydantic.BaseModel):
    shortcode: str = pydantic.Field(min_length=3, max_length=10)
    acknowledged: bool = pydantic.Field(False)
    registered_at: datetime.datetime = pydantic.Field(datetime.datetime.now())


class ProjectMemberPermission(pydantic.BaseModel):
    discord_id: int
    priority: int = 0


class ProjectMembersDiscordList(pydantic.BaseModel):
    discord_id: list[ProjectMemberPermission] = pydantic.Field()


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

            return [ProjectSummary(
                id=p[0],
                title=p[1],
                description=p[2],
                created_at=p[3]) for p in cur.fetchall()]


class ProjectFullDetails(ProjectSummary):
    id: int
    project_owners: list[str] = pydantic.Field([])
    project_members: list[str] = pydantic.Field([])
    tags: list[str] = pydantic.Field([])


@project_router.get("/all")
def get_project_all(
    count: int | None = None
) -> list[ProjectFullDetails]:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT ma.id, ma.title, ma.description, ma.created_at, "
                    "ARRAY("
                    "SELECT map.user_id FROM project.project_members mem "
                    "INNER JOIN public.mapping map ON map.shortcode=mem.shortcode WHERE mem.id=ma.id AND mem.priority=0) as owners, "
                    "ARRAY("
                    "SELECT map.user_id FROM project.project_members mem "
                    "INNER JOIN public.mapping map ON map.shortcode=mem.shortcode WHERE mem.id=ma.id AND mem.priority!=0) as members, "
                    "ARRAY(SELECT type "
                    "FROM project.project_type ty "
                    "WHERE ty.id=ma.id "
                    ") as tags "
                    "FROM project.project_master ma "
                    "ORDER BY ma.created_at DESC "
                    "LIMIT %s"
                ),
                (count, )
            )

            project_detail = cur.fetchall()
            logging.info(project_detail)
            return [
                ProjectFullDetails(
                    id=p[0],
                    title=p[1],
                    description=p[2],
                    created_at=p[3],
                    project_owners=[str(a) for a in p[4]],
                    project_members=[str(a) for a in p[5]],
                    tags=[str(a) for a in p[6]],
                )
                for p in project_detail
            ]


@project_router.get("/owned/discord/full/filtered")
def get_project_filtered(
    discord_id: int,
    count: int | None = Query(None),
) -> list[ProjectFullDetails]:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT ma.id, ma.title, ma.description, ma.created_at, "
                    "ARRAY("
                    "SELECT map.user_id FROM project.project_members mem "
                    "INNER JOIN public.mapping map ON map.shortcode=mem.shortcode WHERE mem.id=ma.id AND mem.priority=0) as owners, "
                    "ARRAY("
                    "SELECT map.user_id FROM project.project_members mem "
                    "INNER JOIN public.mapping map ON map.shortcode=mem.shortcode WHERE mem.id=ma.id AND mem.priority!=0) as members, "
                    "ARRAY(SELECT type "
                    "FROM project.project_type ty "
                    "WHERE ty.id=ma.id "
                    ") as tags "
                    "FROM project.project_master ma "
                    "JOIN project.project_members mem "
                    "ON mem.id=ma.id "
                    "INNER JOIN public.mapping map ON map.shortcode=mem.shortcode "
                    "WHERE map.user_id=%s AND mem.priority=0 "
                    "GROUP BY ma.id "
                    "ORDER BY ma.created_at DESC "
                    "LIMIT %s"
                ),
                (str(discord_id), count, )
            )

            project_detail = cur.fetchall()
            logging.info(project_detail)
            return [
                ProjectFullDetails(
                    id=p[0],
                    title=p[1],
                    description=p[2],
                    created_at=p[3],
                    project_owners=[str(a) for a in p[4]],
                    project_members=[str(a) for a in p[5]],
                    tags=[str(a) for a in p[6]],
                )
                for p in project_detail
            ]


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


@project_router.post(r"/{id}/member")
def register_member_for_project(
    id: int,
    members: list[ProjectMembers]
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT IGNORE INTO project.project_members "
                "(id, shortcode, acknowledged, registered_at) "
                "VALUES(%s,%s,%s,%s) "
                "ON CONFLICT DO NOTHING",
                [(id, mem.shortcode, mem.acknowledged, mem.registered_at)
                 for mem in members]
            )
            return CountResponse(count=cur.rowcount)


@project_router.post(r"/{id}/member/discord")
def register_discord_members_for_project(
    id: int,
    members: ProjectMembersDiscordList
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO project.project_members "
                "(id, shortcode, priority) "
                "SELECT %s, shortcode, %s "
                "FROM public.mapping "
                "WHERE user_id=%s and shortcode is not NULL "
                "ON CONFLICT DO NOTHING "
                "RETURNING %s as discord_id",
                [(id, mem.priority,  str(mem.discord_id), mem.discord_id)
                 for mem in members.discord_id],
                returning=True,
            )
            v = [c[0] for c in cur.fetchall()]
            logging.info(f"Inserted {v}")
            return {
                "members": v
            }


@project_router.get("/owned/discord")
def get_projects_owned(
    id: int,
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT m.id, m.title, m.description, m.created_at "
                "FROM project.project_master m "
                "JOIN project.project_members mem "
                "ON mem.id=m.id "
                "INNER JOIN public.mapping map "
                "ON map.shortcode=mem.shortcode "
                "WHERE map.user_id=%s and mem.priority=0",
                (str(id),)
            )
            return [ProjectSummary(
                id=p[0],
                title=p[1],
                description=p[2],
                created_at=p[3]) for p in cur.fetchall()]


@project_router.get("/discord")
def get_all_projects_discord(
    id: int,
):
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT m.id, m.title, m.description, m.created_at, mem.priority "
                "FROM project.project_master m "
                "JOIN project.project_members mem "
                "ON mem.id=m.id "
                "INNER JOIN public.mapping map "
                "ON map.shortcode=mem.shortcode "
                "WHERE map.user_id=%s",
                (str(id),)
            )
            return [ProjectSummary(
                id=p[0],
                title=p[1],
                description=p[2],
                created_at=p[3],
                priority=p[4]) for p in cur.fetchall()]


class ProjectTag(pydantic.BaseModel):
    tag: str = pydantic.Field()
    registered_at: datetime.datetime = pydantic.Field(datetime.datetime.now())


class ProjectTags(pydantic.BaseModel):
    id: int = pydantic.Field(-1)
    tags: list[ProjectTag] = pydantic.Field()


@project_router.get(r"/{id}/tags")
def get_project_tags(
    id: int,
) -> ProjectTags:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT type, registered_at "
                "FROM project.project_type "
                "WHERE id=%s",
                (str(id),)
            )
            return ProjectTags(
                id=id,
                tags=[
                    ProjectTag(
                        tag=p[0],
                        registered_at=p[1],
                    ) for p in cur.fetchall()])


@project_router.post(r"/{id}/tags")
def add_project_tags(
    id: int,
    project_tags: ProjectTags,
) -> CountResponse:
    with main_db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO project.project_type (id, type) "
                "VALUES "
                "(%s, %s) "
                "ON CONFLICT DO NOTHING ",
                [(id, tag.tag) for tag in project_tags.tags],
            )
            count = cur.rowcount
            logging.info(f"Inserted {count}")

            return CountResponse(count=count)

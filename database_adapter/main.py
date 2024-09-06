from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager

from psycopg_pool import ConnectionPool

from src.server import discord_id_router, shortcode_router
from src.print_metrics import print_metrics_router
from src.member import member_router
from src.summary import summary
from src.auth import auth_router
from src.meme import meme_router
from src.induction_quiz import induction_router
from src.project_box import project_box_router
from src.database import main_db_pool, meme_db_pool

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ])


@asynccontextmanager
async def lifespan(app: FastAPI):
    main_db_pool.open()
    meme_db_pool.open()
    yield
    main_db_pool.close()
    meme_db_pool.close()

app = FastAPI(lifespan=lifespan)

app.include_router(discord_id_router)
app.include_router(shortcode_router)
app.include_router(print_metrics_router)
app.include_router(member_router)
app.include_router(summary)
app.include_router(auth_router)
app.include_router(meme_router)
app.include_router(induction_router)
app.include_router(project_box_router)


def db_pool_healthy(db_pool: ConnectionPool):
    db_pool.check()
    stats = db_pool.get_stats()

    errors = stats.get("requests_errors", 0)
    errors += stats.get("returns_bad", 0)
    errors += stats.get("connections_errors", 0)
    errors += stats.get("connections_lost", 0)

    return errors < 5


@app.get("/healthz")
async def get_health():
    main_db_pool.check()
    meme_db_pool.check()

    if db_pool_healthy(main_db_pool) and db_pool_healthy(meme_db_pool):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Something bad happened to the db pools.\n"
                f"Main: {main_db_pool.get_stats()}.\n"
                f"Meme: {meme_db_pool.get_stats()}."),
        )

    return True

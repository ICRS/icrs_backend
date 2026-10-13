import logging
from contextlib import asynccontextmanager

# Before importing src, which logs while discovering the printer
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S')

from fastapi import FastAPI  # noqa: E402
from src.server import (router, status_router, print_router,  # noqa: E402
                        calibration_router, filament_router, ams_router,
                        start_background_tasks)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tasks = start_background_tasks()
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.include_router(status_router)
app.include_router(print_router)
app.include_router(calibration_router)
app.include_router(filament_router)
app.include_router(ams_router)

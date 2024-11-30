from fastapi import FastAPI
from src.server import (router, status_router, print_router,
                        calibration_router, filament_router, ams_router)

app = FastAPI()
app.include_router(router)
app.include_router(status_router)
app.include_router(print_router)
app.include_router(calibration_router)
app.include_router(filament_router)
app.include_router(ams_router)

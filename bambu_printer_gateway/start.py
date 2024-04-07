from fastapi import FastAPI
from src.server import router, status_router

app = FastAPI()
app.include_router(router)
app.include_router(status_router)
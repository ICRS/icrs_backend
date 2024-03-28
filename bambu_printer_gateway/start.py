from fastapi import FastAPI
from src.server import router

app = FastAPI()
app.include_router(router)
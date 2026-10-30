from fastapi import FastAPI
from src.server import admin_server_router
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ])


app = FastAPI()
app.include_router(admin_server_router)

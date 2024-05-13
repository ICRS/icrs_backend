from fastapi import FastAPI
from src.server import discord_id_router, shortcode_router
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

app = FastAPI()
app.include_router(discord_id_router)
app.include_router(shortcode_router)

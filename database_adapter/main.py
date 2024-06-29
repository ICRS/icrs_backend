from fastapi import FastAPI
from src.server import discord_id_router, shortcode_router
from src.print_metrics import print_metrics_router
from src.member import member_router
from src.summary import summary
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
app.include_router(print_metrics_router)
app.include_router(member_router)
app.include_router(summary)


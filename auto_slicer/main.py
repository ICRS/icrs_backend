import logging
from fastapi import FastAPI

from src.server import router


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s',  # noqa
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.StreamHandler()
                    ])

logging.info("Starting server")
app = FastAPI()
app.include_router(router)

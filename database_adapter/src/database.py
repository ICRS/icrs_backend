from configparser import ConfigParser
import os

from psycopg_pool import ConnectionPool

config = ConfigParser()
config.read('postgres.ini')

DB_CONFIG = {
    'dbname': config['postgres']['database'],
    'user': config['postgres']['user'],
    'password': config['postgres']['password'],
    'host': config['postgres']['host'],
    'port': config['postgres']['port']
}

MEME_DB = os.getenv("MEME_DB")

MEME_DB_CONFIG = {
    'dbname': MEME_DB,
    'user': config['postgres']['user'],
    'password': config['postgres']['password'],
    'host': config['postgres']['host'],
    'port': config['postgres']['port'],
}

main_db_pool = ConnectionPool(
    " ".join(f"{k}={v}" for k, v in DB_CONFIG.items()))
meme_db_pool = ConnectionPool(
    " ".join(f"{k}={v}" for k, v in MEME_DB_CONFIG.items()))

main_db_pool.wait()
meme_db_pool.wait()

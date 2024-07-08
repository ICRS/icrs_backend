from configparser import ConfigParser
import os


config = ConfigParser()
config.read('postgres.ini')

DB_CONFIG = {
    'database': config['postgres']['database'],
    'user': config['postgres']['user'],
    'password': config['postgres']['password'],
    'host': config['postgres']['host'],
    'port': config['postgres']['port']
}

MEME_DB = os.getenv("MEME_DB")

MEME_DB_CONFIG = {
    'database': MEME_DB,
    'user': config['postgres']['user'],
    'password': config['postgres']['password'],
    'host': config['postgres']['host'],
    'port': config['postgres']['port'],
}

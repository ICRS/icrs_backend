from configparser import ConfigParser

config = ConfigParser()
config.read('postgres.ini')

DB_CONFIG = {
    'database': config['postgres']['database'],
    'user': config['postgres']['user'],
    'password': config['postgres']['password'],
    'host': config['postgres']['host'],
    'port': config['postgres']['port']
}

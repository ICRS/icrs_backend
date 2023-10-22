import schedule
import time
import sqlite3
import requests
import os
from dotenv import load_dotenv
load_dotenv()

try:
    env = os.environ["ENV"]
except:
    env = "dev"

URL = 'http://127.0.0.1:8888/registerUsers'
def update_valid():
    res = requests.get(URL)
    print(res)
    
if __name__ == "__main__":
    schedule.every().day.at("18:00").do(update_valid)

    while True:
        schedule.run_pending()
        time.sleep(1)

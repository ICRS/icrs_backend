import base64
import csv
from datetime import datetime
from io import StringIO
import logging

from mailjet_rest import Client
import requests
import os
from requests.auth import HTTPBasicAuth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s]: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

API_KEY = os.environ['MJ_APIKEY_PUBLIC']
API_SECRET = os.environ['MJ_APIKEY_PRIVATE']
EMAIL = os.environ['MJ_EMAIL']
DATABASE_IP = os.environ["DATABASE_IP"]
DATABASE_ADAPTER_USER = os.getenv("DATABASE_ADAPTER_USER")
DATABASE_ADAPTER_PASSWORD = os.getenv("DATABASE_ADAPTER_PASSWORD")

BASIC_AUTH = HTTPBasicAuth(DATABASE_ADAPTER_USER, DATABASE_ADAPTER_PASSWORD)


def main():
    res = requests.get(
        f"{DATABASE_IP}/v2/summary/inducted/recent",
        params={"update": False},
        auth=BASIC_AUTH)

    if res.status_code != 200:
        msg = f"Could not get all inducted members: {res.reason}"
        logging.error(msg)
        return

    j = res.json()
    logging.debug(j)
    updated = [[
        v.get("name"),
        v.get("shortcode"),
        v.get("cid"),
        v.get("shortcode") + "@ic.ac.uk"]
        for v in j[0]]

    if not updated:
        logging.info("No records received, email not sending!")
        return

    update_csv_file = StringIO()
    writer = csv.writer(update_csv_file)
    writer.writerow(["name", "shortcode", "cid", "email"])
    writer.writerows(updated)
    update_csv_file.seek(0)

    mailjet = Client(auth=(API_KEY, API_SECRET))
    today = datetime.today().strftime(r'%Y-%m-%d')
    data = {
        'FromEmail': EMAIL,
        'Subject': 'Recent Inducted Members Report',
        'Text-part': f'Recently inducted {len(updated)} members',
        'Recipients': [{'Email': EMAIL}],
        "Attachments": [
            {
                "Content-type": "text/csv",
                "Filename": f"{today}.csv",
                "content": base64.b64encode(
                    update_csv_file.getvalue().encode()),
            }
        ],
    }

    result = mailjet.send.create(data=data)
    logging.info(result.status_code)
    logging.info(result.json())


if __name__ == "__main__":
    main()

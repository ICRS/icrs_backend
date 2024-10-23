import logging
from fastapi import APIRouter, Query
import requests
import json
import asyncio

from dotenv import load_dotenv
import os

from notion_client import AsyncClient


load_dotenv(override=True)

notion = AsyncClient(auth=os.environ["NOTION_SECRET"])

router = APIRouter(
    tags=["server"],
)

LATEST_UPDATES: list = []


class Row(dict):
    def __init__(self, row: dict):
        self.row = {}
        for k, v in row.items():
            if isinstance(v, dict):
                if v["type"] == "multi_select":
                    values = [val for val in v["multi_select"]]
                    if isinstance(values, list):
                        values = [v["name"] for v in values]
                    self.row.update({k: values})

                elif v["type"] == "title":
                    self.row.update({k: v["title"][0]["plain_text"]})

                else:
                    self.row.update({k: v[v["type"]]})

        super().__init__(self.row)

    def __getitem__(self, key):
        return self.row[key]


class Column(dict):
    def __init__(self, data, column):
        self.column = {}
        for row in data:
            d: dict = row["properties"][column]
            idx = len(self.column.keys())
            val: list[dict] = d[d.get("type", 0)]
            if isinstance(val, list):
                if val[0].get("type", 0) == "text":
                    val = [v.get("plain_text", 0) for v in val]
                else:
                    val = [v.get("name", 0) for v in val]
            self.column.update({idx: val})
        super().__init__(self.column)

    def __getitem__(self, key):
        return self.column[key]


class DB(dict):
    def __init__(self, db):
        self.db = dict(db)
        self.data = dict(self.db)["results"]
        self.columns = list(dict(self.data[0]["properties"]).keys())

    def get_columns(self) -> list:
        return self.columns

    def __getitem__(self, item):
        if isinstance(item, int):
            return Row(self.data[item]["properties"])
        elif isinstance(item, str):
            return Column(self.data, item)


async def func():
    db = await notion.databases.query(database_id=os.environ["NOTION_DATABASE_ID"])
    db = DB(db)
    print(db.get_columns())
    print(db["Item"])
    print(db[1])

# asyncio.get_running_loop().create_task(func())


def create_page():
    pass


@router.post("/add_component")
async def add_component():
    notion.databases.query(database_id=os.environ["NOTION_DATABASE_ID"])
    return




# @router.post("/availability")
# async def update_availability(
#     uid: str = "",
#     printer_name: str = Query(enum=PRINTER_NAMES),
#     available: bool = False,
# ):
#     logging.info(f"Updating availability for {uid} to {available}")
#     uid = uid.strip().replace(" ", "").rjust(8, "0")
#     r = requests.post(
#         f"http://{printer_name}{PRINTER_GATEWAY_ENDPOINT_SUFFIX}/printer/available", # noqa
#         params={"uid": uid, "available": available},
#     )

#     return r.status_code

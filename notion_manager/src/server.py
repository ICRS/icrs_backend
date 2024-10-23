import logging
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import os
from dotenv import load_dotenv

from notion_client import AsyncClient

# Load environment variables from a .env file, overriding any existing ones
load_dotenv(override=True)

# Initialize the Notion client with the secret API key from environment variables
notion = AsyncClient(auth=os.environ["NOTION_SECRET"])

# Create an API router with a tag 'server'
router = APIRouter(
    tags=["server"],
)

# Global variable to store the latest database updates
LOCAL_DB: 'DB' = None


class DB:
    """Database class to handle Notion database responses."""

    def __init__(self, db_response):
        # Store the list of results from the database query
        self.data = db_response["results"]
        # Extract the column names from the properties of the first result
        self.columns = list(self.data[0]["properties"].keys())

    def get_columns(self) -> list:
        # Return the list of column names
        return self.columns

    def __getitem__(self, item):
        # Allow indexing by integer (row) or string (column)
        if isinstance(item, int):
            # Return a Row object for the given index
            return Row(self.data[item]["properties"])
        elif isinstance(item, str):
            # Return a Column object for the given column name
            return Column(self.data, item)

    def __iter__(self):
        # Make the DB object iterable over its rows
        for row_data in self.data:
            yield Row(row_data["properties"])


class Row:
    """Row class to represent a row in the Notion database."""

    def __init__(self, row_props: dict):
        self.row = {}
        # Iterate over each property in the row
        for k, v in row_props.items():
            # Handle different property types accordingly
            if v["type"] == "multi_select":
                # Extract the names of selected options
                values = [option["name"] for option in v["multi_select"]]
                self.row[k] = values
            elif v["type"] == "title":
                # Extract the plain text from the title
                self.row[k] = v["title"][0]["plain_text"]
            elif v["type"] == "unique_id":
                # Construct the unique ID with prefix and number
                prefix = v["unique_id"].get("prefix", None)
                number = v["unique_id"]["number"]
                self.row[k] = f"{'' if prefix is None else prefix}{number}"
            elif v["type"] == "rich_text":
                # Concatenate all plain texts in the rich text
                texts = [text["plain_text"] for text in v["rich_text"]]
                self.row[k] = ''.join(texts)
            elif v["type"] == "number":
                # Store the numerical value
                self.row[k] = v["number"]
            elif v["type"] == "url":
                # Store the URL string
                self.row[k] = v["url"]
            else:
                # For other types, attempt to get the value directly
                self.row[k] = v.get(v["type"], None)

    def __getitem__(self, key):
        # Allow dictionary-like access to row data
        return self.row[key]

    def __dict__(self):
        # Return the row data as a dictionary
        return self.row


class Column:
    """Column class to represent a column in the Notion database."""

    def __init__(self, data, column_name):
        self.column = {}
        # Iterate over each row to extract the column data
        for idx, row in enumerate(data):
            # Get the property for the specified column
            prop = row["properties"][column_name]
            # Handle different property types accordingly
            if prop["type"] == "multi_select":
                # Extract the names of selected options
                values = [option["name"] for option in prop["multi_select"]]
                self.column[idx] = values
            elif prop["type"] == "title":
                # Extract the plain text from the title
                self.column[idx] = prop["title"][0]["plain_text"]
            elif prop["type"] == "unique_id":
                # Construct the unique ID with prefix and number
                prefix = prop["unique_id"].get("prefix", None)
                number = prop["unique_id"]["number"]
                self.column[idx] = f"{'' if prefix is None else prefix}{number}"
            elif prop["type"] == "rich_text":
                # Concatenate all plain texts in the rich text
                texts = [text["plain_text"] for text in prop["rich_text"]]
                self.column[idx] = ''.join(texts)
            elif prop["type"] == "number":
                # Store the numerical value
                self.column[idx] = prop["number"]
            elif prop["type"] == "url":
                # Store the URL string
                self.column[idx] = prop["url"]
            else:
                # For other types, attempt to get the value directly
                self.column[idx] = prop.get(prop["type"], None)

    def __getitem__(self, key):
        # Allow dictionary-like access to column data
        return self.column[key]


class ItemInfo(BaseModel):
    """Pydantic model for item information."""
    Item: str
    Link: Optional[str] = None
    Quantity: Optional[int] = None
    Requested_by: Optional[str] = None


class Item(dict):
    """Item class to format data according to Notion API requirements."""

    def __init__(self, item_info: ItemInfo):
        self.data = {}
        if item_info.Item:
            # Format the 'Item' property as a Notion title type
            self.data["Item"] = {
                "title": [
                    {
                        "text": {
                            "content": item_info.Item
                        }
                    }
                ]
            }
        if item_info.Link:
            # Format the 'Link' property as a Notion URL type
            self.data["Link"] = {
                "url": item_info.Link
            }
        if item_info.Quantity is not None:
            # Format the 'Quantity' property as a Notion number type
            self.data["Quantity"] = {
                "number": item_info.Quantity
            }
        if item_info.Requested_by:
            # Format the 'Requested_by' property as a Notion rich text type
            self.data["Requested_by"] = {
                "rich_text": [
                    {"text": {"content": item_info.Requested_by}}
                ]
            }
        # Add a default 'Tags' property with a multi-select value
        self.data["Tags"] = {
            "multi_select": [
                {"name": "To buy"}
            ]
        }
        # Initialize the dictionary with the formatted data
        super().__init__(self.data)

    def __getitem__(self, key):
        # Allow dictionary-like access to item data
        return self.data[key]


async def update_LOCAL_DB():
    """Background task to update the latest database entries periodically."""
    global LOCAL_DB
    while True:
        try:
            # Query the Notion database to get the latest data
            db_response = await notion.databases.query(database_id=os.environ["NOTION_DATABASE_ID"])
            # Update the local database with the new data
            LOCAL_DB = DB(db_response)
            # Wait for 60 seconds before updating again
            await asyncio.sleep(60)
        except Exception as e:
            # Log any exceptions that occur during the update
            logging.error(f"Error updating latest updates: {e}")
            # Wait before retrying to avoid rapid failure loops
            await asyncio.sleep(60)


@router.on_event("startup")
async def startup_event():
    """Startup event to start the background task."""
    # Schedule the update_LOCAL_DB function to run in the background
    asyncio.create_task(update_LOCAL_DB())


@router.post("/add_item")
async def add_item(item_info: ItemInfo):
    """
    Route to add an item to the Notion database.
    """
    # Create a new Item object from the provided item_info
    new_order = Item(item_info)
    try:
        # Use the Notion API to create a new page in the database
        response = await notion.pages.create(
            parent={"database_id": os.environ["NOTION_DATABASE_ID"]},
            properties=new_order
        )
        # Return a success message along with the response data
        return {"status": "success", "data": response}
    except Exception as e:
        # Log any exceptions that occur during the item addition
        logging.error(f"Error adding item: {e}")
        # Raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove_item")
async def remove_item(page_id: str):
    """
    Route to remove (archive) an item from the Notion database using its page ID.
    """
    try:
        # Use the Notion API to update the page and set 'archived' to True
        response = await notion.pages.update(page_id=page_id, archived=True)
        # Return a success message along with the response data
        return {"status": "success", "data": response}
    except Exception as e:
        # Log any exceptions that occur during the item removal
        logging.error(f"Error removing item: {e}")
        # Raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_items")
async def get_items():
    """
    Route to get the latest items from the Notion database.
    """
    global LOCAL_DB
    if LOCAL_DB is None:
        # Return an error message if the local database hasn't been initialized yet
        return {"status": "error", "message": "No data available"}
    else:
        # Convert each row in the local database to a dictionary
        data = [row.row for row in LOCAL_DB]
        # Return a success message along with the data
        return {"status": "success", "data": data}


@router.get("/get_item/{item_id}")
async def get_item(item_id: str):
    """
    Route to get a specific item from the Notion database using its page ID.
    """
    try:
        # Retrieve the page from the Notion database using the page ID
        page = await notion.pages.retrieve(page_id=item_id)
        # Extract the properties of the page
        properties = page["properties"]
        # Create a Row object from the properties
        item = Row(properties)
        # Return a success message along with the item data
        return {"status": "success", "data": item.row}
    except Exception as e:
        # Log any exceptions that occur during item retrieval
        logging.error(f"Error retrieving item: {e}")
        # Raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail=str(e))

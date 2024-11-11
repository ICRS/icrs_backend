import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os

from notion_client import AsyncClient
from .notion_classes import DB, Row

# =============================================================================
# Load environment variables from a .env file
# Note: This is only needed if you are running the server locally

# from dotenv import load_dotenv

# load_dotenv(override=True)
# =============================================================================

# Initialize the Notion client with
# the secret API key from environment variables
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
notion = AsyncClient(auth=os.environ["NOTION_SECRET"])

# Create an API router with a tag 'server'
router = APIRouter(
    prefix="/notion",
    tags=["server"],
)

# Global variable to store the latest database updates
LOCAL_DB: 'DB' = None


class ItemInfo(BaseModel):
    """Pydantic model for item information."""
    Item: str
    URL: Optional[str] = None
    Quantity: Optional[int] = None
    Requested_by: Optional[str] = None
    Reason: Optional[str] = None


class Item(dict):
    """Item class to format data according to Notion API requirements."""

    def __init__(self, item_info: ItemInfo):
        self.data: dict[str, dict[str, int | str | list | dict]] = {}
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
        if item_info.URL:
            # Format the 'URL' property as a Notion URL type
            self.data["URL"] = {
                "url": item_info.URL
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
        if item_info.Reason:
            # Format the 'Reason' property as a Notion rich text type
            self.data["Reason"] = {
                "rich_text": [
                    {"text": {"content": item_info.Reason}}
                ]
            }
        # Add a default 'Tags' property with a multi-select value
        self.data["Tags"] = {
            "multi_select": [
                {"name": "Discord"}
            ]
        }
        # Add a default 'Status' property with a select value
        self.data["Status"] = {
            "status": {
                "id": "ebc3b8a1-9df6-4fed-a380-1ab15fad1f1a",
                "name": "Todo"
            }
        }
        # Initialize the dictionary with the formatted data
        super().__init__(self.data)

    def __getitem__(self, key):
        # Allow dictionary-like access to item data
        return self.data[key]


def compare_databases(old_db: Optional[DB], new_db: DB) -> Dict[str, Any]:
    """Compare two databases and return the changes."""
    changes: dict[str, list] = {
        'added': [],
        'removed': [],
        'modified': []
    }

    old_pages = old_db.pages if old_db else {}
    new_pages = new_db.pages

    old_page_ids = set(old_pages.keys())
    new_page_ids = set(new_pages.keys())

    # Pages added
    for page_id in new_page_ids - old_page_ids:
        changes['added'].append(new_pages[page_id])

    # Pages removed
    for page_id in old_page_ids - new_page_ids:
        changes['removed'].append(old_pages[page_id])

    # Pages modified
    for page_id in old_page_ids & new_page_ids:
        old_page = old_pages[page_id]
        new_page = new_pages[page_id]
        if old_page != new_page:
            changes['modified'].append({'old': old_page, 'new': new_page})

    return changes


def handle_db_changes(changes: Dict[str, Any]):
    """Handle changes detected between databases."""
    # Print the changes
    if changes['added']:
        print("Added pages:")
        for page in changes['added']:
            print(f"Page ID: {page.page_id}, Data: {page.row}")

    if changes['removed']:
        print("Removed pages:")
        for page in changes['removed']:
            print(f"Page ID: {page.page_id}, Data: {page.row}")

    if changes['modified']:
        print("Modified pages:")
        for change in changes['modified']:
            old_page = change['old']
            new_page = change['new']
            print(f"Page ID: {old_page.page_id}")
            for key in old_page.row.keys():
                if old_page.row[key] != new_page.row[key]:
                    print(f"Changed {key}: {old_page.row[key]}"
                          f" -> {new_page.row[key]}")


async def update_LOCAL_DB():
    """Background task to update the latest database entries periodically."""
    global LOCAL_DB
    while True:
        try:
            # Query the Notion database to get the latest data
            db_response = await notion.databases.query(
                database_id=NOTION_DATABASE_ID)
            # Create a new DB instance
            new_db = DB(db_response)

            # Compare the new DB with the local DB
            if LOCAL_DB is not None:
                changes = compare_databases(LOCAL_DB, new_db)
                # If there are any changes, handle them
                if changes['added'] or changes['removed'] \
                        or changes['modified']:
                    handle_db_changes(changes)
            else:
                # If LOCAL_DB is None, this is the first run
                print("Initial database loaded.")

            # Update the local database with the new data
            LOCAL_DB = new_db

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
            parent={"database_id": NOTION_DATABASE_ID},
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
    Route to remove (archive) an item from
    the Notion database using its page ID.
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
        # Return an error message if the
        # local database hasn't been initialized yet
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
        item = Row(properties, item_id)
        # Return a success message along with the item data
        return {"status": "success", "data": item.row}
    except Exception as e:
        # Log any exceptions that occur during item retrieval
        logging.error(f"Error retrieving item: {e}")
        # Raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["DB", "Row", "Column"]


class DB:
    """Database class to handle Notion database responses."""

    def __init__(self, db_response):
        # Store the list of results from the database query
        self.data = db_response["results"]
        # Extract the column names from the properties of the first result
        self.columns = list(self.data[0]["properties"].keys()) if self.data else []
        # Create a mapping from page_id to Row
        self.pages = {page["id"]: Row(page["properties"], page["id"]) for page in self.data}

    def get_columns(self) -> list:
        # Return the list of column names
        return self.columns

    def __getitem__(self, item):
        # Allow indexing by integer (row) or string (column)
        if isinstance(item, int):
            # Return a Row object for the given index
            page = self.data[item]
            return Row(page["properties"], page["id"])
        elif isinstance(item, str):
            # Return a Column object for the given column name
            return Column(self.data, item)

    def __iter__(self):
        # Make the DB object iterable over its rows
        for page in self.data:
            yield Row(page["properties"], page["id"])


class Row:
    """Row class to represent a row in the Notion database."""

    def __init__(self, row_props: dict, page_id: str):
        self.row = {}
        self.page_id = page_id  # Store the page ID
        # Iterate over each property in the row
        for k, v in row_props.items():
            # Handle different property types accordingly
            if v["type"] == "multi_select":
                # Extract the names of selected options
                values = [option["name"] for option in v["multi_select"]]
                self.row[k] = values
            elif v["type"] == "title":
                # Extract the plain text from the title
                self.row[k] = v["title"][0]["plain_text"] if v["title"] else ''
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

    def __eq__(self, other):
        # Check if two Row objects are equal based on their data
        if not isinstance(other, Row):
            return False
        return self.row == other.row

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
                self.column[idx] = prop["title"][0]["plain_text"] if prop["title"] else ''
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

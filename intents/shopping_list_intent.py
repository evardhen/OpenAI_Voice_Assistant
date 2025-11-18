import requests
import json
from datetime import datetime
from langchain_core.tools import tool


@tool("read_shoppinglist")
def read_shoppinglist_tool():
    """Fetches and reads today's shopping list items."""
    return process()

def get_today_date():
    """Returns today's date formatted as used in the shopping list API (e.g., 'Tue Jan 21 2025')."""
    return datetime.today().strftime("%a %b %d %Y")  # Formats date in the same way as the shopping list.

def extract_date_from_list_entry(list_entry):
    """
    Extracts only the date from a list entry.
    Handles cases where 'List' is an integer.
    Example:
      Input: "0 - Tue Jan 21 2025"  → Output: "Tue Jan 21 2025"
      Input: 0                      → Output: "" (Invalid)
    """
    if isinstance(list_entry, int):  # If 'List' is an integer, return an empty string
        return ""
    
    list_entry = str(list_entry)  # Ensure it's a string
    parts = list_entry.split(" - ")  # Splitting by " - " to remove the ID prefix
    return parts[1] if len(parts) > 1 else list_entry  # Returning only the date part

def process():
    """Fetches and reads only the shopping list items for today."""
    yolo_url = "http://130.149.154.54:3000/shopping_list"

    try:
        today_date = get_today_date()  # Get today's formatted date
        print(f"Checking shopping list for: {today_date}")  # Debugging

        response = requests.get(yolo_url)
        if response.status_code != 200:
            return f"Error: Failed to fetch shopping list. Server returned status code {response.status_code}."

        try:
            raw_data = response.content  
            json_data = json.loads(raw_data.decode('utf-8'))  
        except Exception as e:
            return f"Error: Failed to parse the server response: {str(e)}"

        shopping_list = json_data.get("data", [])
        if not shopping_list:
            return "The shopping list is empty."

        # Filter today's shopping list items
        filtered_items = [
            item for item in shopping_list if extract_date_from_list_entry(item.get("List", "")) == today_date
        ]

        if not filtered_items:
            return f"No shopping items found for {today_date}."

        # Format the response for today’s shopping list
        text_to_read = f"Here are the items for today, {today_date}:\n"
        for item in filtered_items:
            amount = item.get("Amount", "unknown amount")
            unit = item.get("Unit", "unknown unit")
            name = item.get("Name", "unknown item")
            checked = "checked" if item.get("Checked", False) else "not checked"

            text_to_read += f"  - {amount} {unit} of {name} ({checked})\n"

        return text_to_read

    except requests.exceptions.RequestException as req_err:
        return f"Error: Network issue while fetching the shopping list: {str(req_err)}"
    except Exception as e:
        return f"Error: An unexpected issue occurred while processing the shopping list: {str(e)}"

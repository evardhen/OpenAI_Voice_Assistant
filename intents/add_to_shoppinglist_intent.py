from langchain.tools import BaseTool
import requests
import os
import json
from datetime import datetime

from pydantic import Field, BaseModel
from langchain_core.tools import tool

class AddToShoppingListToolArgs(BaseModel):
    query: str = Field(
        description=(
            "Extract the inventory item details from the user's request in valid JSON format.\n"
            "Return **ONLY** a JSON object like this:\n"
            '{ "name": "Apples", "amount": 2, "unit": "pcs" }\n\n'
            "For solid items (apples, bananas, carrots), use 'pcs'.\n"
            "For liquids (milk, water), use 'ml' or 'liters'.\n"
            "For powdered items (rice, flour, sugar), use 'gr'.\n"
            "For packaged items (cheese, butter), use 'pkg'.\n"
            "Ensure the JSON response contains **NO additional text**."
        )
    )

@tool("add_items_to_shoppinglist", args_schema=AddToShoppingListToolArgs)
def add_items_to_shoppinglist_tool(query):
    """Extracts an item from user input and adds it to the shopping list."""
    return process(query)

def get_today_date():
    """Returns today's date formatted as 'Tue Jan 21 2025'."""
    return datetime.today().strftime("%a %b %d %Y")  # Matches the shopping list format.

def process(query: str):
    """Extracts item details and adds it to today's shopping list."""
    shopping_list_url = "http://130.149.154.54:3000/shopping_list"
    today_date = get_today_date()

    if not query:
        return "I couldn't understand the item details. Please try again."

    data = {
        "Name": query["name"],
        "Amount": query["amount"],
        "Unit": query["unit"],
        "Checked": False,  # Default to unchecked
        "List": f"0 - {today_date}"  # Assigning today's shopping list
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(shopping_list_url, headers=headers, json=data)

        if response.status_code == 201:
            return f" {query['amount']} {query['unit']} of {query['name']} has been added to your shopping list."
        else:
            return f" Error: Could not add item to the shopping list. Server returned status code {response.status_code}."

    except requests.exceptions.RequestException as req_err:
        return f" Network issue while adding the item to the shopping list: {str(req_err)}"
    except Exception as e:
        return f" An unexpected issue occurred while adding the item to the shopping list: {str(e)}"

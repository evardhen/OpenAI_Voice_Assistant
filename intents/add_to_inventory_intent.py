import requests
import json
from pydantic import Field, BaseModel
from langchain_core.tools import tool

class AddToInventoryToolArgs(BaseModel):
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

@tool("add_to_inventory", args_schema=AddToInventoryToolArgs)
def add_to_inventory_tool(query):
    """Extracts an item from user input and adds it to the inventory storage."""
    return process(query)

def process(query: str):
    """Extracts item details and adds them to the inventory storage."""
    inventory_url = "http://130.149.154.54:3000/storage"

    if not query:
        return "I couldn't understand the item details. Please try again."

    data = {
        "Name": query["name"],
        "Amount": query["amount"],
        "Unit": query["unit"]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(inventory_url, headers=headers, json=data)

        print(f" Request Sent: {json.dumps(data, indent=4)}")
        print(f" Response Status Code: {response.status_code}")
        print(f" Response Body: {response.text}")

        # Handling different success cases
        if response.status_code in [200, 201]:
            try:
                response_json = response.json()
                if "state" in response_json:
                    return f" {data['Amount']} {data['Unit']} of {data['Name']} has been successfully added to your inventory."
                elif "ID" in response_json:
                    return f" {data['Amount']} {data['Unit']} of {data['Name']} has been successfully added. ID: {response_json['ID']}"
                else:
                    return f" Unexpected response format: {response_json}"
            except json.JSONDecodeError:
                return f" Could not parse JSON response: {response.text}"

        else:
            return f" Error: Could not add item to inventory. Server returned status {response.status_code}."

    except requests.exceptions.RequestException as req_err:
        return f" Network issue while adding item to inventory: {str(req_err)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

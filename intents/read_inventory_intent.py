import requests
import json 
from langchain_core.tools import tool

@tool("read_inventory")
def read_inventory_tool():
    """This tool sends a GET request to a server to fetch and read inventory items."""
    return process()

def process():
    yolo_url = "http://130.149.154.54:3000/storage"
    try:
        # Sende eine GET-Anfrage an den YOLO-Server
        response = requests.get(yolo_url)
        if response.status_code != 200:
            return f"Failed to fetch inventory. Server returned status code {response.status_code}."

        # Dekodiere die Antwort und parse das JSON
        try:
            raw_data = response.content  # Rohdaten (bytes)
            json_data = json.loads(raw_data.decode('utf-8'))  # Dekodiere und parse
        except Exception as e:
            return f"Failed to parse JSON response: {str(e)}"

        # Daten extrahieren
        inventory = json_data.get("data", [])
        if not inventory:
            text_to_read = "The inventory is empty."
        else:
            text_to_read = "Here are the items in your storage:\n"
            for item in inventory:
                # Sichere Abfrage der Felder
                amount = item.get("Amount", "unknown amount")
                unit = item.get("Unit", "unknown unit")
                name = item.get("Name", "unknown item")
                category = item.get("Category", "uncategorized")
                storage_condition = item.get("StorageCondition", "unspecified condition")
                expiration_date = item.get("ExpirationDate", "unknown expiration date")

                text_to_read += (
                    f'{amount} {unit} of {name}, categorized as {category}. '
                    f'Store it in {storage_condition}. It expires on {expiration_date}.\n'
                )
        return text_to_read

    except requests.exceptions.RequestException as req_err:
        return f"Network error while fetching inventory: {str(req_err)}"
    except Exception as e:
        return f"An unexpected error occurred while processing the inventory: {str(e)}"
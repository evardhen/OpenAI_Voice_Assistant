from pydantic import Field, BaseModel
from langchain_core.tools import tool
import requests
from urllib.parse import quote_plus

BASE_URL = "http://130.149.154.54"

class AvailabilityArgs(BaseModel):
    query: str = Field(
        description=(
            "Extract ONLY the product name from the user's request.\n"
            "Return the name in english as plain text with no quotes and no extra words. Always use the singular form of the word."
        )
    )

@tool("check_product_availability", args_schema=AvailabilityArgs)
def check_product_availability_tool(query: str):
    """Use this tool when asked for the availability of a product. Returns a short status."""
    return check_availability(query)

def check_availability(name: str) -> str:
    name = name.strip()
    if not name:
        return "Missing product name."
    url = f"{BASE_URL}/api/storage/available/{quote_plus(name)}"
    try:
        r = requests.get(url, timeout=5)
    except requests.RequestException as e:
        return f"{name}: network error ({e.__class__.__name__})."
    if r.status_code == 404:
        return f"{name}: not found."
    if r.status_code >= 500:
        return f"{name}: server error {r.status_code}."
    if r.status_code != 200:
        return f"{name}: HTTP {r.status_code}."
    try:
        payload = r.json()
    except ValueError:
        t = r.text.strip().lower()
        if t in {"true", "false"}:
            return f"{name}: {'available' if t == 'true' else 'unavailable'}."
        return f"{name}: unknown response."
    if isinstance(payload, dict):
        if "success" in payload and not payload["success"]:
            return "Failed to read server storage."
        if "item" in payload and payload["item"]["is_cupboard"]:
            return f'{name}: available, {payload["item"]["amount"]} {payload["item"]["unit"]}'
        if "message" in payload or ("item" in payload and not payload["item"]["is_cupboard"]):
            return f"{name}: unavailable"
    return f"{name}: unknown availability."

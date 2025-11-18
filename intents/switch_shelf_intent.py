import requests
from langchain.tools import BaseTool
import subprocess
from pydantic import Field, BaseModel
from langchain_core.tools import tool

SHELF_MANIPULATION_PATH = "utils/shelf_manipulation.py" 

class SwitchCabinetPositionToolArgs(BaseModel):
    shelf_identifier: str = Field(
        description=" The input parameter is always in english. There are 4 cabinets in total. The available options for the input parameter are: \"one\", \"two\", \"three\", \"four\", \"left\", \"middle-left\", \"middle-right\", \"right\", where \"one\" and \"left\" refer to the same cabinet, etc."
        )

@tool("switch_cabinet_position", args_schema=SwitchCabinetPositionToolArgs)
def switch_cabinet_position_tool(shelf_identifier):
    """always use this tool when you want to open or close one of the cabinets."""
    return switch_shelf_position(shelf_identifier) + "\n\n"


def switch_shelf_position(shelf_identifier):

    # Replace with the IP address or hostname of your ESP32
    esp32_url = "http://10.42.8.215"  # Use the mDNS hostname

    # Endpoint to switch the relay
    relay_endpoint_left_shelf = "/relay_left_shelf"
    relay_endpoint_middle_left_shelf = "/relay_middle_left_shelf"
    relay_endpoint_middle_right_shelf = "/relay_middle_right_shelf"
    relay_endpoint_right_shelf = "/relay_right_shelf"

    try:
        if shelf_identifier in ["one", "left"]:
            return activate_relay(esp32_url + relay_endpoint_left_shelf, shelf_identifier)
        elif shelf_identifier in ["two", "middle-left"]:
            return activate_relay(esp32_url + relay_endpoint_middle_left_shelf, shelf_identifier)
        elif shelf_identifier in ["three", "middle-right"]:
            return activate_relay(esp32_url + relay_endpoint_middle_right_shelf, shelf_identifier)
        elif shelf_identifier in ["four", "right"]:
            return activate_relay(esp32_url + relay_endpoint_right_shelf, shelf_identifier)
        else:
            return "Unhandled error..."
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def activate_relay(url, shelf_identifier):
    response = requests.get(url)
    print(response.text)
    if response.status_code == 200:
        return f"Shelf {shelf_identifier} switched successfully"
    else:
        return f"Failed to open shelf. HTTP Status Code: {response.status_code}"

# if __name__ == "__main__":
#     subprocess.run(["python", SHELF_MANIPULATION_PATH, "open_shelf"])

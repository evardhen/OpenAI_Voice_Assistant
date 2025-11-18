from datetime import datetime
from langchain.tools import BaseTool

from pydantic import Field, BaseModel
from langchain_core.tools import tool


@tool("get_date")
def get_date_tool():
    """useful when you want to get the current date or the current weekday of the assistant Luna."""
    return get_date() + "\n\n"

def get_date():
    # Get current date and time
    current_datetime = datetime.now()
    # Extract date
    current_date = current_datetime.date()
    formatted_date = current_date.strftime("%d.%m.%Y")

    # Get the day of the week as an integer (0=Monday, 1=Tuesday, ..., 6=Sunday)
    day_of_week_int = current_date.weekday()

    # Define a list of weekday names
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Get the actual name of the day of the week
    day_of_week_name = weekday_names[day_of_week_int]

    # Print the day of the week
    return f"Today is {day_of_week_name}, the {formatted_date}."
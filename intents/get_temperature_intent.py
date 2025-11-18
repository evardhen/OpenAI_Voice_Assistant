import requests
import dotenv
import os
from datetime import datetime, timedelta
import re
from pydantic import Field, BaseModel
from langchain_core.tools import tool

class GetTemperatureToolArgs(BaseModel):
    day: str = Field(
        description=(
            "The input must be either a date, a weekday, today, tommorrow or the day after tomorrow.\n" 
            "If there is information about the weekday and a date, only use the date.\n" 
            "The date should have the format day, month, year, seperated by a dot, like \"01.01.2023\" or \"03.05\".\n" 
            "If the year or month is missing, leave an empty space for that parameter. Always pass the input in english.\n" 
            "Examples are \"monday\", \"saturday\", \"tomorrow\" or \"day after tomorrow\".\n"
        )
    )

@tool("get_temperature", args_schema=GetTemperatureToolArgs)
def get_temperature_tool(day):
    """useful when you want to get the temperature of a specified day."""
    return get_temperature(day)

def get_temperature(day):
    dotenv.load_dotenv()
    api_key = os.environ.get('OPEN_WEATHER_API')

    # Specify the city and country code (e.g., London,GB for London, United Kingdom)
    city = 'Berlin'
    country_code = 'DE'

    # Make a request to the OpenWeatherMap API forecast endpoint
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city},{country_code}&appid={api_key}'
    response = requests.get(url)

    day = day.lower()
    day = day.replace("next ", "")
    date_pattern_no_year = r'\d{2}\.\d{2}'
    dates_no_year = re.findall(date_pattern_no_year, day)
    if day == "today":
        # Get today's date
        specified_date = datetime.now().date().strftime("%Y-%m-%d")
        day_of_week = datetime.now().strftime("%A")
    elif day == "tomorrow":
        # Get tomorrow's date
        specified_date = datetime.now() + timedelta(days=1)
        day_of_week = specified_date.strftime("%A")
        specified_date = specified_date.date().strftime("%Y-%m-%d")
    elif day == "day after tomorrow":
        # Get tomorrow's date
        specified_date = datetime.now() + timedelta(days=2)
        day_of_week = specified_date.strftime("%A")
        specified_date = specified_date.date().strftime("%Y-%m-%d")
    elif day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]:
        # Calculate the date for tomorrow
        day_difference = get_day_difference(day)
        specified_date = datetime.now() + timedelta(days=day_difference)
        day_of_week = specified_date.strftime("%A")
        specified_date = specified_date.date().strftime("%Y-%m-%d")
    elif len(dates_no_year) > 0:
        # Get the current year
        current_year = datetime.now().year

        # Add the current year to the date string
        date_with_year = f"{dates_no_year[0]}.{current_year}"
        # Parse the original date string
        original_date = datetime.strptime(date_with_year, '%d.%m.%Y')
        day_of_week = original_date.strftime("%A")
        # Format it in the desired output format
        specified_date = original_date.strftime('%Y-%m-%d')
    else:
        return "The requested day is none of the next 5 days or has the wrong input format, I can only give information about the next 5 days."
    print(specified_date)
   # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        # Initialize variables to store weather information
        max_temperature = None
        description = None
        total_rain_percentage = 0
        count_entries = 0

        for entry in data['list']:
            date_time = entry['dt_txt']
            date = date_time.split()[0]  # Extract date from date_time

            # Check if the entry is for tomorrow
            if date == specified_date:
                max_temperature_kelvin = entry['main']['temp_max']  # Use 'temp_max' for max temperature
                max_temperature_celsius = max_temperature_kelvin - 273.15  # Convert to Celsius
                description = entry['weather'][0]['description']
                rain_percentage = entry.get('pop', 0) * 100  # Probability of Precipitation

                # Update max temperature if necessary
                if max_temperature is None or max_temperature_celsius > max_temperature:
                    max_temperature = max_temperature_celsius
                
                total_rain_percentage += rain_percentage
                count_entries += 1

            # Calculate average rain percentage
            if count_entries > 0:
                avg_rain_percentage = total_rain_percentage / count_entries
            else:
                avg_rain_percentage = 0

        # Generate the descriptive sentence
        if max_temperature is not None and description is not None:
            weather_description = f"On {day_of_week} it will be maximum {max_temperature:.2f} degrees, {description}, with an average {avg_rain_percentage:.0f}% chance of precipitation in Berlin."
            return weather_description
        else:
            return "Unable to retrieve weather forecast from json object, maybe the date is too far ahead in the future."
    else:
        return f"Error: Unable to retrieve data. Status code {response.status_code}"
    

def get_day_difference(target_weekday):
    # Define a mapping from weekday names to their corresponding numerical values
    weekday_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    # Get the current day of the week as a numerical value (0=Monday, 1=Tuesday, ..., 6=Sunday)
    current_weekday = datetime.now().weekday()

    # Get the numerical value of the target weekday
    target_weekday = weekday_mapping.get(target_weekday.lower())

    # Calculate the difference in days
    day_difference = (target_weekday - current_weekday) % 7
    return day_difference

if __name__ == "__main__":
        day = "03.05"
        # Get the current year
        current_year = datetime.now().year

        # Add the current year to the date string
        date_with_year = f"{day}.{current_year}"
        print(date_with_year)
        # Parse the original date string
        original_date = datetime.strptime(date_with_year, '%d.%m.%Y')

        # Format it in the desired output format
        specified_date = original_date.strftime('%Y-%m-%d')
        print(specified_date)

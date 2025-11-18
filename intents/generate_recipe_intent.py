from langchain.tools import BaseTool
import requests
import os
import json

from pydantic import Field, BaseModel
from langchain_core.tools import tool


@tool("generate_recipe")
def generate_recipe_tool(query):
    """Generates a concise recipe using available inventory ingredients."""
    return generate_recipe()

def fetch_inventory():
    """Fetches all available ingredients from the storage API."""
    inventory_url = "http://130.149.154.54:3000/storage"
    
    try:
        response = requests.get(inventory_url)
        if response.status_code != 200:
            return None

        inventory_data = response.json().get("data", [])
        return inventory_data

    except Exception as e:
        print(f"Error fetching inventory: {str(e)}")
        return None

def generate_recipe():
    """Generates a shorter, more concise recipe based on available ingredients."""
    inventory = fetch_inventory()
    if inventory is None:
        return "I couldn't access the inventory. Please try again later."

    if not inventory:
        return "Your inventory is empty. Please add some ingredients."

    # Extract ingredient names from inventory
    ingredient_names = [item["Name"] for item in inventory]
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # **GPT-Prompt for concise recipe generation**
    prompt = (
        f"Create a SHORT and SIMPLE recipe using the following ingredients: {', '.join(ingredient_names)}.\n"
        "Limit it to: \n"
        "- A short title\n"
        "- A brief ingredient list\n"
        "- At most 3-5 short steps for preparation.\n"
        "Make it very easy to follow in one go."
    )

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "Generate a SHORT and SIMPLE recipe including a title, a brief ingredient list, and only 3-5 short preparation steps. Ensure it's easy to read in one go. You don't need to use all of the ingredients when the user asks for a dessert, then generate a dessert recipe. When the user wants vegeterian use no meat but if it is not the case you can use meat. For the vegan don't use animal products. If nothing specified for the recipe you can generate something random."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,  # Reduce max length for shorter response
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            return f"Error: Failed to generate recipe. Server returned status code {response.status_code}."

        result = response.json()
        #recipe_text = result["choices"][0]["message"]["content"]

        return f"Here is your simple recipe:\n\n{result}"

    except Exception as e:
        return f"Error: An unexpected issue occurred while generating the recipe: {str(e)}"

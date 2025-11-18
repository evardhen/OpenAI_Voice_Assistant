from pydantic import Field, BaseModel
from langchain_core.tools import tool

class ExampleToolArgs(BaseModel):
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

@tool("example_tool_name", args_schema=ExampleToolArgs)
def example_tool_name_tool(query):
    """Extracts an item from user input and adds it to the inventory storage."""
    return process(query)

def process():
   # This function impements the actual logic and returns a string containing the answer
   pass
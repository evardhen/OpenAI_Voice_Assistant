from langchain_community.utilities import GoogleSearchAPIWrapper
from pydantic import Field, BaseModel
from langchain_core.tools import tool

class GoogleSearchToolArgs(BaseModel):
    query: str = Field(
        description=("The google search query.")
    )

@tool("google_search", args_schema=GoogleSearchToolArgs)
def google_search_tool(query):
    """Useful for when you need to answer questions about current events, people, locations or historic events. Searches Google and returns the first two results. The function output needs further text summarization."""
    search = GoogleSearchAPIWrapper(k=2)
    return search.run(query)

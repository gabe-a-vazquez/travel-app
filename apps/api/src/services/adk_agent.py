import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search

root_env = Path(__file__).parents[4] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

travel_agent = Agent(
    name="travel_assistant",
    model="gemini-2.5-flash",
    instruction="""You are a helpful travel planning assistant.
    Help users plan their trips by providing information about destinations,
    suggesting itineraries, finding attractions, and answering travel-related questions.
    Use Google Search when you need current information about destinations, hotels,
    attractions, or travel conditions.""",
    description="A travel planning assistant that helps users plan their trips and find travel information.",
    tools=[google_search],
)

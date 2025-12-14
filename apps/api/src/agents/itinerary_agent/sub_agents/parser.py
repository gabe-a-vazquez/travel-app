"""
Parser agent for itinerary enrichment workflow.

This LlmAgent parses raw itinerary text into structured day-by-day data.
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google.adk.agents import Agent
from ..tools import parse_itinerary_tool


parser_agent = Agent(
    model='gemini-2.5-flash',
    name='parser_agent',
    description='Parses raw itinerary text into structured day-by-day data',
    instruction="""You are an itinerary parsing specialist.

Your task:
1. Use parse_itinerary tool to extract structured information from the itinerary text
2. The tool returns JSON with days, locations, activities, and overnight stays
3. Your final response MUST be ONLY the JSON result from the tool, nothing else

IMPORTANT: After calling the tool, output ONLY the exact JSON result that the tool returned. Do not add any explanation or additional text.""",
    tools=[parse_itinerary_tool],
    output_key='parsed_days'
)

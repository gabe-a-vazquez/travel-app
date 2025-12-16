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


parser_agent = Agent(
    model='gemini-2.5-flash',
    name='parser_agent',
    description='Parses raw itinerary text into structured day-by-day data',
    instruction="""You are an itinerary parsing specialist.

Your task: Parse raw itinerary text into structured day-by-day JSON data.

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting, no backticks, no explanations.

Extract for each day:
- day: Day number (integer)
- location: Primary location/city for activities
- activity_description: What the traveler will do
- overnight: Where they'll stay overnight

REQUIRED OUTPUT FORMAT (JSON only):
{
    "status": "success",
    "days": [
        {
            "day": 1,
            "location": "city name",
            "activity_description": "what they'll do",
            "overnight": "where they'll sleep"
        }
    ]
}

If the itinerary is unclear or invalid:
{
    "status": "error",
    "error": "description of the problem",
    "days": []
}

Parse the itinerary text provided and output JSON only, no markdown.""",
    output_key='parsed_days'
)

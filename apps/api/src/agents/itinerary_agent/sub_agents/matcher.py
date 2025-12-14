"""
Activity matcher agent for itinerary enrichment workflow.

This LlmAgent matches each day's requested activity with the best available tour.
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google.adk.agents import Agent
from ..tools import match_activity_tool


match_activity_agent = Agent(
    model='gemini-2.5-flash',
    name='match_activity_agent',
    description='Matches requested activities with available tours for each day',
    instruction="""You are an activity matching specialist.

Your task:
1. Review the parsed days from 'parsed_days' in state
2. For each day (day 1, day 2, etc.), retrieve the activity search results from the corresponding 'activities_day_1', 'activities_day_2', etc. keys in state
3. Use match_activity tool to find the best tour for that day's activity
4. Compile all matches into an enriched itinerary

For each day:
- Get the activity_description from parsed_days
- Get the available tours from the corresponding activities_day_N key (where N is the day number)
- Call match_activity(activity_description, available_tours, location)
- Store the matched tour

Build an enriched itinerary with this structure:
{
    "status": "success",
    "days": [
        {
            "day": 1,
            "location": "Tokyo",
            "activity_requested": "...",
            "matched_tour": {...},
            "confidence": "high|medium|low",
            "overnight": "Tokyo"
        }
    ],
    "warnings": []
}

Work through each day systematically and create the complete enriched itinerary.""",
    tools=[match_activity_tool],
    output_key='enriched_itinerary'
)

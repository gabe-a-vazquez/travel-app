"""
Root itinerary enrichment agent.

A SequentialAgent that orchestrates the multi-step workflow to enrich
a travel itinerary with matched tours and activities from Amadeus API.

Workflow:
1. parser_agent → Parse itinerary into structured days
2. location_search_agent → Dynamically create and run location search ParallelAgent
3. activity_search_agent → Dynamically create and run activity search ParallelAgent
4. match_activity_agent → Match tours to requested activities
5. format_activity_agent → Format enriched itinerary for presentation
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from .sub_agents import (
    parser_agent,
    location_search_agent,
    activity_search_agent,
    match_activity_agent,
    format_activity_agent
)


# Create the root SequentialAgent
root_agent = SequentialAgent(
    name='itinerary_agent',
    description='Enriches travel itineraries with matched tours and activities',
    sub_agents=[
        parser_agent,
        location_search_agent,
        activity_search_agent,
        match_activity_agent,
        format_activity_agent
    ]
)

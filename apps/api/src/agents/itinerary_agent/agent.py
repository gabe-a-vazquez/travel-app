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


async def run_itinerary_agent(itinerary_text: str):
    """
    Run the itinerary enrichment workflow.

    Args:
        itinerary_text: Raw itinerary in any format (table, bullets, prose)

    Returns:
        Dict with enriched itinerary from session state
    """
    # Create an InMemoryRunner to execute the agent
    runner = InMemoryRunner(agent=root_agent)

    # Use run_debug for simple testing - it handles session creation automatically
    print("\n" + "=" * 70)
    print("RUNNING ITINERARY AGENT")
    print("=" * 70)

    await runner.run_debug(
        user_messages=itinerary_text,
        verbose=True
    )

    # Access session service (it's a public attribute)
    session_service = runner.session_service
    user_id = "debug_user_id"
    session_id = "debug_session_id"

    # Get the session
    session = await session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id
    )

    if session:
        session_state = session.state
        print(f"\n=== Session State Keys: {list(session_state.keys())}")
    else:
        print("\n=== No session found!")
        session_state = {}

    # Extract results from session state
    enriched_itinerary = session_state.get('enriched_itinerary')
    formatted_output = session_state.get('formatted_itinerary')
    parsed_days = session_state.get('parsed_days')

    return {
        "status": "success" if parsed_days else "error",
        "parsed_days": parsed_days,
        "enriched_itinerary": enriched_itinerary,
        "formatted_output": formatted_output or "Enriched itinerary created successfully"
    }

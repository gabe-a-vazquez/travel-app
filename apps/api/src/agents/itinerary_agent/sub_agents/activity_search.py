"""
Activity search agent for itinerary enrichment workflow.

A self-contained agent that reads parsed days and location coordinates from state,
creates dynamic sub-agents for each day, and runs them in parallel.
"""

import sys
import os
import json

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from typing import AsyncGenerator
from google.adk.agents import ParallelAgent, Agent, BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from ..tools import search_activities_tool


class ActivitySearchAgent(BaseAgent):
    """
    Agent that dynamically creates and runs activity searches in parallel.

    Compatible with SequentialAgent interface (has name and _run_async_impl).
    """

    name: str = 'search_activity_agent'
    description: str = 'Search for tours and activities for each day in parallel'

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read parsed days and location coords from state, create activity sub-agents, and run them.

        Args:
            ctx: InvocationContext containing session and state

        Yields:
            Events from the parallel activity search agents
        """
        # Extract session from context
        session = ctx.session

        # Get parsed days from session state
        parsed_data = session.state.get('parsed_days')

        # Handle case where parsed_data might be a JSON string
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                # Early exit - invalid JSON
                return

        if not parsed_data or parsed_data.get('status') != 'success':
            # Early exit - no valid data
            return

        parsed_days = parsed_data.get('days', [])

        # Create activity search agents
        activity_agents = []

        for day in parsed_days:
            day_num = day.get('day')
            location = day.get('location')

            if not day_num or not location:
                continue

            # Look up coordinates from session state
            coords_key = f'coords_{location}'
            coords_data = session.state.get(coords_key)

            if not coords_data:
                continue

            # Handle case where coords_data might be a JSON string
            if isinstance(coords_data, str):
                try:
                    coords_data = json.loads(coords_data)
                except json.JSONDecodeError:
                    continue

            # Extract latitude/longitude
            primary_location = coords_data.get('primary_location')
            if not primary_location:
                continue

            lat = primary_location.get('latitude')
            lon = primary_location.get('longitude')

            if not lat or not lon:
                continue

            # Create agent for this day
            agent = Agent(
                model='gemini-2.5-flash',
                name=f'search_activities_day_{day_num}',
                description=f'Search activities for day {day_num} in {location}',
                instruction=f"""Search for tours and activities in {location} for day {day_num}.

Location coordinates:
- Latitude: {lat}
- Longitude: {lon}

Use the search_activities tool with these coordinates.
Use radius_km=5 for a good search area.""",
                tools=[search_activities_tool],
                output_key=f'activities_day_{day_num}'
            )
            activity_agents.append(agent)

        if not activity_agents:
            # Early exit - no agents to run
            return

        # Create and run ParallelAgent
        parallel_agent = ParallelAgent(
            name='activity_searcher',
            description=f'Search activities for {len(activity_agents)} days in parallel',
            sub_agents=activity_agents
        )

        # Run the parallel agent and yield all events
        async for event in parallel_agent.run_async(ctx):
            yield event


# Create singleton instance for use in SequentialAgent
activity_search_agent = ActivitySearchAgent()

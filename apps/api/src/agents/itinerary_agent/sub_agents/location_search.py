"""
Location search agent for itinerary enrichment workflow.

A custom agent that reads parsed days from state, creates dynamic
sub-agents for each location, and runs them in parallel.

This demonstrates a custom agent pattern where sub-agents are created
dynamically at runtime based on state values, as per ADK documentation:
https://google.github.io/adk-docs/agents/custom-agents/
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import json
from typing import AsyncGenerator
from google.adk.agents import ParallelAgent, Agent, BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from ..tools import search_location_tool


class LocationSearchAgent(BaseAgent):
    """
    Custom agent that dynamically creates and runs location searches in parallel.

    This agent demonstrates conditional orchestration by:
    1. Reading session state to determine runtime behavior
    2. Creating sub-agents dynamically based on state values
    3. Properly yielding events from sub-agents upstream

    Inherits from BaseAgent and implements _run_async_impl as per ADK spec.
    """

    # Allow arbitrary types (needed for Pydantic to work with ADK agent types)
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self):
        """
        Initialize the location search agent.

        Note: Sub-agents are created dynamically in _run_async_impl based on
        runtime state, so we pass an empty list here.
        """
        super().__init__(
            name='search_location_agent',
            description='Search for coordinates of all locations in parallel',
            sub_agents=[]  # Sub-agents created dynamically at runtime
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read parsed days from state, create location sub-agents, and run them in parallel.

        This method demonstrates the custom agent pattern:
        - Uses ctx.session.state to read shared data
        - Implements conditional logic based on state values
        - Creates sub-agents dynamically
        - Properly yields events from sub-agents

        Args:
            ctx: InvocationContext containing session and state

        Yields:
            Events from the parallel location search agents
        """
        # Access session state - the primary way to share data between agents
        session = ctx.session
        print("GABE STATE:", session.state)

        # Read from session state
        parsed_data = session.state.get('parsed_days')

        # Handle case where parsed_data might be a JSON string
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                # Invalid JSON, early exit (conditional logic)
                return

        # Unwrap the tool response if it's wrapped with 'parse_itinerary_response'
        if parsed_data and 'parse_itinerary_response' in parsed_data:
            parsed_data = parsed_data['parse_itinerary_response']

        # Conditional logic: check prerequisites before proceeding
        if not parsed_data or parsed_data.get('status') != 'success':
            # Early exit - no work to do
            return

        parsed_days = parsed_data.get('days', [])

        # Extract unique locations from state
        unique_locations = list(set(
            day['location']
            for day in parsed_days
            if 'location' in day and day['location']
        ))

        # Conditional logic: early exit if no locations found
        if not unique_locations:
            return

        # Dynamic sub-agent creation based on runtime state
        # This is a key feature of custom agents - creating agents on-the-fly
        location_agents = []
        for location in unique_locations:
            safe_name = location.lower().replace(" ", "_").replace(",", "")

            # Each location gets its own agent with a unique output_key
            # The output_key writes results to session.state for downstream agents
            agent = Agent(
                model='gemini-2.5-flash',
                name=f'search_{safe_name}',
                description=f'Search for coordinates of {location}',
                instruction=f"""Search for the coordinates of {location}.

Use the search_location tool with location_name="{location}".
Extract the primary location from results and save coordinates.""",
                tools=[search_location_tool],
                output_key=f'coords_{location}'  # Results written to session.state
            )
            location_agents.append(agent)

        # Create ParallelAgent to orchestrate sub-agents
        parallel_agent = ParallelAgent(
            name='location_searcher',
            description=f'Search {len(location_agents)} locations in parallel',
            sub_agents=location_agents
        )

        # Properly yield events from sub-agent upstream
        # This is the correct pattern per ADK documentation:
        # "async for event in sub_agent.run_async(ctx): yield event"
        async for event in parallel_agent.run_async(ctx):
            yield event


# Create singleton instance for use in parent agents
location_search_agent = LocationSearchAgent()

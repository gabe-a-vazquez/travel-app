"""
Location search agent for itinerary enrichment workflow.

A custom agent that reads parsed days from state and performs location
searches WITHOUT using an LLM. This demonstrates LLM-free orchestration
within the ADK framework - deterministic operations that don't require
reasoning can skip the LLM overhead entirely.

Pattern: Custom BaseAgent + direct tool function calls + session state management
https://google.github.io/adk-docs/agents/custom-agents/
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import json
import asyncio
import logging
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from google.genai import types
# Import the underlying Python function directly, not the FunctionTool wrapper
from ..tools.amadeus_tools import search_location

# Initialize logger for this module
logger = logging.getLogger(__name__)


class LocationSearchAgent(BaseAgent):
    """
    Custom agent that searches for location coordinates WITHOUT using an LLM.

    This agent demonstrates LLM-free orchestration within ADK by:
    1. Reading session state to determine runtime behavior
    2. Calling tool functions directly (no LLM needed for deterministic API calls)
    3. Running searches in parallel using asyncio
    4. Writing results directly to session state

    Key insight: When operations are deterministic (input → tool → output),
    skip the LLM overhead entirely and call the underlying functions directly.
    """

    # Allow arbitrary types (needed for Pydantic to work with ADK agent types)
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self):
        """Initialize the location search agent (no sub-agents needed)."""
        super().__init__(
            name='search_location_agent',
            description='Search for coordinates of all locations in parallel',
            sub_agents=[]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read parsed_days from state, search locations in parallel, write results to state.

        This demonstrates LLM-free orchestration:
        - Reads structured data from session state
        - Calls Python functions directly (no LLM inference)
        - Runs operations in parallel with asyncio
        - Writes results to session state for downstream agents

        Args:
            ctx: InvocationContext containing session and state

        Yields:
            Event: Start and completion events for web UI logging
        """
        session = ctx.session
        logger.info("=" * 70)
        logger.info("LOCATION SEARCH AGENT (LLM-FREE) INVOKED")
        logger.info("=" * 70)

        # Yield start event for web UI logging
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Starting location search for all itinerary destinations...")])
        )

        # Read from session state
        parsed_data = session.state.get('parsed_days')
        logger.debug(f"Session state: {session.state}")

        # Handle case where parsed_data might be a JSON string
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                # print("ERROR: Invalid JSON in parsed_days")
                return

        # Conditional logic: check prerequisites
        if not parsed_data or parsed_data.get('status') != 'success':
            logger.warning("No valid parsed_data in session state")
            return

        parsed_days = parsed_data.get('days', [])

        # Extract unique locations
        unique_locations = list(set(
            day['overnight']
            for day in parsed_days
            if 'overnight' in day and day['overnight']
        ))

        if not unique_locations:
            logger.error("No locations found in parsed itinerary")
            return

        logger.info(f"Found {len(unique_locations)} unique locations: {unique_locations}")

        # Define async wrapper for the synchronous search_location function
        async def search_location_async(location: str) -> tuple[str, dict]:
            """Call search_location in thread pool to avoid blocking."""
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                search_location,
                location,
                None  # country_code
            )
            return location, result

        # Run all location searches in parallel
        logger.info("Starting parallel location searches...")
        search_tasks = [search_location_async(loc) for loc in unique_locations]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Write results to session state (mimicking what output_key does)
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"Location search failed: {item}")
                continue

            location, result = item
            state_key = f'coords_{location}'
            session.state[state_key] = result
            logger.debug(f"Saved coordinates for '{location}' to state key '{state_key}'")

        logger.info(f"Location search completed: {len(results)} results")
        logger.debug(f"Final session state: {session.state}")
        logger.info("=" * 70)

        # Yield completion event for web UI logging
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(
                text=f"Location search completed: {success_count}/{len(results)} locations found"
            )])
        )


# Create singleton instance for use in parent agents
location_search_agent = LocationSearchAgent()

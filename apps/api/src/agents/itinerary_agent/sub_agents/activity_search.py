"""
Activity search agent for itinerary enrichment workflow.

A custom agent that reads parsed days and location coordinates from state,
and performs activity searches WITHOUT using an LLM. This demonstrates
LLM-free orchestration within the ADK framework - deterministic operations
that don't require reasoning can skip the LLM overhead entirely.

Pattern: Custom BaseAgent + direct tool function calls + session state management
https://google.github.io/adk-docs/agents/custom-agents/
"""

import sys
import os
import json
import re
import asyncio

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from google.genai import types
# Import the underlying Python function directly, not the FunctionTool wrapper
from ..tools.amadeus_tools import search_activities


class ActivitySearchAgent(BaseAgent):
    """
    Custom agent that searches for activities WITHOUT using an LLM.

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
        """Initialize the activity search agent (no sub-agents needed)."""
        super().__init__(
            name='search_activity_agent',
            description='Search for tours and activities for each day in parallel (LLM-free)',
            sub_agents=[]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read parsed days and coords from state, search activities in parallel, write results to state.

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
        print("\n" + "=" * 70)
        print("ACTIVITY SEARCH AGENT (LLM-FREE) INVOKED")
        print("=" * 70)
        print("Session state keys:", list(session.state.keys()))

        # Yield start event for web UI logging
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Starting activity search for all destinations...")])
        )

        # Read from session state
        parsed_data = session.state.get('parsed_days')

        # Handle case where parsed_data might be a JSON string
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse parsed_data JSON: {e}")
                return

        # Conditional logic: check prerequisites
        if not parsed_data or parsed_data.get('status') != 'success':
            print("ERROR: No valid parsed_data in session state")
            return

        parsed_days = parsed_data.get('days', [])
        print(f"Found {len(parsed_days)} parsed days")

        if not parsed_days:
            print("ERROR: No days found in parsed_data")
            return

        # Extract coordinates for each day and prepare search tasks
        search_tasks = []

        for day in parsed_days:
            day_num = day.get('day')
            location = day.get('overnight')

            if not day_num or not location:
                print(f"WARNING: Skipping day - day_num={day_num}, location={location}")
                continue

            # Look up coordinates from session state
            coords_key = f'coords_{location}'
            coords_data = session.state.get(coords_key)

            if not coords_data:
                print(f"WARNING: No coordinates found for '{location}' (key: {coords_key})")
                continue

            # Extract lat/lon from coords_data
            lat, lon = self._extract_coordinates(coords_data)

            if not lat or not lon:
                print(f"WARNING: Could not extract coordinates for '{location}'")
                continue

            print(f"✓ Day {day_num}: {location} ({lat}, {lon})")
            search_tasks.append((day_num, lat, lon))

        if not search_tasks:
            print("ERROR: No valid search tasks created")
            return

        # Define async wrapper for the synchronous search_activities function
        async def search_activities_async(day_num: int, lat: float, lon: float) -> tuple[int, dict]:
            """Call search_activities in thread pool to avoid blocking."""
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                search_activities,
                lat,
                lon,
                5,  # radius_km
                20  # max_results
            )
            return day_num, result

        # Run all activity searches in parallel
        print(f"\nStarting parallel activity searches for {len(search_tasks)} days...")
        tasks = [search_activities_async(day_num, lat, lon) for day_num, lat, lon in search_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Write results to session state
        for item in results:
            if isinstance(item, Exception):
                print(f"ERROR: Activity search failed: {item}")
                continue

            day_num, result = item
            state_key = f'activities_day_{day_num}'
            session.state[state_key] = result
            print(f"✓ Saved activities for day {day_num} to state key '{state_key}'")

        print(f"Activity search completed: {len(results)} results")
        print(f"State: {session.state.keys()}")
        print("=" * 70 + "\n")

        # Yield completion event for web UI logging
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(
                text=f"Activity search completed: {success_count}/{len(results)} days processed"
            )])
        )

    def _extract_coordinates(self, coords_data: any) -> tuple[float | None, float | None]:
        """
        Extract latitude and longitude from various coordinate data formats.

        Args:
            coords_data: Coordinate data from session state (can be dict, string, etc.)

        Returns:
            Tuple of (latitude, longitude) or (None, None) if extraction fails
        """
        lat = None
        lon = None

        # Handle JSON string
        if isinstance(coords_data, str):
            try:
                coords_data = json.loads(coords_data)
            except json.JSONDecodeError:
                # Try to extract from plain text (e.g., "latitude: 35.6762, longitude: 139.6503")
                lat_match = re.search(r'latitude[:\s]+(-?[0-9]+\.?[0-9]*)', coords_data, re.IGNORECASE)
                lon_match = re.search(r'longitude[:\s]+(-?[0-9]+\.?[0-9]*)', coords_data, re.IGNORECASE)

                if lat_match and lon_match:
                    lat = float(lat_match.group(1))
                    lon = float(lon_match.group(1))
                return lat, lon

        # Extract from dict (various formats)
        if isinstance(coords_data, dict):
            # Format 1: {"primary_location": {"latitude": X, "longitude": Y}}
            if 'primary_location' in coords_data:
                primary_location = coords_data['primary_location']
                lat = primary_location.get('latitude')
                lon = primary_location.get('longitude')

            # Format 2: {"coordinate_search_result": {"coordinates": {"latitude": X, "longitude": Y}}}
            elif 'coordinate_search_result' in coords_data:
                coord_result = coords_data['coordinate_search_result']
                if 'coordinates' in coord_result:
                    coords = coord_result['coordinates']
                    lat = coords.get('latitude')
                    lon = coords.get('longitude')

            # Format 3: {"latitude": X, "longitude": Y} (direct)
            elif 'latitude' in coords_data and 'longitude' in coords_data:
                lat = coords_data.get('latitude')
                lon = coords_data.get('longitude')

        return lat, lon


# Create singleton instance for use in SequentialAgent
activity_search_agent = ActivitySearchAgent()

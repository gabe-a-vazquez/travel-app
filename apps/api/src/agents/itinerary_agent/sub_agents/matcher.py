"""
Activity matcher agent for itinerary enrichment workflow.

A custom agent that uses LLM for intelligent matching but maintains determinism
by only selecting indices and constructing results from state data.

Pattern: Hybrid approach - LLM for reasoning, state for data integrity
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from typing import AsyncGenerator, Dict, Any, List
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from google.genai import types
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env from root of monorepo
root_env = Path(__file__).parents[5] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

# Configure Gemini for index selection
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class MatcherAgent(BaseAgent):
    """
    Custom agent that matches activities using LLM intelligence with deterministic output.

    This agent demonstrates the hybrid pattern:
    1. Reading session state to get parsed days and activity results
    2. Using LLM to intelligently SELECT which activity index is best (reasoning)
    3. Constructing final results from state data (determinism - no hallucination)
    4. Running matches in parallel using asyncio

    Key insight: LLM outputs only indices/metadata, not the actual activity data.
    This ensures activity details match Amadeus API results exactly.
    """

    # Allow arbitrary types (needed for Pydantic to work with ADK agent types)
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self):
        """Initialize the matcher agent (no sub-agents needed)."""
        super().__init__(
            name='match_activity_agent',
            description='Matches requested activities with best available tours using intelligent index selection',
            sub_agents=[]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read parsed days and activities from state, match in parallel, construct enriched itinerary.

        This demonstrates hybrid LLM usage:
        - Reads structured data from session state
        - Uses LLM to select best activity index (intelligent matching)
        - Runs matching in parallel with asyncio
        - Constructs final result from state data (deterministic)

        Args:
            ctx: InvocationContext containing session and state

        Yields:
            Event: Start and completion events for web UI logging
        """
        session = ctx.session
        print("\n" + "=" * 70)
        print("MATCHER AGENT (HYBRID) INVOKED")
        print("=" * 70)
        print("Session state keys:", list(session.state.keys()))

        # Yield start event for web UI logging
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Matching activities to user requests using AI...")])
        )

        # Read parsed_days from session state
        parsed_data = session.state.get('parsed_days')

        # Handle case where parsed_data might be a JSON string
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse parsed_data JSON: {e}")
                session.state['enriched_itinerary'] = {
                    "status": "error",
                    "error": "Invalid parsed_days data"
                }
                return

        # Validate prerequisites
        if not parsed_data or parsed_data.get('status') != 'success':
            print("ERROR: No valid parsed_data in session state")
            session.state['enriched_itinerary'] = {
                "status": "error",
                "error": "No parsed itinerary data available"
            }
            return

        parsed_days = parsed_data.get('days', [])
        print(f"Found {len(parsed_days)} parsed days")

        if not parsed_days:
            print("ERROR: No days found in parsed_data")
            session.state['enriched_itinerary'] = {
                "status": "error",
                "error": "No days in parsed itinerary"
            }
            return

        # Prepare matching tasks for parallel execution
        match_tasks = []
        for day_data in parsed_days:
            day_num = day_data.get('day')
            location = day_data.get('overnight')
            activity_requested = day_data.get('activity_description')

            if not day_num:
                print(f"WARNING: Skipping day - missing day number")
                continue

            # Get activities from state
            activities_key = f'activities_day_{day_num}'
            activities_data = session.state.get(activities_key)

            if not activities_data:
                print(f"WARNING: No activities found for day {day_num} (key: {activities_key})")
                # Add task with no activities (will generate warning)
                match_tasks.append({
                    'day': day_num,
                    'location': location,
                    'activity_requested': activity_requested,
                    'overnight': day_data.get('overnight'),
                    'available_tours': []
                })
                continue

            # Parse activities if string
            if isinstance(activities_data, str):
                try:
                    activities_data = json.loads(activities_data)
                except json.JSONDecodeError:
                    print(f"WARNING: Failed to parse activities for day {day_num}")
                    continue

            # Extract tours array (amadeus_tools returns 'activities', not 'tours')
            available_tours = activities_data.get('activities', []) if isinstance(activities_data, dict) else []

            print(f"✓ Day {day_num}: {location} - {len(available_tours)} tours available")
            match_tasks.append({
                'day': day_num,
                'location': location,
                'activity_requested': activity_requested,
                'overnight': day_data.get('overnight'),
                'available_tours': available_tours
            })

        if not match_tasks:
            print("ERROR: No valid matching tasks created")
            session.state['enriched_itinerary'] = {
                "status": "error",
                "error": "No valid days to match"
            }
            return

        # Run all matches in parallel
        print(f"\nStarting parallel matching for {len(match_tasks)} days...")
        results = await asyncio.gather(
            *[self._match_day_async(task) for task in match_tasks],
            return_exceptions=True
        )

        # Construct enriched itinerary from results
        enriched_days = []
        warnings = []

        for result in results:
            if isinstance(result, Exception):
                print(f"ERROR: Matching failed: {result}")
                warnings.append(f"Matching failed: {str(result)}")
                continue

            if result.get('status') == 'no_match':
                # No tour available for this day
                enriched_days.append({
                    'day': result['day'],
                    'location': result['location'],
                    'activity_requested': result['activity_requested'],
                    'matched_tour': None,
                    'confidence': 'none',
                    'reasoning': result.get('reasoning', 'No tours available'),
                    'overnight': result['overnight']
                })
                warnings.append(f"No tours found for day {result['day']} in {result['location']}")
            elif result.get('status') == 'success':
                enriched_days.append({
                    'day': result['day'],
                    'location': result['location'],
                    'activity_requested': result['activity_requested'],
                    'matched_tour': result['matched_tour'],  # Actual data from state
                    'confidence': result['confidence'],
                    'reasoning': result['reasoning'],
                    'overnight': result['overnight']
                })

        # Build final enriched itinerary
        enriched_itinerary = {
            'status': 'success',
            'days': sorted(enriched_days, key=lambda x: x['day']),  # Ensure day order
            'warnings': warnings
        }

        # Write to session state
        session.state['enriched_itinerary'] = enriched_itinerary
        print(f"\n✓ Enriched itinerary created with {len(enriched_days)} days")
        print(f"  Warnings: {len(warnings)}")
        print("=" * 70 + "\n")

        # Yield completion event for web UI logging
        matched_count = sum(1 for d in enriched_days if d.get('matched_tour'))
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(
                text=f"Activity matching completed: {matched_count}/{len(enriched_days)} days matched successfully"
            )])
        )

    async def _match_day_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a single day's activity using LLM to select the best tour index.

        Args:
            task: Dictionary with day, location, activity_requested, available_tours

        Returns:
            Dictionary with matched result (includes actual tour data from state)
        """
        day = task['day']
        location = task['location']
        activity_requested = task['activity_requested']
        overnight = task['overnight']
        available_tours = task['available_tours']
        print(task)
        # Handle no tours case
        if not available_tours:
            return {
                'status': 'no_match',
                'day': day,
                'location': location,
                'activity_requested': activity_requested,
                'overnight': overnight,
                'reasoning': f'No tours available in {location}'
            }

        # Prepare tour summaries for LLM (minimal data to reduce tokens)
        # Use actual Amadeus API field names
        tour_summaries = []
        for i, tour in enumerate(available_tours):
            # Extract description (HTML) and strip tags for summary
            description = tour.get('description', '')
            # Simple HTML tag removal for display
            if description:
                import re
                description = re.sub(r'<[^>]+>', '', description)[:200]  # Strip HTML, truncate

            summary = {
                'index': i,
                'name': tour.get('name', 'Unnamed tour'),
                'description': description,
                'price': tour.get('price', {}).get('amount', 'N/A') if tour.get('price') else 'N/A',
                'duration': tour.get('minimumDuration', 'N/A')
            }
            tour_summaries.append(summary)

        # Create LLM prompt for index selection
        prompt = f"""You are an expert travel activity matcher. Select the best tour index.

TRAVELER REQUEST:
Desired Activity: {activity_requested}

AVAILABLE TOURS:
{json.dumps(tour_summaries, indent=2)}

TASK:
1. Analyze which tour best matches the requested activity
2. Consider: activity type, keywords in name/description, relevance
3. Assign confidence: "high" (excellent match), "medium" (good match), "low" (weak match)

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting.

OUTPUT FORMAT (required):
{{
    "selected_index": 0,
    "confidence": "high",
    "reasoning": "Brief explanation of why this tour matches"
}}

If no good match exists (all tours are completely irrelevant):
{{
    "selected_index": null,
    "confidence": "none",
    "reasoning": "Why no tours match well"
}}

Analyze and respond now. JSON only, no markdown."""

        try:
            # Create Gemini model for index selection
            model = genai.GenerativeModel("gemini-2.5-flash")

            # Call LLM to get index selection (run in thread pool)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                model.generate_content,
                prompt
            )

            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()

            selection = json.loads(result_text)

            # Handle no match
            selected_index = selection.get('selected_index')
            if selected_index is None:
                return {
                    'status': 'no_match',
                    'day': day,
                    'location': location,
                    'activity_requested': activity_requested,
                    'overnight': overnight,
                    'reasoning': selection.get('reasoning', 'No suitable match')
                }

            # Validate index
            if not isinstance(selected_index, int) or selected_index < 0 or selected_index >= len(available_tours):
                print(f"WARNING: Invalid index {selected_index} for day {day}, using first tour")
                selected_index = 0

            # DETERMINISTIC: Get actual tour data from available_tours (from state)
            # This is the EXACT object from Amadeus API - no modifications, no LLM generation
            matched_tour = available_tours[selected_index]

            # Verify we have the expected Amadeus structure
            print(f"  → Day {day}: Matched tour '{matched_tour.get('name')}' (ID: {matched_tour.get('id')})")
            print(f"     Amadeus fields present: {list(matched_tour.keys())}")

            return {
                'status': 'success',
                'day': day,
                'location': location,
                'activity_requested': activity_requested,
                'matched_tour': matched_tour,  # Exact Amadeus API data (type, id, self, name, description, geoCode, price, pictures, bookingLink, minimumDuration)
                'confidence': selection.get('confidence', 'medium'),
                'reasoning': selection.get('reasoning', ''),
                'overnight': overnight
            }

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse LLM response for day {day}: {e}")
            # Fallback: use first tour
            return {
                'status': 'success',
                'day': day,
                'location': location,
                'activity_requested': activity_requested,
                'matched_tour': available_tours[0],
                'confidence': 'low',
                'reasoning': 'Fallback selection due to parsing error',
                'overnight': overnight
            }
        except Exception as e:
            print(f"ERROR: Matching failed for day {day}: {e}")
            return {
                'status': 'no_match',
                'day': day,
                'location': location,
                'activity_requested': activity_requested,
                'overnight': overnight,
                'reasoning': f'Error during matching: {str(e)}'
            }


# Create singleton instance for use in SequentialAgent
match_activity_agent = MatcherAgent()

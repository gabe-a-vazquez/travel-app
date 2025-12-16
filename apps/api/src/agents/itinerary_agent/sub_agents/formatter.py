"""
Formatter agent for itinerary enrichment workflow.

A deterministic agent that formats the enriched itinerary into markdown
using EXACT data from Amadeus API (no LLM generation or paraphrasing).

Pattern: LLM-free formatting for data integrity
"""

import sys
import os
import json
from typing import AsyncGenerator

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from google.genai import types


class FormatterAgent(BaseAgent):
    """
    Custom agent that formats enriched itinerary WITHOUT using an LLM.

    This agent demonstrates deterministic formatting:
    1. Reading enriched_itinerary from session state
    2. Building markdown using EXACT Amadeus API data
    3. No paraphrasing, no summarizing, no hallucination

    Key insight: Formatting is a deterministic operation - no LLM needed.
    Using actual API data ensures users get accurate tour information.
    """

    # Allow arbitrary types (needed for Pydantic to work with ADK agent types)
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self):
        """Initialize the formatter agent (no sub-agents needed)."""
        super().__init__(
            name='format_activity_agent',
            description='Formats enriched itinerary into markdown using exact Amadeus data',
            sub_agents=[]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Read enriched_itinerary from state and format as markdown.

        This demonstrates deterministic formatting:
        - Reads structured data from session state
        - Builds markdown using exact Amadeus API fields
        - No LLM inference (100% accurate to source data)

        Args:
            ctx: InvocationContext containing session and state

        Yields:
            Event: Start and completion events for web UI logging
        """
        session = ctx.session
        print("\n" + "=" * 70)
        print("FORMATTER AGENT (DETERMINISTIC) INVOKED")
        print("=" * 70)

        # Yield start event for web UI logging
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Formatting enriched itinerary...")])
        )

        # Read enriched_itinerary from session state
        enriched_data = session.state.get('enriched_itinerary')

        # Handle JSON string
        if isinstance(enriched_data, str):
            try:
                enriched_data = json.loads(enriched_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse enriched_itinerary JSON: {e}")
                session.state['formatted_itinerary'] = "Error: Invalid enriched itinerary data"
                return

        # Validate data
        if not enriched_data or enriched_data.get('status') != 'success':
            print("ERROR: No valid enriched_itinerary in session state")
            session.state['formatted_itinerary'] = "Error: No enriched itinerary available"
            return

        days = enriched_data.get('days', [])
        warnings = enriched_data.get('warnings', [])

        print(f"Formatting {len(days)} days with exact Amadeus data...")

        # Build markdown using exact Amadeus API data
        markdown_parts = []
        markdown_parts.append("# Your Enriched Travel Itinerary\n")

        total_cost = 0.0
        currency = None

        # Format each day
        for day_data in days:
            day_num = day_data.get('day', '?')
            location = day_data.get('location', 'Unknown')
            activity_requested = day_data.get('activity_requested', 'No activity specified')
            matched_tour = day_data.get('matched_tour')
            confidence = day_data.get('confidence', 'unknown')
            reasoning = day_data.get('reasoning', '')
            overnight = day_data.get('overnight', location)


            markdown_parts.append(f"\n## Day {day_num}: {location}\n")
            markdown_parts.append(f"**Requested Activity:** {activity_requested}\n")
            markdown_parts.append(f"**Overnight:** {overnight}\n\n")

            if matched_tour:
                # Use EXACT Amadeus API fields - no paraphrasing!
                tour_name = matched_tour.get('name', 'Unnamed Tour')
                tour_id = matched_tour.get('id', 'N/A')
                tour_type = matched_tour.get('type', 'activity')

                # Description (HTML - strip tags for markdown)
                description = matched_tour.get('description', 'No description available')
                if description:
                    import re
                    description = re.sub(r'<[^>]+>', '', description)  # Strip HTML tags

                # Price
                price_data = matched_tour.get('price', {})
                price_amount = price_data.get('amount', 'N/A')
                price_currency = price_data.get('currencyCode', 'USD')

                if price_amount != 'N/A':
                    try:
                        total_cost += float(price_amount)
                        if currency is None:
                            currency = price_currency
                    except (ValueError, TypeError):
                        pass

                # Duration
                duration = matched_tour.get('minimumDuration', 'Duration not specified')

                # Booking link
                booking_link = matched_tour.get('booking_link', '')

                # GeoCode
                geocode = matched_tour.get('geoCode', {})
                latitude = geocode.get('latitude', 'N/A')
                longitude = geocode.get('longitude', 'N/A')

                # Format tour details
                markdown_parts.append(f"### ✅ Matched Tour: {tour_name}\n")
                markdown_parts.append(f"**Confidence:** {confidence.upper()}\n")
                if reasoning:
                    markdown_parts.append(f"**Why this match:** {reasoning}\n\n")

                markdown_parts.append(f"**Description:**\n{description}\n\n")
                markdown_parts.append(f"**Details:**\n")
                markdown_parts.append(f"- **Tour ID:** {tour_id}\n")
                markdown_parts.append(f"- **Type:** {tour_type}\n")
                markdown_parts.append(f"- **Duration:** {duration}\n")
                markdown_parts.append(f"- **Price:** {price_amount} {price_currency}\n")
                markdown_parts.append(f"- **Location:** {latitude}, {longitude}\n\n")

                if booking_link:
                    markdown_parts.append(f"**[📅 Book This Tour]({booking_link})**\n")

                # Pictures (show first 3)
                pictures = matched_tour.get('pictures', [])
                if pictures:
                    markdown_parts.append(f"\n**Photos:** ({len(pictures)} available)\n")
                    for i, pic_url in enumerate(pictures[:3]):
                        markdown_parts.append(f"![Tour photo {i+1}]({pic_url})\n")
                    if len(pictures) > 3:
                        markdown_parts.append(f"*...and {len(pictures) - 3} more photos*\n")

            else:
                # No tour matched
                markdown_parts.append(f"### ⚠️ No Tour Matched\n")
                markdown_parts.append(f"**Reason:** {reasoning}\n\n")

            markdown_parts.append("\n---\n")

        # Add summary
        markdown_parts.append("\n## Summary\n\n")
        if total_cost > 0:
            markdown_parts.append(f"**Total Estimated Cost:** {total_cost:.2f} {currency or 'USD'}\n\n")

        if warnings:
            markdown_parts.append("### ⚠️ Warnings\n\n")
            for warning in warnings:
                markdown_parts.append(f"- {warning}\n")
            markdown_parts.append("\n")

        markdown_parts.append("---\n\n")
        markdown_parts.append("*All tour data provided by Amadeus API*\n")

        # Join and write to state
        formatted_markdown = ''.join(markdown_parts)
        session.state['formatted_itinerary'] = formatted_markdown

        print(f"✓ Formatted itinerary created ({len(formatted_markdown)} characters)")
        print("\n\n\n")
        print(formatted_markdown)
        print("\n\n\n")
        print("=" * 70 + "\n")

        # Yield completion event for web UI logging
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(
                text=f"Itinerary formatted successfully ({len(days)} days, {len(formatted_markdown)} characters)"
            )])
        )


# Create singleton instance
format_activity_agent = FormatterAgent()

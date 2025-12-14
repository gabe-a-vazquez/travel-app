"""
Formatter agent for itinerary enrichment workflow.

This LlmAgent formats the enriched itinerary into a user-friendly output.
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google.adk.agents import Agent


format_activity_agent = Agent(
    model='gemini-2.5-flash',
    name='format_activity_agent',
    description='Formats the enriched itinerary into a user-friendly presentation',
    instruction="""You are an itinerary presentation specialist.

Your task:
1. Get the enriched itinerary from 'enriched_itinerary' in state
2. Format it into a beautiful, user-friendly presentation

Create output with:
- **Day-by-day breakdown** with tour names, descriptions, prices
- **Total estimated cost** summed across all matched tours
- **Booking links** for each activity
- **Warnings** for any days where matches weren't found or have low confidence
- **Helpful tips** about the itinerary

Format as clean, readable markdown with:
- Headers for each day
- Bullet points for details
- Clear pricing information
- Easy-to-click booking links

Make it engaging and helpful for trip planning!""",
    tools=[],  # No tools needed, just formatting
    output_key='formatted_itinerary'
)

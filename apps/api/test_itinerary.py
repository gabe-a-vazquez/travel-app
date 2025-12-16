#!/usr/bin/env python
"""Minimal test script for itinerary agent - run in debug mode."""
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from src.agents.itinerary_agent.agent import root_agent

async def main():
    app_name = "itinerary_agent"
    user_id = "test_user"
    session_id = "test_session"

    # Create runner
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)

    # Create session
    await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    # Run agent
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="Day 1 Arrive in Tokyo, Karaoke Clubs Day 2 Tokyo Customized Private Tour Day 3 Day Trip to Nikko National Park")]
        )
    ):
        print(f"Event: {event}")
        if event.is_final_response():
            print(f"\nFinal Response: {event.content.parts[0].text.strip()}")

if __name__ == "__main__":
    asyncio.run(main())

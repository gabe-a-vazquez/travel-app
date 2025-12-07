#!/usr/bin/env python3
"""
Startup script for Google ADK Web UI.
This script launches the ADK web interface for the travel assistant agent.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

root_env = Path(__file__).parents[2] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    print("Please set GOOGLE_API_KEY in your .env file or environment.")
    sys.exit(1)

print("Starting Google ADK Web UI...")
print("The web interface will be available at http://localhost:8001")
print("Note: ADK Web is for development and debugging only, not for production use.")
print("\nPress Ctrl+C to stop the server.\n")

os.system("/usr/local/bin/adk web src/services/adk_agent.py --port 8001")

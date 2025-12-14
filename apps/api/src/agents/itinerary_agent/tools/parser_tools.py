"""
Itinerary parsing tools using Gemini.

This module provides tools for parsing raw itinerary text
into structured day-by-day data.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from google.adk.tools import FunctionTool

# Load .env from root of monorepo
root_env = Path(__file__).parents[5] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")


def parse_itinerary(itinerary_text: str) -> Dict[str, Any]:
    """
    Parse raw itinerary text into structured day-by-day breakdown.

    Args:
        itinerary_text: Raw itinerary in any format (table, bullets, prose)

    Returns:
        Dictionary with:
        {
            "status": "success" | "error",
            "days": [
                {
                    "day": 1,
                    "location": "Tokyo",
                    "activity_description": "Arrive in Tokyo, explore Shibuya",
                    "overnight": "Tokyo"
                },
                ...
            ],
            "error": "error message if status is error"
        }
    """
    prompt = f"""You are an expert travel itinerary parser. Extract structured information from raw itinerary text.

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting, no backticks.

Extract for each day:
- day: Day number (integer)
- location: Primary location/city for activities
- activity_description: What the traveler will do
- overnight: Where they'll stay overnight

INPUT ITINERARY:
{itinerary_text}

REQUIRED OUTPUT FORMAT (JSON only):
{{
    "status": "success",
    "days": [
        {{
            "day": 1,
            "location": "city name",
            "activity_description": "what they'll do",
            "overnight": "where they'll sleep"
        }}
    ]
}}

If unclear or invalid:
{{
    "status": "error",
    "error": "description of the problem",
    "days": []
}}

Parse now. JSON only, no markdown."""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Remove markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        parsed_result = json.loads(result_text)

        if "status" not in parsed_result:
            parsed_result["status"] = "success"

        if "days" not in parsed_result:
            return {
                "status": "error",
                "error": "Parser did not return 'days' array",
                "days": []
            }

        return parsed_result

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Failed to parse response as JSON: {str(e)}",
            "days": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error parsing itinerary: {str(e)}",
            "days": []
        }


# Export as FunctionTool
parse_itinerary_tool = FunctionTool(func=parse_itinerary)

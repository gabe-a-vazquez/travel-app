"""
Activity matching tools using Gemini.

This module provides tools for matching requested activities
with available tours from Amadeus API results.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
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


def match_activity(
    activity_description: str,
    available_tours: List[Dict[str, Any]],
    location: str
) -> Dict[str, Any]:
    """
    Match a requested activity with the best available tour from search results.

    Uses Gemini to intelligently match a user's desired activity with actual tours,
    considering activity type, keywords, duration, and description similarity.

    Args:
        activity_description: What the user wants to do (e.g., "Day Trip to Nikko")
        available_tours: List of tour objects from Amadeus search results
        location: Location name for context (e.g., "Tokyo")

    Returns:
        Dictionary with:
        {
            "status": "success" | "no_match" | "error",
            "matched_tour": {...},      # Full tour object (if found)
            "confidence": "high" | "medium" | "low" | "none",
            "reasoning": "why this tour was selected"
        }
    """
    if not available_tours:
        return {
            "status": "error",
            "error": f"No tours available in {location}",
            "matched_tour": None,
            "confidence": "none",
            "reasoning": f"No tours found within search radius of {location}"
        }

    # Prepare tour summaries for the prompt
    tour_summaries = []
    for i, tour in enumerate(available_tours):
        summary = {
            "index": i,
            "name": tour.get("name", "Unnamed tour"),
            "short_description": tour.get("short_description", "")[:200],
            "price": tour.get("price"),
            "rating": tour.get("rating")
        }
        tour_summaries.append(summary)

    prompt = f"""You are an expert travel activity matcher. Find the best tour that matches what the traveler wants to do.

TRAVELER REQUEST:
Location: {location}
Desired Activity: {activity_description}

AVAILABLE TOURS:
{json.dumps(tour_summaries, indent=2)}

TASK:
1. Analyze which tour best matches the requested activity
2. Consider: activity type, keywords in name/description, location coverage
3. Assign confidence: "high" (excellent match), "medium" (good match), "low" (weak match)

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting.

REQUIRED OUTPUT FORMAT:
{{
    "status": "success",
    "matched_index": 0,
    "confidence": "high",
    "reasoning": "explanation of why this tour matches"
}}

If no good match exists:
{{
    "status": "no_match",
    "confidence": "none",
    "reasoning": "why no tours match well"
}}

Analyze and respond now. JSON only, no markdown."""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Remove markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        match_result = json.loads(result_text)

        if match_result.get("status") == "no_match":
            return {
                "status": "no_match",
                "matched_tour": None,
                "confidence": "none",
                "reasoning": match_result.get("reasoning", "No suitable tours found")
            }

        # Extract the matched tour
        matched_index = match_result.get("matched_index")
        if matched_index is None or matched_index >= len(available_tours):
            return {
                "status": "error",
                "error": "Invalid tour index returned",
                "matched_tour": None,
                "confidence": "none",
                "reasoning": ""
            }

        matched_tour = available_tours[matched_index]

        return {
            "status": "success",
            "matched_tour": matched_tour,
            "confidence": match_result.get("confidence", "medium"),
            "reasoning": match_result.get("reasoning", "")
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Failed to parse matcher response as JSON: {str(e)}",
            "matched_tour": None,
            "confidence": "none",
            "reasoning": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error matching activity: {str(e)}",
            "matched_tour": None,
            "confidence": "none",
            "reasoning": ""
        }


# Export as FunctionTool
match_activity_tool = FunctionTool(func=match_activity)

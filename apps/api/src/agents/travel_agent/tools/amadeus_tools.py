"""
Amadeus API tools for the travel agent.

These tools allow the agent to:
1. Search for locations/cities by name to get coordinates
2. Search for tours and activities at specific coordinates
"""

from typing import Optional
from google.adk.tools import FunctionTool

# Import using relative path to avoid module resolution issues with ADK
import sys
import os
# Add the src directory to the path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from services.amadeus_client import get_amadeus_service


def search_location(
    location_name: str,
    country_code: Optional[str] = None
) -> dict:
    """
    Search for a city or location by name to find its coordinates.

    Use this tool when the user mentions a location (city, neighborhood, landmark)
    and you need to find its latitude/longitude for further searches.

    Args:
        location_name: Name of the city, neighborhood, or location (e.g., "Shibuya", "Paris", "Tokyo")
        country_code: Optional 2-letter country code to narrow search (e.g., "JP" for Japan, "FR" for France)

    Returns:
        A dictionary containing:
        - List of matching cities with their coordinates (latitude, longitude)
        - City names, IATA codes, and country information

    Example:
        search_location("Shibuya", country_code="JP")
        Returns locations in Shibuya area with coordinates for Tokyo
    """
    amadeus = get_amadeus_service()
    results = amadeus.search_city(
        keyword=location_name,
        country_code=country_code,
        max_results=5
    )

    # Check for errors
    if isinstance(results, dict) and results.get('error'):
        return {
            'success': False,
            'error': results.get('message'),
            'suggestions': [
                'Try a different spelling of the location',
                'Add a country code to narrow the search',
                'Use a nearby major city name instead'
            ]
        }

    if not results:
        return {
            'success': False,
            'message': f'No locations found for "{location_name}"',
            'suggestions': [
                'Check the spelling',
                'Try a nearby major city',
                'Use a country code to help narrow the search'
            ]
        }

    return {
        'success': True,
        'count': len(results),
        'locations': results,
        'primary_location': results[0] if results else None
    }


def search_activities(
    latitude: float,
    longitude: float,
    radius_km: int = 2,
    max_results: int = 15
) -> dict:
    """
    Search for tours and activities near specific coordinates.

    Use this tool after finding a location's coordinates to discover
    things to do in that area.

    Args:
        latitude: Latitude coordinate (e.g., 35.6595 for Shibuya)
        longitude: Longitude coordinate (e.g., 139.7004 for Shibuya)
        radius_km: Search radius in kilometers (default: 2km, max: 20km)
        max_results: Maximum number of activities to return (default: 15)

    Returns:
        A dictionary containing:
        - List of tours and activities with names, descriptions, prices
        - Ratings, pictures, and booking links
        - Location coordinates for each activity

    Example:
        search_activities(latitude=35.6595, longitude=139.7004, radius_km=2)
        Returns tours and activities in the Shibuya area
    """
    amadeus = get_amadeus_service()
    results = amadeus.search_tours_and_activities(
        latitude=latitude,
        longitude=longitude,
        radius=radius_km,
        max_results=max_results
    )

    # Check for errors
    if isinstance(results, dict) and results.get('error'):
        return {
            'success': False,
            'error': results.get('message'),
            'suggestions': [
                'Try a larger search radius',
                'Search a nearby major tourist area',
                'Verify the coordinates are correct'
            ]
        }

    if not results:
        return {
            'success': False,
            'message': f'No activities found within {radius_km}km of the specified location',
            'suggestions': [
                f'Try increasing the radius (currently {radius_km}km)',
                'Search for activities in a nearby major city',
                'This location may not have many tourist activities'
            ]
        }

    return {
        'success': True,
        'count': len(results),
        'search_params': {
            'latitude': latitude,
            'longitude': longitude,
            'radius_km': radius_km
        },
        'activities': results
    }


# ADK Function Declarations for the agent
search_location_tool = FunctionTool(func=search_location)
search_activities_tool = FunctionTool(func=search_activities)

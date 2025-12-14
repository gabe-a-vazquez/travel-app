"""
Amadeus API tools for itinerary enrichment.

These tools allow agents to:
1. Search for locations/cities by name to get coordinates
2. Search for tours and activities at specific coordinates
"""

from typing import Optional
from google.adk.tools import FunctionTool
import sys
import os

# Add src directory to path
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

    Use this tool when you need to find latitude/longitude for a location.

    Args:
        location_name: Name of the city, neighborhood, or location (e.g., "Tokyo", "Paris")
        country_code: Optional 2-letter country code to narrow search (e.g., "JP", "FR")

    Returns:
        Dictionary containing matching cities with their coordinates (latitude, longitude)
    """
    amadeus = get_amadeus_service()
    results = amadeus.search_city(
        keyword=location_name,
        country_code=country_code,
        max_results=5
    )

    if isinstance(results, dict) and results.get('error'):
        return {
            'success': False,
            'error': results.get('message'),
            'suggestions': [
                'Try a different spelling',
                'Add a country code',
                'Use a nearby major city'
            ]
        }

    if not results:
        return {
            'success': False,
            'message': f'No locations found for "{location_name}"'
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
    radius_km: int = 5,
    max_results: int = 15
) -> dict:
    """
    Search for tours and activities near specific coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius_km: Search radius in kilometers (default: 5km, max: 20km)
        max_results: Maximum number of activities to return (default: 15)

    Returns:
        Dictionary containing tours and activities with names, descriptions, prices, ratings
    """
    amadeus = get_amadeus_service()
    results = amadeus.search_tours_and_activities(
        latitude=latitude,
        longitude=longitude,
        radius=radius_km,
        max_results=max_results
    )

    if isinstance(results, dict) and results.get('error'):
        return {
            'success': False,
            'error': results.get('message')
        }

    if not results:
        return {
            'success': False,
            'message': f'No activities found within {radius_km}km'
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


# Export as FunctionTools
search_location_tool = FunctionTool(func=search_location)
search_activities_tool = FunctionTool(func=search_activities)

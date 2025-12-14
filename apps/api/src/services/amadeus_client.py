"""
Amadeus API client for travel services.

This module provides a wrapper around the Amadeus SDK for:
- City/location search (to get coordinates)
- Tours and Activities search
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load environment variables from root .env file (4 levels up from this file)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
load_dotenv(env_path)


class AmadeusService:
    """Service for interacting with Amadeus APIs."""

    def __init__(self):
        """Initialize Amadeus client with API credentials."""
        api_key = os.getenv('AMADEUS_API_KEY')
        api_secret = os.getenv('AMADEUS_API_SECRET')

        if not api_key or not api_secret:
            raise ValueError(
                "AMADEUS_API_KEY and AMADEUS_API_SECRET must be set in .env file. "
                "Get credentials at https://developers.amadeus.com/"
            )

        self.client = Client(
            client_id=api_key,
            client_secret=api_secret,
            hostname='test'  # Use 'production' when ready to go live
        )

    def search_city(
        self,
        keyword: str,
        country_code: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for cities by keyword to get their coordinates.

        Args:
            keyword: City name or keyword (3-10 characters)
            country_code: Optional ISO 3166-1 alpha-2 country code (e.g., 'JP' for Japan)
            max_results: Maximum number of results to return (default: 5)

        Returns:
            List of city results with coordinates and metadata

        Example:
            results = search_city("Shibuya", country_code="JP")
            # Returns: [{'name': 'Tokyo', 'iataCode': 'TYO',
            #            'geoCode': {'latitude': 35.6895, 'longitude': 139.6917}, ...}]
        """
        try:
            params = {
                'keyword': keyword,
                'max': max_results
            }

            if country_code:
                params['countryCode'] = country_code

            response = self.client.reference_data.locations.cities.get(**params)

            # Parse and return city data
            cities = []

            # Check if response has data before iterating
            if not response.data:
                return cities

            for city in response.data:
                cities.append({
                    'name': city.get('name'),
                    'iata_code': city.get('iataCode'),
                    'country_code': city.get('address', {}).get('countryCode'),
                    'state_code': city.get('address', {}).get('stateCode'),
                    'latitude': city.get('geoCode', {}).get('latitude'),
                    'longitude': city.get('geoCode', {}).get('longitude'),
                })

            return cities

        except ResponseError as error:
            # Handle API errors gracefully
            return {
                'error': True,
                'message': f"Amadeus API error: {error.description}",
                'code': error.code
            }

    def search_tours_and_activities(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for tours and activities by coordinates.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius: Search radius in kilometers (default: 1km)
            max_results: Maximum number of results (default: 20, max: 150)

        Returns:
            List of tours and activities with details

        Example:
            activities = search_tours_and_activities(
                latitude=35.6595,
                longitude=139.7004,
                radius=2
            )
        """
        try:
            response = self.client.shopping.activities.get(
                latitude=latitude,
                longitude=longitude,
                radius=radius
            )

            # Parse and return activity data
            activities = []

            # Check if response has data before iterating
            if not response.data:
                return activities

            for activity in response.data:
                activities.append({
                    'id': activity.get('id'),
                    'name': activity.get('name'),
                    'short_description': activity.get('shortDescription'),
                    'description': activity.get('description'),
                    'rating': activity.get('rating'),
                    'pictures': activity.get('pictures', []),
                    'price': {
                        'amount': activity.get('price', {}).get('amount'),
                        'currency': activity.get('price', {}).get('currencyCode')
                    } if activity.get('price') else None,
                    'booking_link': activity.get('bookingLink'),
                    'location': {
                        'latitude': activity.get('geoCode', {}).get('latitude'),
                        'longitude': activity.get('geoCode', {}).get('longitude')
                    }
                })

            return activities

        except ResponseError as error:
            return {
                'error': True,
                'message': f"Amadeus API error: {error.description}",
                'code': error.code
            }


# Singleton instance
_amadeus_service: Optional[AmadeusService] = None


def get_amadeus_service() -> AmadeusService:
    """Get or create the Amadeus service singleton."""
    global _amadeus_service
    if _amadeus_service is None:
        _amadeus_service = AmadeusService()
    return _amadeus_service

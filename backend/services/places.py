import requests
import json
from typing import Dict, List, Optional
from flask import current_app

class PlacesService:
    """Google Places API service for restaurant autocomplete and details"""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    @classmethod
    def autocomplete(cls, query: str, session_token: str = None) -> List[Dict]:
        """
        Get autocomplete suggestions for restaurants
        
        Args:
            query: Search query
            session_token: Session token for billing (optional)
            
        Returns:
            List of place predictions
        """
        # Use GOOGLE_MAPS_API_KEY for backend API calls
        api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            # Return mock data when API key is not configured
            return cls._get_mock_autocomplete(query)
        
        params = {
            'input': query,
            'types': 'restaurant|food',
            'key': api_key,
            'language': 'de',
            'components': 'country:ch'  # Restrict to Switzerland
        }
        
        if session_token:
            params['sessiontoken'] = session_token
        
        try:
            response = requests.get(f"{cls.BASE_URL}/autocomplete/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('predictions', [])
            else:
                current_app.logger.warning(f"Places API error: {data.get('status')}")
                return []
                
        except Exception as e:
            current_app.logger.error(f"Places API request failed: {e}")
            return []
    
    @classmethod
    def get_place_details(cls, place_id: str, session_token: str = None) -> Optional[Dict]:
        """
        Get detailed information about a place
        
        Args:
            place_id: Google Place ID
            session_token: Session token for billing (optional)
            
        Returns:
            Place details or None if not found
        """
        # Use GOOGLE_MAPS_API_KEY for backend API calls
        api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            # Return mock data when API key is not configured
            return cls._get_mock_place_details(place_id)
        
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,types,website,url,price_level,address_components',
            'key': api_key,
            'language': 'de'
        }
        
        if session_token:
            params['sessiontoken'] = session_token
        
        try:
            response = requests.get(f"{cls.BASE_URL}/details/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('result')
            else:
                current_app.logger.warning(f"Places Details API error: {data.get('status')}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Places Details API request failed: {e}")
            return None
    
    @classmethod
    def _get_mock_autocomplete(cls, query: str) -> List[Dict]:
        """Return mock autocomplete data for testing"""
        mock_restaurants = [
            {
                'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
                'description': 'Restaurant Adler, Bahnhofstrasse 1, 8001 Zürich, Schweiz',
                'structured_formatting': {
                    'main_text': 'Restaurant Adler',
                    'secondary_text': 'Bahnhofstrasse 1, 8001 Zürich'
                }
            },
            {
                'place_id': 'ChIJKxjxIMCuEmsRwLwy8mK9NTE',
                'description': 'Restaurant Kronenhalle, Rämistrasse 4, 8001 Zürich, Schweiz',
                'structured_formatting': {
                    'main_text': 'Restaurant Kronenhalle',
                    'secondary_text': 'Rämistrasse 4, 8001 Zürich'
                }
            },
            {
                'place_id': 'ChIJL6wn6kOuEmsRwLwy8mK9NTE',
                'description': 'Restaurant Zeughauskeller, Bahnhofstrasse 28a, 8001 Zürich, Schweiz',
                'structured_formatting': {
                    'main_text': 'Restaurant Zeughauskeller',
                    'secondary_text': 'Bahnhofstrasse 28a, 8001 Zürich'
                }
            }
        ]
        
        # Filter by query
        filtered = [r for r in mock_restaurants if query.lower() in r['description'].lower()]
        return filtered[:5]  # Limit to 5 results
    
    @classmethod
    def _get_mock_place_details(cls, place_id: str) -> Optional[Dict]:
        """Return mock place details for testing"""
        mock_details = {
            'ChIJN1t_tDeuEmsRUsoyG83frY4': {
                'name': 'Restaurant Adler',
                'formatted_address': 'Bahnhofstrasse 1, 8001 Zürich, Schweiz',
                'geometry': {
                    'location': {
                        'lat': 47.3769,
                        'lng': 8.5417
                    }
                },
                'types': ['restaurant', 'food', 'establishment'],
                'website': 'https://www.restaurant-adler.ch',
                'url': 'https://maps.google.com/maps/place?cid=123456789',
                'price_level': 3,
                'address_components': [
                    {'long_name': '1', 'short_name': '1', 'types': ['street_number']},
                    {'long_name': 'Bahnhofstrasse', 'short_name': 'Bahnhofstrasse', 'types': ['route']},
                    {'long_name': '8001', 'short_name': '8001', 'types': ['postal_code']},
                    {'long_name': 'Zürich', 'short_name': 'Zürich', 'types': ['locality']},
                    {'long_name': 'Schweiz', 'short_name': 'CH', 'types': ['country']}
                ]
            },
            'ChIJKxjxIMCuEmsRwLwy8mK9NTE': {
                'name': 'Restaurant Kronenhalle',
                'formatted_address': 'Rämistrasse 4, 8001 Zürich, Schweiz',
                'geometry': {
                    'location': {
                        'lat': 47.3728,
                        'lng': 8.5412
                    }
                },
                'types': ['restaurant', 'food', 'establishment'],
                'website': 'https://www.kronenhalle.ch',
                'url': 'https://maps.google.com/maps/place?cid=987654321',
                'price_level': 4,
                'address_components': [
                    {'long_name': '4', 'short_name': '4', 'types': ['street_number']},
                    {'long_name': 'Rämistrasse', 'short_name': 'Rämistrasse', 'types': ['route']},
                    {'long_name': '8001', 'short_name': '8001', 'types': ['postal_code']},
                    {'long_name': 'Zürich', 'short_name': 'Zürich', 'types': ['locality']},
                    {'long_name': 'Schweiz', 'short_name': 'CH', 'types': ['country']}
                ]
            },
            'ChIJL6wn6kOuEmsRwLwy8mK9NTE': {
                'name': 'Restaurant Zeughauskeller',
                'formatted_address': 'Bahnhofstrasse 28a, 8001 Zürich, Schweiz',
                'geometry': {
                    'location': {
                        'lat': 47.3765,
                        'lng': 8.5419
                    }
                },
                'types': ['restaurant', 'food', 'establishment'],
                'website': 'https://www.zeughauskeller.ch',
                'url': 'https://maps.google.com/maps/place?cid=456789123',
                'price_level': 2,
                'address_components': [
                    {'long_name': '28a', 'short_name': '28a', 'types': ['street_number']},
                    {'long_name': 'Bahnhofstrasse', 'short_name': 'Bahnhofstrasse', 'types': ['route']},
                    {'long_name': '8001', 'short_name': '8001', 'types': ['postal_code']},
                    {'long_name': 'Zürich', 'short_name': 'Zürich', 'types': ['locality']},
                    {'long_name': 'Schweiz', 'short_name': 'CH', 'types': ['country']}
                ]
            }
        }
        
        return mock_details.get(place_id)
    
    @classmethod
    def extract_address_components(cls, address_components: List[Dict]) -> Dict:
        """Extract address components from Google Places API response"""
        components = {
            'street_number': '',
            'route': '',
            'postal_code': '',
            'locality': '',
            'country': ''
        }
        
        for component in address_components:
            types = component.get('types', [])
            if 'street_number' in types:
                components['street_number'] = component.get('long_name', '')
            elif 'route' in types:
                components['route'] = component.get('long_name', '')
            elif 'postal_code' in types:
                components['postal_code'] = component.get('long_name', '')
            elif 'locality' in types:
                components['locality'] = component.get('long_name', '')
            elif 'country' in types:
                components['country'] = component.get('long_name', '')
        
        return components

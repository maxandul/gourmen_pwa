/**
 * Google Maps API Integration for Frontend
 * Provides direct access to Google Maps APIs when frontend API key is available
 */

class GoogleMapsAPI {
    constructor() {
        this.apiKey = null;
        this.isLoaded = false;
        this.init();
    }
    
    async init() {
        await this.loadConfig();
        if (this.apiKey) {
            await this.loadGoogleMapsScript();
        }
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/events/places/config');
            const config = await response.json();
            this.apiKey = config.api_key;
        } catch (error) {
            console.warn('Could not load Google Maps API config:', error);
        }
    }
    
    async loadGoogleMapsScript() {
        if (this.isLoaded || !this.apiKey) return;
        
        return new Promise((resolve, reject) => {
            // Check if script is already loaded
            if (window.google && window.google.maps) {
                this.isLoaded = true;
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${this.apiKey}&libraries=places`;
            script.async = true;
            script.defer = true;
            
            script.onload = () => {
                this.isLoaded = true;
                resolve();
            };
            
            script.onerror = () => {
                reject(new Error('Failed to load Google Maps API'));
            };
            
            document.head.appendChild(script);
        });
    }
    
    async createAutocomplete(inputElement, options = {}) {
        if (!this.isLoaded) {
            await this.loadGoogleMapsScript();
        }
        
        if (!window.google || !window.google.maps) {
            throw new Error('Google Maps API not loaded');
        }
        
        const defaultOptions = {
            types: ['restaurant', 'food'],
            componentRestrictions: { country: 'ch' },
            language: 'de'
        };
        
        const autocomplete = new google.maps.places.Autocomplete(
            inputElement, 
            { ...defaultOptions, ...options }
        );
        
        return autocomplete;
    }
    
    async getPlaceDetails(placeId) {
        if (!this.isLoaded) {
            await this.loadGoogleMapsScript();
        }
        
        if (!window.google || !window.google.maps) {
            throw new Error('Google Maps API not loaded');
        }
        
        return new Promise((resolve, reject) => {
            const service = new google.maps.places.PlacesService(
                document.createElement('div')
            );
            
            const request = {
                placeId: placeId,
                fields: ['name', 'formatted_address', 'geometry', 'types', 'website', 'url', 'price_level', 'address_components']
            };
            
            service.getDetails(request, (place, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    resolve(place);
                } else {
                    reject(new Error(`Places API error: ${status}`));
                }
            });
        });
    }
    
    createMap(element, options = {}) {
        if (!this.isLoaded) {
            throw new Error('Google Maps API not loaded');
        }
        
        const defaultOptions = {
            zoom: 15,
            center: { lat: 47.3769, lng: 8.5417 }, // Zürich
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        
        return new google.maps.Map(element, { ...defaultOptions, ...options });
    }
    
    createMarker(map, position, options = {}) {
        if (!this.isLoaded) {
            throw new Error('Google Maps API not loaded');
        }
        
        return new google.maps.Marker({
            position: position,
            map: map,
            ...options
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.googleMapsAPI = new GoogleMapsAPI();
});

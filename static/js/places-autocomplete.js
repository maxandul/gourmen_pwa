/**
 * Google Places Autocomplete for Event Creation
 * Provides autocomplete, details, and save workflow
 */

class PlacesAutocomplete {
    constructor() {
        this.sessionToken = this.generateSessionToken();
        this.selectedPlace = null;
        this.apiKey = null;
        this.init();
    }
    
    async init() {
        await this.loadConfig();
        this.setupAutocomplete();
        this.setupEventListeners();
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/events/places/config');
            const config = await response.json();
            this.apiKey = config.api_key;
        } catch (error) {
            console.warn('Could not load Places API config:', error);
        }
    }
    
    generateSessionToken() {
        // Generate a simple session token for billing purposes
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupAutocomplete() {
        const restaurantInput = document.getElementById('restaurant');
        if (!restaurantInput) return;
        
        // Create autocomplete container
        const autocompleteContainer = document.createElement('div');
        autocompleteContainer.id = 'places-autocomplete';
        autocompleteContainer.className = 'places-autocomplete';
        restaurantInput.parentNode.insertBefore(autocompleteContainer, restaurantInput.nextSibling);
        
        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'places-loading';
        loadingIndicator.className = 'places-loading';
        loadingIndicator.innerHTML = '🔍 Suche...';
        loadingIndicator.style.display = 'none';
        autocompleteContainer.appendChild(loadingIndicator);
        
        // Add results container
        const resultsContainer = document.createElement('div');
        resultsContainer.id = 'places-results';
        resultsContainer.className = 'places-results';
        autocompleteContainer.appendChild(resultsContainer);
        
        // Add details container
        const detailsContainer = document.createElement('div');
        detailsContainer.id = 'places-details';
        detailsContainer.className = 'places-details';
        detailsContainer.style.display = 'none';
        autocompleteContainer.appendChild(detailsContainer);
    }
    
    setupEventListeners() {
        const restaurantInput = document.getElementById('restaurant');
        if (!restaurantInput) return;
        
        let debounceTimer;
        
        restaurantInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                this.hideResults();
                return;
            }
            
            debounceTimer = setTimeout(() => {
                this.searchPlaces(query);
            }, 300);
        });
        
        restaurantInput.addEventListener('focus', () => {
            const query = restaurantInput.value.trim();
            if (query.length >= 2) {
                this.searchPlaces(query);
            }
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#places-autocomplete') && !e.target.closest('#restaurant')) {
                this.hideResults();
            }
        });
    }
    
    async searchPlaces(query) {
        const loadingIndicator = document.getElementById('places-loading');
        const resultsContainer = document.getElementById('places-results');
        
        if (!loadingIndicator || !resultsContainer) return;
        
        loadingIndicator.style.display = 'block';
        resultsContainer.innerHTML = '';
        
        try {
            const response = await fetch(`/events/places/autocomplete?query=${encodeURIComponent(query)}&session_token=${this.sessionToken}`);
            const predictions = await response.json();
            
            loadingIndicator.style.display = 'none';
            this.displayResults(predictions);
            
        } catch (error) {
            console.error('Places API error:', error);
            loadingIndicator.style.display = 'none';
            this.showError('Fehler beim Laden der Vorschläge');
        }
    }
    
    displayResults(predictions) {
        const resultsContainer = document.getElementById('places-results');
        if (!resultsContainer) return;
        
        if (predictions.length === 0) {
            resultsContainer.innerHTML = '<div class="places-no-results">Keine Restaurants gefunden</div>';
            resultsContainer.style.display = 'block';
            return;
        }
        
        const resultsHtml = predictions.map(prediction => `
            <div class="places-result" data-place-id="${prediction.place_id}">
                <div class="places-result-main">${prediction.structured_formatting?.main_text || prediction.description}</div>
                <div class="places-result-secondary">${prediction.structured_formatting?.secondary_text || ''}</div>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
        resultsContainer.style.display = 'block';
        
        // Add click listeners
        resultsContainer.querySelectorAll('.places-result').forEach(result => {
            result.addEventListener('click', () => {
                this.selectPlace(result.dataset.placeId);
            });
        });
    }
    
    async selectPlace(placeId) {
        const loadingIndicator = document.getElementById('places-loading');
        const resultsContainer = document.getElementById('places-results');
        const detailsContainer = document.getElementById('places-details');
        
        if (!loadingIndicator || !resultsContainer || !detailsContainer) return;
        
        loadingIndicator.style.display = 'block';
        resultsContainer.style.display = 'none';
        
        try {
            const response = await fetch(`/events/places/details/${placeId}?session_token=${this.sessionToken}`);
            const placeDetails = await response.json();
            
            if (response.ok) {
                this.selectedPlace = placeDetails;
                this.displayPlaceDetails(placeDetails);
            } else {
                this.showError('Fehler beim Laden der Details');
            }
            
        } catch (error) {
            console.error('Places Details API error:', error);
            this.showError('Fehler beim Laden der Details');
        }
        
        loadingIndicator.style.display = 'none';
    }
    
    displayPlaceDetails(place) {
        const detailsContainer = document.getElementById('places-details');
        const restaurantInput = document.getElementById('restaurant');
        
        if (!detailsContainer || !restaurantInput) return;
        
        // Update restaurant input
        restaurantInput.value = place.name;
        
        // Create details HTML
        const priceLevel = place.price_level ? '€'.repeat(place.price_level) : 'Nicht verfügbar';
        const types = place.types ? place.types.join(', ') : '';
        
        const detailsHtml = `
            <div class="places-details-header">
                <h4>📍 ${place.name}</h4>
                <button type="button" class="places-close" onclick="placesAutocomplete.hideDetails()">✕</button>
            </div>
            <div class="places-details-content">
                <div class="places-detail-item">
                    <strong>Adresse:</strong> ${place.formatted_address}
                </div>
                <div class="places-detail-item">
                    <strong>Typ:</strong> ${types}
                </div>
                <div class="places-detail-item">
                    <strong>Preislevel:</strong> ${priceLevel}
                </div>
                ${place.website ? `
                <div class="places-detail-item">
                    <strong>Website:</strong> 
                    <a href="${place.website}" target="_blank" rel="noopener">${place.website}</a>
                </div>
                ` : ''}
                <div class="places-detail-item">
                    <strong>Google Maps:</strong> 
                    <a href="${place.url}" target="_blank" rel="noopener">Auf Google Maps anzeigen</a>
                </div>
            </div>
            <div class="places-details-actions">
                <button type="button" class="btn btn-primary" onclick="placesAutocomplete.savePlaceDetails()">
                    ✅ Details übernehmen
                </button>
                <button type="button" class="btn btn-secondary" onclick="placesAutocomplete.hideDetails()">
                    Abbrechen
                </button>
            </div>
        `;
        
        detailsContainer.innerHTML = detailsHtml;
        detailsContainer.style.display = 'block';
        
        // Populate hidden fields
        this.populateHiddenFields(place);
    }
    
    populateHiddenFields(place) {
        const fields = {
            'place_id': place.place_id || '',
            'place_name': place.name || '',
            'place_address': place.formatted_address || '',
            'place_lat': place.geometry?.location?.lat || '',
            'place_lng': place.geometry?.location?.lng || '',
            'place_types': JSON.stringify(place.types || []),
            'place_website': place.website || '',
            'place_maps_url': place.url || '',
            'place_price_level': place.price_level || ''
        };
        
        // Extract address components
        if (place.address_components) {
            const components = this.extractAddressComponents(place.address_components);
            fields['place_street_number'] = components.street_number;
            fields['place_route'] = components.route;
            fields['place_postal_code'] = components.postal_code;
            fields['place_locality'] = components.locality;
            fields['place_country'] = components.country;
        }
        
        // Set hidden field values
        Object.keys(fields).forEach(fieldName => {
            const field = document.getElementById(fieldName);
            if (field) {
                field.value = fields[fieldName];
            }
        });
    }
    
    extractAddressComponents(addressComponents) {
        const components = {
            street_number: '',
            route: '',
            postal_code: '',
            locality: '',
            country: ''
        };
        
        addressComponents.forEach(component => {
            const types = component.types || [];
            if (types.includes('street_number')) {
                components.street_number = component.long_name;
            } else if (types.includes('route')) {
                components.route = component.long_name;
            } else if (types.includes('postal_code')) {
                components.postal_code = component.long_name;
            } else if (types.includes('locality')) {
                components.locality = component.long_name;
            } else if (types.includes('country')) {
                components.country = component.long_name;
            }
        });
        
        return components;
    }
    
    savePlaceDetails() {
        if (!this.selectedPlace) return;
        
        // Auto-populate some fields
        const kuecheInput = document.getElementById('kueche');
        const websiteInput = document.getElementById('website');
        
        if (kuecheInput && this.selectedPlace.types) {
            const types = this.selectedPlace.types.filter(type => 
                !['establishment', 'point_of_interest'].includes(type)
            );
            if (types.length > 0) {
                kuecheInput.value = types.join(', ');
            }
        }
        
        if (websiteInput && this.selectedPlace.website) {
            websiteInput.value = this.selectedPlace.website;
        }
        
        this.hideDetails();
        this.showSuccess('Restaurant-Details erfolgreich übernommen!');
    }
    
    hideResults() {
        const resultsContainer = document.getElementById('places-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
    
    hideDetails() {
        const detailsContainer = document.getElementById('places-details');
        if (detailsContainer) {
            detailsContainer.style.display = 'none';
        }
    }
    
    showError(message) {
        const resultsContainer = document.getElementById('places-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="places-error">❌ ${message}</div>`;
            resultsContainer.style.display = 'block';
        }
    }
    
    showSuccess(message) {
        // Create a temporary success message
        const successDiv = document.createElement('div');
        successDiv.className = 'places-success';
        successDiv.innerHTML = `✅ ${message}`;
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    if (document.getElementById('restaurant')) {
        window.placesAutocomplete = new PlacesAutocomplete();
    }
});

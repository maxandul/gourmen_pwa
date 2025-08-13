# Google Maps API Konfiguration

Diese Anwendung unterstützt drei verschiedene Google Maps API-Schlüssel für verschiedene Zwecke:

## API-Schlüssel

### 1. GOOGLE_PLACES_API_KEY (Legacy - Optional)
- **Verwendung**: Backend API-Aufrufe (Places Autocomplete & Details)
- **Sicherheit**: Wird nur serverseitig verwendet
- **Einschränkungen**: Kann auf bestimmte IP-Adressen beschränkt werden
- **Status**: Nicht mehr benötigt, wenn GOOGLE_MAPS_API_KEY vorhanden ist

### 2. GOOGLE_MAPS_API_KEY (Backend)
- **Verwendung**: Backend API-Aufrufe (Places Autocomplete & Details)
- **Sicherheit**: Wird nur serverseitig verwendet
- **Einschränkungen**: Kann auf bestimmte IP-Adressen beschränkt werden
- **Priorität**: Hat Vorrang vor GOOGLE_PLACES_API_KEY

### 3. GOOGLE_MAPS_API_KEY_FRONTEND (Frontend)
- **Verwendung**: Direkte Frontend API-Aufrufe (Maps, Autocomplete)
- **Sicherheit**: Wird im Browser sichtbar
- **Einschränkungen**: Muss auf bestimmte Domains beschränkt werden

## Konfiguration

### 1. .env-Datei konfigurieren

```bash
# Backend API-Schlüssel (für serverseitige Aufrufe)
GOOGLE_MAPS_API_KEY=your_backend_api_key_here

# Frontend API-Schlüssel (für clientseitige Aufrufe)
GOOGLE_MAPS_API_KEY_FRONTEND=your_frontend_api_key_here

# Legacy-Schlüssel (optional, nicht mehr benötigt wenn GOOGLE_MAPS_API_KEY vorhanden)
# GOOGLE_PLACES_API_KEY=your_legacy_api_key_here
```

### 2. Google Cloud Console konfigurieren

#### Backend API-Schlüssel (GOOGLE_MAPS_API_KEY)
1. Erstellen Sie einen neuen API-Schlüssel
2. Aktivieren Sie folgende APIs:
   - Places API
   - Geocoding API
3. Beschränken Sie den Schlüssel auf:
   - **IP-Adressen**: Ihre Server-IP-Adressen
   - **APIs**: Nur die benötigten APIs

#### Frontend API-Schlüssel (GOOGLE_MAPS_API_KEY_FRONTEND)
1. Erstellen Sie einen neuen API-Schlüssel
2. Aktivieren Sie folgende APIs:
   - Maps JavaScript API
   - Places API
   - Geocoding API
3. Beschränken Sie den Schlüssel auf:
   - **HTTP-Referrer**: Ihre Domain (z.B. `https://yourdomain.com/*`)
   - **APIs**: Nur die benötigten APIs

## Verwendung im Code

### Backend (Python)
```python
from backend.services.places import PlacesService

# Autocomplete
predictions = PlacesService.autocomplete("Restaurant")

# Place Details
details = PlacesService.get_place_details("place_id")
```

### Frontend (JavaScript)
```javascript
// Direkte Google Maps API-Verwendung
const autocomplete = await googleMapsAPI.createAutocomplete(inputElement);
const placeDetails = await googleMapsAPI.getPlaceDetails(placeId);
const map = googleMapsAPI.createMap(mapElement);
```

## Sicherheitshinweise

1. **Backend-Schlüssel**: Niemals im Frontend-Code verwenden
2. **Frontend-Schlüssel**: Immer auf spezifische Domains beschränken
3. **API-Beschränkungen**: Verwenden Sie so restriktive Einschränkungen wie möglich
4. **Monitoring**: Überwachen Sie die API-Nutzung regelmäßig

## Fallback-Verhalten

1. `GOOGLE_MAPS_API_KEY` wird für Backend-Aufrufe verwendet
2. Falls nicht verfügbar, werden Mock-Daten zurückgegeben
3. Frontend-API-Schlüssel ist optional und wird nur für erweiterte Funktionen benötigt

## Kostenoptimierung

- Verwenden Sie Session-Tokens für zusammengehörige Anfragen
- Implementieren Sie Caching für häufig abgefragte Orte
- Überwachen Sie die API-Nutzung und setzen Sie Limits
- Verwenden Sie Mock-Daten für Entwicklung und Tests

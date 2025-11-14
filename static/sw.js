/**
 * Service Worker für Gourmen PWA
 * Verbesserte Offline-Funktionalität und Update-Management
 */

const CACHE_NAME = 'gourmen-v1.4.4';
const STATIC_CACHE = 'gourmen-static-v1.4.4';
const DYNAMIC_CACHE = 'gourmen-dynamic-v1.4.4';

// Assets die gecacht werden sollen (nur wirklich statische Dateien!)
// JavaScript-Dateien NICHT hier, damit Updates sofort ankommen
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/manifest.json',
    '/static/img/pwa/icon-16.png',
    '/static/img/pwa/icon-32.png',
    '/static/img/pwa/icon-96.png',
    '/static/img/pwa/icon-192.png',
    '/static/img/pwa/icon-512.png',
    '/static/img/pwa/apple-touch-icon.png',
    '/static/favicon.ico'
];

// API-Endpunkte die gecacht werden sollen
const API_CACHE = [
    '/api/events',
    '/api/members',
    '/api/ggl/stats',
    '/api/billbro/status'
];

// Install Event - Cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        (async () => {
            const cache = await caches.open(STATIC_CACHE);
            console.log('Service Worker: Caching static assets');
            
            // Cache assets mit besseren Fehlerbehandlung für Apple-Geräte
            const cachePromises = STATIC_ASSETS.map(async (url) => {
                try {
                    const response = await fetch(url, {
                        cache: 'no-cache', // Verhindert Cache-Probleme auf iOS
                        credentials: 'same-origin'
                    });
                    
                    if (response.ok) {
                        await cache.put(url, response);
                        console.log('Service Worker: Cached successfully:', url);
                    } else {
                        console.warn('Service Worker: Failed to cache (HTTP error):', url, response.status);
                    }
                } catch (e) {
                    // Schlucke Fehler einzelner Assets (z. B. 401/404), damit die Installation nicht komplett fehlschlägt
                    console.warn('Service Worker: Asset konnte nicht gecacht werden:', url, e && e.message ? e.message : e);
                }
            });
            
            await Promise.allSettled(cachePromises);
            console.log('Service Worker: Static assets caching completed');
        })()
    );
    
    // Apple Safari kompatibler skipWaiting
    event.waitUntil(
        new Promise((resolve) => {
            // Verzögerung für bessere Safari-Kompatibilität
            setTimeout(() => {
                if (self.registration.active) {
                    console.log('Service Worker: Update detected, skipping waiting...');
                    self.skipWaiting();
                } else {
                    console.log('Service Worker: First installation, activating immediately');
                    // Bei der ersten Installation sofort aktivieren
                    self.skipWaiting();
                }
                resolve();
            }, 200);
        })
    );
    
    // Notify clients about new installation
    self.clients.matchAll().then(clients => {
        clients.forEach(client => {
            client.postMessage({
                type: 'SW_INSTALLED',
                data: { 
                    version: CACHE_NAME,
                    userAgent: self.navigator?.userAgent || 'unknown'
                }
            });
        });
    });
});

// Activate Event - Clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && 
                            cacheName !== DYNAMIC_CACHE && 
                            cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            
            // Take control of all clients
            self.clients.claim()
        ])
    );
});

// Fetch Event - Network first with cache fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Ignore non-HTTP(S) schemes (e.g., chrome-extension://)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return;
    }

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(request)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
    } else if (isApiRequest(request)) {
        event.respondWith(networkFirst(request, DYNAMIC_CACHE));
    } else {
        event.respondWith(networkFirst(request, DYNAMIC_CACHE));
    }
});

// Message Event - Handle updates and other messages
self.addEventListener('message', (event) => {
    const { data } = event;
    
    if (data && data.type === 'SKIP_WAITING') {
        console.log('Service Worker: Skip waiting requested');
        self.skipWaiting();
    } else if (data && data.type === 'CHECK_UPDATE') {
        console.log('Service Worker: Update check requested');
        // Check for updates
        checkForUpdates();
    } else if (data && data.type === 'FORCE_UPDATE') {
        console.log('Service Worker: Force update requested');
        // Force immediate update
        self.skipWaiting();
    } else if (data && data.type === 'GET_STATUS') {
        console.log('Service Worker: Status requested');
        // Send status back to client
        event.ports[0].postMessage({
            type: 'SW_STATUS',
            data: {
                state: self.registration.active ? 'active' : 'inactive',
                scope: self.registration.scope,
                updateViaCache: self.registration.updateViaCache
            }
        });
    }
});

// Push Event - Handle Push Notifications
// Konsolidierter Push-Handler
// Konsolidierter Push-Handler (dedupliziert)
self.addEventListener('push', (event) => {
    try {
        if (!event.data) return;
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: data.icon || '/static/img/pwa/icon-192.png',
            badge: data.badge || '/static/img/pwa/icon-96.png',
            tag: data.tag || 'gourmen-notification',
            data: data.data || {},
            actions: data.actions || [],
            requireInteraction: data.requireInteraction ?? false,
            vibrate: data.vibrate || [200, 100, 200],
            silent: data.silent || false
        };
        event.waitUntil(self.registration.showNotification(data.title || 'Gourmen', options));
    } catch (error) {
        console.error('Service Worker: Error processing push notification:', error);
        event.waitUntil(self.registration.showNotification('Gourmen', {
            body: 'Neue Nachricht von Gourmen',
            icon: '/static/img/pwa/icon-192.png',
            badge: '/static/img/pwa/icon-96.png',
            tag: 'gourmen-fallback'
        }));
    }
});

// Notification Click Event - Handle Deep Links
// Konsolidierter Notification-Click-Handler
// Konsolidierter Notification-Click-Handler (dedupliziert)
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const data = event.notification.data || {};
    const action = event.action;
    let url = data.url || (data.event_id ? `/events/${data.event_id}` : '/');
    if (action === 'close') return;
    if ((action === 'view' || action === 'view_event') && data.event_id) {
        url = `/events/${data.event_id}`;
    }
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
            for (const client of clientList) {
                if (client.url.includes(url) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});

// Background Sync Event (für zukünftige Offline-Funktionen)
// Konsolidierter Background-Sync-Handler
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(Promise.resolve());
    }
});

// Cache First Strategy
async function cacheFirst(request, cacheName) {
    try {
        // Only handle HTTP(S)
        const reqUrl = new URL(request.url);
        if (reqUrl.protocol !== 'http:' && reqUrl.protocol !== 'https:') {
            return fetch(request);
        }
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            try {
                await cache.put(request, networkResponse.clone());
            } catch (_) {
                // Ignore caching failures for unsupported schemes
            }
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Cache First failed:', error);
        return new Response('Offline - Keine Verbindung', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain' }
        });
    }
}

// Network First Strategy
async function networkFirst(request, cacheName) {
    try {
        // Apple Safari kompatible Fetch-Optionen
        const fetchOptions = {
            cache: 'no-cache',
            credentials: 'same-origin',
            headers: {
                'Cache-Control': 'no-cache'
            }
        };
        
        const networkResponse = await fetch(request, fetchOptions);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            // Klone Response für Cache, da Safari manchmal Probleme mit bereits gelesenen Responses hat
            const responseClone = networkResponse.clone();
            try {
                await cache.put(request, responseClone);
            } catch (cacheError) {
                console.warn('Service Worker: Could not cache response:', cacheError);
            }
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        // Prüfe zuerst im Cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('Service Worker: Serving from cache:', request.url);
            return cachedResponse;
        }
        
        // Für Navigations-Requests, versuche die Startseite aus dem Cache
        if (request.mode === 'navigate') {
            const homePageResponse = await caches.match('/');
            if (homePageResponse) {
                console.log('Service Worker: Serving home page from cache for navigation request');
                return homePageResponse;
            }
        }
        
        // Fallback: Return a simple offline message
        return new Response(`
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <title>Offline - Gourmen</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="theme-color" content="#354e5e">
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        height: 100vh; 
                        margin: 0; 
                        background: linear-gradient(135deg, #354e5e, #2c3e50);
                        color: white;
                        text-align: center;
                    }
                    .offline-message {
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                        max-width: 400px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    .offline-icon { font-size: 64px; margin-bottom: 20px; }
                    h1 { margin-bottom: 16px; font-weight: 600; }
                    p { line-height: 1.6; opacity: 0.9; }
                    .retry-btn {
                        background: rgba(113, 198, 166, 0.8);
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 25px;
                        margin-top: 20px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }
                    .retry-btn:hover {
                        background: rgba(113, 198, 166, 1);
                        transform: translateY(-2px);
                    }
                </style>
            </head>
            <body>
                <div class="offline-message">
                    <div class="offline-icon">📡</div>
                    <h1>Keine Internetverbindung</h1>
                    <p>Bitte überprüfe deine Internetverbindung und versuche es erneut.</p>
                    <button class="retry-btn" onclick="window.location.reload()">Erneut versuchen</button>
                </div>
            </body>
            </html>
        `, {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache'
            }
        });
    }
}

// Check if request is for static assets
function isStaticAsset(request) {
    const url = new URL(request.url);
    return STATIC_ASSETS.includes(url.pathname) ||
           url.pathname.startsWith('/static/') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.ico');
}

// Check if request is for API
function isApiRequest(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/api/') ||
           API_CACHE.includes(url.pathname);
}

// Check for updates
async function checkForUpdates() {
    try {
        const registration = await self.registration;
        console.log('Service Worker: Checking for updates...');
        
        // Force update check
        await registration.update();
        
        // Notify clients about update check completion
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'UPDATE_CHECK_COMPLETE',
                data: { 
                    hasUpdate: !!registration.waiting,
                    version: CACHE_NAME
                }
            });
        });
        
        console.log('Service Worker: Update check completed');
    } catch (error) {
        console.log('Update check failed:', error);
        
        // Notify clients about update check failure
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'UPDATE_CHECK_FAILED',
                data: { error: error.message }
            });
        });
    }
}

// Entfernt doppelte sync-Registrierung (bereits oben konsolidiert)

async function doBackgroundSync() {
    try {
        // Sync offline data when connection is restored
        console.log('Background sync: Syncing offline data');
        
        // Get all clients
        const clients = await self.clients.matchAll();
        
        // Notify clients about sync
        clients.forEach(client => {
            client.postMessage({
                type: 'BACKGROUND_SYNC',
                data: { message: 'Offline-Daten werden synchronisiert' }
            });
        });
    } catch (error) {
        console.log('Background sync failed:', error);
    }
}

// Push Notifications (if supported)
// Entfernt: zweiter Push-Listener war doppelt

// Notification Click
// Entfernt: zweiter Notification-Click-Listener war doppelt

// Handle notification actions
// Entfernt: separate Action-Handler-Funktion, Logik ist im konsolidierten Click-Handler

// Error handling
self.addEventListener('error', (event) => {
    console.error('Service Worker Error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker Unhandled Rejection:', event.reason);
});

console.log('Service Worker: Loaded successfully');

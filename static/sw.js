/**
 * Service Worker fÃ¼r Gourmen PWA
 * Verbesserte Offline-FunktionalitÃ¤t und Update-Management
 */

const VERSION = '3.10.9';
const CACHE_NAME = `gourmen-v${VERSION}`;
const STATIC_CACHE = `gourmen-static-v${VERSION}`;
const DYNAMIC_CACHE = `gourmen-dynamic-v${VERSION}`;
// Aktive Caches dieser SW-Version - alles andere wird beim Activate gelÃ¶scht
const ACTIVE_CACHES = new Set([STATIC_CACHE, DYNAMIC_CACHE, CACHE_NAME]);

// Assets die gecacht werden sollen (nur wirklich statische Dateien!)
// JavaScript-Dateien NICHT hier, damit Updates sofort ankommen
const STATIC_ASSETS = [
    '/static/manifest.json',
    '/static/css/main-v2.6c7c933d.css',
    '/static/css/public.b273baad.css',
    '/static/favicon.6d319de4.ico',
    '/static/favicon.0c03bb1d.svg',
    '/static/img/pwa/icon-16.498c3d3b.png',
    '/static/img/pwa/icon-32.fc5d4966.png',
    '/static/img/pwa/icon-192.ee7f0987.png',
    '/static/img/pwa/icon-512.21a600c7.png',
    '/static/img/pwa/icon-192-maskable.9cc8e23a.png',
    '/static/img/pwa/icon-512-maskable.dea3b97a.png',
    '/static/img/pwa/apple-touch-icon-120.91482342.png',
    '/static/img/pwa/apple-touch-icon-152.8e3cd071.png',
    '/static/img/pwa/apple-touch-icon-167.5c73f892.png',
    '/static/img/pwa/apple-touch-icon-180.8b095258.png',
    '/static/img/pwa/badge-72.d5fcf4dc.png',
    '/static/img/pwa/badge-96.054a5b81.png',
    '/static/offline.fa95ff80.html'
];

const STATIC_ASSET_SET = new Set(STATIC_ASSETS);

// API-Endpunkte die gecacht werden sollen
const API_CACHE = [
    '/api/events',
    '/api/members',
    '/api/ggl/stats',
    '/api/billbro/status'
];

// Install Event - Cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing version', VERSION);

    // Sofort skipWaiting() aufrufen - der neue SW wartet nicht auf Tab-Schliessung.
    // Synchron im Install-Handler, damit es sicher vor 'waiting' passiert.
    self.skipWaiting();

    event.waitUntil(
        (async () => {
            const cache = await caches.open(STATIC_CACHE);
            console.log('Service Worker: Caching static assets');

            const cachePromises = STATIC_ASSETS.map(async (url) => {
                try {
                    const response = await fetch(url, {
                        cache: 'no-cache',
                        credentials: 'same-origin'
                    });

                    if (response.ok) {
                        await cache.put(url, response);
                    } else {
                        console.warn('Service Worker: Failed to cache (HTTP error):', url, response.status);
                    }
                } catch (e) {
                    console.warn('Service Worker: Asset konnte nicht gecacht werden:', url, e && e.message ? e.message : e);
                }
            });

            await Promise.allSettled(cachePromises);
            console.log('Service Worker: Static assets caching completed');
        })()
    );
});

// Activate Event - Clean up old caches + claim clients sofort
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating version', VERSION);

    event.waitUntil((async () => {
        // 1) Alle alten/fremden Caches loeschen (auch Dynamic-Caches frueherer Versionen,
        //    die potenziell veraltete HTML-Antworten enthalten koennten).
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames
                .filter((name) => !ACTIVE_CACHES.has(name))
                .map((name) => {
                    console.log('Service Worker: Deleting old cache:', name);
                    return caches.delete(name);
                })
        );

        // 2) Eigenen Dynamic-Cache fuer diese Version komplett zuruecksetzen,
        //    damit garantiert keine HTML-Reste aus der vorherigen Session uebrig sind.
        await caches.delete(DYNAMIC_CACHE);

        // 3) Navigation Preload aktivieren (falls verfuegbar) -> schnellere HTML-Antworten.
        if (self.registration.navigationPreload) {
            try {
                await self.registration.navigationPreload.enable();
            } catch (e) {
                console.warn('Service Worker: navigationPreload.enable() failed:', e);
            }
        }

        // 4) Sofort die Kontrolle uebernehmen, damit alle offenen Tabs den neuen SW
        //    benutzen. Der pwa.js-controllerchange-Listener triggert dann ein Reload.
        await self.clients.claim();

        // 5) Alle Clients informieren, dass eine neue Version aktiv ist.
        const clients = await self.clients.matchAll({ includeUncontrolled: true });
        clients.forEach((client) => {
            client.postMessage({
                type: 'SW_ACTIVATED',
                data: { version: VERSION, cache: CACHE_NAME }
            });
        });

        console.log('Service Worker: Activated and claimed all clients');
    })());
});

// Fetch Event - HTML strikt vom Netz, Static-Assets cache-first, API network-first
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return;
    }

    if (request.method !== 'GET') {
        return;
    }

    if (isNavigationRequest(request)) {
        // HTML/Navigation: NIE aus dem SW-Cache. Frisches HTML vom Server,
        // Offline-Fallback ist die offline.html aus STATIC_CACHE.
        event.respondWith(networkOnlyHtml(event));
    } else if (isStaticAsset(request)) {
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
            badge: data.badge || '/static/img/pwa/badge-96.054a5b81.png',
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
            icon: '/static/img/pwa/icon-192.ee7f0987.png',
            badge: '/static/img/pwa/badge-96.054a5b81.png',
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

// Background Sync Event (fÃ¼r zukÃ¼nftige Offline-Funktionen)
// Konsolidierter Background-Sync-Handler
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(Promise.resolve());
    }
});

// Network-Only Strategy fuer HTML/Navigation:
// - Versucht zuerst Navigation Preload Response (falls aktiv)
// - Sonst frischer fetch() mit cache: 'no-store' (umgeht Browser-HTTP-Cache)
// - Keine Cache-Schreibe -> nichts veraltet, Updates kommen sofort an
// - Offline-Fallback: offline.html aus STATIC_CACHE
async function networkOnlyHtml(event) {
    const request = event.request;
    try {
        if (event.preloadResponse) {
            const preload = await event.preloadResponse;
            if (preload) return preload;
        }

        return await fetch(request, {
            cache: 'no-store',
            credentials: 'same-origin'
        });
    } catch (error) {
        console.log('Service Worker: HTML offline -> offline.html', error && error.message);
        const offlineResponse = await caches.match('/static/offline.fa95ff80.html');
        if (offlineResponse) return offlineResponse;
        return new Response('Offline - Keine Verbindung', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
    }
}

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
            // Klone Response fÃ¼r Cache, da Safari manchmal Probleme mit bereits gelesenen Responses hat
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
        
        // PrÃ¼fe zuerst im Cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('Service Worker: Serving from cache:', request.url);
            return cachedResponse;
        }
        
        // Fallback: Return a simple offline message
        // Attempt to return the offline fallback page if cached
        const offlineResponse = await caches.match('/static/offline.fa95ff80.html');
        if (offlineResponse) {
            return offlineResponse;
        }
        // Fallback to plain text if offline page is not available
        return new Response('Offline - Keine Verbindung', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 
                'Content-Type': 'text/plain; charset=utf-8',
                'Cache-Control': 'no-cache'
            }
        });
    }
}

// Erkennt HTML-/Navigation-Requests (Page-Loads, GET text/html).
// Bewusst breit gefasst: request.mode === 'navigate' deckt Top-Level-Navigationen ab,
// der Accept-Header faengt eingebettete HTML-Fetches (z.B. via fetch()) zusaetzlich.
function isNavigationRequest(request) {
    if (request.mode === 'navigate') return true;
    const accept = request.headers.get('accept') || '';
    return accept.includes('text/html');
}

// Check if request is for static assets
function isStaticAsset(request) {
    const url = new URL(request.url);
    return STATIC_ASSET_SET.has(url.pathname);
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

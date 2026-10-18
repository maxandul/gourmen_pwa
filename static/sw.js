/**
 * Service Worker für Gourmen PWA
 * Verbesserte Offline-Funktionalität und Update-Management
 */

const VERSION = '3.16.12';
const CACHE_NAME = `gourmen-v${VERSION}`;
const STATIC_CACHE = `gourmen-static-v${VERSION}`;
// Nur bekannte eigene Cache-Familien entfernen; fremde Origin-Caches erhalten.
const APP_CACHE_NAME = /^gourmen-(?:static-|dynamic-)?v\d+\.\d+\.\d+$/;

// Assets die gecacht werden sollen (nur wirklich statische Dateien!)
// JavaScript-Dateien NICHT hier, damit Updates sofort ankommen
const STATIC_ASSETS = [
    '/static/manifest.json',
    '/static/css/main-v2.fa47ba3e.css',
    '/static/css/public.604da1b3.css',
    '/static/icons/lucide-sprite.072ce5e4.svg',
    '/static/favicon.6d319de4.ico',
    '/static/img/brand/logo-round-256.fcebdffa.webp',
    '/static/img/brand/logo-round-512.a0d83b7d.webp',
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
    '/static/offline.1fe76e29.html'
];

const STATIC_ASSET_SET = new Set(STATIC_ASSETS);

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
                        cache: 'no-store',
                        credentials: 'same-origin'
                    });

                    if (isCacheableResponse(response)) {
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
        // Alte eigene Caches entfernen, insbesondere private dynamische Altantworten.
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames
                .filter((name) => APP_CACHE_NAME.test(name) && name !== STATIC_CACHE)
                .map((name) => {
                    console.log('Service Worker: Deleting old cache:', name);
                    return caches.delete(name);
                })
        );

        // Kein Preload-Pfad mit abweichender HTTP-Cache-Semantik.
        if (self.registration.navigationPreload) {
            try {
                await self.registration.navigationPreload.disable();
            } catch (_) { /* Preload-Antworten werden ohnehin nicht verwendet. */ }
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

// Private Antworten werden weder gespeichert noch aus Alt-Caches gelesen.
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    if (!['http:', 'https:'].includes(url.protocol) || request.method !== 'GET') return;
    if (isStaticAsset(request)) {
        event.respondWith(staticResponse(event));
    } else {
        event.respondWith(networkOnly(request));
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

// Background Sync Event (für zukünftige Offline-Funktionen)
// Konsolidierter Background-Sync-Handler
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(Promise.resolve());
    }
});

// Public ist eine explizite Zulassung, private/no-store haben immer Vorrang.
function isCacheableResponse(response) {
    const directives = (response.headers.get('Cache-Control') || '')
        .toLowerCase().split(',').map(value => value.trim().split('=')[0]);
    return response.status === 200 && !response.redirected &&
        directives.includes('public') &&
        !directives.includes('private') && !directives.includes('no-store') &&
        !response.headers.has('Content-Disposition');
}

const STATIC_ASSET_EXTENSIONS = /\.(css|js|svg|png|jpe?g|webp|gif|ico|woff2?|ttf|json|map)$/i;
const FINGERPRINTED = /\.[0-9a-f]{8}\.[a-z0-9]+$/i;
function isStaticAsset(request) {
    const url = new URL(request.url);
    return url.origin === self.location.origin &&
        !request.headers.has('Authorization') && !request.headers.has('Range') &&
        [...url.searchParams.keys()].every(key => key === 'v') &&
        (STATIC_ASSET_SET.has(url.pathname) ||
         (url.pathname.startsWith('/static/') && STATIC_ASSET_EXTENSIONS.test(url.pathname)));
}

function offlineFailure(request) {
    const json = new URL(request.url).pathname.startsWith('/api/') ||
        (request.headers.get('Accept') || '').includes('application/json');
    return new Response(json ? JSON.stringify({error: 'offline', message: 'Keine Verbindung'}) :
        'Offline - Keine Verbindung', {status: 503, headers: {
            'Content-Type': json ? 'application/json' : 'text/plain; charset=utf-8',
            'Cache-Control': 'no-store'
        }});
}

async function cachedStatic(request) {
    try {
        const cache = await caches.open(STATIC_CACHE);
        const response = await cache.match(request);
        if (response && isCacheableResponse(response)) return response;
    } catch (_) { /* Cache ist optional. */ }
    return null;
}

async function fetchStatic(request) {
    const response = await fetch(request, {cache: 'no-store', credentials: 'same-origin'});
    try {
        const cache = await caches.open(STATIC_CACHE);
        if (isCacheableResponse(response)) {
            await cache.put(request, response.clone());
        } else {
            await cache.delete(request);
        }
    } catch (_) { /* Speicherfehler duerfen Online-Antworten nicht verhindern. */ }
    return response;
}

async function staticResponse(event) {
    const request = event.request;
    const url = new URL(request.url);
    const immutable = STATIC_ASSET_SET.has(url.pathname) || FINGERPRINTED.test(url.pathname);
    // Hintergrundarbeit vor dem ersten await an die Worker-Lebenszeit binden.
    const network = immutable ? null : fetchStatic(request).catch(() => null);
    if (network) event.waitUntil(network);
    const cached = await cachedStatic(request);
    if (cached) return cached;
    try {
        return (await (network || fetchStatic(request))) || offlineFailure(request);
    } catch (_) {
        return offlineFailure(request);
    }
}

async function networkOnly(request) {
    try {
        return await fetch(request, {cache: 'no-store', credentials: 'same-origin'});
    } catch (_) {
        // Kein Request/Token oder Netzwerkfehlertext in Logs.
        if (request.mode === 'navigate' || (request.headers.get('Accept') || '').includes('text/html')) {
            const offline = await cachedStatic('/static/offline.1fe76e29.html');
            if (offline) return offline;
        }
        return offlineFailure(request);
    }
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

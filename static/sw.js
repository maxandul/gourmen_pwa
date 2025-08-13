/**
 * Service Worker für Gourmen PWA
 * Verbesserte Offline-Funktionalität und Update-Management
 */

const CACHE_NAME = 'gourmen-v1.2.0';
const STATIC_CACHE = 'gourmen-static-v1.2.0';
const DYNAMIC_CACHE = 'gourmen-dynamic-v1.2.0';

// Assets die gecacht werden sollen
const STATIC_ASSETS = [
    '/',
    '/static/css/base.css',
    '/static/js/pwa.js',
    '/static/manifest.json',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png',
    '/static/img/apple-touch-icon.png',
    '/static/favicon.ico',
    '/dashboard',
    '/events',
    '/ggl',
    '/billbro'
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
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE).then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            }),
            
            // Skip waiting to activate immediately
            self.skipWaiting()
        ])
    );
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
        self.skipWaiting();
    } else if (data && data.type === 'CHECK_UPDATE') {
        // Check for updates
        checkForUpdates();
    }
});

// Cache First Strategy
async function cacheFirst(request, cacheName) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
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
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/offline');
        }
        
        return new Response('Offline - Keine Verbindung', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain' }
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
        await registration.update();
    } catch (error) {
        console.log('Update check failed:', error);
    }
}

// Background Sync (if supported)
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

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
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/img/icon-192.png',
            badge: '/static/img/icon-96.png',
            tag: 'gourmen-notification',
            data: data.data || {},
            actions: data.actions || [],
            requireInteraction: data.requireInteraction || false,
            silent: data.silent || false
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Notification Click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action) {
        // Handle notification actions
        handleNotificationAction(event.action, event.notification.data);
    } else {
        // Default action - open app
        event.waitUntil(
            self.clients.matchAll().then((clients) => {
                if (clients.length > 0) {
                    clients[0].focus();
                } else {
                    self.clients.openWindow('/');
                }
            })
        );
    }
});

// Handle notification actions
function handleNotificationAction(action, data) {
    switch (action) {
        case 'view_event':
            self.clients.openWindow(`/events/${data.eventId}`);
            break;
        case 'view_dashboard':
            self.clients.openWindow('/dashboard');
            break;
        default:
            self.clients.openWindow('/');
    }
}

// Error handling
self.addEventListener('error', (event) => {
    console.error('Service Worker Error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker Unhandled Rejection:', event.reason);
});

console.log('Service Worker: Loaded successfully');

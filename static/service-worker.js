// Service Worker für Gourmen PWA
const CACHE_NAME = 'gourmen-v2'; // Version erhöht für Update-Test
const urlsToCache = [
  '/',
  '/static/css/base.css',
  '/static/manifest.json'
];

// Install event
self.addEventListener('install', event => {
  console.log('Service Worker: Install Event');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Opened cache', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
  );
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', event => {
  console.log('Service Worker: Activate Event');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control of all pages immediately
  return self.clients.claim();
});

// Message event für Update-Checks
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('Service Worker: Skip waiting requested');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    console.log('Service Worker: Update check requested');
    // Sende Update-Info an alle Clients
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({
          type: 'UPDATE_AVAILABLE',
          version: CACHE_NAME
        });
      });
    });
  }
});

// Fetch event
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      }
    )
  );
});

// Push event - Handle incoming push notifications
self.addEventListener('push', event => {
  console.log('Push received:', event);
  
  const options = {
    body: 'Es gibt Updates von Gourmen!',
    icon: '/static/img/pwa/icon-192.png',
    badge: '/static/img/pwa/icon-192.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'open',
        title: 'Öffnen',
        icon: '/static/img/pwa/icon-192.png'
      },
      {
        action: 'close',
        title: 'Schließen'
      }
    ],
    requireInteraction: true,
    tag: 'gourmen-notification'
  };

  if (event.data) {
    try {
      const data = event.data.json();
      options.title = data.title || 'Gourmen';
      options.body = data.body || options.body;
      options.data = { ...options.data, ...data };
      
      // Special handling for BillBro notifications
      if (data.type === 'billbro_start') {
        options.body = `🍽️ BillBro gestartet für ${data.event_name}! Jetzt schätzen.`;
        options.requireInteraction = true;
        options.tag = 'billbro-start';
      } else if (data.type === 'billbro_reminder') {
        options.body = `⏰ Schätzung noch ausstehend für ${data.event_name}`;
        options.tag = 'billbro-reminder';
      } else if (data.type === 'event_reminder') {
        options.body = `📅 Event-Erinnerung: ${data.event_name} am ${data.event_date}`;
        options.tag = 'event-reminder';
      }
    } catch (e) {
      console.error('Error parsing push data:', e);
    }
  } else {
    options.title = 'Gourmen';
  }

  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const data = event.notification.data;
  let urlToOpen = '/';
  
  // Determine URL based on notification type
  if (data && data.type) {
    switch (data.type) {
      case 'billbro_start':
      case 'billbro_reminder':
        urlToOpen = `/billbro?event_id=${data.event_id}`;
        break;
      case 'event_reminder':
        urlToOpen = `/events/${data.event_id}`;
        break;
      default:
        urlToOpen = '/dashboard';
    }
  }
  
  // Handle action buttons
  if (event.action === 'close') {
    return; // Just close, don't open anything
  }
  
  // Open the app
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(urlToOpen);
            return client.focus();
          }
        }
        
        // If app is not open, open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
}); 
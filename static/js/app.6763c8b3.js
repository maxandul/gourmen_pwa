/**
 * Gourmen App JavaScript
 * Hauptfunktionalität für die Webapp
 */

// CSRF Token für AJAX requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Helper, um CSRF Token konsistent zu liefern
function getCSRFToken() {
    // Bevorzugt global gecachten Wert
    if (csrfToken) return csrfToken;
    // Fallback: erneut aus dem DOM lesen
    const meta = document.querySelector("meta[name='csrf-token']");
    return meta?.getAttribute('content') || '';
}

// Stelle sicher, dass die Funktion global verfügbar ist (PWA/installed context)
// und von anderen Skripten wie pwa.js referenziert werden kann.
window.getCSRFToken = getCSRFToken;

/** Lucide-Sprite wie in Templates (use href); Fallback = aktuell ausgelieferter Hash. */
function getLucideSpriteBaseHref() {
    const useEl = document.querySelector('use[href*=".svg#"]');
    if (useEl) {
        const href = useEl.getAttribute('href') || '';
        const hash = href.indexOf('#');
        if (hash > 0) {
            return href.slice(0, hash);
        }
    }
    return '/static/icons/lucide-sprite.7e463391.svg';
}

function lucideInlineIcon(symbolId, extraIconClasses) {
    const base = getLucideSpriteBaseHref();
    const extra = (extraIconClasses || '').trim().split(/\s+/).filter(Boolean);
    const cls = ['icon'].concat(extra).join(' ');
    return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="${base}#${symbolId}"></use></svg>`;
}

/**
 * Kurz-Hinweise (AJAX, Push): einheitlich über V2 Toast (`static/js/v2/toast.js`).
 * Läuft erst nach vollem Seitenaufbau; Toast ist dann global verfügbar.
 */
function showToast(message, type = 'info', options = {}) {
    const {
        timeout = 5000,
        persistent = false,
    } = options;
    const duration = persistent ? 0 : timeout;
    const allowed = ['success', 'error', 'warning', 'info'];
    const normalized = allowed.includes(type) ? type : 'info';

    if (typeof Toast !== 'undefined' && typeof Toast.show === 'function') {
        Toast.show(normalized, String(message ?? ''), null, { duration });
        return null;
    }

    console.warn('[app] Toast nicht verfügbar:', message);
    return null;
}

/** Legacy-Hook: früher `.top-notification`; nur noch für Fremd-HTML relevant. */
function removeTopNotification(notification) {
    if (!notification || !notification.parentNode) return;
    notification.style.animation = 'slideOutUp 0.3s ease forwards';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
            updateFlashMessagesPosition();
        }
    }, 300);
}

/**
 * Falls Flash-Bereich `position: fixed` nutzt (Legacy-CSS): unter `#top-notifications` ausrichten.
 * Im V2-Layout sind Flash-Meldungen im normalen Dokumentfluss — dann ist diese Funktion wirkungslos.
 */
function updateFlashMessagesPosition() {
    const container = document.getElementById('top-notifications');
    const flashRoot = document.querySelector('.flash-messages');
    if (!container || !flashRoot) return;
    const pos = window.getComputedStyle(flashRoot).position;
    if (pos !== 'fixed') return;

    flashRoot.style.top = `${70 + container.offsetHeight}px`;
}

function showLegacyToast(message, type = 'info') {
    console.warn('showLegacyToast ist veraltet, bitte showToast verwenden.');
    return showToast(message, type);
}

// Loading state management
function setLoadingState(button, loading) {
    if (loading) {
        button.disabled = true;
        button.setAttribute('data-original-text', button.textContent);
        button.innerHTML = '<span class="spinner"></span> ' + button.textContent;
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || button.textContent;
    }
}

// Auto-hide flash messages
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
                updateFlashMessagesPosition();
            }, 300);
        }, 5000);
    });

    updateFlashMessagesPosition();
}

// Star Rating System
function initializeStarRatings() {
    const starRatings = document.querySelectorAll('.star-rating');
    
    starRatings.forEach(rating => {
        const stars = rating.querySelectorAll('.star');
        const hiddenInput = rating.querySelector('input[type="hidden"]');
        
        // Set initial state
        if (hiddenInput.value) {
            const value = parseInt(hiddenInput.value);
            stars.forEach((star, index) => {
                if (index < value) {
                    star.classList.add('selected');
                }
            });
        }
        
        // Add click handlers
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const value = index + 1;
                hiddenInput.value = value;
                
                // Update visual state
                stars.forEach((s, i) => {
                    if (i < value) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
            });
            
            // Add hover effects
            star.addEventListener('mouseenter', () => {
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            });
            
            star.addEventListener('mouseleave', () => {
                stars.forEach(s => s.classList.remove('active'));
            });
        });
    });
}

function isLocalhostServiceWorkerDisabled() {
    const isLocalhost = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
    const forceEnableSw = (
        new URLSearchParams(window.location.search).get('pwa_sw') === '1' ||
        localStorage.getItem('PWA_SW_DEV') === '1'
    );
    return isLocalhost && !forceEnableSw;
}

/** Wenn auf localhost kein SW registriert ist (pwa.js Dev-Default), darf nicht auf `serviceWorker.ready` gewartet werden – das blockiert ohne Ende. */
function wireTechnicalPushButtonWithoutServiceWorker() {
    const enableBtn = document.getElementById('enable-push-btn');
    if (!enableBtn) {
        return;
    }
    enableBtn.addEventListener('click', () => {
        const msg = 'Auf localhost ist der Service Worker standardmäßig aus. Für Push dieselbe Seite mit ?pwa_sw=1 aufrufen oder localStorage PWA_SW_DEV auf "1" setzen, dann neu laden.';
        if (typeof Toast !== 'undefined') {
            Toast.warning('Service Worker fehlt', msg, { duration: 14000 });
        } else {
            alert(msg);
        }
    });
}

// Push Notification Management
async function initializePushNotifications() {
    console.log('🔔 Initializing push notifications...');
    
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }
    
    try {
        if (isLocalhostServiceWorkerDisabled()) {
            const existingReg = await navigator.serviceWorker.getRegistration();
            if (!existingReg) {
                console.warn('Push: Kein Service Worker auf localhost (ohne ?pwa_sw=1) – Hinweis am Einstellungen-Button');
                wireTechnicalPushButtonWithoutServiceWorker();
                return;
            }
        }

        // Warte auf Service Worker (nutzt das native ready-Promise)
        const registration = await navigator.serviceWorker.ready;
        console.log('✅ Service Worker bereit für Push-Benachrichtigungen:', registration);
        
        // Hole VAPID public key
        const vapidPublicKey = await getVAPIDPublicKey();
        if (!vapidPublicKey) {
            console.error('Could not get VAPID public key');
            return;
        }
        
        // Prüfe Subscription-Status auf dem Server
        const serverStatus = await getPushSubscriptionStatus();
        if (!serverStatus.subscribed) {
            console.log('Not subscribed to push notifications yet');
            // Button per UI vorhanden (Account-Seite). Klick-Handler jetzt registrieren.
            const enableBtn = document.getElementById('enable-push-btn');
            if (enableBtn) {
                enableBtn.addEventListener('click', async () => {
                    enableBtn.disabled = true;
                    enableBtn.innerHTML = lucideInlineIcon('loader-circle', 'icon--spin') + '<span class="btn-text">Aktiviere...</span>';
                    const ok = await subscribeToPushNotifications(registration, vapidPublicKey);
                    if (!ok) {
                        enableBtn.disabled = false;
                        enableBtn.innerHTML = lucideInlineIcon('bell') + '<span class="btn-text">Benachrichtigungen aktivieren</span>';
                    } else {
                        // Erfolg: Button ausblenden
                        enableBtn.remove();
                    }
                });
            }
        } else {
            console.log('Already subscribed to push notifications:', serverStatus);
            // Prüfe ob Browser-Subscription noch existiert
            const existingSubscription = await registration.pushManager.getSubscription();
            if (!existingSubscription) {
                console.log('Browser subscription lost, re-subscribing...');
                await subscribeToPushNotifications(registration, vapidPublicKey);
            }
            // Falls bereits subscribed, Button ausblenden
            const enableBtn = document.getElementById('enable-push-btn');
            if (enableBtn) enableBtn.remove();
        }
        
    } catch (error) {
        console.error('Error initializing push notifications:', error);
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');
        
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function getVAPIDPublicKey() {
    try {
        const response = await fetch('/api/vapid-public-key');
        if (!response.ok) {
            throw new Error(`Server hat geantwortet mit HTTP ${response.status}.`);
        }
        const data = await response.json();
        if (!data.public_key) {
            throw new Error('Kein öffentlicher Schlüssel in der Antwort.');
        }
        return data.public_key;
    } catch (error) {
        console.error('Error getting VAPID public key:', error);
        throw new Error('Öffentlicher VAPID-Schlüssel konnte nicht geladen werden. Push ist derzeit nicht möglich.');
    }
}

async function getPushSubscriptionStatus() {
    try {
        const csrf = document.querySelector("meta[name='csrf-token']")?.getAttribute('content') || '';
        const headers = csrf ? { 'X-CSRFToken': csrf } : {};
        const response = await fetch('/api/push/subscription-status', {
            headers,
            credentials: 'same-origin'
        });
        return await response.json();
    } catch (error) {
        console.error('Error getting push subscription status:', error);
        return { subscribed: false };
    }
}

async function subscribeToPushNotifications(registration, vapidPublicKey) {
    try {
        // Validiere VAPID Key
        if (!vapidPublicKey || vapidPublicKey.length < 80) {
            throw new Error('Der Server hat einen ungültigen VAPID-Schlüssel geliefert.');
        }
        
        // iOS Version Check
        const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
        if (isIOS) {
            const iOSVersionMatch = navigator.userAgent.match(/OS (\d+)_/);
            const iOSVersion = iOSVersionMatch ? parseFloat(iOSVersionMatch[1]) : 0;
            if (iOSVersion > 0 && iOSVersion < 16.4) {
                throw new Error('Push benötigt iOS 16.4 oder neuer. Bitte aktualisiere dein Gerät.');
            }
        }
        
        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            throw new Error('Zugriff auf Benachrichtigungen wurde verweigert.');
        }
        
        // Subscribe to push notifications
        let subscription;
        try {
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
            });
        } catch (subError) {
            console.error('Push subscription error:', subError);
            throw new Error(`Push-Subscription fehlgeschlagen: ${subError.message}`);
        }
        
        // Send subscription to server
        const csrf = document.querySelector("meta[name='csrf-token']")?.getAttribute('content') || '';
        const response = await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf ? { 'X-CSRFToken': csrf } : {})
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });
        
        if (!response.ok) {
            let details = '';
            try {
                const err = await response.json();
                details = err?.error || JSON.stringify(err);
            } catch (_) {}
            throw new Error(`Registrierung der Subscription fehlgeschlagen (HTTP ${response.status} ${response.statusText}) ${details}`);
        }
        
        const result = await response.json();
        console.log('Successfully subscribed to push notifications:', result);

        document.querySelectorAll('.pwa-push-standalone-alert').forEach((el) => el.remove());

        const button = document.getElementById('push-notification-btn');
        if (button) {
            button.remove();
        }
        
        showToast('Push-Benachrichtigungen aktiviert.', 'success');
        return true;
        
    } catch (error) {
        console.error('Error subscribing to push notifications:', error);
        showToast(`Fehler beim Aktivieren der Push-Benachrichtigungen: ${error.message}`, 'error');
        return false;
    }
}

/** Fuer `pwa.js` (Top-Leiste): gleicher Subscribe-Flow wie Account/Dashboard. */
window.gourmenSubscribeToPushNotifications = subscribeToPushNotifications;
window.gourmenGetVAPIDPublicKey = getVAPIDPublicKey;

function showPushNotificationButton(registration, vapidPublicKey) {
    // Prüfe ob Button bereits existiert
    if (document.getElementById('push-notification-btn')) return;
    
    // Erstelle Button für Push-Benachrichtigungen
    const button = document.createElement('button');
    button.id = 'push-notification-btn';
    button.className = 'btn btn--primary push-notification-btn';
    button.innerHTML = lucideInlineIcon('bell') + '<span class="btn-text">Push-Benachrichtigungen aktivieren</span>';
    
    button.addEventListener('click', async () => {
        button.disabled = true;
        button.innerHTML = lucideInlineIcon('loader-circle', 'icon--spin') + '<span class="btn-text">Aktiviere...</span>';
        
        const success = await subscribeToPushNotifications(registration, vapidPublicKey);
        
        if (!success) {
            button.disabled = false;
            button.innerHTML = lucideInlineIcon('bell') + '<span class="btn-text">Push-Benachrichtigungen aktivieren</span>';
        }
    });
    
    // Füge Button zur Seite hinzu (z.B. in der Account-Sektion)
    const container = document.querySelector('.page-actions') || document.querySelector('.card-actions') || document.body;
    container.appendChild(button);
}

async function testPushNotification() {
    try {
        const csrf = document.querySelector("meta[name='csrf-token']")?.getAttribute('content') || '';
        const response = await fetch('/api/push/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf ? { 'X-CSRFToken': csrf } : {})
            },
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
        } else {
            throw new Error(result.error || 'Test fehlgeschlagen');
        }
        
    } catch (error) {
        console.error('Error testing push notification:', error);
        showToast(`Push-Test fehlgeschlagen: ${error.message}`, 'error');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Gourmen App initialisiert');
    
    // Initialize flash messages
    initializeFlashMessages();
    
    // Initialize star ratings
    initializeStarRatings();
    
    // Check if user is authenticated (this will be set by the template)
    const isAuthenticated = document.body.hasAttribute('data-authenticated');
    
    if (isAuthenticated) {
        initializePushNotifications();
        // setupEventPushNotifications(); // optional
    }
});

// Event Push Notification Functions
async function setupEventPushNotifications() {
    console.log('🔔 Setting up event push notifications...');
    
    // Füge Event-spezifische Buttons hinzu
    addEventPushButtons();
}

function addEventPushButtons() {
    // Suche nach Event-Detail-Seiten und füge Push-Buttons hinzu
    const eventId = getEventIdFromUrl();
    if (eventId) {
        addReminderButtons(eventId);
    }
}

function getEventIdFromUrl() {
    // Extrahiere Event-ID aus der URL
    const path = window.location.pathname;
    const match = path.match(/\/events\/(\d+)/);
    return match ? parseInt(match[1]) : null;
}


function addReminderButtons(eventId) {
    // Prüfe ob Buttons bereits existieren
    if (document.getElementById('send-reminders-btn')) return;
    
    // Erstelle Button für Push-Erinnerungen senden
    const reminderBtn = document.createElement('button');
    reminderBtn.id = 'send-reminders-btn';
    reminderBtn.className = 'btn btn-warning';
    reminderBtn.innerHTML = '<span class="btn-icon">📢</span><span class="btn-text">Push-Erinnerungen senden</span>';
    reminderBtn.onclick = () => sendParticipationReminders(eventId);
    
    // Füge Button zur Event-Actions hinzu
    const actionsContainer = document.querySelector('.event-actions') || 
                            document.querySelector('.card-actions') || 
                            document.querySelector('.card-header') ||
                            document.querySelector('.page-actions');
    
    if (actionsContainer) {
        // Erstelle Container für Event-Push-Actions falls nicht vorhanden
        let pushActionsContainer = document.getElementById('event-push-actions');
        if (!pushActionsContainer) {
            pushActionsContainer = document.createElement('div');
            pushActionsContainer.id = 'event-push-actions';
            pushActionsContainer.className = 'event-push-actions';
            pushActionsContainer.style.cssText = 'margin-top: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #71c6a6;';
            
            const title = document.createElement('h4');
            title.textContent = '📱 Push-Benachrichtigungen';
            title.style.cssText = 'margin: 0 0 8px 0; color: #354e5e; font-size: 14px; font-weight: 600;';
            pushActionsContainer.appendChild(title);
            
            actionsContainer.appendChild(pushActionsContainer);
        }
        
        pushActionsContainer.appendChild(reminderBtn);
    }
}


async function sendParticipationReminders(eventId) {
    try {
        // Bestätigung vor dem Senden
        if (!confirm('Möchtest du wirklich Push-Erinnerungen an alle Mitglieder senden, die noch nicht geantwortet haben?')) {
            return;
        }
        
        const reminderBtn = document.getElementById('send-reminders-btn');
        setLoadingState(reminderBtn, true);
        
        const csrf = document.querySelector("meta[name='csrf-token']")?.getAttribute('content') || '';
        const response = await fetch(`/api/events/${eventId}/send-reminders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf ? { 'X-CSRFToken': csrf } : {})
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
        } else {
            throw new Error(result.message || 'Unbekannter Fehler');
        }
        
    } catch (error) {
        console.error('Error sending reminders:', error);
        showToast(`Fehler beim Senden der Push-Erinnerungen: ${error.message}`, 'error');
    } finally {
        const reminderBtn = document.getElementById('send-reminders-btn');
        setLoadingState(reminderBtn, false);
    }
}


// Export functions for global use
window.showToast = showToast;
window.removeTopNotification = removeTopNotification;
window.updateFlashMessagesPosition = updateFlashMessagesPosition;
window.setLoadingState = setLoadingState;
window.sendParticipationReminders = sendParticipationReminders;
window.testPushNotification = testPushNotification;




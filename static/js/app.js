/**
 * Gourmen App JavaScript
 * Hauptfunktionalität für die Webapp
 */

// CSRF Token für AJAX requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Toast message function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    document.body.appendChild(toast);

    // Auto-remove nach 5 Sekunden
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
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
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
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

// Push Notification Management
async function initializePushNotifications() {
    console.log('🔔 Initializing push notifications...');
    
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }
    
    try {
        // Prüfe zuerst die globale Service Worker-Referenz von PWA
        let registration = window.gourmenServiceWorker;
        
        if (!registration) {
            console.log('No service worker registration found - waiting for PWA initialization...');
            // Warte bis zu 5 Sekunden auf Service Worker
            for (let i = 0; i < 50; i++) {
                await new Promise(resolve => setTimeout(resolve, 100));
                registration = window.gourmenServiceWorker || await navigator.serviceWorker.getRegistration('/');
                if (registration) break;
            }
            if (!registration) {
                console.log('Service worker still not available after waiting');
                return;
            }
        }
        
        console.log('Using existing Service Worker for push notifications:', registration);
        
        // Stelle sicher, dass der Service Worker aktiv ist, bevor wir subscriben
        try {
            await navigator.serviceWorker.ready;
        } catch (_) {
            console.log('Service worker ready() failed or timed out');
            return;
        }
        
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
            // Zeige Button zum Aktivieren
            showPushNotificationButton(registration, vapidPublicKey);
        } else {
            console.log('Already subscribed to push notifications:', serverStatus);
            // Prüfe ob Browser-Subscription noch existiert
            const existingSubscription = await registration.pushManager.getSubscription();
            if (!existingSubscription) {
                console.log('Browser subscription lost, re-subscribing...');
                await subscribeToPushNotifications(registration, vapidPublicKey);
            }
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
        const data = await response.json();
        return data.public_key;
    } catch (error) {
        console.error('Error getting VAPID public key:', error);
        // Fallback key (should not be used in production)
        return 'BJrWx8xCvf_8kT2j3R3_7nqJ2x3kX4c2Pd4FVk1cJ5q_QH7_0LlCPT9gU8NZ_ZEt4QP8vP2N_YfXYt8aU0rN_E4';
    }
}

async function getPushSubscriptionStatus() {
    try {
        const response = await fetch('/api/push/subscription-status', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Error getting push subscription status:', error);
        return { subscribed: false };
    }
}

async function subscribeToPushNotifications(registration, vapidPublicKey) {
    try {
        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            throw new Error('Push notification permission denied');
        }
        
        // Subscribe to push notifications
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
        });
        
        // Send subscription to server
        const response = await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to register subscription: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Successfully subscribed to push notifications:', result);
        
        // Verstecke Button falls vorhanden
        const button = document.getElementById('push-notification-btn');
        if (button) {
            button.remove();
        }
        
        showToast('Push-Benachrichtigungen aktiviert! 🔔', 'success');
        return true;
        
    } catch (error) {
        console.error('Error subscribing to push notifications:', error);
        showToast(`Fehler beim Aktivieren der Push-Benachrichtigungen: ${error.message}`, 'error');
        return false;
    }
}

function showPushNotificationButton(registration, vapidPublicKey) {
    // Prüfe ob Button bereits existiert
    if (document.getElementById('push-notification-btn')) return;
    
    // Erstelle Button für Push-Benachrichtigungen
    const button = document.createElement('button');
    button.id = 'push-notification-btn';
    button.className = 'btn btn-primary push-notification-btn';
    button.innerHTML = `
        <span class="btn-icon">🔔</span>
        <span class="btn-text">Push-Benachrichtigungen aktivieren</span>
    `;
    
    button.addEventListener('click', async () => {
        button.disabled = true;
        button.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Aktiviere...</span>';
        
        const success = await subscribeToPushNotifications(registration, vapidPublicKey);
        
        if (!success) {
            button.disabled = false;
            button.innerHTML = '<span class="btn-icon">🔔</span><span class="btn-text">Push-Benachrichtigungen aktivieren</span>';
        }
    });
    
    // Füge Button zur Seite hinzu (z.B. in der Account-Sektion)
    const container = document.querySelector('.page-actions') || document.querySelector('.card-actions') || document.body;
    container.appendChild(button);
}

async function testPushNotification() {
    try {
        const response = await fetch('/api/push/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
        } else {
            throw new Error(result.error || 'Test failed');
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
        setupEventPushNotifications();
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
        
        const response = await fetch(`/api/events/${eventId}/send-reminders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`✅ ${result.message}`, 'success');
        } else {
            throw new Error(result.message || 'Unbekannter Fehler');
        }
        
    } catch (error) {
        console.error('Error sending reminders:', error);
        showToast(`❌ Fehler beim Senden der Push-Erinnerungen: ${error.message}`, 'error');
    } finally {
        const reminderBtn = document.getElementById('send-reminders-btn');
        setLoadingState(reminderBtn, false);
    }
}


// Export functions for global use
window.showToast = showToast;
window.setLoadingState = setLoadingState;
window.sendParticipationReminders = sendParticipationReminders;
window.testPushNotification = testPushNotification;




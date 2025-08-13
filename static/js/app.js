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

// Push Notification Management
async function initializePushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }
    
    try {
        // Register service worker
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('Service Worker registered:', registration);
        
        // Check if already subscribed
        const existingSubscription = await registration.pushManager.getSubscription();
        if (existingSubscription) {
            console.log('Already subscribed to push notifications');
            return;
        }
        
        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.log('Push notification permission denied');
            return;
        }
        
        // Subscribe to push notifications
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(getVapidPublicKey())
        });
        
        // Send subscription to server
        await fetch('/notifications/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });
        
        console.log('Successfully subscribed to push notifications');
        
    } catch (error) {
        console.error('Error setting up push notifications:', error);
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

function getVapidPublicKey() {
    // This will be set from backend config
    return 'BJrWx8xCvf_8kT2j3R3_7nqJ2x3kX4c2Pd4FVk1cJ5q_QH7_0LlCPT9gU8NZ_ZEt4QP8vP2N_YfXYt8aU0rN_E4';
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Gourmen App initialisiert');
    
    // Initialize flash messages
    initializeFlashMessages();
    
    // Check if user is authenticated (this will be set by the template)
    const isAuthenticated = document.body.hasAttribute('data-authenticated');
    
    if (isAuthenticated) {
        initializePushNotifications();
    }
});

// Export functions for global use
window.showToast = showToast;
window.setLoadingState = setLoadingState;




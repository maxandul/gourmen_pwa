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
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }
    
    try {
        // Warte auf Service Worker Registrierung
        let registration = await navigator.serviceWorker.getRegistration();
        if (!registration) {
            console.log('No service worker registration found - waiting for PWA initialization...');
            // Warte bis zu 5 Sekunden auf Service Worker
            for (let i = 0; i < 50; i++) {
                await new Promise(resolve => setTimeout(resolve, 100));
                registration = await navigator.serviceWorker.getRegistration();
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
        const vapidPublicKey = await getVapidPublicKey();
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
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

async function getVapidPublicKey() {
    try {
        const response = await fetch('/notifications/vapid-public-key');
        const data = await response.json();
        return data.publicKey;
    } catch (error) {
        console.error('Error getting VAPID public key:', error);
        // Fallback key (should not be used in production)
        return 'BJrWx8xCvf_8kT2j3R3_7nqJ2x3kX4c2Pd4FVk1cJ5q_QH7_0LlCPT9gU8NZ_ZEt4QP8vP2N_YfXYt8aU0rN_E4';
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
    }
});

// Export functions for global use
window.showToast = showToast;
window.setLoadingState = setLoadingState;




/**
 * PWA (Progressive Web App) Funktionalität für Gourmen
 * Verbesserte Version mit modernen Features
 */

class PWA {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.updateAvailable = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkInstallation();
        this.setupServiceWorker();
        this.setupNetworkStatus();
        this.setupNotifications();
        this.setupUpdateDetection();
        // this.showDebugInfo(); // Debug-Info anzeigen - auskommentiert
    }

    setupEventListeners() {
        // Install-Prompt Event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('🚀 beforeinstallprompt Event gefangen');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // App installiert Event
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            this.showToast('App erfolgreich installiert! 🎉', 'success');
        });

        // Online/Offline Status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showToast('Verbindung wiederhergestellt', 'success');
            this.updateNetworkStatus();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showToast('Keine Internetverbindung', 'warning');
            this.updateNetworkStatus();
        });

        // Service Worker Updates
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'UPDATE_AVAILABLE') {
                    this.updateAvailable = true;
                    this.showUpdateButton();
                }
            });
        }
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registriert:', registration);
                    
                    // Prüfe auf Updates
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.updateAvailable = true;
                                this.showUpdateButton();
                            }
                        });
                    });
                })
                .catch(error => {
                    console.error('Service Worker Registrierung fehlgeschlagen:', error);
                    // Fallback: Zeige Info über Service Worker Problem
                    // this.showToast('Service Worker konnte nicht registriert werden', 'warning');
                });
        } else {
            console.log('Service Worker nicht unterstützt');
            // this.showToast('Service Worker nicht unterstützt - PWA-Installation nicht möglich', 'warning');
        }
    }

    setupNetworkStatus() {
        this.updateNetworkStatus();
        
        // Erstelle Network Status Indicator
        const networkIndicator = document.createElement('div');
        networkIndicator.id = 'network-status';
        networkIndicator.className = 'network-indicator';
        document.body.appendChild(networkIndicator);
    }

    setupNotifications() {
        // Prüfe Notification-Berechtigung
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                this.showNotificationPermissionButton();
            }
        }
    }

    setupUpdateDetection() {
        // Prüfe regelmäßig auf Updates
        setInterval(() => {
            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({ type: 'CHECK_UPDATE' });
            }
        }, 60000); // Jede Minute
    }

    checkInstallation() {
        // Prüfe ob App bereits installiert ist
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                            window.navigator.standalone === true;
        
        console.log('🚀 Installation-Check:', {
            displayMode: window.matchMedia('(display-mode: standalone)').matches,
            navigatorStandalone: window.navigator.standalone,
            isStandalone: isStandalone
        });
        
        if (isStandalone) {
            this.isInstalled = true;
            this.hideInstallButton();
            console.log('🚀 App bereits installiert');
        } else {
            console.log('🚀 App nicht installiert, Install-Prompt möglich');
        }
    }

    showInstallButton() {
        console.log('🚀 Zeige Install-Button an');
        
        // Nur anzeigen wenn App nicht bereits installiert ist
        if (this.isInstalled) {
            console.log('🚀 App bereits installiert, Button nicht anzeigen');
            return;
        }
        
        // Prüfe ob Benutzer eingeloggt ist (optional)
        const isAuthenticated = document.body.hasAttribute('data-authenticated');
        if (isAuthenticated) {
            console.log('🚀 Benutzer eingeloggt, Install-Button anzeigen');
        }

        const existingBtn = document.getElementById('pwa-install-btn');
        if (existingBtn) {
            console.log('🚀 Install-Button bereits vorhanden');
            return;
        }

        const installBtn = document.createElement('button');
        installBtn.id = 'pwa-install-btn';
        installBtn.className = 'pwa-install-btn-subtle';
        installBtn.innerHTML = `
            <span style="display: flex; align-items: center; gap: 8px;">
                📱 Installieren
            </span>
        `;
        
        installBtn.addEventListener('click', () => this.installApp());
        document.body.appendChild(installBtn);
        
        console.log('🚀 Install-Button hinzugefügt');

        // Auto-hide nach 10 Sekunden
        setTimeout(() => {
            if (installBtn.parentNode) {
                installBtn.style.opacity = '0.7';
                console.log('🚀 Install-Button ausgeblendet');
            }
        }, 10000);
    }

    hideInstallButton() {
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.remove();
        }
    }

    async installApp() {
        if (!this.deferredPrompt) {
            this.showToast('Installation nicht verfügbar', 'error');
            return;
        }

        try {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                this.showToast('Installation gestartet...', 'info');
            } else {
                this.showToast('Installation abgebrochen', 'warning');
            }
            
            this.deferredPrompt = null;
            this.hideInstallButton();
        } catch (error) {
            console.error('Installation fehlgeschlagen:', error);
            this.showToast('Installation fehlgeschlagen', 'error');
        }
    }

    showNotificationPermissionButton() {
        const existingBtn = document.getElementById('notification-permission-btn');
        if (existingBtn) return;

        const permissionBtn = document.createElement('button');
        permissionBtn.id = 'notification-permission-btn';
        permissionBtn.className = 'notification-permission-btn';
        permissionBtn.innerHTML = `
            <span style="display: flex; align-items: center; gap: 8px;">
                🔔 Benachrichtigungen aktivieren
            </span>
        `;
        
        permissionBtn.addEventListener('click', () => this.requestNotificationPermission());
        document.body.appendChild(permissionBtn);
    }

    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            this.showToast('Benachrichtigungen nicht unterstützt', 'error');
            return;
        }

        try {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                this.showToast('Benachrichtigungen aktiviert!', 'success');
                this.hideNotificationPermissionButton();
                
                // Sende Test-Benachrichtigung
                this.sendNotification('Gourmen App', 'Benachrichtigungen sind jetzt aktiv!');
            } else {
                this.showToast('Benachrichtigungen abgelehnt', 'warning');
            }
        } catch (error) {
            console.error('Notification Permission Error:', error);
            this.showToast('Fehler bei der Berechtigung', 'error');
        }
    }

    hideNotificationPermissionButton() {
        const permissionBtn = document.getElementById('notification-permission-btn');
        if (permissionBtn) {
            permissionBtn.remove();
        }
    }

    showUpdateButton() {
        if (!this.updateAvailable) return;

        const existingBtn = document.getElementById('pwa-update-btn');
        if (existingBtn) return;

        const updateBtn = document.createElement('button');
        updateBtn.id = 'pwa-update-btn';
        updateBtn.className = 'pwa-update-btn';
        updateBtn.innerHTML = `
            <span style="display: flex; align-items: center; gap: 8px;">
                🔄 Update verfügbar
            </span>
        `;
        
        updateBtn.addEventListener('click', () => this.updateApp());
        document.body.appendChild(updateBtn);
    }

    updateApp() {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
            
            // Reload nach Update
            window.location.reload();
        }
    }

    updateNetworkStatus() {
        const indicator = document.getElementById('network-status');
        if (!indicator) return;

        if (this.isOnline) {
            indicator.className = 'network-indicator online';
            indicator.innerHTML = '🌐 Online';
        } else {
            indicator.className = 'network-indicator offline';
            indicator.innerHTML = '📡 Offline';
        }
    }

    showToast(message, type = 'info') {
        // Entferne existierende Toasts
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());

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

    async sendNotification(title, body, options = {}) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }

        const defaultOptions = {
            icon: '/static/img/icon-192.png',
            badge: '/static/img/icon-96.png',
            tag: 'gourmen-notification',
            requireInteraction: false,
            ...options
        };

        try {
            const notification = new Notification(title, defaultOptions);
            
            // Auto-close nach 5 Sekunden
            setTimeout(() => {
                notification.close();
            }, 5000);

            return notification;
        } catch (error) {
            console.error('Notification Error:', error);
        }
    }

    // Utility Methoden
    isStandalone() {
        return window.matchMedia('(display-mode: standalone)').matches || 
               window.navigator.standalone === true;
    }

    getAppInfo() {
        return {
            isInstalled: this.isInstalled,
            isStandalone: this.isStandalone(),
            isOnline: this.isOnline,
            updateAvailable: this.updateAvailable,
            notificationPermission: 'Notification' in window ? Notification.permission : 'not-supported'
        };
    }

    showDebugInfo() {
        // Debug-Info direkt auf der Seite anzeigen
        const debugInfo = document.createElement('div');
        debugInfo.id = 'pwa-debug-info';
        debugInfo.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.95);
            color: black;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            font-family: monospace;
            z-index: 9999;
            max-width: 300px;
            word-wrap: break-word;
            border: 2px solid #dc693c;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        `;
        
        const info = this.getAppInfo();
        debugInfo.innerHTML = `
            <strong>PWA Debug Info:</strong><br>
            Installiert: ${info.isInstalled}<br>
            Standalone: ${info.isStandalone}<br>
            Online: ${info.isOnline}<br>
            DeferredPrompt: ${this.deferredPrompt ? 'JA' : 'NEIN'}<br>
            ServiceWorker: ${'serviceWorker' in navigator ? 'JA' : 'NEIN'}<br>
            Manifest: ${document.querySelector('link[rel="manifest"]') ? 'JA' : 'NEIN'}<br>
            <br>
            <strong>Manueller Test:</strong><br>
            <button onclick="window.gourmenPWA.manualInstall()" style="margin: 5px 0; padding: 5px 10px; background: #28a745; border: none; color: white; border-radius: 4px; cursor: pointer;">Install Test</button>
            <button onclick="this.parentElement.remove()" style="margin-top: 5px; padding: 2px 8px; background: #dc693c; border: none; color: white; border-radius: 4px; cursor: pointer;">Schließen</button>
        `;
        
        document.body.appendChild(debugInfo);
    }

    manualInstall() {
        // Manueller Install-Test
        if (this.deferredPrompt) {
            console.log('🚀 Manueller Install gestartet');
            this.deferredPrompt.prompt();
            this.deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('✅ User hat Installation akzeptiert');
                    this.showToast('Installation gestartet!', 'success');
                } else {
                    console.log('❌ User hat Installation abgelehnt');
                    this.showToast('Installation abgebrochen', 'warning');
                }
                this.deferredPrompt = null;
            });
        } else {
            console.log('❌ Kein DeferredPrompt verfügbar');
            
            // Detaillierte Diagnose
            let diagnosis = 'PWA-Diagnose:\n';
            diagnosis += `ServiceWorker: ${'serviceWorker' in navigator ? 'JA' : 'NEIN'}\n`;
            diagnosis += `BeforeInstallPromptEvent: ${'BeforeInstallPromptEvent' in window ? 'JA' : 'NEIN'}\n`;
            diagnosis += `Manifest: ${document.querySelector('link[rel="manifest"]') ? 'JA' : 'NEIN'}\n`;
            diagnosis += `HTTPS/localhost: ${window.location.protocol === 'https:' || window.location.hostname === 'localhost' ? 'JA' : 'NEIN'}\n`;
            diagnosis += `URL: ${window.location.href}\n`;
            diagnosis += `User Agent: ${navigator.userAgent.substring(0, 50)}...`;
            
            this.showToast(diagnosis, 'info');
        }
    }
}

// PWA CSS für Network Indicator
const pwaStyles = `
.network-indicator {
    position: fixed;
    top: 70px;
    right: 16px;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    z-index: 1004;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.network-indicator.online {
    background: rgba(40, 167, 69, 0.9);
    color: white;
}

.network-indicator.offline {
    background: rgba(220, 53, 69, 0.9);
    color: white;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.toast-close {
    background: none;
    border: none;
    color: inherit;
    font-size: 18px;
    cursor: pointer;
    margin-left: 12px;
    opacity: 0.7;
    transition: opacity 0.2s;
}

.toast-close:hover {
    opacity: 1;
}

/* Toast Notifications */
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 16px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 1005;
    max-width: 300px;
    word-wrap: break-word;
    display: flex;
    align-items: center;
    justify-content: space-between;
    animation: slideIn 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast.info {
    background: rgba(23, 162, 184, 0.9);
}

.toast.success {
    background: rgba(40, 167, 69, 0.9);
}

.toast.warning {
    background: rgba(255, 193, 7, 0.9);
    color: #1b232e;
}

.toast.error {
    background: rgba(220, 53, 69, 0.9);
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Verbesserte PWA Buttons */
.pwa-install-btn,
.notification-permission-btn,
.pwa-update-btn {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #dc693c, #804539);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(220, 105, 60, 0.3);
    z-index: 1003;
    /* animation: bounce 2s infinite; */ /* Animation entfernt */
    cursor: pointer;
    transition: all 0.3s ease;
}

/* Dezenterer Install-Button */
.pwa-install-btn-subtle {
    position: fixed;
    top: 80px;
    right: 16px;
    background: rgba(220, 105, 60, 0.9);
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(220, 105, 60, 0.3);
    z-index: 1003;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.pwa-install-btn-subtle:hover {
    background: rgba(220, 105, 60, 1);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(220, 105, 60, 0.4);
}

.pwa-install-btn:hover,
.notification-permission-btn:hover,
.pwa-update-btn:hover {
    background: linear-gradient(135deg, #e67a4d, #9a5543);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 6px 20px rgba(220, 105, 60, 0.4);
}

.notification-permission-btn {
    bottom: 160px;
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
}

.notification-permission-btn:hover {
    background: linear-gradient(135deg, #1ea085, #8e44ad);
}

.pwa-update-btn {
    bottom: 220px;
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: #1b232e;
}

.pwa-update-btn:hover {
    background: linear-gradient(135deg, #e0a800, #e67e22);
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% {
        transform: translateX(-50%) translateY(0);
    }
    40% {
        transform: translateX(-50%) translateY(-10px);
    }
    60% {
        transform: translateX(-50%) translateY(-5px);
    }
}
`;

// CSS hinzufügen
const styleSheet = document.createElement('style');
styleSheet.textContent = pwaStyles;
document.head.appendChild(styleSheet);

// PWA initialisieren
let pwa;
document.addEventListener('DOMContentLoaded', () => {
    pwa = new PWA();
    
    // Debug-Info in der Konsole
    console.log('🚀 Gourmen PWA initialisiert');
    console.log('App Info:', pwa.getAppInfo());
    
    // Globale PWA-Referenz für Debugging
    window.gourmenPWA = pwa;
    
    // Manueller Test des Install-Prompts (für Debugging)
    setTimeout(() => {
        console.log('🚀 PWA Status nach 2 Sekunden:', {
            deferredPrompt: !!pwa.deferredPrompt,
            isInstalled: pwa.isInstalled,
            isOnline: pwa.isOnline
        });
    }, 2000);
});

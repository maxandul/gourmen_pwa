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
            console.log('🚀 App wurde erfolgreich installiert');
        });

        // Online/Offline Status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showToast('🌐 Verbindung wiederhergestellt', 'success');
            this.updateNetworkStatus();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showToast('📡 Keine Internetverbindung - Offline-Modus aktiv', 'warning', 8000);
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
            navigator.serviceWorker.register('/static/sw.js')
                .then(registration => {
                    console.log('Service Worker registriert:', registration);
                    
                    // Prüfe auf Updates
                    registration.addEventListener('updatefound', () => {
                        console.log('🔄 Service Worker Update gefunden!');
                        const newWorker = registration.installing;
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed') {
                                if (navigator.serviceWorker.controller) {
                                    console.log('🔄 Neuer Service Worker installiert - Update verfügbar!');
                                    this.updateAvailable = true;
                                    this.showUpdateButton();
                                } else {
                                    console.log('🔄 Service Worker installiert - App bereit für Offline-Nutzung');
                                }
                            }
                        });
                    });
                    
                    // Prüfe sofort auf Updates beim Laden
                    registration.update();
                    
                    // Zusätzlicher Update-Check alle 5 Minuten
                    setInterval(() => {
                        registration.update();
                    }, 300000); // 5 Minuten
                })
                .catch(error => {
                    console.error('Service Worker Registrierung fehlgeschlagen:', error);
                    this.showToast('Service Worker konnte nicht registriert werden', 'warning');
                });
        } else {
            console.log('Service Worker nicht unterstützt');
            this.showToast('Service Worker nicht unterstützt - PWA-Installation nicht möglich', 'warning');
        }
    }

    setupNetworkStatus() {
        // Network Status wird jetzt über Toasts angezeigt
        // Kein permanenter Indicator mehr nötig
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
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistration().then(registration => {
                    if (registration) {
                        console.log('🔄 Checking for updates...');
                        registration.update();
                    }
                });
            }
        }, 60000); // Alle 60 Sekunden für bessere Update-Erkennung
        
        // Zusätzlicher Update-Check beim Seitenladen
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('🔄 Service Worker controller changed - reloading page');
                window.location.reload();
            });
            
            // Update-Check beim Fokus der Seite
            window.addEventListener('focus', () => {
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.getRegistration().then(registration => {
                        if (registration) {
                            registration.update();
                        }
                    });
                }
            });
        }
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
            this.showToast('App wird installiert...', 'info');
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                this.showToast('Installation läuft...', 'info');
                // Warte auf das appinstalled Event für die finale Bestätigung
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
                🔄 Update verfügbar - Jetzt installieren
            </span>
        `;
        
        updateBtn.addEventListener('click', () => this.updateApp());
        document.body.appendChild(updateBtn);
        
        // Zeige auch eine Toast-Benachrichtigung
        this.showToast('🔄 Neues Update verfügbar! Klicke auf den Update-Button.', 'info');
        
        // Auto-hide nach 60 Sekunden falls nicht geklickt
        setTimeout(() => {
            if (updateBtn.parentNode && !this.updateAvailable) {
                updateBtn.remove();
            }
        }, 60000);
    }
    
    hideUpdateButton() {
        const updateBtn = document.getElementById('pwa-update-btn');
        if (updateBtn) {
            updateBtn.remove();
        }
    }

    updateApp() {
        if ('serviceWorker' in navigator) {
            console.log('🔄 Updating app...');
            this.updateAvailable = false;
            this.hideUpdateButton();
            this.showToast('Update wird installiert...', 'info');
            
            navigator.serviceWorker.getRegistration().then(registration => {
                if (registration && registration.waiting) {
                    // Sende Skip-Waiting Message an den wartenden Service Worker
                    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                } else if (navigator.serviceWorker.controller) {
                    // Fallback: Sende Message an den aktuellen Controller
                    navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
                }
                
                // Reload nach Update
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            });
        }
    }
    
    // Manueller Update-Check für Benutzer (nur für Debugging/Admin)
    checkForUpdates() {
        if ('serviceWorker' in navigator) {
            this.showToast('🔄 Suche nach Updates...', 'info');
            
            navigator.serviceWorker.getRegistration().then(registration => {
                if (registration) {
                    console.log('🔄 Manual update check...');
                    return registration.update();
                } else {
                    throw new Error('Keine Service Worker Registrierung gefunden');
                }
            })
            .then(() => {
                this.showToast('✅ Update-Check abgeschlossen', 'success');
            })
            .catch(error => {
                console.error('Update check failed:', error);
                this.showToast('❌ Update-Check fehlgeschlagen', 'error');
            });
        } else {
            this.showToast('❌ Service Worker nicht unterstützt', 'error');
        }
    }
    

    updateNetworkStatus() {
        // Network Status wird jetzt über Toasts angezeigt
        // Diese Methode bleibt für Kompatibilität, macht aber nichts mehr
    }

    showToast(message, type = 'info', duration = 5000) {
        // Entferne existierende Toasts des gleichen Typs
        const existingToasts = document.querySelectorAll(`.toast.${type}`);
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;

        document.body.appendChild(toast);

        // Auto-remove nach definierter Zeit
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
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
            this.showToast('App wird installiert...', 'info');
            this.deferredPrompt.prompt();
            this.deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('✅ User hat Installation akzeptiert');
                    this.showToast('Installation läuft...', 'info');
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

// PWA CSS - Network Indicator entfernt, nur noch Toast-System
const pwaStyles = `

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

/* Toast Notifications - Einheitliches System */
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 20px;
    border-radius: 12px;
    color: white;
    font-weight: 500;
    z-index: 1005;
    max-width: 350px;
    min-width: 280px;
    word-wrap: break-word;
    display: flex;
    align-items: center;
    justify-content: space-between;
    animation: slideIn 0.4s ease;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.toast.info {
    background: linear-gradient(135deg, rgba(23, 162, 184, 0.95), rgba(23, 162, 184, 0.85));
    border-left: 4px solid #17a2b8;
}

.toast.success {
    background: linear-gradient(135deg, rgba(113, 198, 166, 0.95), rgba(113, 198, 166, 0.85));
    border-left: 4px solid #71c6a6;
}

.toast.warning {
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.95), rgba(255, 193, 7, 0.85));
    color: #1b232e;
    border-left: 4px solid #ffc107;
}

.toast.error {
    background: linear-gradient(135deg, rgba(220, 53, 69, 0.95), rgba(220, 53, 69, 0.85));
    border-left: 4px solid #dc3545;
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
    background: linear-gradient(135deg, #71c6a6, #5ba68a);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(113, 198, 166, 0.3);
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
    background: rgba(113, 198, 166, 0.9);
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(113, 198, 166, 0.3);
    z-index: 1003;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.pwa-install-btn-subtle:hover {
    background: rgba(113, 198, 166, 1);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(113, 198, 166, 0.4);
}

.pwa-install-btn:hover,
.notification-permission-btn:hover,
.pwa-update-btn:hover {
    background: linear-gradient(135deg, #8dd4b8, #71c6a6);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 6px 20px rgba(113, 198, 166, 0.4);
}

.notification-permission-btn {
    bottom: 160px;
    background: linear-gradient(135deg, #17a2b8, #71c6a6);
}

.notification-permission-btn:hover {
    background: linear-gradient(135deg, #1ea085, #8dd4b8);
}

.pwa-update-btn {
    bottom: 220px;
    background: linear-gradient(135deg, #ffc107, #71c6a6);
    color: #1b232e;
}

.pwa-update-btn:hover {
    background: linear-gradient(135deg, #e0a800, #8dd4b8);
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

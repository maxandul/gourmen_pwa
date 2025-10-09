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
        this.serviceWorkerRegistration = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkInstallation();
        this.setupServiceWorker();
        this.setupNetworkStatus();
        this.setupNotifications();
        this.updateAppInfo();
        this.setupUpdateDetection();
        // Optionaler Button für manuelle Updates (derzeit nicht genutzt)
        if (typeof this.setupManualUpdateButton === 'function') {
            this.setupManualUpdateButton();
        }
        this.setupServiceWorkerInfoCard();
        
        // Debug-Panel nur, wenn aktiviert
        const debugEnabled = (
            (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
            (new URLSearchParams(window.location.search).get('pwa_debug') === '1' || localStorage.getItem('PWA_DEBUG') === '1')
        );
        if (debugEnabled) {
            this.showDebugInfo();
        }
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
                    // Update läuft automatisch - keine Benachrichtigung nötig
                } else if (event.data && event.data.type === 'UPDATE_CHECK_COMPLETE') {
                    this.handleUpdateCheckComplete(event.data);
                } else if (event.data && event.data.type === 'UPDATE_CHECK_FAILED') {
                    this.handleUpdateCheckFailed(event.data);
                } else if (event.data && event.data.type === 'SW_INSTALLED') {
                    this.handleServiceWorkerInstalled(event.data);
                }
            });
        }
    }

    setupServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.log('❌ Service Worker nicht unterstützt');
            this.showToast('Service Worker nicht unterstützt - PWA-Installation nicht möglich', 'warning');
            return;
        }
        
        console.log('🔄 Starte Service Worker Registrierung...');
        
        // Registriere Service Worker (oder hole bestehende Registration)
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then(registration => {
                console.log('✅ Service Worker registriert:', registration);
                this.serviceWorkerRegistration = registration;
                this.setupServiceWorkerEvents(registration);
                
                // Globale Referenz für andere Skripte (z.B. app.js)
                window.gourmenServiceWorker = registration;
                
                // Kein initialer Update-Check mehr - läuft automatisch im Hintergrund
                // (siehe setupUpdateDetection: alle 5 Min + bei focus)
            })
            .catch(error => {
                console.error('❌ Service Worker Registrierung fehlgeschlagen:', error);
                this.showToast('Service Worker konnte nicht registriert werden: ' + error.message, 'error');
                
                // Debug-Info für localhost
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    console.log('🔧 Debug-Info:');
                    console.log('- URL:', window.location.href);
                    console.log('- Protocol:', window.location.protocol);
                    console.log('- Service Worker File:', '/sw.js');
                    console.log('- Error:', error);
                }
            });
    }

    setupServiceWorkerEvents(registration) {
                    // Prüfe auf Updates
                    registration.addEventListener('updatefound', () => {
                        console.log('🔄 Service Worker Update gefunden!');
                        const newWorker = registration.installing;
            if (!newWorker) {
                console.log('ℹ️ Kein installing-Worker vorhanden (evtl. bereits installiert)');
                return;
            }
                        newWorker.addEventListener('statechange', () => {
                if (!newWorker) return;
                            if (newWorker.state === 'installed') {
                                if (navigator.serviceWorker.controller) {
                                    console.log('🔄 Neuer Service Worker installiert - Update läuft automatisch');
                                    this.updateAvailable = true;
                                    // Update läuft automatisch - keine Benachrichtigung nötig
                                } else {
                                    console.log('🔄 Service Worker installiert - App bereit für Offline-Nutzung');
                        // Bei der ersten Installation warten wir auf die Aktivierung
                        if (newWorker.state === 'installed' && !navigator.serviceWorker.controller) {
                            console.log('🔄 Warte auf Service Worker Aktivierung...');
                            // Automatische Aktivierung nach kurzer Verzögerung
                            setTimeout(() => {
                                if (newWorker.state === 'installed') {
                                    console.log('🔄 Aktiviere Service Worker...');
                                    newWorker.postMessage({ type: 'SKIP_WAITING' });
                                }
                            }, 1000);
                        }
                                }
                            }
                        });
                    });
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
        // Warte auf Service Worker Bereitschaft, dann starte Update-Checks
        this.waitForServiceWorker().then(() => {
            console.log('🔄 Service Worker bereit, starte automatische Update-Checks');
            
            // Prüfe regelmäßig auf Updates (alle 5 Minuten)
        setInterval(() => {
                this.performAutomaticUpdateCheck();
            }, 300000); // 5 Minuten
            
            // Update-Check beim Fokus der Seite
            window.addEventListener('focus', () => {
                this.performAutomaticUpdateCheck();
            });
            
            // Sofortiger Update-Check nach Service Worker Bereitschaft
            setTimeout(() => {
                this.performAutomaticUpdateCheck();
            }, 2000);
            
        }).catch(error => {
            console.log('⚠️ Service Worker nicht verfügbar, automatische Updates deaktiviert:', error);
        });
        
        // Service Worker Controller Change Handler
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('🔄 Service Worker controller changed - reloading page');
                window.location.reload();
            });
        }
    }

    async performAutomaticUpdateCheck() {
        if (!('serviceWorker' in navigator)) return;
        
        try {
            const registration = await navigator.serviceWorker.getRegistration();
                        if (registration) {
                console.log('🔄 Automatischer Update-Check...');
                await registration.update();
                
                // Prüfe nach Update-Check, ob ein neuer Service Worker wartet
                setTimeout(() => {
                    if (registration.waiting) {
                        console.log('🔄 Automatisches Update verfügbar - wird installiert');
                        this.updateAvailable = true;
                        // Update läuft automatisch - keine Benachrichtigung nötig
                    }
                }, 1000);
            }
        } catch (error) {
            console.log('⚠️ Automatischer Update-Check fehlgeschlagen:', error);
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
            
            // iOS-User informieren (da kein beforeinstallprompt auf iOS)
            if (this.isIOS() && !this.isInstalled) {
                this.showIOSInstallPrompt();
            }
        }
    }

    isIOS() {
        // Prüfe ob iOS/Safari
        return /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;
    }

    showIOSInstallPrompt() {
        // Zeige dezenten Hinweis für iOS-User
        // Nur einmal anzeigen (localStorage)
        if (localStorage.getItem('ios-install-prompt-shown')) {
            return;
        }

        // Warte 3 Sekunden nach Seitenload
        setTimeout(() => {
            const message = '💡 Tipp: Installiere die Gourmen-App auf deinem iPhone!\n\n' +
                          '1. Tippe auf das Teilen-Symbol ↗️\n' +
                          '2. Wähle "Zum Home-Bildschirm"\n' +
                          '3. Tippe auf "Hinzufügen"';
            
            this.showToast(message, 'info', 12000);
            
            // Markiere als angezeigt
            localStorage.setItem('ios-install-prompt-shown', 'true');
            
            console.log('📱 iOS-Installationshinweis angezeigt');
        }, 3000);
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
        
        // Keine Toast-Benachrichtigung - Update läuft automatisch
        
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
            // Kein Toast mehr - läuft still im Hintergrund
            console.log('🔄 Manual update check requested...');
            
            navigator.serviceWorker.getRegistration().then(registration => {
                if (registration) {
                    console.log('🔄 Running update check...');
                    return registration.update();
                } else {
                    throw new Error('Keine Service Worker Registrierung gefunden');
                }
            })
            .then(() => {
                console.log('✅ Update-Check abgeschlossen');
                // Kein Toast - Update-Button erscheint automatisch wenn verfügbar
            })
            .catch(error => {
                console.error('❌ Update check failed:', error);
                // Nur bei Fehler Toast anzeigen
                if (error.message !== 'Keine Service Worker Registrierung gefunden') {
                    this.showToast('❌ Update-Check fehlgeschlagen', 'error');
                }
            });
        } else {
            console.error('❌ Service Worker nicht unterstützt');
            this.showToast('❌ Service Worker nicht unterstützt', 'error');
        }
    }

    // Service Worker Info Card Funktionalität
    setupServiceWorkerInfoCard() {
        // Prüfe ob wir auf der Profile-Seite sind
        if (!document.getElementById('sw-diagnose-btn')) return;

        // App-Info aktualisieren
        this.updateServiceWorkerInfo();
        
        // Event Listeners für die neuen Buttons
        this.setupServiceWorkerInfoButtons();
    }
    
    setupServiceWorkerInfoButtons() {
        // Diagnose Button
        const diagnoseBtn = document.getElementById('sw-diagnose-btn');
        if (diagnoseBtn) {
            diagnoseBtn.addEventListener('click', () => {
                this.performServiceWorkerDiagnosis();
            });
        }
        
        // Push Test Button
        const testBtn = document.getElementById('sw-test-btn');
        if (testBtn) {
            testBtn.addEventListener('click', () => {
                if (window.testPushNotification) {
                    window.testPushNotification();
                } else {
                    this.testPushNotification();
                }
            });
        }
        
        // Cleanup Button
        const cleanupBtn = document.getElementById('sw-cleanup-btn');
        if (cleanupBtn) {
            cleanupBtn.addEventListener('click', () => {
                this.cleanupServiceWorker();
            });
        }
        
        // Force Register Button
        const forceRegisterBtn = document.getElementById('sw-force-register-btn');
        if (forceRegisterBtn) {
            forceRegisterBtn.addEventListener('click', () => {
                this.forceRegisterServiceWorker();
            });
        }
    }
    
    async performServiceWorkerDiagnosis() {
        const statusDiv = document.getElementById('sw-status');
        const statusText = document.querySelector('#sw-status .status-text');
        
        try {
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker Diagnose läuft...', 'info');
            
            // Sammle Diagnose-Informationen
            const diagnosis = await this.collectServiceWorkerDiagnosis();
            
            // Zeige Ergebnisse
            this.showDiagnosisResults(diagnosis, statusDiv, statusText);
            
        } catch (error) {
            console.error('Service Worker Diagnose fehlgeschlagen:', error);
            this.showUpdateStatus(statusDiv, statusText, `Diagnose fehlgeschlagen: ${error.message}`, 'error');
        }
    }
    
    async collectServiceWorkerDiagnosis() {
        const diagnosis = {
            timestamp: new Date().toISOString(),
            serviceWorkerSupported: 'serviceWorker' in navigator,
            pushSupported: 'PushManager' in window,
            notificationSupported: 'Notification' in window,
            registrations: [],
            errors: []
        };
        
        if (!diagnosis.serviceWorkerSupported) {
            diagnosis.errors.push('Service Worker wird nicht unterstützt');
            return diagnosis;
        }
        
        try {
            // Prüfe alle Registrierungen
            const registrations = await navigator.serviceWorker.getRegistrations();
            diagnosis.registrations = registrations.map(reg => ({
                scope: reg.scope,
                active: reg.active ? reg.active.state : 'none',
                installing: reg.installing ? reg.installing.state : 'none',
                waiting: reg.waiting ? reg.waiting.state : 'none'
            }));
            
            // Prüfe Push-Berechtigung
            if (diagnosis.notificationSupported) {
                diagnosis.notificationPermission = Notification.permission;
            }
            
        } catch (error) {
            diagnosis.errors.push(`Fehler beim Sammeln der Diagnose: ${error.message}`);
        }
        
        return diagnosis;
    }
    
    showDiagnosisResults(diagnosis, statusDiv, statusText) {
        let message = 'Service Worker Diagnose abgeschlossen:\n\n';
        
        message += `✅ Service Worker Support: ${diagnosis.serviceWorkerSupported ? 'JA' : 'NEIN'}\n`;
        message += `✅ Push Support: ${diagnosis.pushSupported ? 'JA' : 'NEIN'}\n`;
        message += `✅ Notification Support: ${diagnosis.notificationSupported ? 'JA' : 'NEIN'}\n\n`;
        
        message += `Registrierungen gefunden: ${diagnosis.registrations.length}\n`;
        diagnosis.registrations.forEach((reg, index) => {
            message += `  ${index + 1}. Scope: ${reg.scope}\n`;
            message += `     Status: Active=${reg.active}, Installing=${reg.installing}, Waiting=${reg.waiting}\n`;
        });
        
        if (diagnosis.notificationPermission) {
            message += `\nNotification Permission: ${diagnosis.notificationPermission}\n`;
        }
        
        if (diagnosis.errors.length > 0) {
            message += `\nFehler:\n`;
            diagnosis.errors.forEach(error => message += `  - ${error}\n`);
        }
        
        this.showUpdateStatus(statusDiv, statusText, message, diagnosis.errors.length > 0 ? 'error' : 'success');
        
        // Zeige auch in Konsole für Debugging
        console.log('🔍 Service Worker Diagnose:', diagnosis);
    }
    
    async testPushNotification() {
        const statusDiv = document.getElementById('sw-status');
        const statusText = document.querySelector('#sw-status .status-text');
        
        try {
            this.showUpdateStatus(statusDiv, statusText, 'Push-Benachrichtigung wird gesendet...', 'info');
            
            if (!('Notification' in window)) {
                throw new Error('Notifications werden nicht unterstützt');
            }
            
            if (Notification.permission !== 'granted') {
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                    throw new Error('Notification-Berechtigung wurde verweigert');
                }
            }
            
            // Sende Test-Benachrichtigung
            const notification = new Notification('Gourmen Test', {
                body: 'Dies ist eine Test-Benachrichtigung vom Service Worker!',
                icon: '/static/img/pwa/icon-192.png',
                tag: 'gourmen-test'
            });
            
            this.showUpdateStatus(statusDiv, statusText, 'Test-Benachrichtigung gesendet!', 'success');
            
            // Schließe Benachrichtigung nach 3 Sekunden
            setTimeout(() => {
                notification.close();
            }, 3000);
            
        } catch (error) {
            console.error('Push-Test fehlgeschlagen:', error);
            this.showUpdateStatus(statusDiv, statusText, `Push-Test fehlgeschlagen: ${error.message}`, 'error');
        }
    }
    
    async cleanupServiceWorker() {
        const statusDiv = document.getElementById('sw-status');
        const statusText = document.querySelector('#sw-status .status-text');
        
        try {
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker wird zurückgesetzt...', 'info');
            
            // Verwende die bestehende Cleanup-Funktion
            await this.cleanupAllSW();
            
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker erfolgreich zurückgesetzt!', 'success');
            
            // Aktualisiere Info nach kurzer Verzögerung
            setTimeout(() => {
                this.updateServiceWorkerInfo();
            }, 1000);
            
        } catch (error) {
            console.error('Service Worker Cleanup fehlgeschlagen:', error);
            this.showUpdateStatus(statusDiv, statusText, `Cleanup fehlgeschlagen: ${error.message}`, 'error');
        }
    }
    
    async forceRegisterServiceWorker() {
        const statusDiv = document.getElementById('sw-status');
        const statusText = document.querySelector('#sw-status .status-text');
        
        try {
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker wird neu registriert...', 'info');
            
            // Verwende die bestehende Force-Register-Funktion
            await this.forceRegisterSW();
            
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker erfolgreich neu registriert!', 'success');
            
            // Aktualisiere Info nach kurzer Verzögerung
            setTimeout(() => {
                this.updateServiceWorkerInfo();
            }, 1000);
            
        } catch (error) {
            console.error('Service Worker Force-Register fehlgeschlagen:', error);
            this.showUpdateStatus(statusDiv, statusText, `Neu-Registrierung fehlgeschlagen: ${error.message}`, 'error');
        }
    }
    
    async updateServiceWorkerInfo() {
        // Aktualisiere Service Worker Status
        const statusSpan = document.getElementById('sw-registration-status');
        const scopeSpan = document.getElementById('sw-scope');
        const pushSpan = document.getElementById('push-status');
        
        if (statusSpan) {
            try {
                const registration = await navigator.serviceWorker.getRegistration('/');
                if (registration) {
                    statusSpan.textContent = 'Registriert';
                    statusSpan.className = 'status-available';
                    
                    if (scopeSpan) {
                        scopeSpan.textContent = registration.scope;
                    }
                } else {
                    statusSpan.textContent = 'Nicht registriert';
                    statusSpan.className = 'status-unavailable';
                    
                    if (scopeSpan) {
                        scopeSpan.textContent = '-';
                    }
                }
            } catch (error) {
                statusSpan.textContent = 'Fehler';
                statusSpan.className = 'status-unavailable';
            }
        }
        
        // Aktualisiere Push-Status
        if (pushSpan) {
            if (!('Notification' in window)) {
                pushSpan.textContent = 'Nicht unterstützt';
                pushSpan.className = 'status-unavailable';
            } else {
                const permission = Notification.permission;
                pushSpan.textContent = permission === 'granted' ? 'Aktiviert' : permission === 'denied' ? 'Verweigert' : 'Nicht erteilt';
                pushSpan.className = permission === 'granted' ? 'status-available' : 'status-warning';
            }
        }
    }

    // Warte auf Service Worker Registrierung
    async waitForServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            throw new Error('Service Worker nicht unterstützt');
        }

        // Verwende das native ready-Promise
        try {
            const registration = await navigator.serviceWorker.ready;
            console.log('✅ Service Worker bereit:', registration);
            return registration;
        } catch (error) {
            console.error('❌ Service Worker ready fehlgeschlagen:', error);
            throw new Error('Service Worker nicht verfügbar: ' + error.message);
        }
    }

    async performManualUpdate(btn, statusDiv, statusText) {
        if (!('serviceWorker' in navigator)) {
            this.showUpdateStatus(statusDiv, statusText, 'Service Worker nicht unterstützt', 'error');
            return;
        }

        // Button deaktivieren und Loading-Status anzeigen
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Suche Updates...</span>';
        this.showUpdateStatus(statusDiv, statusText, 'Suche nach Updates...', 'info');

        try {
            // Warte auf Service Worker Registrierung
            const registration = await this.waitForServiceWorker();
            
            if (!registration) {
                throw new Error('Service Worker Registrierung nicht verfügbar');
            }

            console.log('Service Worker gefunden, starte Update-Check...');

            // Prüfe auf Updates
            await registration.update();
            
            // Kurz warten, damit der Service Worker Zeit hat zu antworten
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Prüfe ob ein neuer Service Worker wartet
            if (registration.waiting) {
                this.showUpdateStatus(statusDiv, statusText, 'Update verfügbar! Installiere...', 'success');
                
                // Update installieren
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                
                // Warte kurz und lade dann neu
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                
            } else {
                this.showUpdateStatus(statusDiv, statusText, 'App ist bereits auf dem neuesten Stand', 'success');
            }

        } catch (error) {
            console.error('Manual update failed:', error);
            
            // Benutzerfreundlichere Fehlermeldungen
            let errorMessage = 'Update-Check fehlgeschlagen';
            if (error.message.includes('Service Worker nicht unterstützt')) {
                errorMessage = 'Service Worker wird von diesem Browser nicht unterstützt';
            } else if (error.message.includes('Timeout')) {
                errorMessage = 'Service Worker ist noch nicht bereit. Bitte warte einen Moment und versuche es erneut.';
            } else if (error.message.includes('Registrierung')) {
                errorMessage = 'Service Worker ist noch nicht registriert. Bitte lade die Seite neu.';
            } else {
                errorMessage = `Update-Check fehlgeschlagen: ${error.message}`;
            }
            
            this.showUpdateStatus(statusDiv, statusText, errorMessage, 'error');
        } finally {
            // Button wieder aktivieren
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔄</span><span class="btn-text">Nach Updates suchen</span>';
        }
    }

    showUpdateStatus(statusDiv, statusText, message, type) {
        if (!statusDiv || !statusText) return;
        
        statusText.textContent = message;
        statusDiv.className = `update-status ${type}`;
        statusDiv.style.display = 'block';
        
        // Auto-hide nach 5 Sekunden für Erfolgsmeldungen
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }

    updateAppInfo() {
        // App-Version anzeigen
        const versionSpan = document.getElementById('app-version');
        if (versionSpan) {
            versionSpan.textContent = '1.4.0';
        }

        // Installationsstatus prüfen
        const installedSpan = document.getElementById('app-installed');
        if (installedSpan) {
            const isInstalled = this.isStandalone();
            installedSpan.textContent = isInstalled ? 'Ja (PWA)' : 'Nein (Browser)';
            installedSpan.className = isInstalled ? 'status-installed' : 'status-browser';
        }

        // Offline-Status - prüfe Service Worker Status
        const offlineSpan = document.getElementById('offline-status');
        if (offlineSpan) {
            this.updateOfflineStatus(offlineSpan);
        }
    }

    async updateOfflineStatus(offlineSpan) {
        if (!('serviceWorker' in navigator)) {
            offlineSpan.textContent = 'Nicht unterstützt';
            offlineSpan.className = 'status-unavailable';
            return;
        }

        try {
            const registration = await navigator.serviceWorker.getRegistration();
            if (registration) {
                offlineSpan.textContent = 'Verfügbar';
                offlineSpan.className = 'status-available';
            } else {
                offlineSpan.textContent = 'Wird registriert...';
                offlineSpan.className = 'status-browser';
                
                // Versuche es nach 2 Sekunden erneut
                setTimeout(() => {
                    this.updateOfflineStatus(offlineSpan);
                }, 2000);
            }
        } catch (error) {
            offlineSpan.textContent = 'Fehler';
            offlineSpan.className = 'status-unavailable';
        }
    }

    // Service Worker Message Handlers
    handleUpdateCheckComplete(data) {
        console.log('Update check completed:', data);
        
        if (data.hasUpdate) {
            this.updateAvailable = true;
            // Update läuft automatisch - keine Benachrichtigung nötig
            
            // Update Status auf Account-Seite (nur dort, kein Toast)
            const statusDiv = document.getElementById('update-status');
            const statusText = document.querySelector('#update-status .status-text');
            if (statusDiv && statusText) {
                this.showUpdateStatus(statusDiv, statusText, 'Update wird automatisch installiert...', 'success');
            }
        } else {
            // Kein Toast - läuft still im Hintergrund
            console.log('✅ App ist bereits auf dem neuesten Stand');
            
            // Update Status nur auf Account-Seite zeigen
            const statusDiv = document.getElementById('update-status');
            const statusText = document.querySelector('#update-status .status-text');
            if (statusDiv && statusText) {
                this.showUpdateStatus(statusDiv, statusText, 'App ist bereits auf dem neuesten Stand', 'success');
            }
        }
    }

    handleUpdateCheckFailed(data) {
        console.error('Update check failed:', data);
        
        // Update Status auf Account-Seite
        const statusDiv = document.getElementById('update-status');
        const statusText = document.querySelector('#update-status .status-text');
        if (statusDiv && statusText) {
            this.showUpdateStatus(statusDiv, statusText, 'Update-Check fehlgeschlagen: ' + data.error, 'error');
        }
    }

    handleServiceWorkerInstalled(data) {
        console.log('Service Worker installed:', data);
        
        // Zeige Toast-Benachrichtigung
        this.showToast('🔄 App wurde aktualisiert!', 'success');
        
        // Update App-Info
        this.updateAppInfo();
    }
    

    updateNetworkStatus() {
        // Network Status wird jetzt über Toasts angezeigt
        // Diese Methode bleibt für Kompatibilität, macht aber nichts mehr
    }

    showToast(message, type = 'info', duration = 5000) {
        // Erstelle oder hole Toast Container
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // Erstelle Toast Element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Toast Content
        const content = document.createElement('div');
        content.className = 'toast-content';
        content.textContent = message;
        
        // Close Button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = () => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        };
        
        // Zusammenbauen
        toast.appendChild(content);
        toast.appendChild(closeBtn);
        container.appendChild(toast);

        // Auto-remove nach Dauer
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.animation = 'slideOutRight 0.3s ease';
                    setTimeout(() => {
                        if (toast.parentNode) {
                            toast.remove();
                        }
                    }, 300);
                }
            }, duration);
        }

        return toast;
    }

    async sendNotification(title, body, options = {}) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }

        const defaultOptions = {
            icon: '/static/img/pwa/icon-192.png',
            badge: '/static/img/pwa/icon-96.png',
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
            padding: 15px;
            border-radius: 8px;
            font-size: 11px;
            font-family: monospace;
            z-index: 9999;
            max-width: 350px;
            word-wrap: break-word;
            border: 2px solid #dc693c;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            line-height: 1.4;
        `;
        
        const info = this.getAppInfo();
        debugInfo.innerHTML = `
            <strong>🔧 PWA Debug Info (localhost):</strong><br>
            Installiert: ${info.isInstalled}<br>
            Standalone: ${info.isStandalone}<br>
            Online: ${info.isOnline}<br>
            DeferredPrompt: ${this.deferredPrompt ? 'JA' : 'NEIN'}<br>
            ServiceWorker: ${'serviceWorker' in navigator ? 'JA' : 'NEIN'}<br>
            Manifest: ${document.querySelector('link[rel="manifest"]') ? 'JA' : 'NEIN'}<br>
            <br>
            <strong>Service Worker Status:</strong><br>
            <span id="sw-status">Prüfe...</span><br>
            <br>
            <strong>Tests:</strong><br>
            <button onclick="window.gourmenPWA.testServiceWorker()" style="margin: 2px; padding: 4px 8px; background: #17a2b8; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">SW Test</button>
            <button onclick="window.gourmenPWA.forceRegisterSW()" style="margin: 2px; padding: 4px 8px; background: #6f42c1; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Force Reg</button>
            <button onclick="window.gourmenPWA.cleanupAllSW()" style="margin: 2px; padding: 4px 8px; background: #dc3545; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Cleanup</button>
            <button onclick="window.gourmenPWA.diagnoseSW()" style="margin: 2px; padding: 4px 8px; background: #20c997; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Diagnose</button>
            <button onclick="window.gourmenPWA.simpleTest()" style="margin: 2px; padding: 4px 8px; background: #e83e8c; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Test</button>
            <button onclick="window.gourmenPWA.registerSW()" style="margin: 2px; padding: 4px 8px; background: #28a745; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Reg SW</button>
            <button onclick="window.gourmenPWA.toggleAutoUpdate()" style="margin: 2px; padding: 4px 8px; background: #6c757d; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Auto Off</button>
            <button onclick="window.gourmenPWA.stopAllUpdates()" style="margin: 2px; padding: 4px 8px; background: #dc3545; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Stop All</button>
            <button onclick="window.gourmenPWA.updateDebugServiceWorkerStatus()" style="margin: 2px; padding: 4px 8px; background: #fd7e14; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Refresh</button>
            <button onclick="window.gourmenPWA.manualInstall()" style="margin: 2px; padding: 4px 8px; background: #28a745; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Install</button>
            <button onclick="this.parentElement.remove()" style="margin: 2px; padding: 4px 8px; background: #dc693c; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 10px;">Schließen</button>
        `;
        
        document.body.appendChild(debugInfo);
        
        // Service Worker Status aktualisieren
        this.updateDebugServiceWorkerStatus();
        
        // Automatische Aktualisierung alle 10 Sekunden (weiter reduziert)
        this.debugUpdateInterval = setInterval(() => {
            this.updateDebugServiceWorkerStatus();
        }, 10000);
    }

    async updateDebugServiceWorkerStatus() {
        const statusSpan = document.getElementById('sw-status');
        if (!statusSpan) {
            console.log('⚠️ Debug Status Span nicht gefunden');
            return;
        }

        if (!('serviceWorker' in navigator)) {
            statusSpan.textContent = 'Nicht unterstützt';
            statusSpan.style.color = '#dc3545';
            return;
        }

        try {
            // 1) Versuche alle Registrierungen zu holen
            let registrations = [];
            try {
                registrations = await navigator.serviceWorker.getRegistrations();
                console.log('🔍 Gefundene Service Worker Registrierungen:', registrations.length);
            } catch (e) {
                console.log('ℹ️ getRegistrations() nicht verfügbar/fehlgeschlagen:', e?.message || e);
            }

            let mainRegistration = null;

            if (registrations && registrations.length > 0) {
                // Bevorzugt Root-Scope
                mainRegistration = registrations.find(reg => reg.scope === window.location.origin + '/') || registrations[0];
            }

            // 2) Fallback: einzelne Registration anfragen
            if (!mainRegistration) {
                try {
                    const single = await navigator.serviceWorker.getRegistration();
                    if (single) {
                        console.log('ℹ️ Registration via getRegistration() gefunden:', single.scope);
                        mainRegistration = single;
                    }
                } catch (e) {
                    console.log('ℹ️ getRegistration() fehlgeschlagen:', e?.message || e);
                }
            }

            // 3) Fallback: ready abwarten
            if (!mainRegistration) {
                try {
                    const readyReg = await navigator.serviceWorker.ready;
                    if (readyReg) {
                        console.log('ℹ️ Registration via ready gefunden:', readyReg.scope);
                        mainRegistration = readyReg;
                    }
                } catch (e) {
                    console.log('ℹ️ navigator.serviceWorker.ready fehlgeschlagen:', e?.message || e);
                }
            }

            if (mainRegistration) {
                statusSpan.textContent = `Registriert (${mainRegistration.scope})`;
                statusSpan.style.color = '#28a745';
                console.log('✅ Service Worker Status aktualisiert: Registriert', mainRegistration.scope);
                this.serviceWorkerRegistration = mainRegistration;
            } else {
                statusSpan.textContent = 'Nicht registriert';
                statusSpan.style.color = '#ffc107';
                console.log('⚠️ Service Worker Status aktualisiert: Nicht registriert');
            }
        } catch (error) {
            statusSpan.textContent = `Fehler: ${error.message}`;
            statusSpan.style.color = '#dc3545';
            console.error('❌ Fehler beim Aktualisieren des Service Worker Status:', error);
        }
    }

    async testServiceWorker() {
        console.log('🧪 Service Worker Test gestartet...');
        
        try {
            // Prüfe ob Service Worker unterstützt wird
            if (!('serviceWorker' in navigator)) {
                this.showToast('❌ Service Worker nicht unterstützt', 'error');
                return;
            }

            // Prüfe ob bereits eine Registration existiert
            const existingRegistration = await navigator.serviceWorker.getRegistration();
            if (existingRegistration) {
                console.log('✅ Service Worker bereits registriert:', existingRegistration);
                this.showToast('✅ Service Worker ist bereits registriert', 'success');
                this.updateDebugServiceWorkerStatus();
                return;
            }

            // Versuche neue Registrierung
            console.log('🔄 Versuche Service Worker Registrierung...');
            const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
            console.log('✅ Service Worker erfolgreich registriert:', registration);
            this.showToast('✅ Service Worker erfolgreich registriert', 'success');
            
            // Speichere Registration
            this.serviceWorkerRegistration = registration;
            
        } catch (error) {
            console.error('❌ Service Worker Test fehlgeschlagen:', error);
            
            // Detaillierte Fehleranalyse
            let errorMessage = 'Service Worker Registrierung fehlgeschlagen: ';
            if (error.message.includes('Failed to register')) {
                errorMessage += 'Service Worker Datei nicht gefunden oder ungültig';
            } else if (error.message.includes('network')) {
                errorMessage += 'Netzwerkfehler - prüfe ob /static/sw.js erreichbar ist';
            } else if (error.message.includes('security')) {
                errorMessage += 'Sicherheitsfehler - HTTPS oder localhost erforderlich';
            } else {
                errorMessage += error.message;
            }
            
            this.showToast(errorMessage, 'error');
            
            // Debug-Info in Konsole
            console.log('🔧 Service Worker Debug-Info:');
            console.log('- URL:', window.location.href);
            console.log('- Protocol:', window.location.protocol);
            console.log('- Hostname:', window.location.hostname);
            console.log('- Service Worker Path:', '/static/sw.js');
            console.log('- Full Error:', error);
        }
        
        // Debug-Status aktualisieren
        this.updateDebugServiceWorkerStatus();
    }

    async forceRegisterSW() {
        console.log('🔄 Force Service Worker Registration...');
        
        try {
            // Entferne alle bestehenden Service Worker
            const registrations = await navigator.serviceWorker.getRegistrations();
            for (let registration of registrations) {
                console.log('🗑️ Entferne bestehende Service Worker Registration:', registration.scope);
                await registration.unregister();
            }
            
            // Warte kurz
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Registriere neuen Service Worker
            console.log('🔄 Registriere neuen Service Worker...');
            const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
            console.log('✅ Service Worker erfolgreich registriert:', registration);
            
            this.serviceWorkerRegistration = registration;
            this.showToast('✅ Service Worker erfolgreich neu registriert', 'success');
            
            // Debug-Status aktualisieren
            this.updateDebugServiceWorkerStatus();
            
        } catch (error) {
            console.error('❌ Force Registration fehlgeschlagen:', error);
            this.showToast('❌ Force Registration fehlgeschlagen: ' + error.message, 'error');
        }
    }

    async cleanupAllSW() {
        console.log('🧹 Cleanup aller Service Worker...');
        
        try {
            // Entferne alle Service Worker Registrierungen
            const registrations = await navigator.serviceWorker.getRegistrations();
            console.log(`🗑️ Entferne ${registrations.length} Service Worker Registrierungen...`);
            
            for (let registration of registrations) {
                console.log('🗑️ Entferne:', registration.scope);
                await registration.unregister();
            }
            
            // Lösche alle Caches
            const cacheNames = await caches.keys();
            console.log(`🗑️ Lösche ${cacheNames.length} Caches...`);
            
            for (let cacheName of cacheNames) {
                console.log('🗑️ Lösche Cache:', cacheName);
                await caches.delete(cacheName);
            }
            
            this.serviceWorkerRegistration = null;
            this.showToast('✅ Alle Service Worker und Caches bereinigt', 'success');
            
            // Debug-Status aktualisieren
            this.updateDebugServiceWorkerStatus();
            
        } catch (error) {
            console.error('❌ Cleanup fehlgeschlagen:', error);
            this.showToast('❌ Cleanup fehlgeschlagen: ' + error.message, 'error');
        }
    }

    async diagnoseSW() {
        console.log('🔍 Service Worker Diagnose gestartet...');
        
        try {
            // Sammle alle verfügbaren Informationen
            const diagnosis = {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                protocol: window.location.protocol,
                hostname: window.location.hostname,
                userAgent: navigator.userAgent.substring(0, 100),
                serviceWorkerSupported: 'serviceWorker' in navigator,
                registrations: [],
                caches: [],
                controller: null,
                ready: null,
                errors: []
            };
            
            console.log('📋 Basis-Informationen gesammelt:', diagnosis);
            
            // Prüfe Service Worker Unterstützung
            if (!('serviceWorker' in navigator)) {
                diagnosis.error = 'Service Worker nicht unterstützt';
                console.log('❌ Service Worker nicht unterstützt');
                this.showDiagnosisResult(diagnosis);
                return;
            }
            
            console.log('✅ Service Worker wird unterstützt');
            
            // Prüfe alle Registrierungen
            console.log('🔍 Prüfe Service Worker Registrierungen...');
            try {
                const registrations = await navigator.serviceWorker.getRegistrations();
                console.log('📋 Gefundene Registrierungen:', registrations.length);
                
                diagnosis.registrations = registrations.map(reg => {
                    const regInfo = {
                        scope: reg.scope,
                        active: reg.active ? reg.active.state : 'none',
                        installing: reg.installing ? reg.installing.state : 'none',
                        waiting: reg.waiting ? reg.waiting.state : 'none',
                        updateViaCache: reg.updateViaCache
                    };
                    console.log('📋 Registration Details:', regInfo);
                    return regInfo;
                });
            } catch (error) {
                console.error('❌ Fehler beim Abrufen der Registrierungen:', error);
                diagnosis.registrationError = error.message;
                diagnosis.errors.push('Registration Error: ' + error.message);
            }
            
            // Prüfe Controller
            console.log('🔍 Prüfe Service Worker Controller...');
            try {
                if (navigator.serviceWorker.controller) {
                    diagnosis.controller = {
                        state: navigator.serviceWorker.controller.state,
                        scriptURL: navigator.serviceWorker.controller.scriptURL
                    };
                    console.log('✅ Controller gefunden:', diagnosis.controller);
                } else {
                    console.log('⚠️ Kein Controller gefunden');
                    diagnosis.controller = null;
                }
            } catch (error) {
                console.error('❌ Fehler beim Prüfen des Controllers:', error);
                diagnosis.controllerError = error.message;
                diagnosis.errors.push('Controller Error: ' + error.message);
            }
            
            // Prüfe Service Worker Ready
            console.log('🔍 Prüfe Service Worker Ready...');
            try {
                const registration = await navigator.serviceWorker.ready;
                diagnosis.ready = {
                    scope: registration.scope,
                    active: registration.active ? registration.active.state : 'none'
                };
                console.log('✅ Service Worker Ready:', diagnosis.ready);
            } catch (error) {
                console.error('❌ Fehler beim Prüfen von Service Worker Ready:', error);
                diagnosis.readyError = error.message;
                diagnosis.errors.push('Ready Error: ' + error.message);
            }
            
            // Prüfe Caches
            console.log('🔍 Prüfe Caches...');
            try {
                const cacheNames = await caches.keys();
                diagnosis.caches = cacheNames;
                console.log('✅ Caches gefunden:', cacheNames);
            } catch (error) {
                console.error('❌ Fehler beim Prüfen der Caches:', error);
                diagnosis.cacheError = error.message;
                diagnosis.errors.push('Cache Error: ' + error.message);
            }
            
            console.log('📋 Diagnose abgeschlossen:', diagnosis);
            
            // Zeige Ergebnis
            this.showDiagnosisResult(diagnosis);
            
        } catch (error) {
            console.error('❌ Diagnose fehlgeschlagen:', error);
            console.error('❌ Error Stack:', error.stack);
            this.showToast('❌ Diagnose fehlgeschlagen: ' + error.message, 'error');
        }
    }

    showDiagnosisResult(diagnosis) {
        console.log('🔍 Service Worker Diagnose Ergebnis:', diagnosis);
        
        try {
            // Erstelle detaillierte Diagnose-Nachricht
            let message = '🔍 Service Worker Diagnose:\n\n';
            message += `URL: ${diagnosis.url}\n`;
            message += `Protocol: ${diagnosis.protocol}\n`;
            message += `Service Worker Support: ${diagnosis.serviceWorkerSupported ? 'JA' : 'NEIN'}\n\n`;
            
            message += `Registrierungen (${diagnosis.registrations.length}):\n`;
            if (diagnosis.registrations.length > 0) {
                diagnosis.registrations.forEach((reg, index) => {
                    message += `  ${index + 1}. Scope: ${reg.scope}\n`;
                    message += `     Active: ${reg.active}\n`;
                    message += `     Installing: ${reg.installing}\n`;
                    message += `     Waiting: ${reg.waiting}\n`;
                });
            } else {
                message += `  KEINE REGISTRIERUNGEN GEFUNDEN\n`;
            }
            
            if (diagnosis.controller) {
                message += `\nController:\n`;
                message += `  State: ${diagnosis.controller.state}\n`;
                message += `  Script: ${diagnosis.controller.scriptURL}\n`;
            } else {
                message += `\nController: KEINER\n`;
            }
            
            if (diagnosis.ready) {
                message += `\nReady:\n`;
                message += `  Scope: ${diagnosis.ready.scope}\n`;
                message += `  Active: ${diagnosis.ready.active}\n`;
            } else {
                message += `\nReady: FEHLER\n`;
            }
            
            message += `\nCaches (${diagnosis.caches.length}): ${diagnosis.caches.join(', ')}\n`;
            
            if (diagnosis.error) {
                message += `\nFehler: ${diagnosis.error}\n`;
            }
            
            if (diagnosis.errors && diagnosis.errors.length > 0) {
                message += `\nWeitere Fehler:\n`;
                diagnosis.errors.forEach(error => {
                    message += `  - ${error}\n`;
                });
            }
            
            console.log('📋 Diagnose-Nachricht erstellt:', message);
            
            // Zeige als Toast (längere Anzeigedauer)
            this.showToast(message, 'info', 15000);
            
            // Zeige auch in Konsole
            console.log('📋 Vollständige Diagnose:', diagnosis);
            
        } catch (error) {
            console.error('❌ Fehler beim Anzeigen der Diagnose:', error);
            this.showToast('❌ Fehler beim Anzeigen der Diagnose: ' + error.message, 'error');
        }
    }

    simpleTest() {
        console.log('🧪 Einfacher Test gestartet...');
        this.showToast('🧪 Test funktioniert!', 'success');
        
        // Teste Service Worker Unterstützung
        if ('serviceWorker' in navigator) {
            console.log('✅ Service Worker wird unterstützt');
            this.showToast('✅ Service Worker wird unterstützt', 'success');
        } else {
            console.log('❌ Service Worker wird nicht unterstützt');
            this.showToast('❌ Service Worker wird nicht unterstützt', 'error');
        }
        
        // Teste einfache Service Worker Abfrage
        navigator.serviceWorker.getRegistrations().then(registrations => {
            console.log('📋 Service Worker Registrierungen:', registrations.length);
            this.showToast(`📋 ${registrations.length} Service Worker gefunden`, 'info');
        }).catch(error => {
            console.error('❌ Fehler beim Abrufen der Registrierungen:', error);
            this.showToast('❌ Fehler beim Abrufen der Registrierungen: ' + error.message, 'error');
        });
    }

    async registerSW() {
        console.log('🔄 Manuelle Service Worker Registrierung...');
        
        try {
            if (!('serviceWorker' in navigator)) {
                this.showToast('❌ Service Worker nicht unterstützt', 'error');
                return;
            }
            
            // Prüfe ob bereits registriert
            const existingRegistrations = await navigator.serviceWorker.getRegistrations();
            if (existingRegistrations.length > 0) {
                console.log('✅ Service Worker bereits registriert:', existingRegistrations[0]);
                this.showToast('✅ Service Worker bereits registriert', 'success');
                this.serviceWorkerRegistration = existingRegistrations[0];
                return;
            }
            
            // Registriere neuen Service Worker
            console.log('🔄 Registriere neuen Service Worker...');
            const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
            console.log('✅ Service Worker erfolgreich registriert:', registration);
            
            this.serviceWorkerRegistration = registration;
            this.setupServiceWorkerEvents(registration);
            this.showToast('✅ Service Worker erfolgreich registriert', 'success');
            
            // Aktualisiere Debug-Status
            this.updateDebugServiceWorkerStatus();
            
        } catch (error) {
            console.error('❌ Service Worker Registrierung fehlgeschlagen:', error);
            this.showToast('❌ Service Worker Registrierung fehlgeschlagen: ' + error.message, 'error');
        }
    }

    toggleAutoUpdate() {
        if (this.debugUpdateInterval) {
            clearInterval(this.debugUpdateInterval);
            this.debugUpdateInterval = null;
            this.showToast('✅ Automatische Aktualisierung gestoppt', 'success');
            console.log('🛑 Automatische Debug-Status-Aktualisierung gestoppt');
        } else {
            this.debugUpdateInterval = setInterval(() => {
                this.updateDebugServiceWorkerStatus();
            }, 5000);
            this.showToast('✅ Automatische Aktualisierung gestartet (alle 5s)', 'success');
            console.log('▶️ Automatische Debug-Status-Aktualisierung gestartet');
        }
    }

    stopAllUpdates() {
        console.log('🛑 Stoppe alle automatischen Updates...');
        
        // Stoppe Debug-Update-Interval
        if (this.debugUpdateInterval) {
            clearInterval(this.debugUpdateInterval);
            this.debugUpdateInterval = null;
            console.log('🛑 Debug-Update-Interval gestoppt');
        }
        
        // Stoppe automatische Update-Checks
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
            console.log('🛑 Auto-Update-Interval gestoppt');
        }
        
        this.showToast('🛑 Alle automatischen Updates gestoppt', 'success');
        console.log('✅ Alle automatischen Updates gestoppt');
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

// PWA initialisieren
// CSS wurde nach static/css/pwa.css ausgelagert
let pwa;
document.addEventListener('DOMContentLoaded', () => {
    pwa = new PWA();
    
    // Debug-Info in der Konsole
    console.log('🚀 Gourmen PWA initialisiert');
    console.log('App Info:', pwa.getAppInfo());
    
    // Globale PWA-Referenz für Debugging und andere Skripte
    window.gourmenPWA = pwa;
    
    // Globale Service Worker-Referenz für app.js
    window.gourmenServiceWorker = pwa.serviceWorkerRegistration;
    
    // Manueller Test des Install-Prompts (für Debugging)
    setTimeout(() => {
        console.log('🚀 PWA Status nach 2 Sekunden:', {
            deferredPrompt: !!pwa.deferredPrompt,
            isInstalled: pwa.isInstalled,
            isOnline: pwa.isOnline
        });
    }, 2000);
});

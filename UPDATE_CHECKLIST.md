# Gourmen PWA Update Checklist

## ⚠️ WICHTIG: Bei JEDER Änderung an der App!

### 1️⃣ **Cache-Version in Service Worker erhöhen**
📁 Datei: `static/sw.js`

```javascript
// IMMER diese Zeilen ändern:
const CACHE_NAME = 'gourmen-v1.3.6';        // ← Versionsnummer erhöhen!
const STATIC_CACHE = 'gourmen-static-v1.3.6';
const DYNAMIC_CACHE = 'gourmen-dynamic-v1.3.6';
```

**Warum?** 
- Browser erkennt Änderung nur wenn sw.js BINÄR anders ist
- Neue Cache-Namen zwingen alte Caches zum Löschen

---

### 2️⃣ **Script-Versionen in base.html aktualisieren**
📁 Datei: `templates/base.html`

```html
<!-- PWA Scripts -->
<script src="{{ url_for('static', filename='js/pwa.js') }}?v=1.3.6" defer></script>
<script src="{{ url_for('static', filename='js/app.js') }}?v=1.3.6" defer></script>
```

**Warum?**
- Verhindert Browser-Caching der alten Scripts
- Garantiert dass neue Version geladen wird

---

### 3️⃣ **App-Version in pwa.js aktualisieren (optional)**
📁 Datei: `static/js/pwa.js`

```javascript
updateAppInfo() {
    const versionSpan = document.getElementById('app-version');
    if (versionSpan) {
        versionSpan.textContent = '1.3.6';  // ← Hier auch ändern
    }
}
```

---

## 📋 **Wann muss ich die Version ändern?**

### ✅ **IMMER bei diesen Änderungen:**
- [ ] CSS-Änderungen (`static/css/*.css`)
- [ ] JavaScript-Änderungen (`static/js/*.js`)
- [ ] Template-Änderungen (HTML)
- [ ] Neue Features
- [ ] Bug-Fixes
- [ ] Icon-Änderungen
- [ ] Manifest-Änderungen

### ⚡ **OPTIONAL bei:**
- [ ] Reine Backend-Änderungen (Python-Code)
- [ ] Datenbank-Änderungen
- [ ] API-Änderungen (wenn Frontend gleich bleibt)

**ABER:** Auch bei Backend-Änderungen empfohlen, um sicher zu gehen!

---

## 🔄 **Was passiert nach dem Deployment?**

### Automatischer Update-Flow:

1. **Benutzer öffnet die App** (innerhalb von 24h)
   - Browser prüft automatisch auf Updates
   - Service Worker erkennt neue Version

2. **PWA zeigt Update-Button**
   ```
   🔄 Update verfügbar - Jetzt installieren
   ```

3. **Benutzer klickt auf Update**
   - Neue Version wird aktiviert
   - Alte Caches werden gelöscht
   - Seite lädt neu mit neuer Version

4. **Falls Benutzer nicht klickt:**
   - Beim nächsten kompletten Page-Reload
   - Oder nach 5 Minuten automatisch (je nach Config)

---

## 🎯 **Versionierungs-Schema**

### Empfehlung: Semantic Versioning

```
v1.3.5
│ │ │
│ │ └─ PATCH: Bug-Fixes, kleine Änderungen
│ └─── MINOR: Neue Features (abwärtskompatibel)
└───── MAJOR: Breaking Changes
```

### Beispiele:
- CSS-Fix: `v1.3.5` → `v1.3.6`
- Neues Feature: `v1.3.6` → `v1.4.0`
- Große Änderung: `v1.4.0` → `v2.0.0`

---

## 🧪 **Testing vor Deployment**

### Lokales Testing:

1. **Änderungen machen**
2. **Version erhöhen** (alle 3 Stellen)
3. **Server neu starten**
4. **Browser öffnen** (DevTools → Application → Service Workers)
5. **"Update on reload"** aktivieren
6. **Seite neu laden** → Neue Version sollte aktiv sein

### Production Testing:

1. **Deployment durchführen**
2. **DevTools öffnen** (F12)
3. **Console checken:**
   ```
   ✅ Service Worker Update gefunden!
   🔄 Neuer Service Worker installiert
   ```
4. **Application Tab → Service Workers:**
   - Sollte "waiting to activate" zeigen
5. **Update-Button klicken** oder Seite neu laden

---

## ⚠️ **Häufige Probleme & Lösungen**

### Problem: "Update wird nicht erkannt"
**Lösung:** 
- Cache-Version in `sw.js` erhöhen
- Hard-Reload: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)

### Problem: "Alte Version bleibt aktiv"
**Lösung:**
- DevTools → Application → Clear Storage → "Clear site data"
- Oder: Service Worker manuell unregister

### Problem: "Push-Notifications funktionieren nicht mehr"
**Lösung:**
- Nach Update Notification-Berechtigung neu prüfen
- Push-Subscription in DB checken

---

## 📊 **Update-Monitoring**

### In der Console prüfen:

```javascript
// Aktuelle Service Worker Version
navigator.serviceWorker.getRegistration().then(reg => {
    console.log('SW Scope:', reg.scope);
    console.log('SW State:', reg.active?.state);
});

// Cache-Namen checken
caches.keys().then(keys => {
    console.log('Aktive Caches:', keys);
});
```

---

## 🚀 **Quick-Update-Script**

Erstelle ein Script für schnelle Updates:

```bash
# update-version.sh
#!/bin/bash

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./update-version.sh 1.3.6"
    exit 1
fi

# Update sw.js
sed -i "s/gourmen-v[0-9.]\+/gourmen-v$VERSION/g" static/sw.js

# Update base.html
sed -i "s/\?v=[0-9.]\+/?v=$VERSION/g" templates/base.html

# Update pwa.js
sed -i "s/textContent = '[0-9.]\+'/textContent = '$VERSION'/g" static/js/pwa.js

echo "✅ Version updated to $VERSION"
```

**Usage:**
```bash
./update-version.sh 1.3.6
```

---

## 📝 **Changelog führen**

Empfohlen: `CHANGELOG.md` pflegen

```markdown
# Changelog

## [1.3.6] - 2025-10-08
### Fixed
- Service Worker Cache-Path korrigiert
- Push-Notification Initialisierung optimiert

### Changed
- Service Worker Registrierung vereinfacht

## [1.3.5] - 2025-10-08
### Added
- Neue Event-Features
```

---

## ✅ **Finale Checkliste vor Deployment**

- [ ] Cache-Version in `sw.js` erhöht
- [ ] Script-Versionen in `base.html` erhöht
- [ ] App-Version in `pwa.js` erhöht
- [ ] Lokales Testing durchgeführt
- [ ] Git Commit mit Versionsnummer
- [ ] Deployment durchgeführt
- [ ] Production Testing durchgeführt
- [ ] Changelog aktualisiert

---

**💡 Tipp:** Bei Zweifeln lieber Version erhöhen! Es schadet nie, aber vergessene Updates können zu alten Versionen bei Nutzern führen.


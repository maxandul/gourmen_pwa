# 🎨 PWA ASSETS SPEZIFIKATION

Diese Dokumentation beschreibt alle benötigten Assets für die Gourmen PWA nach **State-of-the-Art 2025** Standards.

---

## 📁 ÜBERSICHT - Was ist wo?

```
static/img/
├── pwa/                    # PWA & Browser Icons
│   ├── icon-16.png         ✅ Behalten - Browser Favicon
│   ├── icon-32.png         ✅ Behalten - Browser Favicon
│   ├── icon-192.png        ✅ Behalten - PWA Icon + Android
│   ├── icon-512.png        ✅ Behalten - PWA Icon + Android
│   ├── icon-192-maskable.png  ⚠️ NEU ERSTELLEN - Android Adaptive Icon
│   ├── icon-512-maskable.png  ⚠️ NEU ERSTELLEN - Android Adaptive Icon
│   ├── apple-touch-icon.png   ⚠️ NEU ERSTELLEN - iOS Home Screen (180x180)
│   ├── badge-72.png        ✅ Behalten - Android Status Bar Icon
│   └── badge-96.png        ✅ Behalten - Notification Badge
│
├── ui/                     # User Interface Assets
│   └── splash-generic.png  ⚠️ NEU ERSTELLEN - Generischer Splash Screen
│
├── og-image.png            ⚠️ NEU ERSTELLEN - Social Media Preview
└── favicon.ico             ✅ Behalten - Browser Favicon (Root)
```

---

## 🆕 NEU ZU ERSTELLEN

Die folgenden Assets müssen mit dem **neuen V2 Design System** erstellt werden.

---

### 1. 📱 MASKABLE ICONS (Android Adaptive Icons)

**Problem:** Aktuell werden Logo-Teile auf Android abgeschnitten!

**Lösung:** 40% Safe Zone einhalten

#### **icon-192-maskable.png**
- **Größe:** 192x192 px
- **Format:** PNG
- **Hintergrund:** Vollflächig, **KEINE Transparenz**
- **Farbe:** Navy Gradient `linear-gradient(135deg, #1b232e, #354e5e)`
- **Logo:** Zentriert, aber **maximal 40% der Größe vom Zentrum** (Safe Zone!)
- **Safe Zone:** Logo muss innerhalb eines Kreises von 76px Radius bleiben (40% von 192px)

```
┌─────────────────────────────┐
│                             │  ← Navy Gradient Hintergrund
│   ┌─────────────────────┐   │  ← Wird evtl. abgeschnitten
│   │                     │   │
│   │   ┌───────────┐     │   │
│   │   │           │     │   │  ← Safe Zone (40%)
│   │   │   LOGO    │     │   │     Logo hier platzieren!
│   │   │           │     │   │
│   │   └───────────┘     │   │
│   │                     │   │
│   └─────────────────────┘   │
│                             │
└─────────────────────────────┘
    192x192 px
```

**Wichtig:**
- Logo muss **kleiner** sein als aktuell!
- Teste mit: [maskable.app](https://maskable.app)
- Exportiere mit hoher Qualität (keine Kompression)

#### **icon-512-maskable.png**
- **Identisch wie 192px**, nur größer: 512x512 px
- **Safe Zone:** Logo innerhalb 204px Radius (40% von 512px)

---

### 2. 🍎 APPLE TOUCH ICON

#### **apple-touch-icon.png**
- **Größe:** 180x180 px (iOS Standard)
- **Format:** PNG
- **Hintergrund:** Navy Gradient ODER Transparent (beides OK)
- **Logo:** Zentriert, kann näher am Rand sein als maskable (iOS schneidet anders)
- **Ecken:** iOS fügt automatisch runde Ecken hinzu (musst du nicht machen)

**Design:**
```
┌───────────────────┐
│                   │
│                   │
│      GOURMEN      │  Logo zentriert
│        LOGO       │  Kann größer sein als maskable
│                   │
│                   │
└───────────────────┘
   180x180 px
```

---

### 3. 🎬 GENERISCHER SPLASH SCREEN

#### **static/img/ui/splash-generic.png**
- **Größe:** 1170x2532 px (iPhone 14 Pro Max - größter Screen)
- **Format:** PNG
- **Hintergrund:** Navy Gradient `linear-gradient(135deg, #1b232e, #354e5e)`
- **Logo:** Zentriert, ca. 300-400px breit
- **Optional:** "GOURMEN" Text darunter oder "Seit 2021" Claim

**Layout:**
```
┌──────────────────┐
│                  │
│                  │
│                  │  ← Navy Gradient Hintergrund
│                  │
│                  │
│                  │
│     ┌──────┐     │
│     │ LOGO │     │  ← Logo zentriert
│     └──────┘     │
│                  │
│     GOURMEN      │  ← Optional: Text
│   Seit 2021      │
│                  │
│                  │
│                  │
│                  │
│                  │
└──────────────────┘
  1170x2532 px
```

**Warum so groß?**  
Browser/iOS skaliert automatisch auf kleinere Bildschirme runter.  
Ein großes Bild funktioniert für alle!

---

### 4. 🌐 OPEN GRAPH IMAGE (Social Sharing)

#### **static/img/og-image.png**
- **Größe:** 1200x630 px (Standard für Facebook/WhatsApp/LinkedIn)
- **Format:** PNG oder JPG
- **Hintergrund:** Navy Gradient `linear-gradient(135deg, #1b232e, #354e5e)`
- **Logo:** Links oder zentriert platziert
- **Text:** "GOURMEN - Seit 2021" oder Claim
- **Optional:** "Gourmen-Verein Webapp"

**Layout Vorschlag:**
```
┌────────────────────────────────────────────┐
│                                            │
│   ┌──────┐                                 │
│   │ LOGO │    GOURMEN                      │  Navy Gradient
│   └──────┘    Gourmen-Verein Webapp       │  Hintergrund
│               Seit 2021                    │
│                                            │
└────────────────────────────────────────────┘
                1200x630 px
```

**Wo wird das verwendet?**
- WhatsApp Link-Preview
- Facebook Share
- LinkedIn Share
- Twitter Card
- Slack, Discord, etc.

---

## ✅ BEHALTEN (Nicht ändern)

Diese Dateien sind OK und müssen **nicht** neu erstellt werden:

### **Browser Favicons**
```
✅ favicon.ico             (Root, 16x16 + 32x32 Multi-Icon)
✅ icon-16.png            (Browser Tab)
✅ icon-32.png            (Browser Tab)
```

### **Standard PWA Icons**
```
✅ icon-192.png           (PWA + Android)
✅ icon-512.png           (PWA + Android)
```

**Optional:** Du kannst diese auch neu mit V2 Design erstellen, aber **nicht zwingend**.  
Die aktuellen Logos sind neutral genug.

### **Notification Badges**
```
✅ badge-72.png           (Android Status Bar - kleines Icon)
✅ badge-96.png           (Notification Badge)
```

**Verwendung:**
- `badge-72.png`: Kleines Icon in Android Status Bar (neben Akku, Uhrzeit)
- `badge-96.png`: Icon in der Notification selbst

**Design:** Aktuell OK, können aber auch auf V2 Farben angepasst werden.

---

## 🎨 DESIGN SYSTEM V2 - Farben

Alle neuen Assets sollen diese Farben verwenden:

### **Logo-Farben (aus bestehendem Logo):**
```css
Navy Primary:    #1b232e   (Dunkelster Navy)
Navy Secondary:  #354e5e   (Logo-Hauptfarbe)
Türkis:          #73c8a8   ("Since 2021" Text)
Orange:          #dc693c   ("GOURMEN" Text)
```

### **Gradient für Hintergründe:**
```css
background: linear-gradient(135deg, #1b232e, #354e5e);
```

### **Light Mode Alternative:**
Falls du Light Mode Versionen brauchst:
```css
Light Background: #f5f7fa
Light Primary:    #667a91
```

---

## 🛠️ TOOLS & EMPFEHLUNGEN

### **Design-Tools:**
- **Figma** (empfohlen, kostenlos): [figma.com](https://www.figma.com)
- **Photoshop** (professionell)
- **GIMP** (kostenlos, Open Source)
- **Canva** (einfach, online)

### **PWA Icon Generator:**
- **Maskable.app**: [maskable.app](https://maskable.app) - Teste Maskable Icons!
- **RealFaviconGenerator**: [realfavicongenerator.net](https://realfavicongenerator.net)
- **PWA Asset Generator**: [github.com/elegantapp/pwa-asset-generator](https://github.com/elegantapp/pwa-asset-generator)

### **Safe Zone Tester:**
Verwende [maskable.app](https://maskable.app) um zu prüfen ob dein Logo in der Safe Zone ist!

---

## 📝 CHECKLISTE - Assets Erstellung

### **Phase 1: Vorbereitung**
- [ ] Logo als hochauflösendes PNG oder SVG exportieren
- [ ] Design-Tool auswählen (Figma empfohlen)
- [ ] V2 Farben (#1b232e, #354e5e) bereit haben

### **Phase 2: Maskable Icons** (WICHTIG!)
- [ ] `icon-192-maskable.png` erstellen (40% Safe Zone beachten!)
- [ ] `icon-512-maskable.png` erstellen
- [ ] Auf [maskable.app](https://maskable.app) testen
- [ ] Ggf. Logo kleiner machen falls abgeschnitten

### **Phase 3: iOS & Splash**
- [ ] `apple-touch-icon.png` (180x180) erstellen
- [ ] `splash-generic.png` (1170x2532) erstellen

### **Phase 4: Social Media**
- [ ] `og-image.png` (1200x630) erstellen

### **Phase 5: Optional - Refresh**
- [ ] `icon-192.png` mit V2 Design aktualisieren
- [ ] `icon-512.png` mit V2 Design aktualisieren
- [ ] `badge-72.png` mit V2 Farben anpassen
- [ ] `badge-96.png` mit V2 Farben anpassen

### **Phase 6: Testing**
- [ ] Alle Icons in richtigen Ordnern gespeichert
- [ ] manifest.json aktualisiert (siehe unten)
- [ ] base.html Meta-Tags aktualisiert
- [ ] Auf echtem iOS Gerät testen (Home Screen Icon)
- [ ] Auf echtem Android Gerät testen (Adaptive Icon)
- [ ] WhatsApp Link-Preview testen (og-image)

---

## 📋 NACH DEM ERSTELLEN

### **1. Icons hochladen**
Kopiere die neuen Icons in die richtigen Verzeichnisse:
```
static/img/pwa/icon-192-maskable.png
static/img/pwa/icon-512-maskable.png
static/img/pwa/apple-touch-icon.png
static/img/ui/splash-generic.png
static/img/og-image.png
```

### **2. manifest.json aktualisieren**
```json
{
  "name": "Gourmen",
  "short_name": "Gourmen",
  "theme_color": "#1b232e",
  "background_color": "#1b232e",
  "icons": [
    {
      "src": "/static/img/pwa/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/img/pwa/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/img/pwa/icon-192-maskable.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/static/img/pwa/icon-512-maskable.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

### **3. base.html aktualisieren**
Splash Screen Referenzen anpassen:
```html
<!-- Generischer Splash Screen für alle iOS Geräte -->
<link rel="apple-touch-startup-image" 
      href="{{ url_for('static', filename='img/ui/splash-generic.png') }}">
```

Alte gerätespezifische Splash Screens entfernen!

---

## 💡 TIPPS

### **Maskable Icons:**
- **Wichtigste Elemente** (Gesicht, Hauptlogo) müssen in der Mitte sein
- **Text wie "GOURMEN"** sollte weiter innen sein
- Teste mit verschiedenen Formen: Kreis, Squircle, Rounded Square
- Notfalls: Logo komplett neu zentrie

rt und kompakt designen

### **Splash Screen:**
- Halte das Design **simpel** - wird nur kurz angezeigt
- Zu viele Details wirken auf kleinen Screens chaotisch
- Logo + ggf. 1 Zeile Text = perfekt

### **OG-Image:**
- Text muss **groß genug** sein (min. 40px Schriftgröße)
- Teste Preview auf WhatsApp Mobile
- Wird oft auf 500x260px verkleinert angezeigt

---

## ❓ FRAGEN?

Falls du Fragen hast oder Hilfe beim Erstellen brauchst:
1. Schaue die Beispiele in diesem Dokument an
2. Teste auf [maskable.app](https://maskable.app)
3. Nutze einen PWA Asset Generator als Startpunkt

**Wichtig:** Die **Maskable Icons** sind am kritischsten!  
Nimm dir dafür am meisten Zeit.

---

**Version:** 1.0  
**Erstellt:** 2025  
**Für:** Gourmen PWA V2 Design System


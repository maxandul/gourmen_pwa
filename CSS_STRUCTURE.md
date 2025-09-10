# CSS Struktur - base.css

## 📋 Hauptbereiche der CSS-Datei

### 1. **CSS Variables & Farbschema** (Zeile 1-58)
- CSS Variables für das neue Farbschema
- Dark Mode als Standard
- Hauptfarben: primary, secondary, accent, warm, mint
- Abgeleitete Farben: light/dark Varianten
- Status-Farben: success, warning, error, info
- Icon-Farben
- Schatten, Border Radius, Transitions

### 2. **Reset & Base Styles** (Zeile 59-74)
- CSS Reset
- Body-Styling
- Grundlegende Typography

### 3. **Layout & Container** (Zeile 75-127)
- Main Content
- Container für bessere Abstände
- Einheitliche Seiten-Struktur
- Page Header, Subtitle, Content, Actions

### 4. **Card System** (Zeile 128-148)
- Card mit orangem Streifen (wie bei Events)
- Card Hover-Effekte

### 5. **Typography** (Zeile 149-164)
- Überschriften (h1-h6)
- Paragraph-Styling

### 6. **Links** (Zeile 165-176)
- Link-Styling
- Hover-Effekte

### 7. **Button System** (Zeile 177-273)
- Base Button
- Button Variants (4 Hauptvarianten)
- Button Sizes

### 8. **Button Container System** (Zeile 274-337)
- Universal Button Containers
- Mobile Responsive

### 9. **Special Buttons** (Zeile 338-...)
- Header Buttons
- WhatsApp Brand Button
- Legacy Support

### 10. **Weitere Bereiche** (ab Zeile ...)
- Form Elements
- Navigation
- Flash Messages
- Toast Notifications
- PWA Components
- Media Queries
- etc.

## 🎨 **Aktuelles Farbschema**

### Hauptfarben:
- `--primary-color: #1b232e` (Dunkelblau)
- `--secondary-color: #354e5e` (Mittelblau)
- `--accent-color: #dc693c` (Orange)
- `--warm-color: #804539` (Warmes Braun)
- `--mint-color: #71c6a6` (Mint-Grün) ⭐ **NEU**

### Abgeleitete Farben:
- `--mint-light: #8dd4b8` (Helles Mint)
- `--mint-dark: #5ba68a` (Dunkles Mint)

### Status-Farben:
- `--success-color: #28a745` (Grün)
- `--warning-color: #ffc107` (Gelb)
- `--error-color: #dc3545` (Rot)
- `--info-color: #17a2b8` (Blau)

## 🔧 **Verwendete Farben in Komponenten**

### Toast-Meldungen:
- **Info:** Blau (#17a2b8)
- **Success:** Mint (#71c6a6) ⭐ **ANGEPASST**
- **Warning:** Gelb (#ffc107)
- **Error:** Rot (#dc3545)

### PWA-Buttons:
- **Install-Button:** Mint-Gradient (#71c6a6 → #5ba68a) ⭐ **ANGEPASST**
- **Notification-Button:** Blau-Mint-Gradient (#17a2b8 → #71c6a6) ⭐ **ANGEPASST**
- **Update-Button:** Gelb-Mint-Gradient (#ffc107 → #71c6a6) ⭐ **ANGEPASST**

## 📝 **Nächste Schritte**
1. CSS-Syntax-Fehler in Zeile 3145 korrigieren
2. Weitere Komponenten an neues Farbschema anpassen
3. Konsistenz überprüfen

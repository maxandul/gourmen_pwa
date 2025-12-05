# GOURMEN PWA - COMPONENT LIBRARY

> **Status:** In Planning  
> **Last Updated:** 2025-01-30  
> **Design System:** See `DESIGN_SYSTEM.md`

---

## 🏗️ ARCHITECTURE

### Atomic Design Structure

```
ATOMS (Basic Elements)
├── Button
├── Input
├── Label
├── Icon
├── Badge
└── Spinner

MOLECULES (Simple Combinations)
├── Form Field (Label + Input + Error)
├── Search Box (Input + Icon + Button)
├── Info Row (Label + Value)
├── Card Header (Title + Actions)
├── Nav Item (Icon + Label + Badge)
└── Alert / Info Banner

ORGANISMS (Complex Components)
├── Card
├── Modal / Dialog
├── Slide-Over Panel
├── Navigation Sidebar
├── Form Section
├── Data Table
└── Tabs

TEMPLATES (Page Layouts)
├── Dashboard Layout
├── Detail Layout
├── Form Layout
└── List Layout
```

### Naming Convention: BEM (English)

```css
.component-name { }                /* Block */
.component-name__element { }       /* Element */
.component-name--modifier { }      /* Modifier */
.component-name__element--modifier { }
```

---

## 🎨 BUTTON SYSTEM

### Variants (Reduced from 10 to 5)

```html
<!-- Primary: Main actions -->
<button class="btn btn--primary">
  <svg class="icon"><use href="#plus"/></svg>
  Neues Event
</button>

<!-- Success: Positive actions -->
<button class="btn btn--success">
  <svg class="icon"><use href="#check"/></svg>
  Zusagen
</button>

<!-- Danger: Destructive actions (Corporate Design: Orange-Red gradient) -->
<button class="btn btn--danger">
  <svg class="icon"><use href="#trash-2"/></svg>
  Löschen
</button>

<!-- Outline: Secondary actions -->
<button class="btn btn--outline">
  <svg class="icon"><use href="#x"/></svg>
  Abbrechen
</button>

<!-- BillBro: Special (Turquoise) -->
<button class="btn btn--billbro">
  <svg class="icon"><use href="#calculator"/></svg>
  BillBro
</button>
```

### Sizes

```html
<button class="btn btn--sm">Klein</button>
<button class="btn">Standard</button>
<button class="btn btn--lg">Groß</button>
```

### States

```html
<button class="btn btn--primary" disabled>Disabled</button>
<button class="btn btn--primary" aria-busy="true">
  <svg class="icon icon--spin"><use href="#loader"/></svg>
  Loading...
</button>
```

### CSS Implementation

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--btn-padding-y) var(--btn-padding-x);
  border: none;
  border-radius: var(--btn-radius);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: var(--btn-transition);
  min-height: 44px; /* Touch-friendly */
  text-decoration: none;
  
  /* Touch optimizations - no blue tap highlight! */
  -webkit-tap-highlight-color: transparent;
  -webkit-user-select: none;
  user-select: none;
}

.btn:focus-visible {
  outline: 2px solid var(--color-interactive-primary);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* Primary */
.btn--primary {
  background: linear-gradient(135deg, 
    var(--brand-primary-800), 
    var(--brand-primary-700));
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);  /* Better contrast on dark gradient */
  box-shadow: var(--shadow-sm);
}

.btn--primary:hover:not(:disabled) {
  background: linear-gradient(135deg, 
    var(--brand-primary-700), 
    var(--brand-primary-600));
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

/* Success */
.btn--success {
  background: linear-gradient(135deg, #2e7d32, #4caf50);
  color: white;
  box-shadow: var(--shadow-sm);
}

/* Danger (Corporate Design) */
.btn--danger {
  background: linear-gradient(135deg, 
    var(--brand-warm-700), 
    var(--brand-accent-600));
  color: white;
  box-shadow: var(--shadow-sm);
}

/* Outline */
.btn--outline {
  background: transparent;
  border: 2px solid var(--color-border-default);
  color: var(--color-text-primary);
}

/* BillBro */
.btn--billbro {
  background: linear-gradient(135deg, 
    var(--brand-secondary-700), 
    var(--brand-secondary-500));
  color: white;
}

/* Sizes */
.btn--sm {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  min-height: 36px;
}

.btn--lg {
  padding: var(--space-4) var(--space-6);
  font-size: var(--text-lg);
  min-height: 52px;
}

/* Disabled */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}
```

---

## 🌓 THEME TOGGLE BUTTON

**Icon-only Button** zum Wechseln zwischen Light und Dark Mode. Positioniert im User Bar (rechts neben Admin-Button).

### Features

✅ **Icon-only Design**: Nur Icons, kein Text  
✅ **Auto-Initialisierung**: Funktioniert automatisch  
✅ **FOUC Prevention**: Theme wird sofort gesetzt  
✅ **Accessibility**: ARIA-Labels, Screen-Reader-Ankündigungen  
✅ **Position**: User Bar rechts, neben Admin-Button

### HTML Structure

```html
<!-- In templates/base.html - User Bar -->
<div class="user-actions">
  <button id="theme-toggle" class="btn" aria-label="Theme wechseln">
    <svg class="icon icon--theme-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <!-- Sun Icon SVG -->
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <!-- ... weitere Linien für Sonne ... -->
    </svg>
    <svg class="icon icon--theme-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <!-- Moon Icon SVG -->
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  </button>
</div>
```

### CSS Styling

```css
/* Icon-only Button (44x44px Touch Target) */
#theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  width: 44px;
  height: 44px;
  position: relative;
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
}

#theme-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

/* Icons übereinander positioniert */
#theme-toggle .icon--theme-light,
#theme-toggle .icon--theme-dark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  transition: opacity var(--transition-fast);
}
```

### JavaScript

Das System initialisiert sich automatisch über `static/js/v2/theme-toggle.js`. Keine manuelle Initialisierung nötig.

**Implementation Details:**
- Verwendet `ThemeManager` aus `theme.js`
- Auto-Initialisierung aller Buttons mit `id="theme-toggle"`
- Icon-Toggle basierend auf aktuellem Theme
- Screen-Reader-Ankündigungen bei Theme-Wechsel

### Implementation Files

- **CSS**: `static/css/v2/components.css` (Zeile ~1208)
- **JavaScript**: `static/js/v2/theme-toggle.js`
- **Core Logic**: `static/js/v2/theme.js` (ThemeManager Klasse)
- **Template**: `templates/base.html` (User Bar)

Siehe auch: `DESIGN_SYSTEM.md` → Theme Switching für vollständige Dokumentation.

---

## 👑 ADMIN BUTTON

**Icon-only Button** für den Admin-Bereich. Positioniert im User Bar (rechts neben Theme Toggle).

### Features

✅ **Icon-only Design**: Nur Icon, kein Text  
✅ **Konsistent mit Theme Toggle**: Gleiches Styling  
✅ **Accessibility**: ARIA-Label für Screen Reader  
✅ **Position**: User Bar rechts, neben Theme Toggle

### HTML Structure

```html
<!-- In templates/base.html - User Bar -->
<div class="user-actions">
  <a href="{{ url_for('admin.index') }}" 
     id="admin-button" 
     class="btn btn--icon-only" 
     aria-label="Admin-Bereich">
    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
      <path d="M17.8 20.817l-2.172 1.138a.392.392 0 0 1-.568-.41l.413-2.411L13.567 17.3a.392.392 0 0 1 .228-.671l2.428-.035 1.086-2.193a.392.392 0 0 1 .702 0l1.086 2.193 2.428.035a.392.392 0 0 1 .228.67l-1.725 1.844.413 2.411a.392.392 0 0 1-.568.411L17.8 20.817z"/>
    </svg>
  </a>
</div>
```

### CSS Styling

Verwendet die wiederverwendbare `.btn--icon-only` Klasse (siehe Icon-only Button Pattern).

### Icon

- **Icon**: `user-star` (Lucide)
- **Symbolik**: Privilegierter/ausgezeichneter Benutzer für Admin-Bereich

### Implementation Files

- **CSS**: `static/css/v2/components.css` (nach Theme Toggle)
- **Template**: `templates/base.html` (User Bar)

---

## 🎯 ICON-ONLY BUTTON PATTERN

**Wiederverwendbares Pattern** für Icon-only Buttons (z.B. Theme Toggle, Admin Button).

### Verwendung

```html
<a href="#" id="my-icon-button" class="btn btn--icon-only" aria-label="Beschreibung">
  <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
    <!-- Icon SVG -->
  </svg>
</a>
```

### CSS Implementation

```css
.btn--icon-only {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  min-width: 44px;
  min-height: 44px;
  width: 44px;
  height: 44px;
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  text-decoration: none;
}

.btn--icon-only:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.btn--icon-only .icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}
```

### Best Practices

- ✅ **Touch Target**: Mindestens 44x44px (WCAG 2.1)
- ✅ **ARIA-Label**: Immer beschreibendes Label für Screen Reader
- ✅ **Icon Size**: 1.25rem (20px) für gute Sichtbarkeit
- ✅ **Konsistenz**: Gleiches Styling wie Theme Toggle Button

### Beispiele

- Theme Toggle Button (`#theme-toggle`)
- Admin Button (`#admin-button`)

---

## 🎴 CARD SYSTEM (REDESIGNED)

### Problem mit altem System
```
❌ card-secondary INNERHALB card = verschachtelt, unübersichtlich
❌ Zu viele Varianten (variant-accent, variant-info, etc.)
❌ Inkonsistente Margins durch Verschachtelung
```

### Neue Lösung: Card Sections

```html
<!-- HAUPT-CARD (Keine Verschachtelung mehr!) -->
<div class="card">
  <div class="card__header">
    <h2 class="card__title">Profil</h2>
    <div class="card__actions">
      <button class="btn btn--sm btn--outline">Bearbeiten</button>
    </div>
  </div>
  
  <div class="card__body">
    <!-- Section statt card-secondary -->
    <div class="card-section">
      <div class="card-section__header">
        <h3 class="card-section__title">
          <svg class="icon"><use href="#user"/></svg>
          Persönliche Daten
        </h3>
      </div>
      <div class="card-section__body">
        <div class="info-row">
          <span class="info-row__label">Name:</span>
          <span class="info-row__value">Max Mustermann</span>
        </div>
        <div class="info-row">
          <span class="info-row__label">Email:</span>
          <span class="info-row__value">max@example.com</span>
        </div>
      </div>
      <div class="card-section__footer">
        <button class="btn btn--primary">Speichern</button>
      </div>
    </div>
    
    <!-- Weitere Section -->
    <div class="card-section card-section--accent">
      <div class="card-section__header">
        <h3 class="card-section__title">
          <svg class="icon"><use href="#lock"/></svg>
          Sicherheit
        </h3>
      </div>
      <div class="card-section__body">
        <!-- Content -->
      </div>
    </div>
  </div>
  
  <div class="card__footer">
    <button class="btn btn--outline">Zurück</button>
  </div>
</div>
```

### CSS Implementation

```css
/* Card */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  overflow: hidden;
  margin-bottom: var(--space-5);
}

.card:last-child {
  margin-bottom: 0;
}

.card:hover {
  box-shadow: var(--card-hover-shadow);
}

/* Card Header */
.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-secondary);
}

/* Light Mode: Enhanced contrast for card header */
[data-theme="light"] .card__header {
  background: var(--brand-primary-200);  /* #d1d9e1 - More visible vs body bg */
}

.card__title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}
```

### Card Title mit Icon

Card Titles können Icons enthalten:

```html
<h2 class="card__title">
  <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
  Persönliche Daten
</h2>
```

**CSS:** `.card__title` verwendet `display: flex` mit `gap: var(--space-2)` für automatische Icon-Ausrichtung.

.card__actions {
  display: flex;
  gap: var(--space-2);
}

/* Card Body */
.card__body {
  padding: var(--space-5);
}

/* Card Footer */
.card__footer {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-5);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-secondary);
}

/* Card Section (ersetzt card-secondary) */
.card-section {
  background: var(--color-surface-secondary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
}

.card-section:last-child {
  margin-bottom: 0;
}

/* Section Variants */
.card-section--accent {
  border-left: 4px solid var(--brand-accent-600);
  background: var(--color-surface);
}

.card-section--info {
  border-left: 4px solid var(--brand-secondary-600);
}

.card-section--subtle {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
}

/* Section Header */
.card-section__header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.card-section__title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

/* Section Body */
.card-section__body {
  padding: var(--space-4);
}

/* Section Footer */
.card-section__footer {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
}
```

---

## 📊 INFO ROW (ersetzt stats-item)

```html
<div class="info-row">
  <span class="info-row__label">Restaurant:</span>
  <span class="info-row__value">Chez Vrony</span>
</div>

<div class="info-row">
  <span class="info-row__label">Datum:</span>
  <span class="info-row__value">14.02.2025</span>
</div>

<!-- With Icon -->
<div class="info-row">
  <span class="info-row__label">
    <svg class="icon"><use href="#calendar"/></svg>
    Datum:
  </span>
  <span class="info-row__value">14.02.2025</span>
</div>

<!-- With Link -->
<div class="info-row">
  <span class="info-row__label">Restaurant:</span>
  <span class="info-row__value">
    <a href="#" class="info-row__link">Chez Vrony</a>
  </span>
</div>
```

### CSS

```css
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

.info-row__value {
  color: var(--color-text-secondary);  /* Normal text - consistent! */
  text-align: right;
}

.info-row__link {
  color: var(--color-text-link);  /* Orange like all links */
  text-decoration: none;
}

.info-row__link:hover {
  color: var(--color-text-link-hover);
  text-decoration: underline;
}
```

---

## 🧭 NAVIGATION

### Sidebar (Desktop)

**Minimale Implementierung:** Nur Navigation, keine zusätzlichen Features (Header, Footer, User Info, Collapse).

**Design-Entscheidungen:**
- ✅ Minimal: Nur Navigation Items, keine redundanten Features
- ✅ Theme-aware: Passt sich an Dark/Light Mode an
- ✅ Responsive: Nur auf Desktop (≥ 1024px) sichtbar
- ✅ Konsistent: Gleiche Icons und Logik wie Bottom Nav
- ✅ Dark Mode: Hintergrund wie Body (`--color-bg-base`), Border in Sidebar-Farbe für klare Abgrenzung

```html
<aside class="sidebar">
  <nav class="sidebar__nav" aria-label="Hauptnavigation">
    <a href="/dashboard" class="sidebar__item sidebar__item--active">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
      <span class="sidebar__label">Dashboard</span>
    </a>
    
    <a href="/events" class="sidebar__item">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      <span class="sidebar__label">Events</span>
    </a>
  </nav>
</aside>
```

**CSS Implementation:**
- Position: Fixed, unter User Bar (top: 60px)
- Breite: 200px
- Background: `var(--color-surface-secondary)` (Theme-aware)
- Responsive: Display nur auf Desktop (≥ 1024px)
- Content wird automatisch verschoben (`margin-left: 200px`)

**Zukünftige Erweiterungen (optional):**
- Collapse-Funktion (Icon-only Mode)
- User Info im Footer
- Badges für Notifications

### Bottom Nav (Mobile)

**Theme-aware:** Passt sich automatisch an Dark/Light Mode an.

**Icons:** Verwendet Lucide SVG Icons (inline) - konsistent mit den Icons auf den Hauptseiten.

```html
<nav class="bottom-nav">
  <a href="/dashboard" class="nav-item active" aria-label="Dashboard">
    <svg class="nav-icon icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
    <span class="nav-text">Dashboard</span>
  </a>
  <a href="/events" class="nav-item" aria-label="Events">
    <svg class="nav-icon icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
    <span class="nav-text">Events</span>
  </a>
  <a href="/ggl" class="nav-item" aria-label="GGL">
    <svg class="nav-icon icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
      <path d="M4 22h16"/>
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
    </svg>
    <span class="nav-text">GGL</span>
  </a>
  <a href="/member" class="nav-item" aria-label="Member">
    <svg class="nav-icon icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
    <span class="nav-text">Member</span>
  </a>
</nav>
```

**Icon Mapping (konsistent mit Hauptseiten):**
- Dashboard → `home` (Lucide)
- Events → `calendar` (Lucide)
- GGL → `trophy` (Lucide)
- Member → `user` (Lucide)

**CSS Implementation:**
- Background: `var(--color-surface)` (Logo Navy Dark #1b232e im Dark Mode, White im Light Mode)
- Border: `var(--color-border-subtle)` (theme-aware)
- Shadow: `var(--shadow-md)` (theme-aware)
- Active State: Orange (`var(--color-interactive-primary)`)
- Icon Size: 24x24px (`.nav-icon`)

---

## 🔔 ALERT / INFO BANNER

**Use Case:** Informative messages, warnings, errors, or success notifications at page/section level.

```html
<!-- Info Alert -->
<div class="alert alert--info">
  <svg class="alert__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="16" x2="12" y2="12"/>
    <line x1="12" y1="8" x2="12.01" y2="8"/>
  </svg>
  <div class="alert__content">
    <div class="alert__message">
      Diese Informationen werden verschlüsselt gespeichert.
    </div>
  </div>
</div>

<!-- With Title -->
<div class="alert alert--warning">
  <svg class="alert__icon">...</svg>
  <div class="alert__content">
    <div class="alert__title">Achtung</div>
    <div class="alert__message">
      Diese Aktion kann nicht rückgängig gemacht werden.
    </div>
  </div>
</div>

<!-- Success -->
<div class="alert alert--success">
  <svg class="alert__icon">...</svg>
  <div class="alert__content">
    <div class="alert__message">Daten erfolgreich gespeichert!</div>
  </div>
</div>

<!-- Error -->
<div class="alert alert--error">
  <svg class="alert__icon">...</svg>
  <div class="alert__content">
    <div class="alert__title">Fehler</div>
    <div class="alert__message">Bitte alle Pflichtfelder ausfüllen.</div>
  </div>
</div>
```

### When to use

**Alert (persistent):**
- ✅ Important information about the entire page/section
- ✅ Security notices (e.g., encryption info)
- ✅ Validation errors that apply to multiple fields
- ✅ Warnings before destructive actions

**Toast (temporary):**
- ✅ Action feedback (saved, deleted, etc.)
- ✅ Temporary notifications
- ✅ Non-critical updates

### CSS

```css
.alert {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border-left: 4px solid;
  border-radius: var(--radius-md);
}

.alert--info    { border-left-color: var(--brand-primary-600); }
.alert--success { border-left-color: var(--color-success); }
.alert--warning { border-left-color: var(--color-warning); }
.alert--error   { border-left-color: var(--color-error); }
```

---

## 📝 FORMS

### Form Container

Alle Forms sollten die `.form` Klasse verwenden:

```html
<form method="POST" class="form">
```

**CSS:** Die `.form` Klasse hat keine spezifischen Styles und dient primär als Container für Form Fields. Sie ermöglicht konsistente Form-Strukturierung.

### Form Fields

```html
<form class="form">
  <!-- Form Field -->
  <div class="form-field">
    <label class="form-field__label" for="name">
      Name
      <span class="form-field__required">*</span>
    </label>
    <input 
      type="text" 
      id="name" 
      class="form-field__input"
      required>
    <span class="form-field__error">Bitte Namen eingeben</span>
  </div>
  
  <!-- Form Row: Multiple fields side-by-side -->
  <div class="form-row">
    <div class="form-field">
      <label class="form-field__label" for="vorname">Vorname</label>
      <input type="text" id="vorname" class="form-field__input">
    </div>
    <div class="form-field">
      <label class="form-field__label" for="nachname">Nachname</label>
      <input type="text" id="nachname" class="form-field__input">
    </div>
  </div>
  
  <!-- Select -->
  <div class="form-field">
    <label class="form-field__label" for="type">Event-Typ</label>
    <select id="type" class="form-field__select">
      <option>Monatsessen</option>
      <option>Ausflug</option>
    </select>
  </div>
  
  <!-- Textarea -->
  <div class="form-field">
    <label class="form-field__label" for="notes">Notizen</label>
    <textarea id="notes" class="form-field__textarea"></textarea>
  </div>
  
  <!-- Actions -->
  <div class="form-actions">
    <button type="button" class="btn btn--outline">Abbrechen</button>
    <button type="submit" class="btn btn--primary">Speichern</button>
  </div>
</form>
```

### CSS Implementation

```css
.form-field {
  margin-bottom: var(--space-5);
}

.form-field__label {
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
}

.form-field__input,
.form-field__select,
.form-field__textarea {
  width: 100%;
  padding: var(--input-padding);
  border: 2px solid var(--input-border);
  border-radius: var(--input-radius);
  font-size: var(--text-base);
  background-color: var(--color-surface);
  color: var(--color-text-primary);
}

.form-field__input:focus,
.form-field__select:focus,
.form-field__textarea:focus {
  outline: none;
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px rgba(220, 105, 60, 0.1);
}

.form-field__error {
  display: block;
  margin-top: var(--space-2);
  color: var(--color-error);
  font-size: var(--text-sm);
}

/* Form Row: Multiple fields side-by-side */
.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.form-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  padding-top: var(--space-6);
  margin-top: var(--space-6);
  border-top: 1px solid var(--color-border-subtle);
}

@media (max-width: 640px) {
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
```

---

## 📱 MODALS & SLIDE-OVERS

### Modal (Confirmations, Short Forms)

```html
<div class="modal" role="dialog" aria-modal="true">
  <div class="modal__backdrop"></div>
  <div class="modal__container">
    <div class="modal__header">
      <h2 class="modal__title">Event löschen?</h2>
      <button class="modal__close" aria-label="Close">
        <svg class="icon"><use href="#x"/></svg>
      </button>
    </div>
    <div class="modal__body">
      <p>Möchtest du dieses Event wirklich löschen?</p>
    </div>
    <div class="modal__footer">
      <button class="btn btn--outline">Abbrechen</button>
      <button class="btn btn--danger">Löschen</button>
    </div>
  </div>
</div>
```

### Slide-Over (Detail Views)

```html
<div class="slide-over" role="dialog" aria-modal="true">
  <div class="slide-over__backdrop"></div>
  <div class="slide-over__panel">
    <div class="slide-over__header">
      <h2 class="slide-over__title">Event Details</h2>
      <button class="slide-over__close" aria-label="Close">
        <svg class="icon"><use href="#x"/></svg>
      </button>
    </div>
    <div class="slide-over__body">
      <!-- Content -->
    </div>
    <div class="slide-over__footer">
      <button class="btn btn--primary">Bearbeiten</button>
    </div>
  </div>
</div>
```

---

## 🗂️ TABS

**Two Implementations:** JavaScript-based (buttons) or URL-based (links).

### URL-Based Tabs (Recommended)

**Benefits:** Bookmarkable, works without JS, progressive enhancement.

```html
<div class="tabs">
  <nav class="tabs__nav" role="tablist">
    <a href="?tab=profile" 
       class="tabs__tab {{ 'tabs__tab--active' if active_tab == 'profile' else '' }}"
       role="tab">
      Profildaten
    </a>
    <a href="?tab=sensitive" 
       class="tabs__tab {{ 'tabs__tab--active' if active_tab == 'sensitive' else '' }}"
       role="tab">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
      Sensible Daten
    </a>
  </nav>
  
  <div class="tabs__content">
    <div class="tabs__panel {{ 'tabs__panel--active' if active_tab == 'profile' else '' }}"
         role="tabpanel">
      <!-- Profile Content -->
    </div>
    <div class="tabs__panel {{ 'tabs__panel--active' if active_tab == 'sensitive' else '' }}"
         role="tabpanel">
      <!-- Sensitive Content -->
    </div>
  </div>
</div>
```

### JavaScript-Based Tabs (Interactive)

**Benefits:** No page reload, smooth transitions.

```html
<div class="tabs">
  <nav class="tabs__nav" role="tablist">
    <button 
      class="tabs__tab tabs__tab--active" 
      role="tab"
      aria-selected="true"
      aria-controls="panel-1">
      Übersicht
    </button>
    <button 
      class="tabs__tab" 
      role="tab"
      aria-selected="false"
      aria-controls="panel-2">
      Profil
    </button>
  </nav>
  
  <div class="tabs__content">
    <div 
      class="tabs__panel tabs__panel--active" 
      id="panel-1"
      role="tabpanel">
      <!-- Content 1 -->
    </div>
    <div 
      class="tabs__panel" 
      id="panel-2"
      role="tabpanel">
      <!-- Content 2 -->
    </div>
  </div>
</div>
```

### Icons in Tabs

Tabs können Icons enthalten. Die Icons werden automatisch mit `gap: var(--space-2)` ausgerichtet:

```html
<a href="?tab=sensitive" class="tabs__tab" role="tab">
  <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
  Sensible Daten
</a>
```

**CSS:** `.tabs__tab` verwendet `display: inline-flex` mit `gap: var(--space-2)` für automatische Icon-Ausrichtung.

### ARIA-Attribute (Optional, aber empfohlen)

Für bessere Accessibility können URL-based Tabs `aria-selected` verwenden:

```html
<a href="?tab=profile" 
   class="tabs__tab {{ 'tabs__tab--active' if active_tab == 'profile' else '' }}"
   role="tab"
   aria-selected="{{ 'true' if active_tab == 'profile' else 'false' }}">
  Profildaten
</a>
```

### CSS Features

**Design-Entscheidungen:**
- ✅ Tabs mit Hintergrund für bessere Lesbarkeit (nicht transparent)
- ✅ Trennstriche zwischen inaktiven Tabs für klare Abgrenzung
- ✅ Theme-aware Farben (Light/Dark Mode)
- ✅ Horizontales Scrolling mit versteckter Scrollbar
- ✅ Fade-Indikatoren an der Tab-Leiste, gesteuert über Container-Klassen (nur bei Overflow sichtbar, blenden am jeweiligen Rand aus; `static/js/v2/tabs.js`)

```css
.tabs {
  position: relative;
  margin-bottom: var(--space-6);
  overflow: hidden;
}

.tabs__nav {
  display: flex;
  gap: 0; /* Kein Gap, Tabs haben Trennstriche */
  position: relative;
  min-height: var(--tabs-nav-height, 56px);
  overflow-x: auto;
  scrollbar-width: none;               /* Hide scrollbar */
  scroll-behavior: smooth;
  padding-left: 0;
  padding-right: 0;
}

.tabs__tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-secondary);
  border-right: 1px solid var(--color-border-default);
  border-bottom: 2px solid transparent;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  white-space: nowrap;
  flex-shrink: 0;
}

/* Light Mode: Mehr Kontrast für inaktive Tabs */
[data-theme="light"] .tabs__tab {
  background: var(--brand-primary-100);
}

/* Dark Mode: Dunklerer Hintergrund für inaktive Tabs */
[data-theme="dark"] .tabs__tab {
  background: var(--brand-primary-800);
}

.tabs__tab:last-child {
  border-right: none; /* Kein Trennstrich am letzten Tab */
}

.tabs__tab:hover {
  background: var(--color-surface-hover);
}

.tabs__tab--active {
  background: var(--color-surface);
  color: var(--color-interactive-primary);
  border-bottom-color: var(--color-interactive-primary);
  font-weight: var(--font-bold);
}

/* Fades am Container, via Klassen (.tabs--fade-left/right) */
.tabs::before,
.tabs::after {
  content: '';
  position: absolute;
  top: 0;
  width: 56px;
  height: var(--tabs-nav-height, 56px);
  pointer-events: none;
  z-index: 2;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.tabs::before {
  left: 0;
  background: linear-gradient(to right, var(--color-bg-base) 0%, transparent 80%);
}

.tabs::after {
  right: 0;
  background: linear-gradient(to left, var(--color-bg-base) 0%, transparent 80%);
}

.tabs--fade-left::before { opacity: 1; }
.tabs--fade-right::after { opacity: 1; }
```

.tabs__content {
  margin-top: var(--space-5);
}

.tabs__panel {
  display: none;
}

.tabs__panel--active {
  display: block;
  animation: fadeIn 200ms ease;
}
```

### Real-World Example: Events Page with Multiple Tabs

**Use Case:** Events-Hauptseite mit 4 Tabs (Übersicht, Kommend, Archiv, Statistiken), wobei jeder Tab unterschiedliche Daten benötigt.

#### Backend Pattern (Flask)

```python
@bp.route('/')
@login_required
def index():
    """Events main page with tabs"""
    tab = request.args.get('tab', 'overview')  # Default: overview
    now = datetime.utcnow()
    
    # Common data for all tabs
    context = {
        'active_tab': tab,
        'use_v2_design': True
    }
    
    # Tab-specific data (only load what's needed)
    if tab == 'overview':
        current_event = Event.query.filter(
            Event.published == True,
            Event.datum >= three_days_ago,
            Event.datum <= now
        ).order_by(Event.datum.desc()).first()
        
        context.update({
            'current_event': current_event,
            'next_event': next_event,
            'last_event': last_event
        })
    
    elif tab == 'kommend':
        upcoming_events = Event.query.filter(
            Event.published == True,
            Event.datum > now
        ).order_by(Event.datum.asc()).all()
        context['events'] = upcoming_events
    
    elif tab == 'archiv':
        page = request.args.get('page', 1, type=int)
        events = Event.query.filter(
            Event.published == True,
            Event.datum < now
        ).paginate(page=page, per_page=20, error_out=False)
        
        context.update({
            'events': events,
            'years': years,
            'selected_year': year
        })
    
    elif tab == 'stats':
        # Statistics calculations
        past_events = Event.query.filter(...).all()
        context.update({
            'total_events': total_events,
            'avg_participation_rate': avg_rate,
            # ... more stats
        })
    
    return render_template('events/index.html', **context)
```

#### Template Pattern (Jinja2)

**Wichtig:** Variablen nur verwenden, wenn sie definiert sind!

```html
<div class="tabs">
  <nav class="tabs__nav" role="tablist">
    <a href="{{ url_for('events.index', tab='overview') }}"
       class="tabs__tab {{ 'tabs__tab--active' if active_tab == 'overview' else '' }}"
       role="tab"
       aria-selected="{{ 'true' if active_tab == 'overview' else 'false' }}">
      <svg class="icon">...</svg>
      Übersicht
    </a>
    <!-- More tabs -->
  </nav>
  
  <div class="tabs__content">
    <!-- Tab 1: Overview -->
    <div class="tabs__panel {{ 'tabs__panel--active' if active_tab == 'overview' else '' }}"
         role="tabpanel">
      {% if current_event %}
      <div class="card">
        <!-- Current event content -->
      </div>
      {% endif %}
    </div>
    
    <!-- Tab 2: Stats -->
    <div class="tabs__panel {{ 'tabs__panel--active' if active_tab == 'stats' else '' }}"
         role="tabpanel">
      <!-- WICHTIG: Variablen nur verwenden wenn definiert! -->
      {% if total_events is defined %}
      <div class="info-row">
        <span class="info-row__label">Gesamte Events:</span>
        <span class="info-row__value">{{ total_events }}</span>
      </div>
      {% endif %}
      
      {% if avg_participation_rate is defined %}
      <div class="info-row">
        <span class="info-row__label">Durchschnittliche Teilnahme:</span>
        <span class="info-row__value">{{ "%.1f"|format(avg_participation_rate) }}%</span>
      </div>
      {% endif %}
    </div>
  </div>
</div>
```

#### Best Practices

✅ **DO:**
- Default-Tab setzen: `tab = request.args.get('tab', 'overview')`
- Nur benötigte Daten pro Tab laden (Performance)
- Variablen im Template prüfen: `{% if variable is defined %}`
- `active_tab` immer im Context setzen (für Template-Logik)
- ARIA-Attribute für Accessibility: `role="tab"`, `aria-selected`

❌ **DON'T:**
- Alle Daten für alle Tabs laden (ineffizient)
- Variablen verwenden ohne `is defined` Check (500 Error Risiko)
- Verschiedene Default-Tabs pro User (verwirrend)

---

## 📋 PAGE TEMPLATES

### Standard Page Structure

```html
<div class="container">
  <!-- Breadcrumbs (optional) -->
  <nav class="breadcrumbs" aria-label="Breadcrumb">
    <!-- ... -->
  </nav>
  
  <!-- Page Header -->
  <div class="page-header">
    <h1>
      <svg class="icon"><use href="#dashboard"/></svg>
      Dashboard
    </h1>
    <p class="page-subtitle">Willkommen zurück!</p>
    <div class="page-actions">
      <button class="btn btn--primary">Neues Event</button>
    </div>
  </div>
  
  <!-- Page Content -->
  <div class="page-content">
    <div class="card">
      <!-- Content -->
    </div>
  </div>
</div>
```

### CSS Implementation

```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-4);
}

.page-header {
  margin-bottom: var(--space-8);
}

.page-header h1 {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.page-header h1 .icon {
  width: 1.75rem;
  height: 1.75rem;
  flex-shrink: 0;
}

.page-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
}

.page-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

/* Icon-only Actions (kompakt, wiederverwendbar) */
.page-actions--icons {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.page-actions--icons .btn--icon-only,
.page-actions--icons form .btn--icon-only {
  width: 44px;
  min-width: 44px;
  height: 44px;
}

.page-actions--right {
  justify-content: flex-end;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
```

### Featured Page Header (for Hub Pages)

```html
<div class="page-header page-header--featured">
  <h1>
    <svg class="icon"><use href="#events"/></svg>
    Events
  </h1>
  <p class="page-subtitle">Verwalte deine Events</p>
  <div class="page-actions">
    <button class="btn btn--primary">Neues Event</button>
  </div>
</div>
```

**Note:** `.page-header--featured` has centered text, gradient title, and larger typography for hub/dashboard pages.

---

## 📋 USAGE PATTERNS

### Multi-Section Forms (mehrere Cards, ein Submit)

**Use Case:** Form mit mehreren thematischen Sections (z.B. Profil-Seite).

**Problem:** Submit-Button in letzter Card sieht aus als gehört nur zu dieser Section!

**Lösung:** `.form-actions` AUSSERHALB aller Cards verwenden!

```html
<form method="POST">
    <div class="card">
        <div class="card__header">
            <h2 class="card__title">Persönliche Daten</h2>
        </div>
        <div class="card__body">
            <div class="form-field">...</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card__header">
            <h2 class="card__title">Adresse</h2>
        </div>
        <div class="card__body">
            <div class="form-field">...</div>
        </div>
    </div>
    
    <!-- Submit Button außerhalb aller Cards -->
    <div class="form-actions">
        <button type="submit" class="btn btn--primary">Speichern</button>
    </div>
</form>
```

**Wann verwenden:**
- ✅ Profil-Seiten mit mehreren Sections
- ✅ Settings-Seiten
- ✅ Multi-Step Forms auf einer Seite

**Wann NICHT:**
- ❌ Einzelne Card → dort `card__footer` verwenden!

---

### Single-Section Form (eine Card mit Footer)

**Use Case:** Ein Form in einer einzelnen Card.

```html
<form method="POST">
    <div class="card">
        <div class="card__header">
            <h2 class="card__title">Event erstellen</h2>
        </div>
        <div class="card__body">
            <div class="form-field">...</div>
        </div>
        <div class="card__footer">
            <button type="button" class="btn btn--outline">Abbrechen</button>
            <button type="submit" class="btn btn--primary">Erstellen</button>
        </div>
    </div>
</form>
```

---

## ✅ MIGRATION PATTERNS

### Alt → Neu Mapping

```
CARDS:
card-secondary              → card-section
variant-accent              → card-section--accent
variant-info                → card-section--info

INFO DISPLAY:
stats-item                  → info-row
stats-item .label           → info-row__label
stats-item .value           → info-row__value

BUTTONS:
btn-secondary               → btn--outline
btn-info                    → btn--primary
btn-warning                 → btn--outline

ACTIONS:
card-actions                → card__footer OR card-section__footer
page-actions                → page__actions
quick-actions               → Entfernen, direkt in card__body

NAVIGATION:
Bottom Nav (Mobile)         → Behalten
(kein Desktop Nav)          → Sidebar NEU
```

---

## 🎯 USAGE GUIDELINES

### When to use what

**Card:**
- Hauptcontainer für zusammengehörige Inhalte
- Immer auf Page-Level
- NIEMALS verschachteln

**Card Section:**
- Unterabschnitte INNERHALB einer Card
- Ersetzt alte card-secondary
- Maximal 2 Ebenen (Card > Section)

**Info Row:**
- Label/Value Paare
- Innerhalb Card Section oder Card Body
- Automatische Borders

**Modal:**
- Confirmations (Delete, etc.)
- Kurze Forms (Rating, Quick Add)
- Alerts

**Slide-Over:**
- Detail Views (Event, Member)
- Längere Forms (Settings)
- Bleibt Kontext sichtbar

**Tabs:**
- Zusammengelegte Seiten (Member: Profil + Security + Technical)
- Hub-Pages (Events: Kommende + Archiv + Stats)

---

## 🚫 ANTI-PATTERNS (Don'ts)

```html
<!-- ❌ DON'T: Nested Cards -->
<div class="card">
  <div class="card">...</div>
</div>

<!-- ✅ DO: Use Card Sections -->
<div class="card">
  <div class="card-section">...</div>
</div>

<!-- ❌ DON'T: Inline Styles -->
<div class="card" style="margin-top: 20px;">

<!-- ✅ DO: Use Utility Classes or proper spacing -->
<div class="card">

<!-- ❌ DON'T: Too many button variants -->
<button class="btn btn-info btn-lg btn-special">

<!-- ✅ DO: Keep it simple -->
<button class="btn btn--primary btn--lg">

<!-- ❌ DON'T: Emojis in final version -->
<button class="btn">🏠 Dashboard</button>

<!-- ✅ DO: Use Icons -->
<button class="btn">
  <svg class="icon"><use href="#home"/></svg>
  Dashboard
</button>
```

---

## 🎯 UX FEATURES (State-of-the-Art)

Modern UX patterns für bessere User Experience.

---

### Toast Notifications

**Non-intrusive feedback messages** mit auto-dismiss.

#### Features
- ✅ Auto-dismiss nach 5 Sekunden (konfigurierbar)
- ✅ Stackable (mehrere Toasts gleichzeitig)
- ✅ 4 Typen: Success, Error, Warning, Info
- ✅ Optional: Action Button (Undo Pattern)
- ✅ Position: Top-right (Desktop), Bottom (Mobile)
- ✅ Respektiert Safe Area Insets

#### JavaScript API

```javascript
// Basic Toasts
Toast.success('Gespeichert!', 'Änderungen übernommen.');
Toast.error('Fehler!', 'Bitte erneut versuchen.');
Toast.warning('Achtung!', 'Dies ist irreversibel.');
Toast.info('Info', 'Neue Nachricht verfügbar.');

// With Action Button (Undo Pattern)
Toast.info('Event gelöscht', null, {
  action: 'Rückgängig',
  onAction: () => undoDelete(),
  duration: 10000  // 10 seconds
});

// Custom Options
Toast.success('Title', 'Message', {
  duration: 3000,      // Auto-dismiss after 3s
  closeable: false,    // No close button
});

// Manual Dismiss
const toastId = Toast.success('Wait...', 'Processing...');
setTimeout(() => Toast.dismiss(toastId), 2000);
```

#### HTML Structure

```html
<div class="toast-container">
  <div class="toast toast--success" role="alert">
    <svg class="toast__icon">...</svg>
    <div class="toast__content">
      <div class="toast__title">Erfolgreich!</div>
      <p class="toast__message">Änderungen gespeichert.</p>
    </div>
    <button class="toast__close">×</button>
  </div>
</div>
```

---

### Filter Chips

**Clickable tags** zum Filtern von Content.

#### Features
- ✅ Active State
- ✅ Optional: Count Badge
- ✅ Optional: Remove Button
- ✅ Touch-optimiert

#### HTML

```html
<div class="filter-chips">
  <button class="chip chip--active">
    Alle Events
    <span class="chip__count">42</span>
  </button>
  <button class="chip">
    Monatsessen
    <span class="chip__count">30</span>
  </button>
  <button class="chip">
    Archiviert
    <button class="chip__remove">×</button>
  </button>
</div>
```

#### JavaScript

```javascript
// Toggle active state
chip.addEventListener('click', () => {
  chip.classList.toggle('chip--active');
});
```

---

### Instant Search

**Real-time search** mit Live-Filtering.

#### Features
- ✅ Debounced Input (150ms)
- ✅ Clear Button
- ✅ Customizable Target Selector
- ✅ Custom Event für Resultate

#### HTML

```html
<div class="search-field" 
     data-search 
     data-search-target=".event-card">
  <svg class="search-field__icon">...</svg>
  <input type="search" 
         class="search-field__input" 
         placeholder="Suchen...">
  <button class="search-field__clear">×</button>
</div>
```

#### JavaScript (Auto-initializes)

```javascript
// Listen for search results
searchField.addEventListener('search', (e) => {
  console.log(e.detail.visibleResults); // Number of visible items
});
```

---

### Accordion

**Collapsible sections** für lange Content-Bereiche.

#### Features
- ✅ Single oder Multiple Open
- ✅ ARIA compliant
- ✅ Keyboard accessible
- ✅ Smooth animations

#### HTML

```html
<div class="accordion" data-accordion data-allow-multiple>
  <div class="accordion-item accordion-item--open">
    <button class="accordion-item__header">
      <svg class="icon">...</svg>
      <span class="accordion-item__title">Section Title</span>
      <svg class="accordion-item__icon">...</svg>
    </button>
    <div class="accordion-item__content">
      Content here...
    </div>
  </div>
</div>
```

#### JavaScript (Auto-initializes)

```javascript
// Manual control
const accordion = new Accordion(element, { 
  allowMultiple: true 
});

accordion.openAll();
accordion.closeAll();
```

---

### Progressive Disclosure

**Native `<details>` element** für optionale Informationen.

#### HTML

```html
<details class="disclosure">
  <summary class="disclosure__summary">
    Erweiterte Optionen anzeigen
    <svg class="icon">...</svg>
  </summary>
  <div class="disclosure__content">
    Additional information here...
  </div>
</details>
```

#### Wann nutzen?
- ✅ Event-Details (Google Maps, Notizen)
- ✅ Member-Profil (sensible Daten)
- ✅ Admin-Bereiche (erweiterte Optionen)

---

### Breadcrumbs

**Navigation hierarchy** für komplexe Seiten.

#### HTML

```html
<nav class="breadcrumbs" aria-label="Breadcrumb">
  <div class="breadcrumbs__item">
    <a href="#" class="breadcrumbs__link">Admin</a>
    <span class="breadcrumbs__separator">/</span>
  </div>
  <div class="breadcrumbs__item">
    <a href="#" class="breadcrumbs__link">Events</a>
    <span class="breadcrumbs__separator">/</span>
  </div>
  <div class="breadcrumbs__item">
    <span class="breadcrumbs__current">Bearbeiten</span>
  </div>
</nav>
```

#### CSS

```css
.breadcrumbs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding: var(--space-4) 0;
  font-size: var(--text-sm);
}

.breadcrumbs__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.breadcrumbs__link {
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.breadcrumbs__link:hover {
  color: var(--color-text-link);  /* Orange on hover */
}

.breadcrumbs__separator {
  color: var(--color-text-tertiary);
  user-select: none;
}

.breadcrumbs__current {
  color: var(--color-text-primary);
  font-weight: var(--font-medium);
}
```

#### Wann nutzen?
- ✅ Admin-Bereiche (tiefe Navigation)
- ✅ Event-Bearbeitung (Kontext zeigen)
- ❌ Nicht auf flachen Seiten (Dashboard, Listen)

---

### Scroll-to-Top Button

**Fixed button** der ab 300px Scroll-Höhe erscheint.

#### Features
- ✅ Auto-show/hide basierend auf Scroll Position
- ✅ Smooth Scroll zum Anfang
- ✅ Respektiert Safe Area Insets
- ✅ Mobile: Position über Bottom Nav
- ✅ **Theme-aware**: Verbesserter Kontrast im Light Mode

#### CSS Implementation

```css
.scroll-to-top {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  /* ... */
}

.scroll-to-top .icon {
  color: var(--color-text-primary);
}

/* Light Mode: Verbesserter Kontrast */
[data-theme="light"] .scroll-to-top {
  background: var(--brand-primary-700);  /* Navy Hintergrund */
  border-color: var(--brand-primary-600);
}

[data-theme="light"] .scroll-to-top .icon {
  color: #ffffff;  /* Weißes Icon für maximalen Kontrast */
}

[data-theme="light"] .scroll-to-top:hover {
  background: var(--brand-primary-600);
}
```

**Warum:** Im Light Mode wäre weißer Hintergrund auf hellem Seitenhintergrund zu wenig Kontrast. Navy Hintergrund mit weißem Icon bietet bessere Sichtbarkeit.

#### JavaScript (Auto-initializes)

```javascript
// Auto-initialized on page load
// Customize threshold:
new ScrollToTop({ threshold: 500 });
```

---

### Focus Trap

**Keyboard navigation** für Modals.

#### Features
- ✅ Tab bleibt im Modal
- ✅ WCAG 2.1 compliant
- ✅ Return Focus nach Schließen

#### JavaScript

```javascript
const trap = new FocusTrap(modalElement);

// When opening modal
trap.activate();

// When closing modal
trap.deactivate();
```

---

## 📱 MOBILE OPTIMIZATIONS

### Safe Area Insets

**iOS Notch/Dynamic Island Support** automatisch integriert.

```css
/* Already integrated in: */
body {
  padding-top: var(--safe-area-top);
  padding-bottom: var(--safe-area-bottom);
}

.scroll-to-top {
  bottom: calc(var(--space-6) + var(--safe-area-bottom));
}

.toast-container {
  bottom: calc(var(--space-4) + var(--safe-area-bottom));
}
```

### Visual Feedback

**Enhanced active states** für besseres Touch-Feedback.

```css
.btn:active:not(:disabled) {
  transform: scale(0.98);
}

@media (hover: hover) {
  .card--interactive:hover {
    transform: translateY(-2px);
  }
}
```

### Smooth Scroll

**Native smooth scrolling** mit Accessibility Support.

```css
html {
  scroll-behavior: smooth;
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
}
```

---

**See also:** `DESIGN_SYSTEM.md` for design tokens and theme configuration.


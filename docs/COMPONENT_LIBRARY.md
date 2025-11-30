# GOURMEN PWA - COMPONENT LIBRARY

> **Status:** In Planning  
> **Last Updated:** 2025-01-29  
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

.card__title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

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

```html
<aside class="sidebar" data-collapsed="false">
  <div class="sidebar__header">
    <img src="/static/img/logos/logo.png" class="sidebar__logo">
    <button class="sidebar__toggle" aria-label="Toggle sidebar">
      <svg class="icon"><use href="#menu"/></svg>
    </button>
  </div>
  
  <nav class="sidebar__nav" aria-label="Main navigation">
    <a href="/dashboard" class="sidebar__item sidebar__item--active">
      <svg class="icon"><use href="#home"/></svg>
      <span class="sidebar__label">Dashboard</span>
    </a>
    
    <a href="/events" class="sidebar__item">
      <svg class="icon"><use href="#calendar"/></svg>
      <span class="sidebar__label">Events</span>
      <span class="sidebar__badge">3</span>
    </a>
  </nav>
  
  <div class="sidebar__footer">
    <button class="sidebar__item" id="theme-toggle">
      <svg class="icon"><use href="#sun"/></svg>
      <span class="sidebar__label">Theme</span>
    </button>
    
    <div class="sidebar__user">
      <div class="sidebar__user-avatar">M</div>
      <div class="sidebar__user-info">
        <div class="sidebar__user-name">Max</div>
      </div>
    </div>
  </div>
</aside>
```

### Bottom Nav (Mobile)

```html
<nav class="bottom-nav">
  <a href="/dashboard" class="bottom-nav__item bottom-nav__item--active">
    <svg class="icon"><use href="#home"/></svg>
    <span class="bottom-nav__label">Dashboard</span>
  </a>
  <a href="/events" class="bottom-nav__item">
    <svg class="icon"><use href="#calendar"/></svg>
    <span class="bottom-nav__label">Events</span>
  </a>
  <a href="/ggl" class="bottom-nav__item">
    <svg class="icon"><use href="#trophy"/></svg>
    <span class="bottom-nav__label">GGL</span>
  </a>
  <a href="/member" class="bottom-nav__item">
    <svg class="icon"><use href="#user"/></svg>
    <span class="bottom-nav__label">Member</span>
  </a>
</nav>
```

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
  <div class="form__actions">
    <button type="button" class="btn btn--outline">Abbrechen</button>
    <button type="submit" class="btn btn--primary">Speichern</button>
  </div>
</form>
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

### CSS Features

```css
.tabs__nav {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;                    /* Mobile scroll */
  scrollbar-width: none;               /* Hide scrollbar */
}

.tabs__tab {
  display: inline-flex;                /* Icon + text support */
  gap: var(--space-2);
  border-bottom: 2px solid transparent;
  text-decoration: none !important;    /* For <a> tags */
}

.tabs__tab--active {
  color: var(--color-interactive-primary);
  border-bottom-color: var(--color-interactive-primary);
  font-weight: var(--font-bold);
}
```

---

## 📋 PAGE TEMPLATES

### Standard Page Structure

```html
<div class="page">
  <div class="page__header">
    <h1 class="page__title">Dashboard</h1>
    <p class="page__subtitle">Willkommen zurück!</p>
    <div class="page__actions">
      <button class="btn btn--primary">Neues Event</button>
    </div>
  </div>
  
  <div class="page__content">
    <div class="card">
      <!-- Content -->
    </div>
  </div>
</div>
```

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


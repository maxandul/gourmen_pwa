# Design System V2

## 🎨 Logo-based Color System

Alle Farben basieren auf den Gourmen Logo-Farben:
- **Navy:** `#1b232e`, `#354e5e`
- **Orange:** `#dc693c`
- **Teal:** `#73c8a8`

## 📁 Dateistruktur

```
v2/
├── tokens.css       → Design Tokens (Farben, Spacing, Typography)
├── base.css         → Reset, Typography, Base Elements
└── components.css   → Alle Komponenten (Buttons, Cards, Forms, etc.)
```

## 🚀 Usage

```html
<!-- In Template -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/main-v2.css') }}">
```

## 🎯 Komponenten

### Buttons
```html
<button class="btn btn--primary">Primary</button>
<button class="btn btn--success">Success</button>
<button class="btn btn--danger">Danger</button>
<button class="btn btn--outline">Outline</button>
<button class="btn btn--billbro">BillBro</button>
```

### Cards (NEU - Ohne Verschachtelung!)
```html
<div class="card">
  <div class="card__header">
    <h2 class="card__title">Title</h2>
  </div>
  <div class="card__body">
    <div class="card-section card-section--accent">
      <div class="card-section__header">
        <h3 class="card-section__title">Section</h3>
      </div>
      <div class="card-section__body">
        Content
      </div>
    </div>
  </div>
</div>
```

### Info Rows (ersetzt stats-item)
```html
<div class="info-row">
  <span class="info-row__label">Label:</span>
  <span class="info-row__value">Value</span>
</div>
```

## 🌓 Theme Switching

```javascript
// Get theme
const theme = localStorage.getItem('theme') || 'dark';

// Set theme
document.documentElement.setAttribute('data-theme', theme);
localStorage.setItem('theme', theme);
```

## 📖 Dokumentation

Siehe:
- `docs/DESIGN_SYSTEM.md` - Vollständige Design Tokens & Farben
- `docs/COMPONENT_LIBRARY.md` - Alle Komponenten mit Beispielen

## 🎯 Demo

Öffne `/demo/design-system` im Browser um alle Komponenten zu sehen.


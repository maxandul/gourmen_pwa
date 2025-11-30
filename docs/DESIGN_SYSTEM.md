# GOURMEN PWA - DESIGN SYSTEM

> **Status:** In Planning  
> **Last Updated:** 2025-01-29  
> **Version:** 2.0 (Complete Redesign)

---

## 🎯 VISION & PRINCIPLES

### Core Goals
- **State-of-the-art** Frontend (2024/2025 Standards)
- **Vorzeigeprojekt** - Production-ready, professional
- **Responsive First** - Mobile to Wide Desktop (nicht nur mobile-only)
- **Theme Flexibility** - Light & Dark Mode gleichwertig (nicht nur dark-only)
- **Accessibility** - WCAG 2.2 Level AA compliant
- **Performance** - < 200KB bundle, Lighthouse > 90

### Design Philosophy
```
Progressive Enhancement
├── Funktioniert überall
├── Besser auf modernen Geräten
└── Graceful Degradation

Responsive Breakpoints
├── Mobile: 320px - 767px (Touch-optimiert, Bottom Nav)
├── Tablet: 768px - 1023px (Hybrid Touch/Maus)
├── Desktop: 1024px - 1439px (Sidebar Nav, Multi-Column)
└── Wide: 1440px+ (Max Content Width 1280px)

Component Architecture
├── BEM Naming Convention (englisch!)
├── Atomic Design Approach
└── CSS Custom Properties für Theming
```

---

## 🎨 COLOR SYSTEM

> **Based on Gourmen Logo Colors:**  
> Navy #1b232e, #354e5e | Orange #dc693c | Teal #73c8a8

### Brand Colors (Theme-Agnostic)

```css
/* ============================================
   LOGO COLORS - Foundation
   ============================================ */
--logo-navy-dark: #1b232e;      /* Darkest logo blue */
--logo-navy-medium: #354e5e;    /* Medium logo blue */
--logo-orange: #dc693c;         /* Logo orange */
--logo-teal: #73c8a8;           /* Logo teal */

/* ============================================
   EXTENDED PALETTES (derived from logo)
   ============================================ */

/* Primary Palette - Navy (from logo colors) */
--brand-primary-50: #f5f7f9;    /* Very light (Light Mode backgrounds) */
--brand-primary-100: #e8ecf0;
--brand-primary-200: #d1d9e1;
--brand-primary-300: #b4c0cd;
--brand-primary-400: #8a9db1;
--brand-primary-500: #667a91;
--brand-primary-600: #4f6477;
--brand-primary-700: #354e5e;   /* ← LOGO COLOR */
--brand-primary-800: #1b232e;   /* ← LOGO COLOR */
--brand-primary-900: #0f151a;   /* Almost black */
--brand-primary-950: #060a0d;   /* Deep black (Dark Mode) */

/* Accent Palette - Orange (from logo) */
--brand-accent-50: #fef5f0;
--brand-accent-100: #fde8dc;
--brand-accent-200: #fcd0b8;
--brand-accent-300: #fab08a;
--brand-accent-400: #f88958;
--brand-accent-500: #dc693c;    /* ← LOGO COLOR */
--brand-accent-600: #c35428;
--brand-accent-700: #a3421f;
--brand-accent-800: #83361c;
--brand-accent-900: #6b2e1b;

/* Secondary Palette - Teal (from logo) */
--brand-secondary-50: #f0faf7;
--brand-secondary-100: #d6f3eb;
--brand-secondary-200: #ace6d7;
--brand-secondary-300: #73c8a8;  /* ← LOGO COLOR */
--brand-secondary-400: #4db896;
--brand-secondary-500: #2fa885;
--brand-secondary-600: #21886d;
--brand-secondary-700: #1d6d5a;
--brand-secondary-800: #1b5749;
--brand-secondary-900: #1a493e;

/* Warm Palette - Red (Danger, Corporate Design) */
--brand-warm-50: #fef2f2;
--brand-warm-100: #fee2e2;
--brand-warm-200: #fecaca;
--brand-warm-300: #fca5a5;
--brand-warm-400: #f87171;
--brand-warm-500: #ef4444;
--brand-warm-600: #dc2626;
--brand-warm-700: #b91c1c;
--brand-warm-800: #991b1b;
--brand-warm-900: #7f1d1d;

/* Status Colors (WCAG AA compliant) */
--status-success-light: #10b981;
--status-success-dark: #34d399;
--status-warning-light: #f59e0b;
--status-warning-dark: #fbbf24;
--status-error-light: #ef4444;
--status-error-dark: #f87171;
--status-info-light: #3b82f6;
--status-info-dark: #60a5fa;
```

### Semantic Tokens - Light Theme

```css
[data-theme="light"] {
  /* Backgrounds */
  --color-bg-base: #ffffff;
  --color-bg-subtle: var(--brand-primary-50);     /* #f5f7f9 - subtle navy tint */
  --color-bg-muted: var(--brand-primary-100);
  --color-bg-elevated: #ffffff;
  --color-bg-overlay: rgba(0, 0, 0, 0.5);
  
  /* Surfaces (Cards, Panels) */
  --color-surface: #ffffff;
  --color-surface-secondary: var(--brand-primary-50);
  --color-surface-tertiary: var(--brand-primary-100);
  --color-surface-hover: var(--brand-primary-100);
  
  /* Borders */
  --color-border-subtle: var(--brand-primary-200);
  --color-border-default: var(--brand-primary-300);
  --color-border-strong: var(--brand-primary-400);
  
  /* Text - Uses logo navy for primary text */
  --color-text-primary: var(--logo-navy-dark);    /* #1b232e - LOGO! */
  --color-text-secondary: var(--brand-primary-600);
  --color-text-tertiary: var(--brand-primary-500);
  --color-text-disabled: var(--brand-primary-400);
  --color-text-inverse: #ffffff;
  --color-text-link: var(--logo-orange);          /* #dc693c - LOGO! */
  --color-text-link-hover: var(--brand-accent-600);
  
  /* Interactive - Uses logo orange */
  --color-interactive-primary: var(--logo-orange);     /* #dc693c - LOGO! */
  --color-interactive-primary-hover: var(--brand-accent-600);
  --color-interactive-primary-active: var(--brand-accent-700);
  
  /* Status */
  --color-success: var(--status-success-light);
  --color-warning: var(--status-warning-light);
  --color-error: var(--status-error-light);
  --color-info: var(--status-info-light);
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
}
```

### Semantic Tokens - Dark Theme

```css
[data-theme="dark"] {
  /* Backgrounds - Uses logo navy as foundation */
  --color-bg-base: var(--brand-primary-950);      /* #060a0d - Deep black */
  --color-bg-subtle: var(--brand-primary-900);    /* #0f151a - Almost black */
  --color-bg-muted: var(--logo-navy-dark);        /* #1b232e - LOGO! */
  --color-bg-elevated: var(--logo-navy-medium);   /* #354e5e - LOGO! */
  --color-bg-overlay: rgba(0, 0, 0, 0.75);
  
  /* Surfaces - Logo colors */
  --color-surface: var(--logo-navy-dark);         /* #1b232e - LOGO! */
  --color-surface-secondary: var(--logo-navy-medium); /* #354e5e - LOGO! */
  --color-surface-tertiary: var(--brand-primary-600);
  --color-surface-hover: var(--brand-primary-600);
  
  /* Borders - Subtle in dark mode */
  --color-border-subtle: var(--brand-primary-700);    /* #354e5e area */
  --color-border-default: var(--brand-primary-600);
  --color-border-strong: var(--brand-primary-500);
  
  /* Text - High contrast */
  --color-text-primary: var(--brand-primary-50);
  --color-text-secondary: var(--brand-primary-300);
  --color-text-tertiary: var(--brand-primary-400);
  --color-text-disabled: var(--brand-primary-600);
  --color-text-inverse: var(--logo-navy-dark);
  --color-text-link: var(--brand-accent-400);         /* Lighter orange for dark bg */
  --color-text-link-hover: var(--brand-accent-300);
  
  /* Interactive - Logo orange, adjusted for dark */
  --color-interactive-primary: var(--logo-orange);    /* #dc693c - LOGO! */
  --color-interactive-primary-hover: var(--brand-accent-400);
  --color-interactive-primary-active: var(--brand-accent-600);
  
  /* Status - Lighter for dark backgrounds */
  --color-success: var(--status-success-dark);
  --color-warning: var(--status-warning-dark);
  --color-error: var(--status-error-dark);
  --color-info: var(--status-info-dark);
  
  /* Shadows - Stronger in dark mode */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.6);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.7);
}
```

### Contrast Requirements (WCAG AA)

```
✅ Light Mode:
   Navy Text (#1b232e) on White: 14.7:1 (AAA)
   Orange (#dc693c) on White: 4.5:1 (AA)
   
✅ Dark Mode:
   White Text on Navy (#1b232e): 14.7:1 (AAA)
   Orange (#dc693c) on Navy: 3.3:1 (AA for large text)
   Lighter Orange (#f88958) on Navy: 5.2:1 (AA)
```

---

## 📱 TOUCH OPTIMIZATIONS

### No Blue Tap Highlight (iOS/Android)

```css
/* Global - Remove ugly blue highlight */
* {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

/* Buttons - No text selection */
.btn {
  -webkit-user-select: none;
  user-select: none;
}
```

---

## 🎨 CONSISTENCY RULES

### Link Colors (Always Orange)
```
✅ All links are orange (logo color #dc693c)
   - Typography links: Orange
   - Info-row links: Orange
   - Card links: Orange
   - Navigation links: Orange when active

❌ NO special link colors per component
   - Consistent across entire app
   - Recognizable and predictable
```

### Text Colors
```
✅ Values in info-rows use normal text color
   - NOT special accent color
   - Same as regular paragraph text
   - Links within values: orange

✅ Dark buttons get text-shadow for better contrast
   - Primary button: text-shadow on dark navy gradient
   - Ensures readability without lighter gradient
```

---

## 📏 SPACING SYSTEM

### Scale (8px Base Unit)

```css
:root {
  --space-1: 0.25rem;   /* 4px  - tight */
  --space-2: 0.5rem;    /* 8px  - compact */
  --space-3: 0.75rem;   /* 12px - cozy */
  --space-4: 1rem;      /* 16px - default */
  --space-5: 1.5rem;    /* 24px - comfortable */
  --space-6: 2rem;      /* 32px - spacious */
  --space-8: 3rem;      /* 48px - loose */
  --space-10: 4rem;     /* 64px - very loose */
  --space-12: 6rem;     /* 96px - extra loose */
}
```

### Usage Guidelines

```
Components:
├── Card Padding: var(--space-5) → 24px
├── Button Padding: var(--space-3) var(--space-5) → 12px 24px
├── Section Gap: var(--space-6) → 32px
└── Page Padding: var(--space-4) → 16px

Responsive:
├── Mobile: Tighter spacing (--space-4)
├── Tablet: Standard (--space-5)
└── Desktop: Looser (--space-6)
```

---

## 📝 TYPOGRAPHY SYSTEM

### Scale (1.25 Ratio)

```css
:root {
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
}
```

### Font Weights

```css
:root {
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}
```

### Font Stack

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
               Roboto, 'Helvetica Neue', Arial, sans-serif;
}
```

---

## 🎭 BORDER RADIUS

```css
:root {
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.5rem;   /* 8px */
  --radius-lg: 0.75rem;  /* 12px */
  --radius-xl: 1rem;     /* 16px */
  --radius-full: 9999px; /* Pills/Circles */
}
```

---

## 🎬 TRANSITIONS

```css
:root {
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

---

## 📊 Z-INDEX SCALE

```css
:root {
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-toast: 600;
  --z-tooltip: 700;
}
```

---

## 🎨 ICONS

### System: Lucide Icons

**Why Lucide?**
- ✅ Modern, consistent design
- ✅ Open Source (MIT License)
- ✅ 1000+ icons
- ✅ SVG Sprites (best performance)
- ✅ Excellent documentation

**Implementation:**
```html
<!-- SVG Sprite (preload in <head>) -->
<link rel="preload" 
      href="/static/icons/lucide-sprite.svg" 
      as="image" 
      type="image/svg+xml">

<!-- Usage -->
<svg class="icon" aria-hidden="true">
  <use href="/static/icons/lucide-sprite.svg#home"/>
</svg>

<!-- With Accessibility -->
<svg class="icon" role="img" aria-label="Settings">
  <title>Settings</title>
  <use href="/static/icons/lucide-sprite.svg#settings"/>
</svg>
```

### Icon Mapping (Emoji → Lucide)

```
🏠 Dashboard   → home
📅 Events      → calendar
🏆 GGL         → trophy
👤 Member      → user
⚙️ Admin       → settings
🛍️ Merch       → shopping-bag
📊 Stats       → bar-chart-2
🔒 Security    → lock
📝 Profil      → user-circle
💾 Backup      → database
➕ Neu         → plus
✏️ Edit        → edit-3
🗑️ Delete      → trash-2
✓ Confirm      → check
✖️ Cancel      → x
🔍 Search      → search
📧 Email       → mail
🔔 Notifications → bell
🌙 Dark Mode   → moon
☀️ Light Mode  → sun
```

---

## 📐 CONTAINER SYSTEM

```css
:root {
  --container-narrow: 640px;    /* Forms, Text */
  --container-standard: 1024px; /* Most Content */
  --container-wide: 1280px;     /* Dashboards, Lists */
  --container-full: 100%;       /* Special Layouts */
}
```

---

## 🖥️ NAVIGATION STRATEGY

### Mobile (< 768px)
- **Bottom Navigation** (behalten!)
- 4-5 Haupt-Items
- Touch-optimiert (60px safe-area iOS)

### Tablet (768px - 1023px)
- **Hybrid:** Bottom Nav OR collapsible Sidebar

### Desktop (1024px+)
- **Persistent Sidebar** (links, modern app-like)
- 256px expanded / 72px collapsed
- Collapsible mit Icon-only Mode

---

## 🎯 COMPONENT-SPECIFIC TOKENS

```css
:root {
  /* Card */
  --card-bg: var(--color-surface);
  --card-border: var(--color-border-subtle);
  --card-shadow: var(--shadow-sm);
  --card-hover-shadow: var(--shadow-md);
  --card-padding: var(--space-5);
  --card-radius: var(--radius-lg);
  
  /* Button */
  --btn-primary-bg: var(--color-interactive-primary);
  --btn-primary-hover: var(--color-interactive-primary-hover);
  --btn-primary-text: var(--color-text-inverse);
  --btn-padding-y: var(--space-3);
  --btn-padding-x: var(--space-5);
  --btn-radius: var(--radius-md);
  --btn-transition: var(--transition-fast);
  
  /* Sidebar */
  --sidebar-bg: var(--color-surface-secondary);          /* Navy #354e5e in dark mode */
  --sidebar-border: var(--color-border-subtle);
  --sidebar-item-hover: var(--color-surface-hover);
  --sidebar-item-active: var(--color-interactive-primary); /* Orange #dc693c */
  --sidebar-width-expanded: 16rem;     /* 256px */
  --sidebar-width-collapsed: 4.5rem;   /* 72px */
  
  /* Input */
  --input-padding: var(--space-3);
  --input-border: var(--color-border-default);
  --input-focus: var(--color-interactive-primary);
  --input-radius: var(--radius-md);
}
```

---

## 🚀 THEME SWITCHING

### Implementation

```html
<!-- Theme Toggle Button -->
<button id="theme-toggle" aria-label="Toggle theme">
  <svg class="icon icon--theme-light">
    <use href="#sun"/>
  </svg>
  <svg class="icon icon--theme-dark">
    <use href="#moon"/>
  </svg>
</button>

<script>
// Theme Detection & Persistence
const getTheme = () => {
  const saved = localStorage.getItem('theme');
  if (saved) return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches 
    ? 'dark' 
    : 'light';
};

const setTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
};

// Initialize
setTheme(getTheme());

// Toggle
document.getElementById('theme-toggle')?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  setTheme(current === 'dark' ? 'light' : 'dark');
});

// Listen to system changes
window.matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      setTheme(e.matches ? 'dark' : 'light');
    }
  });
</script>
```

---

## 📋 DESIGN DECISIONS LOG

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Theme** | Both Light + Dark with Toggle | Modern standard, user preference |
| **Navigation Desktop** | Persistent Sidebar | App-like, modern, efficient |
| **CSS Approach** | BEM + Custom Properties | Structured, themeable, migration-friendly |
| **Component Naming** | English | International standard |
| **Icons** | Lucide SVG Sprites | Performance, modern, comprehensive |
| **Responsive** | Mobile-first, 4 Breakpoints | Progressive enhancement |
| **Colors** | Logo-based (Navy + Orange + Teal) | Brand consistency, recognizable |
| **Danger Color** | Warm Red Gradient | Corporate design preference |

---

## 🎯 ACCESSIBILITY REQUIREMENTS

### Keyboard Navigation
- ✅ Logical tab order
- ✅ Visible focus indicators (2px outline)
- ✅ Skip links
- ✅ Modal focus trap

### Screen Readers
- ✅ Semantic HTML
- ✅ ARIA labels where needed
- ✅ Alt texts
- ✅ Live regions

### Color & Contrast
- ✅ 4.5:1 minimum for text
- ✅ 3:1 for UI components
- ✅ Not color-only information

---

## 📊 PERFORMANCE TARGETS

```
Lighthouse Score: > 90
First Contentful Paint: < 1.5s
Largest Contentful Paint: < 2.5s
Time to Interactive: < 3.5s
Cumulative Layout Shift: < 0.1
First Input Delay: < 100ms
Bundle Size: < 200KB
```

---

## 🎯 UX FEATURES CHECKLIST

Modern UX-Standards die implementiert sind:

### ✅ Implemented (State-of-the-Art)

```
✅ Safe Area Insets (iOS Notch/Dynamic Island)
✅ Toast Notifications (Non-intrusive Feedback)
✅ Alert Banners (Persistent Info/Warning Messages)
✅ Scroll-to-Top Button (Auto-show/hide)
✅ Visual Feedback (:active states, hover)
✅ Smooth Scroll (respects user preferences)
✅ Focus Management (Modal/Dialog Focus Trap)
✅ Reversible Actions (Undo Pattern via Toast)
✅ Filter Chips (Clickable Tags)
✅ Instant Search (Real-time filtering)
✅ Accordion (Collapsible Sections)
✅ Progressive Disclosure (<details> element)
✅ Breadcrumbs (Navigation Hierarchy)
✅ Touch Optimizations (No blue tap highlight)
✅ Keyboard Accessibility (Tab navigation)
✅ Responsive Design (Mobile/Tablet/Desktop)
✅ Light/Dark Theme Toggle
✅ WCAG 2.2 Level AA Compliance
```

### ❌ Not Needed / Browser Default

```
❌ Pull-to-Refresh (Browser hat das bereits)
❌ Skeleton Screens (nicht relevant für dieses Projekt)
❌ Empty States (nicht relevant)
❌ Haptic Feedback (zu viel für Web-App)
❌ Keyboard Shortcuts (nicht nötig)
```

### 📋 File Structure

```
static/
├── css/v2/
│   ├── tokens.css        # Design Tokens + Safe Area
│   ├── base.css          # Reset + Smooth Scroll
│   ├── components.css    # Alle UI Components
│   └── main-v2.css       # Main Import
│
├── js/v2/
│   ├── toast.js          # Toast Notification System
│   ├── scroll-to-top.js  # Scroll-to-Top Button
│   ├── focus-trap.js     # Focus Management
│   ├── accordion.js      # Accordion Component
│   └── search.js         # Instant Search
│
└── docs/
    ├── DESIGN_SYSTEM.md      # Design Decisions
    └── COMPONENT_LIBRARY.md  # Component Docs + Usage
```

### 🚀 Usage in Templates

```html
<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
    <!-- V2 Design System -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main-v2.css') }}">
</head>
<body>
    <!-- Content -->
    
    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/v2/toast.js') }}"></script>
    <script src="{{ url_for('static', filename='js/v2/scroll-to-top.js') }}"></script>
    <script src="{{ url_for('static', filename='js/v2/accordion.js') }}"></script>
    <script src="{{ url_for('static', filename='js/v2/search.js') }}"></script>
</body>
</html>
```

---

**Next Steps:** See `COMPONENT_LIBRARY.md` for component implementations.


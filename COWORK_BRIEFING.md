# Cowork-Briefing – Hamburg-HTML für Gourmen PWA

> Begleit-Dokument zu `KONZEPT.md`. Enthaelt **alle** Infos, die Claude Cowork braucht, um die Single-File-HTML so zu bauen, dass Andreas sie minimal-invasiv in `gourmen_pwa` einklinken kann.
>
> Stand: 03.05.2026

> **Status (03.05.2026):** HTML wurde geliefert und ist integriert.
> Live-Pfad: `templates/events/hamburg2026.html`, Route `/events/hamburg2026`.
> Bei weiteren Cowork-Patches: Source ist die integrierte Datei (Logo wurde durch
> `url_for('static', filename='brand/logo-master-round.svg')` ersetzt, ein
> `.hamburg-back`-Link zum Dashboard kam dazu, Leaflet-JS-SRI-Hash wurde gefixt).
> Bei Standalone-Tests bitte das Cowork-Workspace nutzen, nicht die PWA-Datei direkt.

---

## 1. Was du baust

Eine **Single-File `.html`** (alles inline – CSS, JS, Daten, Logo als Data-URI oder Inline-SVG). Ziel: Andreas oeffnet die Datei lokal im Browser zum Reviewen, kopiert sie spaeter als Jinja-Template in die PWA und tauscht den `:root`-Token-Block gegen die echten Tokens. **Keine Build-Pipeline**, **keine Frameworks**, **kein npm-Paket**.

Inhaltlich: 6 Sektionen fuers Hamburg-Wochenende (Hero+Countdown / Programm Tag-fuer-Tag mit Tabs / Locations+Karte / Checkliste / Kontakte / Hausregeln). Spec siehe `KONZEPT.md`, Spur 1.

---

## 2. Wie die PWA tickt (Kurz-Kontext)

- **Verein**: Gourmen, kulinarischer Maennerverein Zuerich. UI-Sprache Deutsch (Schweizer Hochdeutsch, **kein Eszett**, "ss" verwenden).
- **Stack PWA**: Flask 3.x (Server-rendered Jinja2) + Custom CSS V2 (BEM + Design Tokens) + Vanilla JS. Kein Tailwind, kein React.
- **Theme-System**: Light + Dark, gesteuert via `<html data-theme="light">` bzw. `data-theme="dark"`. Beide Modi sind gleichwertig – die HTML **muss in beiden Modi gut aussehen**.
- **Mobile-first**: Bottom-Nav (~80px hoch) auf Mobile, Sidebar ab 1024px. Safe-Area-Insets fuer iOS-Notch werden in der PWA global gehandhabt (`env(safe-area-inset-*)`) – du musst dich darum nicht kuemmern, aber **lass den unteren Viewport-Bereich nicht fuer kritische Tap-Targets** (in der PWA wird die Bottom-Nav drueberliegen).
- **PWA-Service-Worker** uebernimmt Offline-Caching und Cache-Busting. Du musst nichts cachen, **aber**: alle externen CDN-Ressourcen (Leaflet) sollten so eingebunden sein, dass sie der Service Worker problemlos cachen kann (= konkrete URL, kein dynamisches Loading).

---

## 3. Visuelle Identitaet – Tokens 1:1 aus der PWA

**Mach es Andreas einfach**: bau die HTML mit genau diesen CSS Custom Properties im `:root`. Beim Integrieren tauscht er nichts aus, weil die Werte bereits identisch zu `static/css/v2/tokens.css` sind.

### 3.1 Logo-Farben (Foundation)

```css
--logo-navy-dark: #1b232e;
--logo-navy-medium: #354e5e;
--logo-orange: #dc693c;
--logo-teal: #73c8a8;
```

### 3.2 Brand-Paletten (Auszug der wichtigsten Stops)

```css
/* Primary (Navy) */
--brand-primary-50:  #f5f7f9;
--brand-primary-100: #e8ecf0;
--brand-primary-200: #d1d9e1;
--brand-primary-300: #b4c0cd;
--brand-primary-400: #8a9db1;
--brand-primary-500: #667a91;
--brand-primary-600: #4f6477;
--brand-primary-700: #354e5e;
--brand-primary-800: #1b232e;
--brand-primary-900: #0f151a;
--brand-primary-950: #060a0d;

/* Accent (Orange) – fuer CTAs, Highlights, Links */
--brand-accent-400: #f88958;
--brand-accent-500: #dc693c;
--brand-accent-600: #c35428;
--brand-accent-700: #a3421f;

/* Secondary (Teal) – fuer Erfolg/positive Hinweise, dezente Akzente */
--brand-secondary-300: #73c8a8;
--brand-secondary-400: #4db896;
--brand-secondary-500: #2fa885;

/* Warm (Red) – nur fuer echte Warnungen, sparsam */
--brand-warm-500: #ef4444;
--brand-warm-600: #dc2626;
```

### 3.3 Spacing (8px-Basis)

```css
--space-1:  0.25rem;  /*  4px */
--space-2:  0.5rem;   /*  8px */
--space-3:  0.75rem;  /* 12px */
--space-4:  1rem;     /* 16px */
--space-5:  1.5rem;   /* 24px */
--space-6:  2rem;     /* 32px */
--space-8:  3rem;     /* 48px */
--space-10: 4rem;     /* 64px */
```

### 3.4 Typography

```css
/* Skala (1.25-Ratio) */
--text-xs:   0.75rem;   /* 12px */
--text-sm:   0.875rem;  /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg:   1.125rem;  /* 18px */
--text-xl:   1.25rem;   /* 20px */
--text-2xl:  1.5rem;    /* 24px */
--text-3xl:  1.875rem;  /* 30px */
--text-4xl:  2.25rem;   /* 36px */

/* Gewichte */
--font-normal:   400;
--font-medium:   500;
--font-semibold: 600;
--font-bold:     700;
```

**Schrift**: System-Fontstack, **keine Webfonts**:

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
             Roboto, 'Helvetica Neue', Arial, sans-serif;
line-height: 1.6;
```

### 3.5 Border-Radius

```css
--radius-sm:   0.25rem;  /*  4px */
--radius-md:   0.5rem;   /*  8px */
--radius-lg:   0.75rem;  /* 12px – Standard fuer Cards */
--radius-xl:   1rem;     /* 16px */
--radius-full: 9999px;   /* Pills/Chips */
```

### 3.6 Transitions

```css
--transition-fast:   150ms ease;
--transition-normal: 200ms ease;
--transition-slow:   300ms ease;
```

### 3.7 Z-Index

```css
--z-base:           0;
--z-dropdown:     100;
--z-sticky:       200;   /* fuer Sticky-Tab-Navigation */
--z-fixed:        300;
--z-modal:        500;
--z-toast:        600;
```

### 3.8 Semantische Tokens (Light + Dark)

**Wichtig**: in Komponenten **niemals direkt** Brand-Farben verwenden, sondern semantische Tokens. Der ganze Theme-Switch funktioniert dann automatisch.

```css
/* ===== LIGHT (Default in :root) ===== */
:root {
  --color-bg-base:        var(--brand-primary-50);   /* #f5f7f9 */
  --color-bg-subtle:      #ffffff;
  --color-bg-muted:       var(--brand-primary-100);
  --color-bg-elevated:    #ffffff;

  --color-surface:            #ffffff;                /* Cards */
  --color-surface-secondary:  var(--brand-primary-50);
  --color-surface-hover:      var(--brand-primary-100);

  --color-border-subtle:  var(--brand-primary-200);
  --color-border-default: var(--brand-primary-300);
  --color-border-strong:  var(--brand-primary-400);

  --color-text-primary:    var(--logo-navy-dark);
  --color-text-secondary:  var(--brand-primary-600);
  --color-text-tertiary:   var(--brand-primary-500);
  --color-text-disabled:   var(--brand-primary-400);
  --color-text-inverse:    #ffffff;
  --color-text-link:       var(--logo-orange);
  --color-text-link-hover: var(--brand-accent-600);

  --color-interactive-primary:        var(--logo-orange);
  --color-interactive-primary-hover:  var(--brand-accent-600);
  --color-interactive-primary-active: var(--brand-accent-700);

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error:   #ef4444;
  --color-info:    #3b82f6;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}

/* ===== DARK ===== */
[data-theme="dark"] {
  --color-bg-base:     var(--brand-primary-950);
  --color-bg-subtle:   var(--logo-navy-dark);
  --color-bg-muted:    var(--brand-primary-800);
  --color-bg-elevated: var(--logo-navy-medium);

  --color-surface:           var(--logo-navy-dark);
  --color-surface-secondary: var(--logo-navy-medium);
  --color-surface-hover:     var(--brand-primary-600);

  --color-border-subtle:  var(--brand-primary-700);
  --color-border-default: var(--brand-primary-600);
  --color-border-strong:  var(--brand-primary-500);

  --color-text-primary:    var(--brand-primary-50);
  --color-text-secondary:  var(--brand-primary-300);
  --color-text-tertiary:   var(--brand-primary-400);
  --color-text-disabled:   var(--brand-primary-600);
  --color-text-inverse:    var(--logo-navy-dark);
  --color-text-link:       var(--brand-accent-400);
  --color-text-link-hover: var(--brand-accent-300);

  --color-interactive-primary:        var(--logo-orange);
  --color-interactive-primary-hover:  var(--brand-accent-400);
  --color-interactive-primary-active: var(--brand-accent-600);

  --color-success: #34d399;
  --color-warning: #fbbf24;
  --color-error:   #f87171;
  --color-info:    #60a5fa;

  --shadow-sm: 0 1px 2px rgba(6, 10, 13, 0.3);
  --shadow-md: 0 4px 6px rgba(6, 10, 13, 0.4);
  --shadow-lg: 0 10px 15px rgba(6, 10, 13, 0.5);
}
```

### 3.9 Theme-Erkennung im Standalone-File

Da die Standalone-HTML noch keinen Theme-Toggle hat, soll sie den Browser-Modus respektieren:

```html
<script>
  // Vor dem ersten Paint setzen, damit kein FOUC
  (function () {
    const stored = localStorage.getItem('hamburg-theme');
    const prefers = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', stored || prefers);
  })();
</script>
```

Optional: kleiner Theme-Toggle (Sonne/Mond) oben rechts. Nicht zwingend – Andreas wird beim PWA-Einbau ohnehin den globalen Toggle drueberlegen.

---

## 4. BEM-Konvention (Pflicht)

Die PWA verwendet strikt BEM mit englischen Klassennamen:

```
.block               → Block
.block__element      → Element innerhalb des Blocks
.block--modifier     → Modifikator (Variante)
.block__element--mod → Element mit Modifier
```

Beispiele aus der PWA:

```css
.card                  /* generischer Card-Container */
.card__header
.card__body
.card__footer
.card--collapsible     /* Variante: aufklappbar */

.btn
.btn--primary
.btn--outline
.btn--danger
```

**Du** baust eigene Bloecke fuer dieses Module mit dem Praefix `hamburg-` (kollidiert garantiert nicht mit der PWA):

```css
.hamburg-hero
.hamburg-hero__countdown
.hamburg-tabs
.hamburg-tabs__nav
.hamburg-tabs__tab
.hamburg-tabs__tab--active
.hamburg-timeline-item
.hamburg-timeline-item--critical
.hamburg-checklist
.hamburg-checklist__item
.hamburg-map
/* etc. */
```

**Verboten**:
- ❌ Generische Namen wie `.btn-blue`, `.card-2`, `.text-bold`
- ❌ Hardcode-Farben (`#FFAA00`) – immer Tokens
- ❌ Hardcode-Pixel fuer Spacing – immer `--space-*`
- ❌ `!important` ausser dokumentiert
- ❌ Inline-Styles in HTML (Style-Tag im `<head>` ist ok – ist ja Single-File)

---

## 5. PWA-Komponenten-Vokabular (zur Inspiration)

Du **musst diese Klassen nicht uebernehmen** (dein Modul ist isoliert mit `hamburg-*`-Praefix), aber wenn du Patterns brauchst, schau dich hier um – Andreas kann beim Integrieren ggf. auf bestehende Klassen umheben:

| Pattern | PWA-Klasse | Hinweis |
|---|---|---|
| Container max-width | `.container` (max 1200px, Padding `--space-4`) | Du: max 720px wie im Konzept |
| Seitentitel | `.page-header` mit nur `<h1>` | Kein Subtitle-Pflicht |
| Karte | `.card` + `.card__header` / `__body` / `__footer` | Padding via `--card-padding: var(--space-5)` |
| Pille/Tag | `.chip` mit `--small`, `--accent` | radius `--radius-full` |
| Inline-Hinweis | `.alert` mit `--success/--warning/--error/--info` | Mit `__icon`, `__content`, `__title`, `__message` |
| Button | `.btn` + `--primary/--outline/--danger` | Padding y `--space-3`, x `--space-5`, radius `--radius-md` |
| Tabs | `.tabs` + `__nav`, `__tab` | Verwende `role="tab"`, `aria-selected` |
| Aufklappbar | `.disclosure` (auf `<details>`) | Standard zugeklappt |
| Label/Wert-Paar | `.info-row` mit `__label`, `__value` | Fuer Kontakt-Listen ideal |
| Tabelle | `.data-table` (in `.data-table-wrap`) | Scroll-Container fuer Mobile |
| Leerstand | `.empty-state` mit `__icon`, `__message` | Falls Liste leer |

Die volle Component Registry steht in `docs/UI.md` Sektion 5.

---

## 6. Logo

Beide Master-Logos liegen in der PWA unter:

- `static/brand/logo-master-round.svg`
- `static/brand/logo-master-square.svg`

Andreas legt dir die SVG-Files in den Cowork-Workspace. **Bind das Logo inline ein** (entweder als `<svg>...</svg>` direkt im Markup oder als Data-URI), damit die Datei wirklich standalone ist:

```html
<!-- Variante A: Inline SVG -->
<div class="hamburg-hero__logo" aria-hidden="true">
  <svg viewBox="0 0 200 200" ...>...</svg>
</div>

<!-- Variante B: Data-URI -->
<img class="hamburg-hero__logo" alt="Gourmen Logo"
     src="data:image/svg+xml;base64,..." />
```

**Konzept-Vorgabe**: Hero verwendet das **runde Logo**, Footer optional das eckige.

---

## 7. Icons

Die PWA nutzt **Lucide** als SVG-Sprite (`static/icons/lucide-sprite.svg`). Fuer dein Standalone-File ist das overkill. Wir machen es so:

- **Emojis sind ok** fuer dein Modul (das Konzept nutzt sie ja: 📅 ✈️ 🏨 🐟 🎭 🎸 🍺 ⛵), weil die HTML emotionaler/freier sein darf als der Rest der PWA.
- Falls du **Lucide-Icons** willst (z.B. fuer Tab-Pfeile, Chevrons, Map-Pin): **inline einbetten**, nicht via Sprite. Die paar Icons, die du brauchst, holst du aus [lucide.dev](https://lucide.dev/icons/) und kopierst das SVG-Markup direkt rein.

```html
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="..."/>
</svg>
```

Standardgroesse `1.25rem × 1.25rem`, Stroke `currentColor`.

---

## 8. Schweizer Konventionen (Pflicht in allem Text)

- **Anfuehrungszeichen**: «...» (Guillemets, nicht "..." oder „...")
- **Gedankenstrich**: – (Halbgeviertstrich, U+2013), nicht — und nicht -
- **Apostroph**: ’ (typografisch) wo moeglich, ' geht zur Not
- **Kein Eszett**: "Strasse" statt "Straße", "Schluss" statt "Schluß", "muss" statt "muß"
- **Tausender-Trennzeichen**: ' (Apostroph), z.B. `5'000 €`
- **Zahl + Einheit**: geschuetzes Leerzeichen `&nbsp;` (z.B. `06:30&nbsp;Uhr`, `5'000&nbsp;€`)
- **Datum**: `Fr 29.05.2026` oder `29. Mai 2026` (kein US-Format)
- **Uhrzeit**: 24h, `06:30`, `18:25` (kein "6:30 AM")

---

## 9. Externe Abhaengigkeiten

Erlaubt nach Konzept:

- **Leaflet** via CDN (cdnjs), pinned auf `1.9.x`. Beispiel:
  ```html
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
        integrity="..."  crossorigin="anonymous">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"
          integrity="..." crossorigin="anonymous" defer></script>
  ```
  **Mit SRI-Hashes** (`integrity`-Attribut). Andreas wird die URLs spaeter ggf. selbst gegen den Service-Worker-Cache verifizieren.
- **Tile-Provider**: OpenStreetMap (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`), Attribution Pflicht: `© OpenStreetMap contributors`.

**Verboten**:
- ❌ Google Fonts (System-Fonts, siehe oben)
- ❌ Google Analytics, Plausible, oder sonstiges Tracking
- ❌ Google Maps (datenschutzrechtlich, Konzept-Vorgabe Leaflet/OSM)
- ❌ jQuery, React, Vue, irgendein Framework
- ❌ Externe Webfonts ueberhaupt
- ❌ Inline `<style>`-Inhalte aus Dritt-CDNs

---

## 10. JavaScript-Konventionen

- **Vanilla ES2020+**, kein Build-Step.
- **Module-Pattern oder IIFE** zur Vermeidung globaler Pollution.
- **`defer`** bei `<script>`-Tags, ausser dem theme-init-Script (das muss synchron im `<head>` laufen).
- **Event-Listener** ueber `addEventListener`, kein `onclick="..."` im Markup.
- **Sparsam mit JS**: alles was ohne JS lesbar bleiben kann (Kontakte, Adressen, Hausregeln) muss ohne JS funktionieren. Tabs-Navigation und Countdown sind die einzigen JS-Pflicht-Teile.
- **`prefers-reduced-motion`** respektieren – keine Auto-Animationen wenn der User Reduced Motion gesetzt hat.

### localStorage-Namespace

Damit nichts mit der PWA kollidiert, **alle Keys praefixen**:

```js
const LS_PREFIX = 'hamburg2026:';

localStorage.setItem(LS_PREFIX + 'checklist', JSON.stringify(state));
localStorage.setItem(LS_PREFIX + 'theme', 'dark');
```

Reset-Button im Checklisten-Block soll **nur** Keys mit diesem Praefix loeschen.

---

## 11. Akzeptanzkriterien (aus KONZEPT.md)

Pflicht-Checkliste fuer dein Final-Build:

- [ ] Single-File HTML, alles inline (CSS, JS, Logo)
- [ ] Laedt in unter 1s auf 4G
- [ ] Funktioniert offline nach erstem Aufruf (= keine externen Calls ausser Leaflet+OSM-Tiles)
- [ ] Kontakte, Adressen, Hausregeln **lesbar ohne JS**
- [ ] Mobile-tested-fit (375px Breite minimum sauber, max. 720px zentriert auf Desktop)
- [ ] Adressen-Tap oeffnet native Maps-App (`geo:`-URI oder `https://www.google.com/maps/dir/?...`-Link)
- [ ] Tel-Links als `tel:+49...` (mit Laendercode!)
- [ ] Mail-Links als `mailto:`
- [ ] Light **und** Dark Theme funktionieren
- [ ] Schweizer Typografie konsequent durchgezogen
- [ ] Alle Texte deutsch, kein Eszett
- [ ] Validates als HTML5 (W3C-Validator gruen)
- [ ] Keyboard-navigierbar (Tabs, Checklisten, Aufklapper)
- [ ] `prefers-reduced-motion` respektiert (Countdown-Tick reicht, kein Wackel-FX)
- [ ] Keine Console-Errors in Chrome DevTools

---

## 12. Datei-Struktur fuer Andreas' Integration (FYI)

Beim Einbau in die PWA wird Andreas:

1. Die Single-File HTML in `templates/events/hamburg2026.html` kopieren
2. Den `<!DOCTYPE>`/`<html>`/`<head>`/`<body>`-Wrapper entfernen
3. `{% extends "base.html" %}` an den Anfang setzen
4. Den restlichen Inhalt in `{% block content %}...{% endblock %}` packen
5. Die Inline-`<style>`s nach `static/css/v2/hamburg.css` extrahieren (oder in components.css mergen)
6. Die Inline-`<script>`s nach `static/js/v2/hamburg.js` extrahieren
7. Das runde Logo durch `<img src="{{ url_for('static', filename='brand/logo-master-round.svg') }}">` ersetzen
8. Eine Blueprint-Route registrieren (`/events/hamburg2026`)
9. Cache-Buster bumpen (`sw.js`, `base.html`, `pwa.js`)

**Du musst dafuer nichts tun** – aber halte die HTML so strukturiert, dass diese Schritte einfach sind:

- CSS in **einem** `<style>`-Block im `<head>`, klar mit Kommentar-Bloecken gegliedert (Tokens / Reset / Layout / Components / Utilities)
- JS in **einem** `<script>`-Block am Ende von `<body>` (ausser theme-init im Head)
- Logo so, dass es leicht durch ein `<img>` ersetzbar ist (separater Wrapper, klares Klassen-Marker)
- Inhalts-Daten (Programm-Eintraege, Kontakte) **als JS-Datenobjekt** am Anfang des Script-Blocks deklarieren, damit Andreas sie ggf. in ein Jinja-Render verwandelt

---

## 13. Was du NICHT tun sollst

- ❌ Keine Build-Tools (kein webpack, vite, rollup, sass)
- ❌ Kein `npm install` von irgendwas
- ❌ Keine externen Webfonts oder Icon-Pakete als CDN
- ❌ Kein Tracking, Analytics, Cookies, Consent-Banner
- ❌ Kein Service Worker im File (uebernimmt die PWA)
- ❌ Kein Manifest.json (uebernimmt die PWA)
- ❌ Keine Push-Notifications (uebernimmt die PWA)
- ❌ Kein Login, keine User-Identitaet, kein Backend-Call
- ❌ Keine Bilder via externe URLs (ausser OSM-Tiles)
- ❌ Kein "Powered by" / Copyright-Footer von Tools
- ❌ Keine Kommentare die nur sagen was der Code macht (`// increment counter`) – nur warum

---

## 14. Schnell-Referenz: was Andreas dir liefert

- ✅ `KONZEPT.md` – Inhalt und Sektionen
- ✅ `COWORK_BRIEFING.md` (dieses Dokument) – Stil und Tech-Vorgaben
- ✅ `logo-master-round.svg` – fuer Hero (inline einbetten)
- ✅ `logo-master-square.svg` – optional fuer Footer
- 🟡 Finale Inhalte (Programm-Slots, Adressen, Telefonnummern, Hausregeln) – ergeben sich aus KONZEPT.md plus Andreas' Recherche; Platzhalter wo unklar (`TODO: Adresse Stambula final`)

## 15. Bei Unklarheit

Stoppen, Andreas fragen. Lieber eine Praezisierung als eine Annahme, die spaeter beim PWA-Einbau zu Refactoring fuehrt. Speziell bei:

- Welche Token-Werte du nehmen sollst, wenn das Konzept und dieses Briefing sich widersprechen → **dieses Briefing gewinnt**
- Welche Sektionsreihenfolge final stimmt → **KONZEPT.md gewinnt**
- Wie ein UX-Pattern aussehen soll, das nicht spezifiziert ist → kurz nachfragen statt erfinden

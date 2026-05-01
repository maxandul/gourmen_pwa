# UI – Designsystem & Component Registry

Verbindliche UI-Konventionen für Gourmen PWA. Vor jeder Template-, CSS- oder JS-Änderung **diese Datei lesen**.

## 1. Grundsatz-Entscheidungen

| Thema | Entscheidung |
|---|---|
| **CSS-Ansatz** | Custom CSS mit BEM + Design Tokens. **Kein** Tailwind, **kein** DaisyUI/Shoelace. |
| **Naming** | BEM (englisch): `block__element--modifier` |
| **Design-Werte** | Nur Tokens aus `static/css/v2/tokens.css`, keine Hex/Pixel-Magic-Numbers |
| **Theming** | `data-theme="light"` und `data-theme="dark"` gleichwertig |
| **Icons** | Lucide via SVG-Sprite (`static/icons/lucide-sprite.svg`); Font Awesome wird abgelöst |
| **Breadcrumbs** | Keine. Nutzung von `.page-back` zum Elternziel |
| **Page-Header** | Nur `h1`, kein zusätzliches Subtitle |
| **Layout** | Mobile-first, Bottom-Nav (4 Bereiche) + Sidebar ab 1024px |
| **Templates** | `base.html` + Partials in `templates/partials/` |

Eine **Abweichung** von einer Grundsatz-Entscheidung erfordert User-Auftrag und einen Eintrag im Entscheidungslog (siehe Sektion 8 unten).

## 2. Datei-Struktur (CSS)

```
static/css/v2/
├── tokens.css          → Design Tokens (Farben, Spacing, Typography, Shadows)
├── base.css            → Reset, Typography, Base-Elements
├── layout.css          → Layout-Container, Grid, Sidebar, Bottom-Nav
└── components.css      → Alle Komponenten (BEM-Klassen)

static/css/
├── animations.css      → Animations / Transitions
├── responsive.css      → Media-Query-Anpassungen
├── mobile-touch.css    → Touch-spezifisches
├── notifications.css   → Toast/Notification-Styles
├── pwa.css             → PWA-spezifisch (Install-Prompt, Update-Banner)
└── (Legacy: components.css, layout.css, core.css, features.css)
```

Bundle-Datei `main-v2.css` wird via Asset-Manifest mit Hash-Suffix ausgeliefert (`main-v2.<hash>.css`).

## 3. Design Tokens (Auszug)

Vollständige Liste in `static/css/v2/tokens.css`. Wichtigste Gruppen:

### Logo-Farben (Foundation)

```css
--logo-navy-dark: #1b232e;
--logo-navy-medium: #354e5e;
--logo-orange: #dc693c;
--logo-teal: #73c8a8;
```

### Brand-Paletten (50–950 Skala)

- `--brand-primary-*` (Navy)
- `--brand-accent-*` (Orange)
- `--brand-secondary-*` (Teal)
- `--brand-warm-*` (Red, Danger)

### Spacing (8px-Basis)

```css
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
--space-5: 24px;  --space-6: 32px;  --space-8: 48px;  --space-10: 64px;
```

### Typography (1.25-Ratio)

```css
--text-xs: 12px;   --text-sm: 14px;   --text-base: 16px;
--text-lg: 18px;   --text-xl: 20px;   --text-2xl: 24px;
--text-3xl: 30px;  --text-4xl: 36px;
```

### Semantische Tokens (Theme-abhängig)

Diese sind in `:root` für Light-Default gesetzt; `[data-theme="dark"]` überschreibt für Dunkelmodus:

- `--color-bg-base`, `--color-bg-subtle`, `--color-bg-muted`, `--color-bg-elevated`
- `--color-surface`, `--color-surface-secondary`, `--color-surface-elevated`
- `--color-border-subtle`, `--color-border-default`, `--color-border-strong`
- `--color-text-primary`, `--color-text-secondary`, `--color-text-tertiary`
- `--color-interactive-primary`, `--color-interactive-primary-hover`
- `--color-success`, `--color-warning`, `--color-error`, `--color-info`
- `--shadow-sm/md/lg/xl`

**Regel**: Komponenten verwenden **semantische Tokens**, niemals direkt Brand-Paletten oder Logo-Farben (außer in `tokens.css` selbst).

## 4. Decision Tree – Brauche ich eine neue Klasse?

```
   Soll eine UI hinzugefügt/geändert werden?
              │
              ▼
   Existiert eine bestehende Klasse, die das abdeckt?
   (Component Registry in Sektion 5 prüfen + grep im Repo)
              │
       ┌──────┴──────┐
       │             │
      JA            NEIN
       │             │
       ▼             ▼
   Verwenden      Reicht ein Modifier (--variant)
                  einer bestehenden Klasse?
                       │
                ┌──────┴──────┐
                │             │
               JA            NEIN
                │             │
                ▼             ▼
        Modifier hinzu   Wirklich neue Klasse:
        (Registry        - User fragen
        ergänzen wenn    - Begründung im Commit
        modifier neu)    - In Component Registry
                           ergänzen + Begründung
                         - BEM-Naming verwenden
                         - Nur semantische Tokens
```

## 5. Component Registry

### 5.1 Atoms / Basis

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.btn` | `--primary`, `--success`, `--danger`, `--outline`, `--billbro` | Buttons, einzige zugelassene Button-Klasse |
| `.icon` | `--sm`, `--md`, `--lg` | SVG-Icon (aus Lucide-Sprite) |
| `.chip` | `--small`, `--accent` | Tag/Label-Pille |
| `.alert` | `--success`, `--warning`, `--error`, `--info` | Inline-Hinweis (im Content), nicht für Flash |
| `.empty-state` | `--filtered` | Leerstand-Anzeige in Listen, mit `__icon`, `__message` |

### 5.2 Layout / Navigation

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.container` | – | Page-Container mit Max-Width |
| `.page-header` | – | Seitentitel-Bereich (nur `h1`) |
| `.page-back` | – | „Zurück"-Link mit chevron-left |
| `.bottom-nav` | – | Bottom-Navigation Mobile |
| `.sidebar` | – | Desktop-Sidebar ab 1024px |
| `.user-bar` | – | Top-Leiste mit Theme-Toggle und User-Menu |
| `.user-menu` | – | mit `__summary`, `__panel`, `__list`, `__link`, `__link--danger`, `__sep`, `__badge` |
| `.settings-nav` | – | mit `__section`, `__section-title`, `__list`, `__row`, `__icon`, `__meta`, `__label`, `__description`, `__badge`, `__chevron` |

### 5.3 Card-Familie

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.card` | `--collapsible`, `--filter` | Generischer Container für zusammenhängende Blöcke |
| `.card__header` | – | Card-Kopfzeile |
| `.card__body` | – | Card-Inhalt |
| `.card__footer` | – | Card-Aktionen unten |
| `.card__title` | – | Titel im Header |
| `.card__actions` | `--split-toggle` | Aktion-Container |
| `.card__actions-chips` | – | Chips neben Toggle |
| `.card__collapsible-content` | – | Inhalt einer collapsiblen Card |
| `.card__toggle` | – | Toggle-Button für collapsible |
| `.card-section` | `--accent` | Sektion innerhalb einer Card |
| `.card-section__header` / `__title` / `__body` | – | Card-Section-Aufbau |

**Regel**: Cards für **Objekte / zusammenhängende Blöcke**. Nicht für jede Info-Liste.

### 5.4 Daten-Anzeige

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.info-row` | – | Label/Value-Paar mit `__label`, `__value` |
| `.data-table-wrap` | – | Wrapper um Tabellen (Scroll-Container) |
| `.data-table` | – | Standard-Tabelle (BEM-aligned) |
| `.data-table__cell--event-type` | – | Spezial-Zelle für Event-Typ-Icons |
| `.stat-tiles` | `--metrics-follow` | Container für Stat-Tiles |
| `.stat-tile` | – | Einzelne Kennzahl-Kachel |
| `.metrics-spotlight` | – | Hero-Kennzahlen mit `__context`, `__hero`, `__metric*` |
| `.metrics-insight-panel` | – | Panel mit `__section`, `__heading`, `__list`, `__item`, `__value` |

**Regel**: Volle `data-table`-Listen direkt im Tab/Panel, **nicht** zusätzlich in eine Card packen.

### 5.5 Hub-Pattern (Übersichtsseiten)

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.hub-grid` | – | Auto-Fit-Grid für Hub-Seiten (Member, Admin, Settings) |
| `.hub-card` | `--featured` | Kachel auf Hub-Grid (kombiniert mit `.card`) |

### 5.6 Forms

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.form` | – | Formular-Container |
| `.form-field` | – | Form-Feld (Label + Input + Error) |
| `.form-actions` | – | Buttons-Container am Form-Ende |

### 5.7 Tabs / Disclosure

| Klasse | Modifikatoren | Zweck |
|---|---|---|
| `.tabs` | `--panel` | Tab-Container (mit `--panel` für Bereichs-Tabs) |
| `.tabs__nav` / `.tabs__tab` | – | Tab-Navigation |
| `.disclosure` | – | Aufklappbares Element (für Tool-Strip) |

### 5.8 Tool-Strip (Filter / Planung)

Sekundäre Toolleisten (Filter, Planung etc.) verwenden ein einheitliches Muster:

```html
<div class="card card--filter tool-surface">
  <details class="disclosure">
    <summary>...</summary>
    <div class="tool-strip__actions">
      <!-- nur Buttons, ohne Eingabefelder -->
    </div>
    <!-- ODER -->
    <form>
      ...
      <div class="form-actions">
        <button class="btn btn--primary">Filtern</button>
      </div>
    </form>
  </details>
</div>
```

Verhalten:
- **Standardmäßig eingeklappt**
- **Nach GET-Submit „Filtern"**: einklappen + State in `sessionStorage`

### 5.9 Bereichs-spezifische Komponenten

#### Dashboard

| Klasse | Zweck |
|---|---|
| `.dashboard-intent` | Container mit `__heading`, `__grid` |
| `.dashboard-intent-tile` | Kachel mit `__icon`, `__body`, `__title`, `__meta`, `__chev`, `--static` |

#### Events / Ratings

| Klasse | Zweck |
|---|---|
| `.events-participants-table` | Teilnehmer-Tabelle mit `__col-member`, `__col-status`, `__row--current` |
| `.events-ratings-others-table` | Andere-User-Ratings mit `__col-member`, `__col-score`, `__col-highlight`, `__highlight-text`, `__dash`, `__row--current` |
| `.event-ratings-all` | Container für alle Ratings + `__heading` |
| `.event-ratings-toolbar` | mit `__hint`, `__actions` |
| `.events-stats-restaurant-block` | Stats-Block mit `__heading`, `__caption` |
| `.events-stats-restaurant-ratings-table` | Restaurant-Ratings-Tabelle |
| `.events-stats-sort-btn` | Sort-Button mit `--active` |
| `.events-stats-inline-rating` | Inline-Rating-Anzeige |
| `.events-cleanup-hint` | Cleanup-Hinweis |

#### GGL

| Klasse | Zweck |
|---|---|
| `.ggl-ranking-table` | GGL-Ranking-Tabelle mit Spalten/Zeilen-Modifikatoren |

#### BillBro

| Klasse | Zweck |
|---|---|
| `.billbro-workflow` | Workflow-Container mit `__step`, `__step--done`, `__step--current`, `__index` |

#### Cleanup-Workflows

| Klasse | Zweck |
|---|---|
| `.cleanup-step-nav` | Schritt-Navigation mit `__counter`, `__actions` |
| `.cleanup-undo-form` | Undo-Form |

#### Errors / PWA

| Klasse | Zweck |
|---|---|
| `.error-page` | HTTP-Fehlerseite mit `__code`, `__actions` |
| `.offline-shell` | PWA-Offline-Shell mit `__inner`, `__lead` |

### 5.10 Deprecated / Legacy

Folgende Klassen existieren historisch und sollen **nicht in neuen Komponenten** verwendet werden. Bei Refactoring wenn möglich entfernen:

- `.dashboard-next-event*`, `card--dash-tile*`, `.dashboard-card-link`
- `.dashboard-hygiene-rows`, `.dashboard-row-link` (+ `--block-start`)
- `.context-actions` (mit `__title`, `__buttons`) – Sonderfall

Komponenten ohne Verwendung in Templates können ohne Diskussion gelöscht werden – aber **erst** mit `grep` verifizieren.

## 6. Verbote

- ❌ **Keine Inline-Styles** in HTML außer mit explizitem User-OK + Begründung im Commit
- ❌ **Keine Hardcode-Farben** (`#FFAA00`) – Token verwenden
- ❌ **Keine Hardcode-Pixel** für Spacing – `--space-*` verwenden
- ❌ **Keine generischen Klassennamen** wie `.btn-blue`, `.card-2`, `.text-bold`
- ❌ **Keine `!important`** außer dokumentiert (siehe `[hidden]` in `base.css` als Beispiel)
- ❌ **Kein Tailwind, DaisyUI, Bootstrap o.ä.** ohne User-Auftrag
- ❌ **Keine neuen Pattern** ohne User-OK + Registry-Update
- ❌ **Keine Brand-Farben direkt** in Komponenten – nur semantische Tokens

## 7. Cache-Buster (Pflicht nach UI-Änderungen!)

PWA-Browser-Caches werden nur invalidiert wenn die Asset-URLs sich ändern. Daher: nach **JEDER** UI-Änderung Cache-Version bumpen.

### Was bumpen

#### `static/sw.js`

```javascript
const CACHE_NAME = 'gourmen-v1.3.6';        // ← bumpen!
const STATIC_CACHE = 'gourmen-static-v1.3.6';
const DYNAMIC_CACHE = 'gourmen-dynamic-v1.3.6';
```

#### `templates/base.html`

```html
<script src="{{ url_for('static', filename='js/pwa.js') }}?v=1.3.6" defer></script>
<script src="{{ url_for('static', filename='js/app.js') }}?v=1.3.6" defer></script>
```

#### `static/js/pwa.js` (optional)

```javascript
updateAppInfo() {
    const versionSpan = document.getElementById('app-version');
    if (versionSpan) {
        versionSpan.textContent = '1.3.6';  // ← auch ändern
    }
}
```

### Wann bumpen

- ✅ **Immer**: CSS-Änderung, JS-Änderung, Template-Änderung, Icon-Änderung, Manifest-Änderung
- ⚡ **Optional**: reine Backend-Änderungen ohne Frontend-Effekt

### Versionierung

Semantic Versioning:
- **Patch** (1.3.5 → 1.3.6): Bug-Fixes, kleine Änderungen
- **Minor** (1.3.6 → 1.4.0): Neue Features (abwärtskompatibel)
- **Major** (1.4.0 → 2.0.0): Breaking Changes

### Helfer-Skript

`scripts/update_pwa_version.py` automatisiert das Bumpen. Aufruf:

```bash
python scripts/update_pwa_version.py 1.3.6
```

(Dann verifizieren in `sw.js`, `base.html`, `pwa.js`.)

## 8. Entscheidungslog

Wenn von Grundsatz-Entscheidungen abgewichen wird, hier dokumentieren.

| Datum | Entscheidung | Begründung | Betroffene Bereiche |
|---|---|---|---|
| 2026-04-03 | BEM + Tokens, kein Tailwind | Maximale Kontrolle, kein Build-Step für CSS | gesamte UI (Phase 0a Redesign) |
| _aktuell_ | _zukünftige Einträge hier_ | | |

## 9. Workflow für UI-Änderungen

```
1. docs/UI.md lesen (diese Datei)
2. Bei aktiver Initiative: deren Phasen-Doc lesen
3. Mit grep prüfen: existiert eine passende Klasse schon?
4. Bei Lücke: Decision Tree anwenden (Sektion 4)
5. Code schreiben (BEM, Tokens)
6. Cache-Buster bumpen (sw.js, base.html, pwa.js)
7. Lokal testen: Mobile + Desktop, Dark + Light
8. Bei neuer Klasse: docs/UI.md Component Registry erweitern
9. Commit
```

## 10. Demo-Page

Die `/demo/design-system`-Route zeigt visuell alle Komponenten. Aktuell Stand prüfen ob noch funktional und gepflegt.

## 11. Quellen / Historie

- Component Registry initial aus Phase-0a des Redesigns (siehe `docs/initiatives/_archive/2025_redesign/REDESIGN.md`).
- Cache-Buster-Workflow ursprünglich aus `UPDATE_CHECKLIST.md` (jetzt obsolet, Inhalt hier integriert).
- Token-System aus `static/css/v2/tokens.css` (Stand 2025-01-29).

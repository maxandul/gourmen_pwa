# Gourmen PWA — UX Redesign (Master-Dokument)

Operatives Handbuch für Agents und Menschen. **Vor jeder Redesign-Änderung** die für die Aufgabe relevanten Abschnitte lesen. **Neue Agents:** Chat-Verläufe sind nicht verfügbar — verbindliche Regeln und Entscheidungen stehen **hier** und im **Entscheidungslog** (Abschnitt 12); Handoff-Regeln in **Abschnitt 6.1**.

---

## 1. Überblick

**Gourmen PWA** ist die Web-App des Gourmen-Vereins (Events, GGL/BillBro, Merch, Mitglieder).

**Redesign-Ziel:** Starke **Usability** und **visuelle Differenzierung** — nicht alles als gleiche Card mit `info-row`. Mobile und Desktop gleichwertig. Langfristig erweiterbar (weitere Hauptbereiche).

**Relevante Pfade:** `templates/**/*.html`, `static/css/v2/*.css`, `static/js/v2/*.js`, gebündelt u. a. als `static/css/main-v2.*.css`. **Abschluss und Aufräumen:** §16.

### Verbindliche technische Grundentscheidung (Phase 0a)

In der Konzeptionsphase als **„Option A“** bezeichnet — **vom Product Owner am 2026-04-03 bestätigt.** Das ist keine offene Alternative mehr, sondern die **Projektregel** für dieses Redesign.

**Inhalt:** Eigenes CSS mit **BEM**-Klassen und **Design Tokens** (`static/css/v2/tokens.css`); **kein** Tailwind CSS, **kein** DaisyUI/Shoelace o. ä. Raster und Breakpoints orientieren sich an gängigen Praktiken (z. B. 4/8-Spacing, 768px / 1024px), die **Umsetzung** erfolgt aber **ausschließlich** über bestehende oder neu definierte **CSS-Variablen** und **benannte Komponenten** laut Registry (Abschnitt 5).

**Für neue Agents — umsetzen:**

- Arbeit an `static/css/v2/*.css` und Templates; neue Bausteine als BEM-Klassen; Snippets in Abschnitt 5 pflegen.
- Farben, Abstände, Schatten nur über **Tokens** / semantische Variablen, keine beliebigen Hex-Werte oder Magic Numbers.

**Für neue Agents — nicht tun (ohne ausdrücklichen User-Auftrag):**

- Kein neues CSS-Utility-Framework einführen oder parallel schalten.
- Keine neuen Komponenten-Klassen „nebenbei“ erfinden: Registry prüfen; bei Lücke User fragen und Registry aktualisieren.
- Keinen erneuten „CSS-Ansatz wählen“-Diskurs starten — die Entscheidung ist dokumentiert; Änderung nur nach User-Vorgabe + Eintrag ins Entscheidungslog.

---

## 2. UX-Leitprinzipien (Kurz)

Entscheidungen beziehen sich auf diese Heuristiken (Nielsen, angepasst):

1. Sichtbarkeit des Systemstatus  
2. Übereinstimmung mit der realen Welt  
3. Nutzerkontrolle und Freiheit  
4. Konsistenz und Standards  
5. Fehlervermeidung  
6. Erkennen statt Erinnern  
7. Flexibilität und Effizienz  
8. Ästhetisches, minimalistisches Design  
9. Fehlerbehebung unterstützen  
10. Hilfe und Dokumentation  

Bei **wesentlichen** UX-Fragen: dem User **Optionen** nennen, **Empfehlung** geben, Begründung mit Prinzipien.

---

## 3. Grundsatzentscheidungen (Phase 0a)

| Thema | Entscheidung |
|--------|----------------|
| **CSS** | Custom **BEM** + **Tokens**; keine Tailwind-/DaisyUI-Migration im aktuellen Redesign. |
| **Card** | Card für **Objekte / zusammenhängende Blöcke**; **nicht** für jede Infoart. KPI-Listen: eigene Muster (**stat-tile**, **compact-list** — in Phase 1 ff. definieren und hier dokumentieren). |
| **Breadcrumbs** | Kein Fokus auf klassische Breadcrumbs auf Mobile; Orientierung über **Nav + Titel**. Optional Desktop oder **„Zurück zu Events“** statt Kette. |
| **Tabs** | Tabs für **getrennte Ansichten innerhalb eines Bereichs** (Events, GGL, Event-Detail). Sparsam halten; langfristig **clientseitiges Umschalten** wo sinnvoll (ohne volle Seitenlast), mit URL-Fallback. |
| **Hauptnavigation** | **Bottom-Nav** (4) + **Sidebar** ab 1024px; **Admin** über User-Bar-Icon, nicht als 5. Tab. Skalierung neuer Bereiche: **„Mehr“** / Drawer o. ä. |
| **Dark/Light** | **Beibehalten** (`data-theme`, Tokens). |
| **Icons** | **Konsolidierung auf Lucide (Sprite)**; Font Awesome langfristig entfernen. |
| **Templates** | `base.html` in **Partials** splitten — **Shell + `<head>`** unter `templates/partials/` (siehe **§13.2**). `{% block title %}`, `{% block og_* %}`, `{% block twitter_* %}`, `{% block head %}` bleiben in **`base.html`** (Jinja-Vererbung). Wiederkehrende Fragmente zusätzlich als **Jinja-Macros**. |
| **Page-Header** | **Standard: nur `h1`** (Seitentitel). Kein verpflichtendes `page-subtitle`; Kurz-Kontext bei Bedarf **in der `h1`-Zeile** (z. B. „Mitglied bearbeiten · Max M.“) oder im Inhalt — nicht als zweite Intro-Zeile unter dem Titel. |
| **Filter-UI** | Überall gleiches Muster: **`card card--filter`** + **`disclosure`**. Visuell **sekundär zur Inhalts-Card**: flach, **ohne** Schatten/Hover-Lift (`components.css`: `.card.card--filter`). |
| **Design-Raster** | Nur **`--space-*`**, Typo- und Farb-Tokens aus `tokens.css`; keine willkürlichen Pixelwerte. Breakpoints wie in `DESIGN_SYSTEM.md` / Layout (u. a. 768, 1024). |

---

## 4. Informationsarchitektur

### 4.1 Hauptbereiche

| Bereich | Inhalt |
|---------|--------|
| **Dashboard** | Persönlicher **Jetzt**-Einstieg: nächstes Event, RSVP, optional GGL-Kurzlink; kein Ersatz für volle Event-/GGL-Listen. |
| **Events** | Termine, RSVP, Detail, BillBro, Bewertungen, Archiv, Statistiken. |
| **GGL** | Saison, Rang, Tabelle, Verlauf — ohne Event-Verwaltung. |
| **Member** | Konto, Profil, Sicherheit, Technik, **Merch-Shop** (kaufen). |
| **Admin** | Mitglieder, **Merch-Verwaltung**, **Events-Meta** (Jahresplanung, Backup-Bearbeitung) — siehe Rollen unten. |

### 4.2 Member- und Admin-Hub

**Keine KPI-Karten-Hubs.** Stattdessen **Einstellungsliste (Settings-Pattern)**:

- Sektionen (z. B. Konto, Merch, Sicherheit, App)
- Zeilen: Icon, Titel, optional **Badge** für Status (z. B. 2FA aus), Chevron/Link
- **Keine** großen Kennzahlenblöcke

**Admin-Hub:** gleiches **Listen-/Navigationsmuster**; Einträge z. B. Mitglieder verwalten, Merch verwalten, Events / Jahresplanung (siehe Rollen).

**Member-Bereich:** für Admins **nicht** viele Deep-Links in die Verwaltung; optional **eine** Zeile „Verwaltung“ → `admin.index`. Primär: **User-Bar → Admin**.

### 4.3 Rollen: Organisator vs. Admin (Events)

- **Organisator** (nicht zwingend Admin): alle inhaltlichen Schritte **nur** über **Events** / **Event-Detail** (Infos, BillBro, Planung). **Kein** Zwang in den Admin-Bereich.
- **Admin:** einmal jährlich **Jahresplanung / Anlage** der kommenden Events; **Backup:** Event bearbeiten, **Organisator umhängen**, löschen. Diese Verwaltungsfunktionen **im Admin-Bereich** auffindbar (parallel zu Merch-Verwaltung).
- **Technisch:** **eine** Bearbeitungs-Oberfläche / Route-Logik wo möglich; **zwei Navigationspfade** für Admins (Admin-Hub + optional weiterhin im Event) sind akzeptabel, **keine** doppelten widersprüchlichen Formulare pflegen.

### 4.4 Kontextuelle Admin-/Organisator-Aktionen (Phase 0b)

**Einheitliches Muster:** **`context-actions`** — schmale **Kontextleiste direkt unter `page-header`**, vor Tabs/Inhalt. Nur sichtbar für berechtigte Rollen. Enthält z. B. „Planung“-Aktionen (Bearbeiten, Jahresplanung nur wo sinnvoll, …). **Keine** zusätzliche volle Card nur für dieselbe Funktion.

Drei-Punkte-Menü nur als **spätere** Ergänzung bei Platzengpass, nicht Standard.

---

## 5. Komponenten-Katalog (lebendes Dokument)

### 5.1 Bestehend (V2) — weiter verwenden bis Migration

| Muster | Klassen (Auszug) | Verwendung |
|--------|-------------------|------------|
| Button | `.btn`, `.btn--primary`, `.btn--outline`, `.btn--danger`, … | Aktionen |
| Card | `.card`, `.card__header`, `.card__body`, `.card__footer` | Objekt-Container |
| Info-Zeile | `.info-row`, `.info-row__label`, `.info-row__value` | Key-Value (überall dort, wo kein spezielleres Muster passt — langfristig reduzieren) |
| Tabs | `.tabs`, `.tabs__nav`, `.tabs__tab`, `.tabs__panel` | Bereichs-Tabs |
| Formular | `.form`, `.form-field`, … | Eingaben |
| Disclosure | `.disclosure`, … | Filter, einklappbare Bereiche (nicht für Planung ersetzen, wenn `context-actions` aktiv) |
| Layout | `.container`, `.page-header`, `.page-content` | Seitenstruktur |
| Stat-Kacheln | `.stat-tiles`, `.stat-tile`, `.stat-tile__label`, `.stat-tile__value`, `.stat-tile__value--muted` | 2–4 Kennzahlen prominent (z. B. GGL „Dein Rang“) |
| Daten-Tabelle (Shell) | `.table-responsive`, `.data-table-wrap`, `.data-table` | Karten-Rahmen, Header-Zeile, Zellen-Raster, letzte Spalte rechts — **gemeinsame Basis** für GGL-Rangliste und Events-Listen (`components.css`) |
| Rangliste GGL | `.data-table` + `.ggl-ranking-table`, Spalten `__col-rank` / `__col-name` / `__col-num`, Zeilen `__row--current`, `__row--rank-1` … `__row--rank-3` | GGL Tabelle-Tab: **Hülle** `data-table-wrap` + Tabelle `data-table ggl-ranking-table` |
| Event-Listen (Tabelle) | wie **Daten-Tabelle**; optional weiter `.table` wo kein Card-Rahmen nötig (z. B. Admin) | Events Kommend/Archiv; RSVP in Zellen: `.data-table td:has(.status-form)` (und `.table` …) in `components.css`; Spalte **Typ** nur Icon: **`.data-table__cell--event-type`** + `sr-only`-Text; Archiv **ohne** Spalte Küche |

**HTML-Referenz:** bestehende Templates + `static/css/v2/components.css`.

### 5.2 Neu — im Redesign einführen

| Muster | Klassen (BEM) | Verwendung |
|--------|----------------|------------|
| Kontextleiste | `.context-actions`, `.context-actions__title`, `.context-actions__buttons` | Admin/Organisator direkt unter `.page-header` (siehe auch `base.css`: `:has(+ .context-actions)`) |
| Settings-Navigation | `.settings-nav`, `.settings-nav__section`, `.settings-nav__section-title`, `.settings-nav__list`, `.settings-nav__row`, `.settings-nav__icon`, `.settings-nav__meta`, `.settings-nav__label`, `.settings-nav__description`, `.settings-nav__badge`, `.settings-nav__badge--warning`, `.settings-nav__chevron` | Member-Hub, Admin-Hub (Listen-Navigation statt KPI-Karten) |

**CSS:** `static/css/v2/components.css` (ab Abschnitt „CONTEXT ACTIONS“ / „SETTINGS NAV“).

#### 5.2.1 HTML-Snippets (Referenz)

**`context-actions`** — unmittelbar nach `.page-header`, vor Tabs oder `.page-content`. Titelzeile optional (nur Buttons reicht).

```html
<nav class="context-actions" aria-label="Aktionen zu dieser Seite">
  <p class="context-actions__title">Planung</p>
  <div class="context-actions__buttons">
    <a href="{{ url_for('events.edit', event_id=event.id) }}" class="btn btn--outline">Bearbeiten</a>
    <a href="{{ url_for('events.year_planning') }}" class="btn btn--primary">Jahresplanung</a>
  </div>
</nav>
```

**`settings-nav`** — Sektionen mit Überschrift und Liste von Zeilen (`<a>` oder `<button>`). Badge und Beschreibung optional.

```html
<div class="settings-nav">
  <section class="settings-nav__section" aria-labelledby="settings-konto">
    <h2 id="settings-konto" class="settings-nav__section-title">Konto</h2>
    <ul class="settings-nav__list" role="list">
      <li>
        <a href="{{ url_for('member.profile') }}" class="settings-nav__row">
          <span class="settings-nav__icon" aria-hidden="true">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><!-- … --></svg>
          </span>
          <span class="settings-nav__meta">
            <span class="settings-nav__label">Profil</span>
            <span class="settings-nav__description">Name und Kontakt</span>
          </span>
          <span class="settings-nav__badge settings-nav__badge--warning">2FA aus</span>
          <svg class="icon settings-nav__chevron" viewBox="0 0 24 24" aria-hidden="true"><!-- chevron-right --></svg>
        </a>
      </li>
    </ul>
  </section>
</div>
```

### 5.3 Entscheidungshilfe: welches Pattern?

| Situation | Richtung |
|-----------|----------|
| 2–4 Kennzahlen prominent | **stat-tiles** / **stat-tile** (§5.1) statt 4× `info-row` in einer Card |
| Viele gleichartige Einträge (Ranking, Liste) | **`.data-table-wrap`** + **`.data-table`**; GGL zusätzlich **`.ggl-ranking-table`**; sonst **`.table`** / eigene Liste — keine N gleichen Cards |
| Workflow (BillBro) | Stepper / Phasen-UI (Phase 4b) |
| Filter / Selten genutzt | `disclosure` oder kompakte Leiste |
| Admin/Organisator auf einer Event-Seite | **`context-actions`** |

---

## 6. Konventionen

### 6.1 Entscheidungen dokumentieren (Agent-Handoff)

Nachfolgende Agents haben **keinen** Zugriff auf frühere Chats. Alles Verbindliche muss in **`REDESIGN.md`** (und bei Bedarf Registry / andere Abschnitte) **ohne versteckte Arbeitsbezeichnungen** stehen.

**Pflicht, sobald der User oder du eine Entscheidung getroffen hast:**

1. **Entscheidungslog** (Abschnitt 12): neue Zeile mit Datum, Phase, **Entscheidung in Klartext** (was gilt ab jetzt konkret?), **Begründung**. Kein Verweis der Art „wie Option B besprochen“ ohne Wiederholung des Inhalts.
2. **Betroffene Abschnitte aktualisieren:** Wenn die Entscheidung Grundsatz, IA, Komponenten oder Phasen betrifft, die **Tabelle oder Liste dort anpassen** — nicht nur den Log pflegen.
3. **Keine Chat-only Codes** im aktiven Regelteil: Interne Namen aus der Planung („Option A“, „Konzept B“, Codenamen) höchstens **einmalig in Klammern** zur Historie; die **normative Formulierung** muss für einen fremden Agenten allein verständlich sein.
4. **Cursor-Rule** (`.cursor/rules/redesign.mdc`): nur **Kurzregeln**; wenn sich eine Grundregel ändert, Kurzform dort spiegeln oder Verweis auf den konkreten Abschnitt in `REDESIGN.md`.
5. **Cleanup-Backlog (§16.2):** bei erkannten Altlasten **eintragen** oder bestehende Zeilen **aktualisieren** (Status, Blockiert bis).

**Prüfung:** Kann ein Agent, der nur `REDESIGN.md` liest, die nächste Aufgabe umsetzen, **ohne** Begriffe aus einem früheren Gespräch zu kennen? Wenn nein — nachschärfen.

### 6.2 Technik und Qualität

- **CSS-Klassen:** englisch, **BEM**, keine willkürlichen Kürzel.
- **Kein Mischen** mit anderen Frameworks.
- **Responsive:** Mobile zuerst; Breakpoints testen (320+, 768+, 1024+).
- **Touch:** mind. **44px** klickbare Flächen wo sinnvoll (Buttons bereits teils definiert).
- **A11y:** sinnvolle Labels, `focus-visible`, semantische Überschriften.

---

## 7. Checkliste pro Seiten-Migration

- [ ] Konventionen aus diesem Dokument  
- [ ] Keine hardcodierten Farben/Abstände  
- [ ] Mobile + Desktop geprüft  
- [ ] Touch-Ziele ausreichend  
- [ ] Links/Formulare funktionsfähig  
- [ ] **§13 Template-Übersicht:** passende Zeile(n) von `pending` → `done` (nur diese beiden Statuswerte; siehe §13 Legende)  
- [ ] Falls User-Entscheidung: Entscheidungslog + betroffene Abschnitte im **Klartext** (Abschnitt 6.1)  
- [ ] Falls beim Arbeiten **ersetzbare Altlasten** sichtbar werden: **§16 Cleanup-Backlog** um eine konkrete Zeile ergänzen (nicht nur mental notieren)  

---

## 8. Phasen (Überblick)

| Phase | Inhalt |
|-------|--------|
| **0c** | Dieses Dokument + Cursor-Rule (erledigt mit Erstanlage) |
| **1** | Technisches Fundament: neue Komponenten (`context-actions`, `settings-nav`), Partials (Shell + `<head>`), Tab-JS optional, Tokens bei Bedarf |
| **2** | GGL-Pilot |
| **3** | Events-Übersicht |
| **4a–c** | Event-Detail (Info, BillBro, Bewertungen) |
| **5** | Dashboard — siehe **§8.1** (Bewertungs-Thema + `cleanup.html`) |
| **6** | Member- + Admin-Hub (Settings-Pattern) |
| **7** | Rest-Templates, Cleanup, Performance — verbindlich mit **§16** (Backlog + Ende-Kriterium) |

Detail-Schritte werden während der Phasen hier nachgetragen.

### 8.1 Phase 5 (Dashboard) — vor Phase 5 mit User/PO klären

Beim Umbau von **`templates/dashboard/index.html`** müssen folgende Punkte **gemeinsam entschieden** und danach im **Entscheidungslog (§12)** im Klartext dokumentiert werden (kein Chat-only):

1. **Ausstehende Bewertungen** — Wo und wie der Nutzer daran erinnert wird (ein oder mehrere Events, Priorität, Duplikat zu Hinweisen auf **`templates/events/index.html`** o. ä.), und wie das zum Rollenkonzept passt.
2. **`templates/events/cleanup.html`** (Datenbereinigung) — Bezug zum Dashboard: z. B. ob der **Cleanup-/Bereinigungs-Fortschritt** oder Verweise dorthin auf dem Dashboard erscheinen sollen, und wie sich das zum Thema **fehlende Bewertungen** und zum bestehenden **Cleanup-Workflow** verhält.

Erst nach diesen Festlegungen Phase 5 umsetzen; bei Abweichung vom Ist-Zustand **§6.1** (Log + betroffene Abschnitte) beachten.

---

## 9. Lokales Testen (Windows)

PowerShell, Projektroot:

```powershell
cd c:\gourmen_pwa
flask --app "backend.app:create_app('development')" run --debug --port 5000
```

- Desktop: `http://localhost:5000`  
- Handy (gleiches WLAN): `http://<LAN-IP-des-PC>:5000`  
- DB: `.env` / `DATABASE_URL`; für reines Layout reicht oft SQLite-Fallback.

---

## 10. Fortschritts-Tracker

| Phase | Status | Anmerkungen |
|-------|--------|----------------|
| 0a Grundsatz + IA | erledigt | Option A, IA + Settings-Hubs dokumentiert |
| 0b Admin-Kontext | erledigt | Muster **`context-actions`** in IA + Konventionen festgelegt (§4.4); **CSS** gehört zu Phase 1 (nicht mit „0b“ verwechseln) |
| 0c Doku | erledigt | `REDESIGN.md`, `.cursor/rules/redesign.mdc` |
| 1 Fundament | erledigt | CSS/Snippets, Shell-Partials, **Head-Partials** (§13.2); Tab-JS für Bereichs-Tabs bleibt **optional** und kann bei Bedarf in späteren Phasen nachgerüstet werden |
| 2 GGL-Pilot | erledigt | `ggl/index.html`: **stat-tiles** (Tab Dein Rang), **Rang-Tabelle** statt Card-Liste; Lucide-Sprite per `url_for`; CSS in `components.css`; Tag **`pre-phase-2`** gesetzt |
| 3 Events-Übersicht | erledigt | `events/index.html` + `backend/routes/events.py`: **context-actions**; Tabs **Kommend / Archiv / Statistiken**; **`.data-table-wrap` / `.data-table`** (wie GGL); kein Tab „Übersicht“ (Default **kommend**, `tab=overview` → Redirect); **rating_prompt_event**-Alert; Spalte **Typ** = nur Icon (`data-table__cell--event-type`); Archiv **ohne** Küche; **stat-tiles** Statistik; Lucide-Sprite |
| 4–7 | offen | siehe Abschnitt 8 |

### NAECHSTER SCHRITT

**Phase 4:** `templates/events/detail.html` (Info-Tab, Tabs, BillBro, Bewertungen) gemäß Redesign und §5.3; §13 Status nach Migration auf **done**. Branch **`redesign`** beibehalten.

---

## 11. Letzte Session-Notiz

- **2026-04-03:** Phase-1-CSS für `context-actions` und `settings-nav` ergänzt; Tracker 0b/1 präzisiert; §5.2.1 Snippets; `main-v2` Fingerprint + `base.html`-Link aktualisiert.
- **2026-04-03:** §16 Ende-Kriterium + Cleanup-Backlog (P0/P1); Starteinträge C-001/C-002.
- **2026-04-03:** §13.1 — Status nur `pending` \| `done`; §7/§16.1 angeglichen.
- **2026-04-03:** Phase 1 — Shell-Partials für `base.html` (`_user_bar`, `_sidebar`, `_bottom_nav`, `_flash_messages`); §13.2; Login-Seite 200 (Smoke).
- **2026-04-03:** Phase 1 — `<head>` in `_head_*.html` Partials; OG/Twitter/Title-Blöcke bleiben in `base.html`; Smoke Login 200.
- **2026-04-03:** Phase 2 — GGL `index.html` Pilot; `stat-tiles` + `ggl-ranking-table`; `main-v2.04743a90.css`; `git tag pre-phase-2`.
- **2026-04-03:** UX — keine verpflichtenden `page-subtitle` mehr (Kontext in `h1` wo nötig); Filter-Cards dezent (`.card.card--filter`); `main-v2` Fingerprint aktualisiert.
- **2026-04-03:** Phase 3 — `events/index.html`: `context-actions` statt Admin-Filter-Card; Tabs-Icons Lucide; Kommend/Archiv als responsive **Tabelle** (§5.3); Statistiken **stat-tiles**; leere Zustände **alert--info**.
- **2026-04-03:** Events-Übersicht — Tab **„Übersicht“** entfernt (Doppelung mit Dashboard); Standard-Tab **Kommend**; `?tab=overview` → Redirect **kommend**; Bewertungs-Hinweis als **Alert** oberhalb der Tabs.
- **2026-04-03:** **§8.1** ergänzt — Phase 5 Dashboard: verbindlicher Klärungsbedarf zu **ausstehenden Bewertungen** und zu **`templates/events/cleanup.html`** (inkl. Entscheidungslog nach Klärung).
- **2026-04-03:** Gemeinsame Tabellen-Hülle **`.data-table-wrap` / `.data-table`** — Events Kommend/Archiv optisch an GGL angeglichen; GGL nutzt dieselbe Basis + `.ggl-ranking-table`-Modifier.
- **2026-04-03:** Events-Tabellen: Spalte **Typ** (Icon statt Text im Raster), **Archiv** ohne Spalte **Küche**; Tracker Phase 3 für nächsten Agent präzisiert — **Phase 4** nächster Schritt: `templates/events/detail.html` (siehe **§10 NAECHSTER SCHRITT**).

---

## 12. Entscheidungslog

Jede Zeile muss **ohne Chat-Kontext** verständlich sein (siehe Abschnitt 6.1). Keine alleinigen Verweise auf Arbeitsbezeichnungen ohne Klartext in derselben Zelle.

| Datum | Phase | Entscheidung | Begründung |
|-------|--------|--------------|------------|
| 2026-04-03 | 0a | Technischer Ansatz: Custom BEM + Tokens, kein Tailwind/Framework (Konzept „Option A“, vom PO bestätigt) | Kontrolle, bestehende V2-Basis, kein Build-Zwang; Agent-Arbeit über Registry |
| 2026-04-03 | 0a | Member/Admin-Hub: Settings-Liste statt KPI-Karten | KPIs unnötig; schnellere Navigation |
| 2026-04-03 | 0b | Kontextleiste `context-actions` für Planung auf Event-Seiten | Sichtbarkeit, ein Muster statt Disclosure-Cards |
| 2026-04-03 | 0a/IA | Organisator nur in Events; Admin-Jahresplanung + Backup im Admin-Bereich; eine Bearbeitungslogik, zwei Admin-Einstiege ok | Rollenklarheit, Merch-Parallele |
| 2026-04-03 | 1 | `context-actions` und `settings-nav` sind in `static/css/v2/components.css` umgesetzt; Referenz-Snippets in §5.2.1; Abstandregel `.page-header:has(+ .context-actions)` in `base.css` | Tracker-Klarheit (0b = Spezifikation, 1 = Umsetzung); Agenten können Templates anbinden |
| 2026-04-03 | Doku | Abschluss des Redesigns: verbindliches **Ende-Kriterium** und gemeinsames **Cleanup-Backlog** in §16; Pflege in §6.1 und §7 | Agents ohne Chat-Kontext wissen, wann „fertig“ ist und welche Altlasten dokumentiert abgearbeitet werden |
| 2026-04-03 | Doku | **§13 Template-Übersicht:** Status-Spalte normiert auf ausschließlich **pending** \| **done** (Legende §13.1); **done** inkl. dokumentierter User-Exempts via §12 | Einheitliche Agent-Handoffs ohne parallele Status-Begriffe |
| 2026-04-03 | 1 | Layout-Shell aus `base.html` in `templates/partials/` ausgelagert (`_user_bar`, `_sidebar`, `_bottom_nav`, `_flash_messages`); Referenz **§13.2** | Phase-1-Rückbau; kleinere `base.html`, gleiche Laufzeitsemantik |
| 2026-04-03 | 1 | `<head>`-Inhalt (Theme-Script, PWA-Meta, Manifest/Icons, Stylesheets, deferred Scripts) in `_head_*.html`; vererbbare **Blöcke** (`title`, `og_*`, `twitter_*`, `head`) verbleiben in `base.html` | Jinja-`extends` bleibt korrekt; Partials ohne eigene `{% block %}` |
| 2026-04-03 | 2 | GGL-Hauptseite: KPIs als **stat-tiles**; Saison-Ranking als **eine Tabelle** (`ggl-ranking-table`) statt pro Zeile eine Card; Referenz **§5.1** | REDESIGN §5.3; bessere Mobile/Desktop-Nutzung, weniger visuelles Gewicht |
| 2026-04-03 | UX | **Page-Header:** kein Standard-`page-subtitle`; nur `h1`, ggf. Kontext in derselben Zeile (z. B. „Bearbeiten · Name“). **`card--filter`:** optisch abgeschwächt (kein Schatten/Hover-Lift, Surface-Hintergrund) — einheitlich mit bestehendem Disclosure-Muster | Weniger Höhe und Redundanz; Filter bleibt erkennbar, Inhalts-Cards visuell im Vordergrund |
| 2026-04-03 | 3 | **Events-Übersicht (`events/index.html`):** Admin-Planung nur noch **`context-actions`** unter dem Page-Header (kein `card--filter`-Disclosure dafür). **Kommend** und **Archiv:** homogene Zeilen in **`.data-table-wrap` / `.data-table`** (`.table-responsive`); **Statistiken:** **`stat-tiles`**. **Lucide** per Sprite (`url_for`) für Tab- und Seiten-Icons. | REDESIGN §4.4, §5.3; konsistent mit Phase-2-Pilot; gemeinsame Tabellen-Hülle mit GGL (siehe unten) |
| 2026-04-03 | 3 | **Tabellen einheitlich:** `.data-table-wrap` und `.data-table` als gemeinsame „Card“-Tabelle (Rahmen, Schatten, Header-Fläche, Zeilenlinien); GGL mit zusätzlich `.ggl-ranking-table` und Spalten-/Zeilen-Modifiern; Events Kommend/Archiv dieselbe Hülle — kein paralleles `ggl-ranking-table-wrap` mehr nötig | Gleiche Lesbarkeit und Hierarchie wie GGL; eine Pflegestelle statt divergierender `.table`-Minimalvariante |
| 2026-04-03 | 3 | **Events-Tabellen:** Spalte **Typ** mit Überschrift „Typ“ — sichtbar nur **Lucide-Icon** zum Event-Typ; **Datum** nur Text. **Archiv:** Spalte **Küche** entfernt (Küche bleibt im Event-Detail). | Kompaktere Liste; Typ weiterhin per `sr-only` + Icon für A11y |
| 2026-04-03 | 3 | **Kein Tab „Übersicht“** mehr auf der Events-Hauptseite: Inhalt (aktuelles/nächstes Event) war **redundant zum Dashboard**. Standard-URL **`/events`** lädt **Kommend** (`tab=kommend`). **`tab=overview`** wird nach **kommend** umgeleitet. **Bewertungs-Hinweis** für das letzte besuchte Event ohne Bewertung bleibt als **`alert--info`** oberhalb der Tab-Leiste sichtbar (nicht dashboard-redundant). | Nutzerwunsch; eine klare Rolle pro Seite (Dashboard = persönlicher Einstieg, Events = Listen/Archiv/Stats) |

---

## 13. Template-Übersicht (Kern)

### 13.1 Status-Spalte (nur diese zwei Werte)

| Wert | Bedeutung |
|------|-----------|
| **pending** | Für diesen Eintrag ist die Migration auf das in der **Phase**-Spalte vorgesehene Redesign-Muster **noch nicht** abgeschlossen. |
| **done** | **Entweder:** Migration erledigt und gegen **§7** geprüft. **Oder:** vom User **ausdrücklich** von der visuellen/IA-Migration ausgenommen — dann **zusätzlich** ein Eintrag im **Entscheidungslog §12** (welches Template, warum exempt). |

**Nicht verwenden:** Zwischenstände wie „wip“, „teilweise“, „in Arbeit“ — Details in **§11** Session-Notiz oder **§16.2** Backlog, nicht in dieser Spalte.

### 13.2 Layout-Partials (`templates/partials/`)

Einbindung in `base.html`: `{% include 'partials/_….html' %}`. **Keine** `{% block %}` in Partials — überschreibbare Blöcke nur im Layout (`base.html`), sonst funktioniert `{% extends %}` nicht.

**Body / Shell**

| Datei | Inhalt |
|-------|--------|
| `_user_bar.html` | Obere Leiste: Logo, Name, V2-Cleanup/Theme/Admin-Aktionen |
| `_sidebar.html` | Desktop-Sidebar (Hauptnavigation) |
| `_bottom_nav.html` | Mobile Bottom-Navigation (4 Tabs) |
| `_flash_messages.html` | Flask Flash-Messages im `<main>` |

**`<head>`** (Reihenfolge: Theme-Script zuerst, dann charset/viewport/titel und OG/Twitter-**Blöcke** in `base.html`, danach Includes)

| Datei | Inhalt |
|-------|--------|
| `_head_theme_script.html` | Inline-Script: `data-theme` + dynamisches `theme-color` vor CSS (FOUC) |
| `_head_pwa_meta.html` | Statische PWA-/SEO-Basis-Meta (ohne OG/Twitter-Blöcke) |
| `_head_manifest_icons.html` | Manifest, Favicons, Apple-Touch, iOS-Splash |
| `_head_stylesheets.html` | V2/V1-CSS, Lucide-Preload, Font Awesome |
| `_head_deferred_scripts.html` | `pwa.js`, `app.js`, CSRF-`meta` (nach `{% block head %}`) |

| Pfad | Phase | Status |
|------|-------|--------|
| `templates/base.html` | 1 | pending |
| `templates/dashboard/index.html` | 5 | pending |
| `templates/events/index.html` | 3 | done |
| `templates/events/detail.html` | 4 | pending |
| `templates/ggl/index.html` | 2 | done |
| `templates/member/index.html` | 6 | pending |
| `templates/admin/index.html` | 6 | pending |
| übrige `templates/**` | 7 | pending |

**Phase 5:** Vor der Migration von `templates/dashboard/index.html` die offenen Punkte in **§8.1** klären (darunter **ausstehende Bewertungen** und Bezug zu **`templates/events/cleanup.html`**). Die visuelle Migration von `events/cleanup.html` erfolgt in **Phase 7** („übrige `templates/**`“); die **IA-/Produktentscheidung** (ob und wie Cleanup bzw. Bewertungs-Druck mit dem Dashboard verzahnt werden) gehört in die Phase-5-Klärung und danach ins **§12**-Log.

---

## 14. Hinweis zu `docs/DESIGN_SYSTEM.md`

Bis zur Konsolidierung dient `DESIGN_SYSTEM.md` als **Referenz** für Farben und Breakpoints. **Verbindliche** Redesign-Regeln und Tracker stehen **hier** in `REDESIGN.md`. Nach Abschluss der Migration kann `DESIGN_SYSTEM.md` durch einen Verweis ersetzt oder entfernt werden.

---

## 15. Git (Kurz)

- Arbeit nur auf Branch **`redesign`**.  
- Kein Push auf `master` aus dem Redesign-Workflow.  
- Vor Phase 2+: `git tag pre-phase-2` usw. setzen.  

Notfall-Befehle: siehe `.cursor/rules/redesign.mdc`.

---

## 16. Ende-Kriterium und Cleanup-Backlog (agentschaftlich)

Dieser Abschnitt ist die **einzige verbindliche Stelle** für „wann ist das Redesign fertig“ und **welcher Alt-Code** noch weg muss. Jeder Agent pflegt ihn **ohne** Zugriff auf frühere Chats weiter.

### 16.1 Ende-Kriterium (GO für Abschluss / Merge nach außen)

Das Redesign gilt **nur dann als abgeschlossen**, wenn **alle** folgenden Punkte erfüllt sind **und** der **User** den Abschluss ausdrücklich bestätigt hat (Agent ersetzt keine PO-Freigabe).

1. **Template-Übersicht (§13):** Alle dort genannten Kern-Templates und die Kategorie „übrige `templates/**`“ haben Status **done** (siehe **§13.1**; Ausnahmen nur mit **§12**-Eintrag).
2. **Kein paralleles Legacy-UI für die produktive App:** Sämtliche für eingeloggte Nutzung relevanten Routen/Templates nutzen **einheitlich V2** (`use_v2_design` bzw. Backend-Flag entsprechend); es gibt **keinen** zweiten „Haupt“-Stylesheet-Pfad mehr für denselben Zweck.
3. **V1-CSS/Assets:** `static/css/main.css` (und nur noch von V1 genutzte Reste) sind **entfernt oder archiviert**; `base.html` (bzw. das finale Layout-Partial) referenziert **nur noch** das V2-Bundle. *(Bis dahin bleibt V1 bewusst stehen — siehe Backlog.)*
4. **Cleanup-Backlog (§16.2):** Alle Einträge mit Priorität **P0** sind auf **done**; Einträge **P1** sind entweder **done** oder im **Entscheidungslog (§12)** mit Datum und Klartext **vom User zurückgestellt**.
5. **Dokumentation:** Fortschritts-Tracker (§10) und Phase **7** auf **erledigt**; optional §14 (Konsolidierung mit `DESIGN_SYSTEM.md`) nach User-Vorgabe erledigt oder Referenz gesetzt.

Erst danach: Branch-Strategie mit dem User klären (z. B. Merge `redesign` → `master`), **kein** stillschweigendes „fertig“ durch Agenten.

### 16.2 Cleanup-Backlog — schriftliche Checkliste

**Zweck:** Sicherstellen, dass am Ende **kein unkoordinierter Totcode** liegen bleibt. Jede Zeile ist **konkret** (was, wo, wann löschbar).

**Pflege-Regeln (für jeden Agenten):**

- **Neuen Eintrag anlegen**, wenn du beim Migrieren **Duplikate**, **nur noch von alter UI genutzte** Dateien, **ersetzte** CSS-Klassen-Muster oder **CDN/Framework-Reste** (z. B. Font Awesome nach Lucide-Umstellung) erkennst — auch wenn das Entfernen erst **später** erlaubt ist.
- Spalte **Blockiert bis:** z. B. „§13 `events/detail` = done“ oder „nach Lucide in `templates/auth/*`“ — damit niemand zu früh bricht.
- Status auf **done** setzen **nur**, wenn die Zeile erledigt ist (Datei gelöscht, Referenz entfernt, Fingerprint bei CSS-Änderungen wie üblich).
- Keine vagen Einträge („Code aufräumen“); immer **messbar**.

| ID | Priorität | Was entfernen / konsolidieren | Ort (Pfade, Muster) | Blockiert bis | Status |
|----|-----------|------------------------------|---------------------|---------------|--------|
| C-001 | P1 | Font Awesome CDN entfernen, wenn alle Icons auf Lucide/Sprite | `templates/base.html` | Lucide in allen V2-Templates; Agent prüft per Suche `fa-` / `font-awesome` | open |
| C-002 | P0 | V1-CSS und Verzweigung `use_v2_design` / Legacy-Zweig in `base.html` entfernen | `templates/base.html`, `static/css/main.css`, ggf. `backend/**` Render-Flags | §13 vollständig **done**; §16.1 Punkt 2–3 | open |
| C-003 | P1 | Alte GGL-Ranking-**Card**-Styles entfernen (ersetzt durch `.ggl-ranking-table`) | `static/css/v2/components.css` (`.ggl-ranking-list`, `.ggl-ranking-card`, …) | Suche im Repo: keine Template-Referenz mehr auf diese Klassen; nach User-Check Layout Phase 7 | open |

*(Weitere Zeilen bei Bedarf fortlaufend nummerieren: C-004 …)*

**Priorität:**

- **P0:** Blockiert das Ende-Kriterium (§16.1) — muss vor Abschluss erledigt oder per §12 vom User befreit werden.
- **P1:** Soll vor Merge erledigt sein; technische oder optische Schulden, die das GO nicht zwingend blockieren, aber dokumentiert abgearbeitet werden sollen.

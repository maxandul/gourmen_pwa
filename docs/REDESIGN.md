# Gourmen PWA — UX Redesign (Master-Dokument)

Operatives Handbuch für Agents und Menschen. **Vor jeder Redesign-Änderung** die für die Aufgabe relevanten Abschnitte lesen. **Neue Agents:** Chat-Verläufe sind nicht verfügbar — verbindliche Regeln und Entscheidungen stehen **hier** und im **Entscheidungslog** (Abschnitt 12); Handoff-Regeln in **Abschnitt 6.1**.

---

## 1. Überblick

**Gourmen PWA** ist die Web-App des Gourmen-Vereins (Events, GGL/BillBro, Merch, Mitglieder).

**Redesign-Ziel:** Starke **Usability** und **visuelle Differenzierung** — nicht alles als gleiche Card mit `info-row`. Mobile und Desktop gleichwertig. Langfristig erweiterbar (weitere Hauptbereiche).

**Relevante Pfade:** `templates/**/*.html`, `static/css/v2/*.css`, `static/js/v2/*.js`, gebündelt u. a. als `static/css/main-v2.*.css`.

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
| **Templates** | `base.html` in **Partials** splitten (`_user_bar`, `_sidebar`, `_bottom_nav`, …); wiederkehrende Fragmente als **Jinja-Macros**. |
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

**HTML-Referenz:** bestehende Templates + `static/css/v2/components.css`.

### 5.2 Neu — im Redesign einführen (CSS + Snippets in späteren Schritten vervollständigen)

| Muster | Klassen (Ziel-BEM) | Verwendung |
|--------|---------------------|------------|
| Kontextleiste | `.context-actions`, `.context-actions__title`, `.context-actions__buttons` (feinjustierbar) | Admin/Organisator unter Seitentitel |
| Settings-Navigation | `.settings-nav`, `.settings-nav__section`, `.settings-nav__section-title`, `.settings-nav__row`, `.settings-nav__icon`, `.settings-nav__meta` | Member-Hub, Admin-Hub |

**Nach Implementierung:** hier **exakte HTML-Snippets** einfügen und ggf. in `.cursor/rules/redesign.mdc` Kurzform ergänzen.

### 5.3 Entscheidungshilfe: welches Pattern?

| Situation | Richtung |
|-----------|----------|
| 2–4 Kennzahlen prominent | **stat-tile** (noch anzulegen) statt 4× `info-row` in einer Card |
| Viele gleichartige Einträge (Ranking, Liste) | **compact-list** / Tabellenzeilen (noch anzulegen) statt N gleicher Cards |
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
- [ ] Tracker unten aktualisiert  
- [ ] Falls User-Entscheidung: Entscheidungslog + betroffene Abschnitte im **Klartext** (Abschnitt 6.1)  

---

## 8. Phasen (Überblick)

| Phase | Inhalt |
|-------|--------|
| **0c** | Dieses Dokument + Cursor-Rule (erledigt mit Erstanlage) |
| **1** | Technisches Fundament: neue Komponenten (`context-actions`, `settings-nav`), Partials, Tab-JS optional, Tokens bei Bedarf |
| **2** | GGL-Pilot |
| **3** | Events-Übersicht |
| **4a–c** | Event-Detail (Info, BillBro, Bewertungen) |
| **5** | Dashboard |
| **6** | Member- + Admin-Hub (Settings-Pattern) |
| **7** | Rest-Templates, Cleanup, Performance |

Detail-Schritte werden während der Phasen hier nachgetragen.

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
| 0b Admin-Kontext | erledigt | `context-actions` |
| 0c Doku | erledigt | `REDESIGN.md`, `.cursor/rules/redesign.mdc` |
| 1 Fundament | offen | CSS-Komponenten, Partials, ggf. Tabs |
| 2–7 | offen | siehe Abschnitt 8 |

### NAECHSTER SCHRITT

**Phase 1 starten:** `context-actions` und `settings-nav` in `components.css` definieren, HTML-Snippets in **Abschnitt 5** ergänzen, `base.html` in Partials splitten (schrittweise, rückwärtskompatibel), Branch `redesign` beibehalten.

---

## 11. Letzte Session-Notiz

- *Wird von Agents bei Bedarf gefüllt.*

---

## 12. Entscheidungslog

Jede Zeile muss **ohne Chat-Kontext** verständlich sein (siehe Abschnitt 6.1). Keine alleinigen Verweise auf Arbeitsbezeichnungen ohne Klartext in derselben Zelle.

| Datum | Phase | Entscheidung | Begründung |
|-------|--------|--------------|------------|
| 2026-04-03 | 0a | Technischer Ansatz: Custom BEM + Tokens, kein Tailwind/Framework (Konzept „Option A“, vom PO bestätigt) | Kontrolle, bestehende V2-Basis, kein Build-Zwang; Agent-Arbeit über Registry |
| 2026-04-03 | 0a | Member/Admin-Hub: Settings-Liste statt KPI-Karten | KPIs unnötig; schnellere Navigation |
| 2026-04-03 | 0b | Kontextleiste `context-actions` für Planung auf Event-Seiten | Sichtbarkeit, ein Muster statt Disclosure-Cards |
| 2026-04-03 | 0a/IA | Organisator nur in Events; Admin-Jahresplanung + Backup im Admin-Bereich; eine Bearbeitungslogik, zwei Admin-Einstiege ok | Rollenklarheit, Merch-Parallele |

---

## 13. Template-Übersicht (Kern)

Status: **pending** = noch nicht auf neues Muster migriert.

| Pfad | Phase | Status |
|------|-------|--------|
| `templates/base.html` | 1 | pending |
| `templates/dashboard/index.html` | 5 | pending |
| `templates/events/index.html` | 3 | pending |
| `templates/events/detail.html` | 4 | pending |
| `templates/ggl/index.html` | 2 | pending |
| `templates/member/index.html` | 6 | pending |
| `templates/admin/index.html` | 6 | pending |
| übrige `templates/**` | 7 | pending |

---

## 14. Hinweis zu `docs/DESIGN_SYSTEM.md`

Bis zur Konsolidierung dient `DESIGN_SYSTEM.md` als **Referenz** für Farben und Breakpoints. **Verbindliche** Redesign-Regeln und Tracker stehen **hier** in `REDESIGN.md`. Nach Abschluss der Migration kann `DESIGN_SYSTEM.md` durch einen Verweis ersetzt oder entfernt werden.

---

## 15. Git (Kurz)

- Arbeit nur auf Branch **`redesign`**.  
- Kein Push auf `master` aus dem Redesign-Workflow.  
- Vor Phase 2+: `git tag pre-phase-2` usw. setzen.  

Notfall-Befehle: siehe `.cursor/rules/redesign.mdc`.

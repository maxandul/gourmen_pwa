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


| Thema               | Entscheidung                                                                                                                                                                                                                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CSS**             | Custom **BEM** + **Tokens**; keine Tailwind-/DaisyUI-Migration im aktuellen Redesign.                                                                                                                                                                                                                   |
| **Card**            | Card für **Objekte / zusammenhängende Blöcke**; **nicht** für jede Infoart. KPI-Listen: eigene Muster (**stat-tile**, **compact-list** — in Phase 1 ff. definieren und hier dokumentieren).                                                                                                             |
| **Breadcrumbs**     | Kein Fokus auf klassische Breadcrumbs auf Mobile; Orientierung über **Nav + Titel**. **Bei jeder Migration einer Unterseite:** keine **`<nav class="breadcrumbs">`**, Kette ersetzen durch **einen** **`.page-back`**-Link (Lucide **`chevron-left`**) zum **sinnvollen Elternziel** — wie **`templates/events/detail.html`**. Mehrstufige Pfadwege nicht als Breadcrumb nachbauen; **§7** und **§8.3.2**. |
| **Tabs**            | Tabs für **getrennte Ansichten innerhalb eines Bereichs** (Events, GGL, Event-Detail). Sparsam halten; langfristig **clientseitiges Umschalten** wo sinnvoll (ohne volle Seitenlast), mit URL-Fallback.                                                                                                 |
| **Hauptnavigation** | **Bottom-Nav** (4) + **Sidebar** ab 1024px. Vierter Bereich: **„Verein“** (siehe **§4.5**); **kein** separater Admin-Tab und **kein** Admin-Icon in der User-Bar. Skalierung neuer Bereiche: **„Mehr“** / Drawer o. ä.                                                                                  |
| **User-Bar**        | **Theme-Toggle** bleibt in der **oberen Leiste** (schneller Zugriff). **User-Menü** (Button): persönliche Daten, Sicherheit, **Logout** — Details **§4.5**.                                                                                                                                             |
| **Dark/Light**      | **Beibehalten** (`data-theme`, Tokens).                                                                                                                                                                                                                                                                 |
| **Icons**           | **Konsolidierung auf Lucide (Sprite)**; Font Awesome langfristig entfernen.                                                                                                                                                                                                                             |
| **Templates**       | `base.html` in **Partials** splitten — **Shell + `<head>`** unter `templates/partials/` (siehe **§13.2**). `{% block title %}`, `{% block og_* %}`, `{% block twitter_* %}`, `{% block head %}` bleiben in `**base.html`** (Jinja-Vererbung). Wiederkehrende Fragmente zusätzlich als **Jinja-Macros**. |
| **Page-Header**     | **Standard: nur `h1`** (Seitentitel). Kein verpflichtendes `page-subtitle`; Kurz-Kontext bei Bedarf **in der `h1`-Zeile** (z. B. „Mitglied bearbeiten · Max M.“) oder im Inhalt — nicht als zweite Intro-Zeile unter dem Titel.                                                                         |
| **Filter-UI / Sekundärleisten** | **Einheitliches Tool-Strip-Muster** (**§5.2.3**): `**card card--filter tool-surface`** + `**details.disclosure**` (Kopfzeile: Chevron, Titel in Primärfarbe, optional Chips). **Planung** und **Filter** dieselbe Struktur; visuell sekundär, flach, **ohne** Schatten/Hover-Lift (**§5.2.2** `tool-surface`). |
| **Design-Raster**   | Nur `**--space-*`**, Typo- und Farb-Tokens aus `tokens.css`; keine willkürlichen Pixelwerte. Breakpoints wie in `DESIGN_SYSTEM.md` / Layout (u. a. 768, 1024).                                                                                                                                          |


---

## 4. Informationsarchitektur

### 4.1 Hauptbereiche


| Bereich                                                                  | Inhalt                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dashboard**                                                            | Persönlicher **Überblick** nach **Nutzerintention**: **Zu erledigen** — **zwei Kacheln** (**§6.3**): **Bereinigung** → **`events.cleanup`** (Lucide **`brush-cleaning`**, Meta **„1 fehlende Angabe“** / **„n fehlende Angaben“**, nur wenn **`retro_cleanup_progress.pending > 0`**); **Zu-/Absage** → **`events.detail`** (Lucide **`calendar`**, Meta **`[Eventtyp] am [Datum]`**) für das **früheste** kommende Event im Fenster **heute … +30 Tage** **ohne** erfasste Zu-/Absage (**`responded_at`** fehlt). Ausstehende **Bewertungen** vergangener Events erscheinen **nur** in der **Bereinigung**, keine eigene Dashboard-Kachel. **Zur Info** (**Nächstes Event** → Detail **ohne** RSVP auf der Kachel; weitere Zu-/Absagen **Event-Detail** / **Events-Liste**); **Dein letzter Anteil**; **GGL** (Untertitel **ohne** Teilnahme-Zähler); **Merch** (nicht geliefert). **Erkunden** nur **Merch-Shop** (Untertitel **„Shop und Bestellungen“**) und **Statistiken** (**„KPIs und Charts“**) — **Events** über **Bottom-Nav**. Optional **Push-Banner**. Technik und Copy-Details **§6.3**.                                                                                                                             |
| **Events**                                                               | Termine, RSVP, Detail, BillBro, Bewertungen, Archiv, Statistiken.                                                                                                                                                                                  |
| **GGL**                                                                  | Saison, Rang, Tabelle, Verlauf — ohne Event-Verwaltung.                                                                                                                                                                                            |
| **Verein** (Nav-Label; technisch z. B. weiter `member.*` / spätere URLs) | **Gemeinsames Vereinsleben:** **Merch-Shop** (kaufen), später **Dokumentablage** und weitere Erweiterungen. **Admins** zusätzlich: **Mitgliederverwaltung**, **Merch-Verwaltung** (Backoffice), später **Buchhaltung** (noch nicht implementiert). |
| **Persönlich** (kein eigener Haupt-Tab)                                  | Profil, Sicherheit (2FA, Passwort), ggf. Technik/PWA — Zugriff über **User-Menü** in der oberen Leiste (**§4.5**).                                                                                                                                 |


Der frühere Begriff **„Member“** als Hauptnavigations-Bereich ist durch **„Verein“** ersetzt; „Member“ bezeichnet weiterhin die **Rolle** / das Datenmodell.

### 4.2 Verein-Hub (Settings-Pattern)

**Keine KPI-Karten-Hubs.** Stattdessen **Einstellungsliste (`settings-nav`)**:

- **Für alle:** **Eine** Zeile **Merch** — ein Ziel-Link, Beschreibung **„Shop und Bestellungen“** (kein Zähler offener Bestellungen im Hub); später **Dokumente** / Ablage — wieder als eigene Zeile(n) unter derselben Sektion **Verein** (kein provisorischer **`docs.*`**-Eintrag in der Hauptnavigation; die bisherige Docs-Route bleibt im Backend bis zur Neugestaltung, erscheint aber nicht in Bottom-Nav/Sidebar).
- **Nur Admins:** eigene Sektion **Verwaltung** mit klar abgegrenzten Zeilen: **Mitglieder** (`admin.members`), **Merch-Verwaltung** (`admin.merch`). **Keine** Navigationszeile zur Admin-Übersicht (`admin.index`); die Route darf für Deep-Links bestehen bleiben, ist aber kein IA-Einstieg.

Legacy-Route `**admin.index`** kann vorerst bestehen bleiben (**KPI-`hub-card`-Template** für Deep-Links/Lesezeichen); **Navigation** führt Admins primär über **Verein** in dieselben Verwaltungsflächen (**§8.2**).

### 4.3 Rollen: Organisator vs. Admin (Events)

- **Organisator** (nicht zwingend Admin): alle inhaltlichen Schritte **nur** über **Events** / **Event-Detail** (Infos, BillBro, Planung). **Kein** Zwang in einen separaten Admin-Bereich.
- **Admin:** **Jahresplanung / Anlage** der kommenden Events; **Backup:** Event bearbeiten, **Organisator umhängen**, **Event löschen** (Löschen nur Admin — **auch in der UI nur für Admins sichtbar**, siehe **§4.5**). Auffindbarkeit: **kontextuelle Leisten** auf der Events-Übersicht und im Event-Detail sowie Einträge unter **Verein** wo sinnvoll.
- **Technisch:** **eine** Bearbeitungs-Oberfläche / Route-Logik wo möglich; mehrere **Navigationspfade** (Verein + Kontext) sind akzeptabel, **keine** doppelten widersprüchlichen Formulare pflegen.

### 4.4 Kontextuelle Admin-/Organisator-Aktionen (Phase 0b, fortgeschrieben)

**Verbindlich (Stand Agent-Doku 2026-04-03):** Kontext- und Filter-Leisten sind **dieselbe Komponentenfamilie** — **`card card--filter tool-surface`** mit **`<details class="disclosure">`** (**§5.2.3**). Kopfzeile einheitlich (Chevron, Titel, optional Chips); der **Inhalt** ist entweder nur Aktionen (**`tool-strip__actions`**) oder ein **Formular** plus **`.form-actions`**.

- **Platzierung:** unmittelbar unter **`page-header`** (z. B. Planung) oder innerhalb **`page-content`** (z. B. Filter über den Events-Tabs) — je nach Seite; immer **vor** den Bereichs-Tabs, wenn Tabs dieselbe Seite strukturieren.
- **Sichtbarkeit:** nur für berechtigte Rollen rendern (z. B. Admin-Planung nur für Admins).
- **`context-actions`** (flache `nav` + `tool-surface`, ohne `details`) bleibt in der Registry (**§5.2**) als **Legacy / Sonderfall** dokumentiert; **neue** Seiten und Refactors sollen das **Tool-Strip-Muster §5.2.3** nutzen, damit Titel, Chevron und Button-Zeilen mit Filter-Leisten übereinstimmen.

**Visuelle Einheit:** **`tool-surface`** auf der **`card.card--filter`** (**§5.2.2**).

Drei-Punkte-Menü nur als **spätere** Ergänzung bei Platzengpass, nicht Standard.

### 4.5 User-Bar, Theme und Verein-Icon (Festlegung)

- **Theme-Toggle:** bleibt **sichtbar in der oberen Leiste** (nicht nur im User-Menü).
- **Kein Admin-Button** mehr in der User-Bar; Admin-Funktionen über **Verein** und **Kontextleisten** am Objekt.
- **User-Menü:** ein Steuerlement (**Lucide `user`** auf dem Summary, **`aria-label`** z. B. „Konto und Einstellungen“) öffnet ein **Dropdown** (Komponente **`user-menu`**, §5.2). Einträge: **Profil**, **Sicherheit** (optional Badge **2FA aus** wie bei **`settings-nav`**), **App & Benachrichtigungen** (`member.technical`), Trennung, **Abmelden**. **Kein** Anzeigetext mit Spirit Animal / Rufname in der Top-Bar — vollständige Anzeige im **Profil**.
- **Hauptnavigation:** vierter Tab **„Verein“** — **Icon:** dasselbe **Lucide-Symbol wie für Generalversammlung** (`landmark` in der Event-Typ-Icon-Konvention), sofern nicht anders vom PO ersetzt; soll **Verein** statt „einzelnes Profil“ assoziieren. **Desktop-Sidebar:** Label und Icon wie Bottom-Nav (**„Verein“**, `landmark`), nicht „Member“.
- **Event löschen:** Aktion **nur für `is_admin()`** — **Button im Template nur rendern, wenn Admin**, nicht für Organisator ohne Admin-Rolle.

---

## 5. Komponenten-Katalog (lebendes Dokument)

### 5.1 Bestehend (V2) — weiter verwenden bis Migration


| Muster                 | Klassen (Auszug)                                                                                                                                    | Verwendung                                                                                                                                                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Button                 | `.btn`, `.btn--primary`, `.btn--outline`, `.btn--danger`, …                                                                                         | Aktionen                                                                                                                                                                                                                    |
| Card                   | `.card`, `.card__header`, `.card__body`, `.card__footer`                                                                                            | Objekt-Container                                                                                                                                                                                                            |
| Info-Zeile             | `.info-row`, `.info-row__label`, `.info-row__value`                                                                                                 | Key-Value (überall dort, wo kein spezielleres Muster passt — langfristig reduzieren)                                                                                                                                        |
| Tabs                   | `.tabs`, `.tabs__nav`, `.tabs__tab`, `.tabs__panel`; optional **`.tabs--panel`**: **Nav** **transparent**, **`gap`** zwischen Tabs; **inaktiv** Light **`--color-bg-muted`**, Dark **`--chrome-inactive-pill-bg`** (Selektor **`:not(.tabs__tab--active)`**, damit der aktive Tab nicht überschrieben wird); **aktiv** + **`tabs__content`** = **`--tabs-panel-body-bg`** (`**--color-surface**`); Tabs **oben abgerundet**, **ohne** sichtbaren Einzel-Rand; untere Panel-Kante mit dezenter Linie/Schatten — **projektweiter Redesign-Standard** in **`components.css`**; Referenz u. a. **`templates/events/index.html`**, **`templates/ggl/index.html`** |
| Formular               | `.form`, `.form-field`, …                                                                                                                           | Eingaben                                                                                                                                                                                                                    |
| Disclosure             | `.disclosure`, `.disclosure__summary`, `.disclosure__content`                                                                                        | **Sekundärleisten** in **`card.card--filter`** (Filter, Planung, …) — verbindliches Muster **§5.2.3**; sonst einklappbare Bereiche (GGL, Merch, …)                                                                             |
| Layout                 | `.container`, `.page-header`, `.page-content`, **`.page-back`** (Zurück-Link unter §3 statt Breadcrumb-Kette; **`base.css`**)                                                                                                       | Seitenstruktur                                                                                                                                                                                                              |
| Stat-Kacheln           | `.stat-tiles`, `.stat-tile`, `.stat-tile__label`, `.stat-tile__value`, `.stat-tile__value--muted`                                                   | Raster für **mehrere** gleichartige KPIs; oft **unter** **`metrics-spotlight`** als **`stat-tiles stat-tiles--metrics-follow`** (zentrierte Kacheln). **Events Statistiken:** zwei Hero-Paare in Spotlight + Folge-**`stat-tiles`**.                                                                                                                                                                            |
| Kennzahlen-Spotlight   | `.metrics-spotlight`, … `__metric-value`, `.metrics-spotlight__metric-hint`; `.metrics-spotlight__metric-value--accent` **nicht** im `__hero` verwenden | **1–2 prominente Kennzahl-Paare** (große Werte, optional Hint). **`__hero`:** CSS-Grid **immer 2 Spalten** (`repeat(2, 1fr)`), gleich breite Kacheln; **jede Metrik-Kachel** mit Rand und `min-height`; äußerer Hero ohne eigenen Panel-Rahmen. Alle Werte gleich eingefärbt; **`metric-value--accent` im Hero deprecated**. CSS: **`components.css`**.                                                                                                                                                                            |
| Insight-Panel (Metriken) | `.metrics-insight-panel` (+ optional **`.metrics-insight-panel__section`**, **`__heading`**, **`__list`**, **`__item`**, **`__value`**)              | Fließtext- und Listen-Einordnung **unter** dem Spotlight (z. B. GGL). Strukturierte Abschnitte können serverseitig als Markup aus **`backend/services/ggl_rules.py`** kommen (`|safe` im Template); Hervorhebungen mit **`__value`**.                                                                                                                                                                            |
| Daten-Tabelle (Shell)  | `.table-responsive`, `.data-table-wrap`, `.data-table`                                                                                              | Karten-Rahmen, **Light:** `thead` = **Card-Header**-Fläche (`--brand-primary-200`); Dark: `--color-surface-secondary`; Zellen-Raster; letzte Spalte rechts — GGL + Events (`components.css`); **`.table thead`** Light ebenso |
| Rangliste GGL          | `.data-table` + `.ggl-ranking-table`, Spalten `__col-rank` / `__col-name` / `__col-num`, Zeilen `__row--current`, `__row--rank-1` … `__row--rank-3` | GGL Tabelle-Tab: **Hülle** `data-table-wrap` + Tabelle `data-table ggl-ranking-table`                                                                                                                                       |
| Schätzungsrangliste BillBro (Event-Detail) | `.data-table` + **`.billbro-guess-ranking-table`**, Spalten **`__col-rank`** / **`__col-name`** / **`__col-num`**, Zeilen **`__row--current`**, **`__row--rank-1` … `__row--rank-3`** | Tab **BillBro** nach gesetztem Rechnungsbetrag: gleiche Spaltenlogik wie GGL-Ranking; Card-Anker **`id="billbro-guess-ranking"`** (**§5.2**, Event-Detail-Bullets). |
| Teilnehmer Event-Detail | `.data-table` + **`.events-participants-table`**, Spalten **`__col-member`** / **`__col-status`**, Zeile **`__row--current`** (eingeloggtes Mitglied) | Wie **Kommend/Archiv**: **`table-responsive data-table-wrap`** direkt im Tab (ohne zusätzliche Card um die Tabelle); Kopf **Teilnahme** rechtsbündig wie Events-Liste |
| Event-Listen (Tabelle) | wie **Daten-Tabelle**; optional weiter `.table` wo kein Card-Rahmen nötig (z. B. Admin)                                                             | Events Kommend/Archiv; RSVP in Zellen: `.data-table td:has(.status-form)` (und `.table` …) in `components.css`; Spalte **Typ** nur Icon: `**.data-table__cell--event-type`** + `sr-only`-Text; Archiv **ohne** Spalte Küche |

**Prinzip — Daten-Tabellen und Cards (verbindlich):** Große **`data-table`**-Listen (Ranking, Teilnehmer, Bewertungen, Vereins-Statistiken usw.) liegen **direkt** im Tab- bzw. Panel-Inhalt in **`table-responsive`** / **`data-table-wrap`** — **ohne** zusätzliche umschließende **`.card`**. Rahmen und Kopfzeilen-Optik kommen vom Tabellenmuster selbst (**`thead`** wie Card-Header, **§5.1** Zeile „Daten-Tabelle“). **`.card`** nutzen für **Formulare**, **Spotlight-/KPI-Blöcke**, **Charts** oder **zusammenhängende Info-Summary** — nicht als äußerer Container um eine volle Datentabelle. **Ausnahmen** nur bewusst und hier oder im **Entscheidungslog §12** festhalten (z. B. Admin mit schlichter **`.table`** ohne Card-Optik).


**HTML-Referenz:** bestehende Templates + `static/css/v2/components.css`.

**Standard-Geltung (Tabs, Tabellenkopf, Filter-/Tool-Leisten):** Die beschriebenen Styles für **`.tabs--panel`**, **`thead`** bei **`.data-table`** / **`.table`**, **`tool-surface`**, **Tool-Strip** (**§5.2.2–5.2.3**) und zugehörige Tokens gelten **für das gesamte Projekt**, sobald ein Template dieselben Klassen verwendet — sie sind **nicht** auf den Events-Index beschränkt. **`static/css/v2/components.css`** ist die **einzige** normative CSS-Quelle dafür; der Events-Index (und weitere migrierte Seiten) sind **Referenz-Implementierungen**, keine Sonderlocke.

#### 5.1.1 Buttons (Migration)

- **Nur** die **`components.css`**-Button-Klassen: **`.btn`** plus Modifikatoren (**`.btn--primary`**, **`.btn--outline`**, **`.btn--danger`**, **`.btn--success`**, **`.btn--ghost`**, **`.btn--icon-only`** … — siehe **`components.css`** und bestehende V2-Templates.
- **Semantik:** Primäraktion = **Primary**; sekundär = **Outline**; zerstörerisch = **Danger**; Erfolg bestätigen = oft **Success** (wo im Projekt schon verwendet).
- **Keine** freien Button-Styles (Inline-`style`, eigene Klassen) ohne User-OK und Registry-Update.

#### 5.1.2 Flash-Meldungen vs. Inline-**`alert`**

Zwei getrennte Muster — beide sind **V2**, aber **unterschiedliches Markup**:

| | **Flash** | **Inline-Alert** |
| --- | --- | --- |
| **Zweck** | Kurzlebige Meldungen nach **Redirect** (Session), **global** über **`_flash_messages.html`** im `<main>` | **Seiteninhalt**: Hinweise, Banner, Zustände **ohne** Session-Flash |
| **Template** | **`templates/partials/_flash_messages.html`** | **`div.alert.alert--…`** mit **`alert__icon`**, **`alert__content`**, **`alert__title`**, **`alert__message`**, optional **`alert__actions`** |
| **CSS** | **`static/css/v2/layout.css`** (`.flash-messages`, `.flash-message`, `.flash-message-*` / `.flash-success` …) | **`static/css/v2/components.css`** (`.alert`, `.alert--info` …) |
| **Wann** | Nur über **`flash()`** vom Backend — Agent ändert am Partial typischerweise **einmal zentral** (Phase **7f** oder eigener Task) | Inhaltliche Hinweise in migrierten Seiten: **hier** das **`.alert`**-Muster nutzen |

**Abgrenzung zu `empty-state`:** Absichtlich ruhige „keine Daten“-Situation → **`empty-state`** (**§5.2**). **Nicht** Flash/Alert dafür missbrauchen.

**Hinweis:** Flash und Alert sind optisch ähnlich (Farben über Tokens), aber **noch nicht** zu einem einzigen HTML-Muster zusammengeführt — bei globalem Flash-Redesign **§16.2** um konkrete Zeile ergänzen oder Entscheidungslog.

### 5.2 Neu — im Redesign einführen


| Muster                  | Klassen (BEM)                                                                                                                                                                                                                                                                                                 | Verwendung                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Kontextleiste (Legacy)  | `.context-actions`, `.context-actions__title`, `.context-actions__buttons`; optional **`.tool-surface`** auf der `nav`                                                                                                                                                                                         | Nur noch **Sonderfall**; Standard ist **Tool-Strip §5.2.3** (`disclosure` in **`card.card--filter`**). `base.css` enthält zusätzlich **`.page-header:has(+ .events-planning-strip)`** für die Events-Planungs-Card. |
| Tool-Strip (Aktionen)   | **`.tool-strip__actions`** (Container in **`disclosure__content`**)                                                                                                                                                                                                                                            | Nur Buttons/Links/inline-Forms **ohne** Feld-Block darüber; gleiche Button-Abstände und Mobile-Stapel wie bei Formular-Aktionszeilen (**§5.2.3**)                                                                 |
| Sekundärfläche          | **`.tool-surface`**                                                                                                                                                                                                                                                                                           | Auf **`card.card--filter`**; optional historisch auf **`context-actions.tool-surface`** (**§5.2.2**)                                                                                                                |
| Settings-Navigation     | `.settings-nav`, `.settings-nav__section`, `.settings-nav__section-title`, `.settings-nav__list`, `.settings-nav__row`, `.settings-nav__icon`, `.settings-nav__meta`, `.settings-nav__label`, `.settings-nav__description`, `.settings-nav__badge`, `.settings-nav__badge--warning`, `.settings-nav__chevron` | **Verein-Hub** (alle + Admin-Zeilen); persönliche Einstiege nach Umsetzung **§4.5** über User-Menü                                                                                           |
| User-Menü (Top-Bar)     | **`.user-menu`** (`<details>`), **`.user-menu__summary`** (mit **`btn` `btn--icon-only`**), **`.user-menu__panel`**, **`.user-menu__list`**, **`.user-menu__link`**, **`.user-menu__link--danger`**, **`.user-menu__sep`**, optional **`.user-menu__badge`** | **§4.5:** Konto-Einstiege und Logout; Trigger nur **Lucide `user`**, kein Name in der Leiste. **`components.css`** Abschnitt „USER MENU“. |
| Leerzustand (Tab/Liste) | `.empty-state`, `.empty-state__icon`, `.empty-state__message`, optional `**.empty-state--filtered`**                                                                                                                                                                                                          | Wenn absichtlich **kein** Alert mit Aktionen gewünscht: ruhiger Hinweis in Tab-Inhalt (z. B. Events **Kommend** ohne Treffer). **Nicht** für Flash-kritische Meldungen — dafür `**.alert`**. |
| BillBro-Phasenleiste     | **`.billbro-workflow-block`** (Rahmen), **`.billbro-workflow`**, **`.billbro-workflow__hint`** (`role="status"`), **`.billbro-workflow__step`**, **`__step--done`**, **`__step--current`**, **`.billbro-workflow__index`**                                                                                                                                                               | Event-Detail **BillBro**: Phasen **Schätzrunde → Rechnung → Gesamtbetrag → Abgeschlossen**; unter der Leiste **Kurztext** je **Organisator** vs. **Mitglied** und Phase (was tun / worauf warten). **`components.css`**. |
| Bewertungsliste (Detail) | `.data-table` + **`.events-ratings-others-table`**, Spalten **`__col-member`** / **`__col-score`** / **`__col-highlight`**, Text **`__highlight-text`** / **`__dash`**, Zeile **`__row--current`** (eigene Bewertung); dazu **`.event-ratings-all`** / **`__heading`**, **`.event-ratings-toolbar`** (Aktionen Bearbeiten/Löschen oberhalb der Tabelle) | Tab **Bewertungen**: Abschnitt **Alle Bewertungen** volle Breite wie Events/GGL; **alle** Einträge in der Tabelle; Formular-Card **nur** bei Neuanlage/Bearbeiten (`#event-ratings-form`); nach gespeicherter Bewertung Toolbar **`#event-ratings-actions`**; Anker **`#event-ratings-all`** für Redirects nach Speichern/Abbrechen (**`ratings.*`** mit **`_anchor`**). |
| Dashboard (Intent-Layout) | **`.dashboard-intent`**, **`.dashboard-intent__heading`**, **`.dashboard-intent__grid`**, **`.dashboard-intent-tile`** (+ **`__icon`**, **`__body`**, **`__title`**, **`__meta`**, **`__chev`**), Modifier **`dashboard-intent-tile--static`**. **`dashboard-intent__stack`** existiert in **`components.css`**, wird auf dem **Dashboard** nicht mehr genutzt (alle drei Sektionen: Kacheln in **`__grid`** — **§6.3**). **Bereinigungsseite (`events/cleanup`):** **`.cleanup-step-nav`** (+ **`__counter`**, **`__actions`**), **`.events-cleanup-hint`**, **`.cleanup-undo-form`**; außerdem **`.events-cleanup-intro`** (Intro unter **`page-header`**). **Legacy / ungenutzt auf Dashboard:** **`.dashboard-next-event*`** (CSS vorhanden), **`a.card--dash-tile__hit`**, **`.card--dash-tile__actions`**, **`.card--dash-tile`**, **`.dashboard-card-link`**, **`.dashboard-hygiene-rows`**, **`.dashboard-row-link`**, **`dashboard-row-link--block-start`**. | Drei Sektionen **Zu erledigen** / **Zur Info** / **Erkunden**; knappe Kacheln. CSS: **`components.css`** „DASHBOARD“ + Bereinigung wie **§6.3**. |


**CSS:** `static/css/v2/components.css` (Abschnitte „TOOL SURFACE“, „DISCLOSURE“, „CONTEXT ACTIONS“ [Legacy], „TOOL-STRIP“ / **`.tool-strip__actions`**, „SETTINGS NAV“, „USER MENU“, „EMPTY STATE“, „BILLBRO WORKFLOW“, „EVENT RATINGS“, „DASHBOARD“, Bereinigung **`.cleanup-step-nav*`** / **`.events-cleanup-*`** / **`.cleanup-undo-form`**, Modifier **`billbro-guess-ranking-table`** / **`events-ratings-others-table`**).

#### 5.2.1 HTML-Snippets (Referenz)

**Primär: Tool-Strip** — siehe **§5.2.3** (Planung/Filter einheitlich). Die folgenden Snippets sind Kurzreferenz; verbindliche Struktur- und Verhaltensregeln stehen in **§5.2.3**.

**`context-actions`** (Legacy / Sonderfall) — flache Leiste **ohne** `<details>`. Nur verwenden, wenn bewusst kein Chevron/Einklapp gewünscht; sonst **§5.2.3**.

```html
<nav class="context-actions tool-surface" aria-label="Aktionen zu dieser Seite">
  <p class="context-actions__title">Planung</p>
  <div class="context-actions__buttons">
    <a href="{{ url_for('events.edit', event_id=event.id) }}" class="btn btn--outline">Bearbeiten</a>
    <a href="{{ url_for('events.year_planning') }}" class="btn btn--primary">Jahresplanung</a>
  </div>
</nav>
```

`**settings-nav**` — Sektionen mit Überschrift und Liste von Zeilen (`<a>` oder `<button>`). Badge und Beschreibung optional.

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

**`user-menu`** — `<details>` in der User-Bar; Summary = **Lucide `user`**, Panel mit Links (siehe **§4.5**).

```html
<details class="user-menu">
  <summary class="btn btn--icon-only user-menu__summary" aria-label="Konto und Einstellungen">
    <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><use href="…#user"></use></svg>
  </summary>
  <div class="user-menu__panel">
    <ul class="user-menu__list" role="list">
      <li><a href="{{ url_for('member.profile') }}" class="user-menu__link">Profil</a></li>
      <li>
        <a href="{{ url_for('member.security') }}" class="user-menu__link">
          <span>Sicherheit</span>
          <!-- optional: <span class="user-menu__badge">2FA aus</span> -->
        </a>
      </li>
      <li><a href="{{ url_for('member.technical') }}" class="user-menu__link">App &amp; Benachrichtigungen</a></li>
    </ul>
    <div class="user-menu__sep" role="presentation"></div>
    <a href="{{ url_for('auth.logout') }}" class="user-menu__link user-menu__link--danger">Abmelden</a>
  </div>
</details>
```

`**empty-state**` — zentrierter Hinweis ohne Call-to-Action (Icon optional, Lucide-Sprite wie üblich).

Neutral (ungefiltert, z. B. keine kommenden Events):

```html
<div class="empty-state" role="status">
  <div class="empty-state__icon" aria-hidden="true">
    <svg class="icon" viewBox="0 0 24 24"><use href="…#calendar"></use></svg>
  </div>
  <p class="empty-state__message">Keine kommenden Events verfügbar.</p>
</div>
```

Gefiltert ohne Treffer (zusätzlicher Modifier, Text mit Filterkontext):

```html
<div class="empty-state empty-state--filtered" role="status">
  <div class="empty-state__icon" aria-hidden="true">
    <svg class="icon" viewBox="0 0 24 24"><use href="…#calendar-off"></use></svg>
  </div>
  <p class="empty-state__message">Für das Jahr … gibt es keine kommenden Events.</p>
</div>
```

#### 5.2.2 Sekundärleiste — `.tool-surface`

**Zweck:** Gemeinsame Fläche für **Filter-Cards** (`**card.card--filter**`) und optional **Legacy** **`context-actions.tool-surface`** (**§5.2.1**).

**CSS:** `static/css/v2/components.css` (Abschnitt **TOOL SURFACE**). Basis **`.tool-surface`:** Hintergrund, Rand, `border-radius`; Theme-Overrides:

- **Light:** **`--brand-primary-50`**, Rand **`--color-border-default`**.
- **Dark:** Hintergrund **`--color-bg-base`** (Leiste wie Seitengrund), Rand **`--color-surface-secondary`**.

**`.card.card--filter.tool-surface`:** **`box-shadow: none`**, kein Hover-Lift; Innenabstand über **`.card--filter .card__body`**. **`.context-actions.tool-surface`** enthält zusätzlich Flex-Layout und **`margin-bottom`** — **§5.2.1**.

**Filter-Chips in der Disclosure-Kopfzeile (`chip chip--info`):** visuell an **inaktive Panel-Tabs** gekoppelt — **Light:** **`--color-bg-muted`**; **Dark:** **`--chrome-inactive-pill-bg`**. Das Token **`--chrome-inactive-pill-bg`** wird auf **`[data-theme="dark"]`** (vor den **`.tabs--panel`**-Regeln) definiert und von **inaktiven** **`.tabs.tabs--panel .tabs__tab`** sowie von **`card--filter .disclosure__summary .chip--info`** genutzt.

**Hülle im Markup:**

```html
<div class="card card--filter tool-surface">
```

#### 5.2.3 Tool-Strip — verbindliches Muster (Filter, Planung, gleiche Leiste)

**Ziel:** Alle **Sekundärleisten** in der „Werkzeug“-Optik verhalten und aussehen gleich: **oranger/interaktiver Titel** (Token: semantisch **`--color-interactive-primary`**), **Chevron** (Lucide **`chevron-down`**, rotiert wenn `open`), optional **`chip chip--info`** für gewählte Filterwerte in der Kopfzeile; **Buttons** und **Eingabefelder** folgen den bestehenden **`.btn`** / **`.form-field`**-Mustern.

**HTML-Struktur (immer):**

1. **`div.card.card--filter.tool-surface`** (optional Seiten-spezifische Klasse, z. B. **`events-planning-strip`** auf der Events-Übersicht für Abstand zur **`page-content`**).
2. **`div.card__body`**
3. **`<details class="disclosure" id="…">`** — stabile **`id`** vergeben, wenn **JavaScript** den Zustand speichert.
4. **`<summary class="disclosure__summary">`** — zuerst Icon, dann **sichtbarer Titel-Text**, dann optional **Chips** (aktive Filter).
5. **`<div class="disclosure__content">`** — **entweder:**
   - **Nur Aktionen (keine Felder darüber):** **`nav.tool-strip__actions`** oder **`div.tool-strip__actions`** mit **`role`** / **`aria-label`** wie passend; darin **`a.btn`** / **`button`** / **`form.form--inline`**.
   - **Mit Filter- oder Suchfeldern:** **`form.form`** mit **`form-row`** / **`form-field`** … und unten **`div.form-actions`** (Trennlinie **oberhalb** der Submit-Zeile — nur sinnvoll, wenn echte Felder folgen).

**Nach Submit eines Filter-GET-Formulars (Primary „Filtern“):** Zugehöriges **`details`** schließen (**`open = false`**) und den **`sessionStorage`**-Key dieser Leiste auf **geschlossen** (`'0'`) setzen, damit die Seite nach dem Reload **eingeklappt** bleibt. *(Umsetzung: Inline-Skript in **Events-Übersicht** und **GGL**; weitere Seiten mit gleichem Muster analog.)*

**CSS:** `static/css/v2/components.css` — Abschnitte **TOOL SURFACE**, **DISCLOSURE**, Regeln unter **`.card--filter .disclosure__summary`** (u. a. **`font-size: text-base`**, **`font-semibold`**, Primärfarbe, **`flex-wrap`**) und **`.card--filter .disclosure__content > .tool-strip__actions`** (rechtsbündig, **`gap`**, **`min-height`** für Buttons, Mobile: stapeln wie bei **`.form-actions`**).

**Events-Übersicht (`templates/events/index.html`):**

- Zwei unabhängige **`details`**: **`id="events-planning-disclosure"`** (nur Admins) und **`id="events-index-filter-disclosure"`**.
- **`{% block scripts %}`:** kleines Inline-Skript stellt den **Offen/Geschlossen**-Zustand aus **`sessionStorage`** wieder her und schreibt bei **`toggle`** zurück.
- **Standard, wenn kein gespeicherter Wert:** **beide eingeklappt** (`open === false`).
- **Keys (nicht ändern ohne Migration):** `gourmen:eventsIndexPlanningDisclosureOpen`, `gourmen:eventsIndexFilterDisclosureOpen`.
- **Tab-Wechsel** (Kommend / Archiv / Statistiken): voller Seiten-Reload mit gleichem Origin — **`sessionStorage`** bleibt erhalten, der **letzte** Zustand der Leisten gilt weiter.
- **Filter-Submit:** siehe oben **„Nach Submit eines Filter-GET-Formulars“** — **`events-index-filter-disclosure`**.

**GGL (`templates/ggl/index.html`):**

- Ein **`details`**-Filter: **`id="ggl-filter-disclosure"`**; **`summary`:** sichtbarer Titel **„Saison“** (nicht „Filter“) + **`chip chip--info`** mit der gewählten Saison — gleiche Disclosure-Kopf-Logik wie bei anderen Tool-Strips (**§5.2.3**). **Lucide** **`chevron-down`** / **`funnel`** am Primary **Filtern**; **`form-actions form-actions--start`** (Reihenfolge **Filtern** → **Zurücksetzen**), wie Events-Filter.
- **`{% block scripts %}`:** **`bindDisclosure('ggl-filter-disclosure', 'gourmen:gglFilterDisclosureOpen', false)`** — Standard **eingeklappt**; Tab-Wechsel (Performance / Tabelle / Spielverlauf) = Reload, Zustand bleibt über **`sessionStorage`**.
- **Saison-Filter-Submit:** wie **§5.2.3** **„Nach Submit eines Filter-GET-Formulars“** — **`ggl-filter-disclosure`**.
- Bereichs-Tabs: **`tabs tabs--panel`** (**§5.1**). Tab **Deine Performance:** Kennzahlen-Bereich **`metrics-spotlight`** + optional **`metrics-insight-panel`** (Inhalt aus Backend-Logik, siehe **§5.1**).

**Event-Detail — Planung:** gleiches **`disclosure`**-Muster; bei **nur** Schaltflächen ohne Felder **`tool-strip__actions`** statt **`form-actions`** (keine künstliche Formular-Trennlinie).

**Event-Detail (`templates/events/detail.html`):**

- **Bearbeiten (Organisator/Admin):** **`details`** mit **`id="event-detail-edit-disclosure"`**; äußere Card mit **`events-planning-strip`**; sichtbarer Titel **„Bearbeiten“**. **`{% block scripts %}`:** **`bindDisclosure('event-detail-edit-disclosure', 'gourmen:eventDetailEditDisclosureOpen', false)`** — Standard **eingeklappt**, **`sessionStorage`** wie Events-Index (**§5.2.3**).
- **Tabs:** **`tabs tabs--panel`**; Lucide-Icons per Sprite-Makros (wie **`events/index.html`**).
- **Tab Infos — erste Card:** Titel **„Summary“**, Icon **`clipboard-list`**; **RSVP** als erste **`info-row`** **„Deine Teilnahme:“** mit **`chip-select`** im **`card__body`** (nicht im Header).
- **Tab BillBro — Live-Update:** GET **`/events/<id>/billbro-sync`** (`**events.billbro_sync**`, JSON, **`Cache-Control: no-store`**) liefert einen kompakten Zustand; bei **`?tab=billbro`** pollt Inline-JS alle **12 s** (nur bei **`document.visibilityState === 'visible'`**), vergleicht JSON; bei Änderung **`location.reload()`**. Hash-Anker bleiben erhalten, wo der Browser es unterstützt.
- **Tab BillBro — Anker:** Cards/Blöcke mit **`id`** **`billbro-share`**, **`billbro-guess-ranking`**, **`billbro-my-guess`**, **`billbro-new-guess`**, **`billbro-attendance`**, **`billbro-enter-bill`**, **`billbro-tip-suggestion`**, **`manual-total`**; **`scroll-margin-top`** für **`[id^="billbro-"]`** und **`#manual-total`**. Redirects aus **`billbro.py`** nutzen **`url_for(..., _anchor='…')`** wo sinnvoll; **`mark_absent` / `mark_present`** zurück aufs Event-Detail mit **`tab=billbro`** und **`#billbro-attendance`**.
- **Tab BillBro — Schätzungsrangliste:** **`data-table billbro-guess-ranking-table`** (wie GGL-Spaltenmuster).
- **Tab Bewertungen:** Card **Gesamtbewertung** mit **`clipboard-list`** + **`metrics-spotlight`** / **`metrics-spotlight__hero`**; Abschnitt **Alle Bewertungen** mit **`events-ratings-others-table`** (alle Zeilen inkl. eigener, **`__row--current`**); Formular nur bei Abgabe/Bearbeiten; Toolbar oberhalb der Tabelle für Bearbeiten/Löschen; Anker **`event-ratings-form`** / **`event-ratings-actions`** / **`event-ratings-all`** (**§5.2**).
- **Orientierung:** statt Breadcrumb-Kette **`.page-back`** „Zurück zu Events“ (**§3**). **Seitentitel (`h1`):** nur **Event-Typ-Icon** (Lucide) + **Datum**; Event-Typ-Name nur **`sr-only`** für Screenreader. **`{% block title %}`:** Datum + „Gourmen“.

**Snippet — Planung (nur Buttons):**

```html
<div class="card card--filter tool-surface events-planning-strip">
  <div class="card__body">
    <details id="events-planning-disclosure" class="disclosure">
      <summary class="disclosure__summary">
        <!-- Lucide chevron-down wie auf der Seite üblich -->
        Planung
      </summary>
      <div class="disclosure__content">
        <nav class="tool-strip__actions" aria-label="Planung und Administration">
          <a href="…" class="btn btn--primary">…</a>
        </nav>
      </div>
    </details>
  </div>
</div>
```

**Snippet — Filter (Felder + Chips in der Kopfzeile):**

```html
<div class="card card--filter tool-surface">
  <div class="card__body">
    <details id="events-index-filter-disclosure" class="disclosure">
      <summary class="disclosure__summary">
        <!-- chevron-down -->
        Filter
        <!-- optional: <span class="chip chip--info">2025</span> … -->
      </summary>
      <div class="disclosure__content">
        <form method="get" class="form" action="…">
          <!-- form-row / form-field … -->
          <div class="form-actions form-actions--start">
            <button type="submit" class="btn btn--primary"><!-- Lucide funnel --> Filtern</button>
            <a class="btn btn--outline" href="…">Zurücksetzen</a>
          </div>
        </form>
      </div>
    </details>
  </div>
</div>
```

**`base.css`:** `.page-header:has(+ .events-planning-strip)` — engerer Abstand unter dem **`h1`**, wenn die Planungs-Card direkt folgt (analog zur früheren Regel für **`context-actions`**).

### 5.3 Entscheidungshilfe: welches Pattern?


| Situation                                       | Richtung                                                                                                                                        |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1–2 Kennzahlen sehr prominent (Hero)            | **`metrics-spotlight`** + **`metrics-spotlight__hero`** (§5.1); optional darunter **`stat-tiles--metrics-follow`** oder **`metrics-insight-panel`** |
| Mehrere gleichwertige KPIs im Raster            | **`stat-tiles`** / **`stat-tile`** (§5.1), ggf. kombiniert mit Spotlight                                                                         |
| Viele gleichartige Einträge (Ranking, Liste)    | `**.data-table-wrap`** + `**.data-table**`; GGL zusätzlich `**.ggl-ranking-table**`; sonst `**.table**` / eigene Liste — keine N gleichen Cards; **keine** extra **`.card`** um die Tabelle (**§5.1** Prinzip Tabellen vs. Cards) |
| Workflow (BillBro)                              | **`.billbro-workflow-block`** + **`.billbro-workflow`** + **`.billbro-workflow__hint`** + Cards/Formulare; optional **Polling** über **`billbro-sync`** bei **`tab=billbro`** (**Event-Detail-Bullets**)                                                                                                                  |
| Event-Bewertungen (Tabelle, Detail)              | **`events-ratings-others-table`** (**§5.2**) — eine Zeile pro Mitglied (inkl. eigene), Spalten inkl. Highlight; Toolbar/Anker siehe **§5.2**                                                                                  |
| Filter / Planung / sekundäre Werkzeug-Leiste    | **Tool-Strip §5.2.3** (`card card--filter tool-surface` + `disclosure`; Inhalt `tool-strip__actions` oder `form` + `form-actions`)                |
| Tab zeigt keine Einträge, kein zusätzlicher CTA | `**empty-state**` (ggf. `**empty-state--filtered**`) — nicht `**alert**`, wenn bewusst ohne Aktion                                              |
| Admin/Organisator auf einer Event-Seite         | **Tool-Strip §5.2.3** (`disclosure` in `card--filter`); **`context-actions`** nur Legacy                                                                 |
| Bereichs-Tabs mit Listen/Karten darunter        | Optional **`.tabs.tabs--panel`**: **§5.1** — gleiches Verhalten **überall** bei Nutzung der Klassen; **`.tabs__content`** mit Innenabstand — Referenz **Events-Index** (`components.css`) |
| Monatsessen-/Vereins-Kennzahlen mit Diagrammen   | Backend **`get_monatsessen_statistics`** (`**backend/services/monatsessen_stats.py**`) + **`metrics-spotlight`** + **`metrics-insight-panel`** (Block **Top & Flop:** **`details.disclosure--in-insight`**, Standard **zu**; Texte Rekorde/Trinkgeld/beste-schlechteste Restaurant; Makro **`stats_star_rating`** im Template) + Chart.js; JSON **`#events-monatsessen-charts-data`**: **`memberParticipation`**, **`organizerCost`**, **`organizerRatings`** (Ø Gesamtbewertung 1–5 je Organisator), **`restaurantRatings`** (alle Restaurants mit Bewertungen), **`kitchens`**. **Restaurant-Tabelle:** **`section.events-stats-restaurant-block`** (ohne Card), **`data-table events-stats-restaurant-ratings-table`**, sortierbare **`events-stats-sort-btn`**, Client **Top 10**; CSS **`events-stats-inline-rating`**, **`base.css`** **`[hidden]`** mit **`!important`** (Kompatibilität mit **`.empty-state`** **`display:flex`**). JS **`static/js/v2/events-monatsessen-stats.js`**. Referenz **`templates/events/index.html`** (`tab=stats`). |


---

## 6. Konventionen

### 6.1 Entscheidungen dokumentieren (Agent-Handoff)

Nachfolgende Agents haben **keinen** Zugriff auf frühere Chats. Alles Verbindliche muss in `**REDESIGN.md`** (und bei Bedarf Registry / andere Abschnitte) **ohne versteckte Arbeitsbezeichnungen** stehen.

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

### 6.3 Handoff: Dashboard & Bereinigung (für den nächsten Agenten ohne Chat-Kontext)

**Wenn du nur diesen Abschnitt liest:** Du hast genug für **Dashboard**, **Bereinigung** (`events.cleanup`) und **`RetroCleanupService`** — ergänzend **§4.1** (Zeile **Dashboard**), **§8.1**, **§12** (neueste Entscheidungen), **§5.1** (Registry-Zeile Dashboard + Bereinigung), **`.cursor/rules/redesign.mdc`**.

**Layout (Stand 2026-04-06):** Jede der drei Sektionen **Zu erledigen**, **Zur Info**, **Erkunden** umschließt ihre Kacheln mit **`dashboard-intent__grid`** (mobil 1 Spalte, ab **480px** 2 Spalten). Es gibt **kein** **`dashboard-intent__stack`** mehr im Dashboard-Template.

**Dashboard — implementierte Pfade:**

| Bereich | Datei / Ort |
| --------|-------------|
| Template | **`templates/dashboard/index.html`** — Push-Banner; **Zu erledigen:** Kachel **Bereinigung** (`url_for('events.cleanup')`, Lucide **`brush-cleaning`**, Titel **„Bereinigung“**, Meta **„1 fehlende Angabe“** / **„n fehlende Angaben“**); Kachel **Zu-/Absage** (`url_for('events.detail', event_id=…)`, Lucide **`calendar`**, Titel **„Zu-/Absage“**, Meta **`event_typ.value ~ ' am ' ~ display_date`**) wenn **`rsvp_prompt_event`** gesetzt. **Zur Info** / **Erkunden** wie §4.1. Jinja-Makro **`dashboard_intent_tile`**. |
| Route | **`backend/routes/dashboard.py`** — u. a. `next_event`, **`ggl_stats`** (**`rank_total`**), `latest_bill_event`, `latest_bill_participation`, **`rsvp_prompt_event`** = **`RetroCleanupService.get_upcoming_rsvp_prompt_event(current_user.id)`**. **`inject_retro_cleanup`** (**`app.py`**) liefert **`retro_cleanup_progress`** via **`RetroCleanupService.get_progress`** (nur **vergangene** Kandidaten, siehe unten). |
| CSS | **`static/css/v2/components.css`** — **DASHBOARD** + Bereinigung (**`.cleanup-step-nav*`**, **`.events-cleanup-hint`**, **`.cleanup-undo-form`**, **`.events-cleanup-intro`**). Nach Änderung: **`python scripts/fingerprint_assets.py`**. |
| User-Bar | **`templates/partials/_user_bar.html`** — **kein** Cleanup-Button; Fortschritt über **`inject_retro_cleanup`**. |

**Fachlogik (verbindlich, Stand 2026-04-06):**

1. **Zu-/Absage-Kachel (kommend):** Veröffentlichte Events mit **`datum`** von **Tagesbeginn UTC heute** bis **Ende des Tages heute + `UPCOMING_WINDOW_DAYS` (30)**; nur Events **nach** Mitglieds-**`beitritt`**; **frühestes** **`datum`**, bei dem **`Participation`** fehlt oder **`responded_at`** **NULL** ist. **Nicht** Teil der Bereinigungsseite — Einstieg ins **Event-Detail** zum Antworten.

2. **Bereinigung (`/events/cleanup`):** **Nur vergangene** Events: **`Event.datum <`** **Tagesbeginn UTC heute** (nicht mehr „7 Tage nach Event“ als Ausschluss). Gleiche **Beitritts-Filterung**. **Offen** = fehlende Zu-/Absage **oder** (bei **Zusage** und **`allow_ratings`**) fehlende **Bewertung**. **Abgesagt** mit gesetzter Antwort ist **abgeschlossen** und erscheint **nicht** in der offenen Liste. **Reihenfolge:** **`datum`** **absteigend** (vom jüngsten vergangenen Datum rückwärts). **Navigation:** Query **`?i=`** (0-basierter Index in der Liste der **offenen** Einträge); **`.cleanup-step-nav`**: „**k von n**“, **Zurück** / **Weiter**. **`cleanup_rsvp`** (POST): nur wenn **`allows_cleanup_rsvp`** — **ausschließlich vergangene** Events. **Rückgängig:** Session-Key **`cleanup_rsvp_undo`** (Snapshot der Teilnahmezeile **vor** dem letzten POST); **`POST /events/cleanup/undo-rsvp`**; Konstante **`CLEANUP_RSVP_UNDO_SESSION_KEY`** in **`backend/routes/events.py`**. Nach **gespeicherter Bewertung** (`**ratings.rate_event**`) wird der Undo-Eintrag für dieselbe **`event_id`** entfernt (**`backend/routes/ratings.py`**), damit keine inkonsistente Kombination (Bewertung ohne passende Teilnahme) entsteht.

3. **`rating_prompt` / `get_rating_prompt_event_for_member`:** für das **Dashboard nicht mehr** verwendet; Datei **`backend/services/rating_prompt.py`** kann noch existieren, ist aber **obsolet**, solange nicht anderweitig referenziert.

**Seite `templates/events/cleanup.html`:** **`h1`** „Bereinigung“, **`.page-back`** → Dashboard. **`.events-cleanup-intro`** aus **`progress.pending`**. Zwischen **Navigation** und **Event-Karte:** **`.events-cleanup-hint`** — entweder „Gib an, ob du am Event dabei warst:“ (noch keine Antwort) **oder** „Du bist beim Event dabei gewesen. …“ (Zusage, ggf. Bewertung/Statuswechsel). Optional **`.cleanup-undo-form`**: „Letzte Zu-/Absage rückgängig“ (auch auf **„Alles erledigt“**, wenn die Session noch einen Undo enthält).

**IA:** **Zur Info** und **Zu erledigen** verlinken **tiefe** Ziele (Detail, Cleanup, Bestell-Detail, GGL mit **`season=`**). **Erkunden** nur **Merch-Shop**, **Statistiken**; **Events** primär über **Bottom-Nav**.

**Nutzer-Status:** **§13** **`templates/dashboard/index.html`** bis PO-Freigabe typischerweise **pending**.

**Git:** Branch **`redesign`**; kein Push auf **`master`** ohne User-Wunsch (**`.cursor/rules/redesign.mdc`**).

---

## 7. Checkliste pro Seiten-Migration

- Konventionen aus diesem Dokument  
- **Navigation:** Keine **Breadcrumb-Kette** (`breadcrumbs` / `breadcrumbs__*`). Stattdessen **`.page-back`** mit einem Link-Text wie **„Zurück zu …“** (Ziel = logische Parent-Route, nicht die vollständige Hierarchie). Referenz: **`templates/events/detail.html`**, **`static/css/v2/base.css`** (`.page-back`).  
- **Buttons:** Nur **`.btn`** + Modifikatoren aus **`components.css`** (**§5.1.1**); keine Ad-hoc-Button-Styles.  
- **Hinweise im Layout:** Session-**Flash** = Partial **`_flash_messages`** (**§5.1.2**); **Inline-Hinweise** auf der Seite = **`.alert`** mit Unterelementen, nicht Flash simulieren.  
- Keine hardcodierten Farben/Abstände  
- Mobile + Desktop geprüft  
- Touch-Ziele ausreichend  
- Links/Formulare funktionsfähig  
- **§13 Template-Übersicht:** passende Zeile(n) von `pending` → `done` (nur diese beiden Statuswerte; siehe §13 Legende)  
- Falls User-Entscheidung: Entscheidungslog + betroffene Abschnitte im **Klartext** (Abschnitt 6.1)  
- Falls beim Arbeiten **ersetzbare Altlasten** sichtbar werden: **§16 Cleanup-Backlog** um eine konkrete Zeile ergänzen (nicht nur mental notieren)
- Nach Änderungen an **`static/css/v2/components.css`** (steht im Fingerprint-Set): **`python scripts/fingerprint_assets.py`** ausführen und die erzeugte **Hash-Datei** unter `static/css/v2/` sowie **`static/asset-manifest.json`** mit committen.

---

## 8. Phasen (Überblick)


| Phase    | Inhalt                                                                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **0c**   | Dieses Dokument + Cursor-Rule (erledigt mit Erstanlage)                                                                                      |
| **1**    | Technisches Fundament: neue Komponenten (`context-actions`, `settings-nav`), Partials (Shell + `<head>`), Tab-JS optional, Tokens bei Bedarf |
| **2**    | GGL-Pilot                                                                                                                                    |
| **3**    | Events-Übersicht                                                                                                                             |
| **4a–c** | Event-Detail (Info, BillBro, Bewertungen)                                                                                                    |
| **5**    | Dashboard — siehe **§8.1** (Bewertungs-Thema + `cleanup.html`)                                                                               |
| **6**    | Verein-Hub + Shell-IA (**`settings-nav`**, User-Menü, Navigation) — **erledigt** (2026-04-05); **`admin.index`** Legacy-KPI-Seite exempt, siehe **§8.2** |
| **7**    | Rest-Templates, Cleanup, Performance — **Pakete §8.3**; Ende-Kriterium **§16**                                                               |


Detail-Schritte: **§8.3** (Phase 7), sonst nachgetragen.

### 8.1 Phase 5 (Dashboard) — §8.1 Klärung (historisch + Aktualisierung 2026-04-06)

**Ursprüngliche Entscheidung** (2026-04-05, PO/User — ältere **§12**-Zeilen): Nacharbeit zu Events über Dashboard; **`rating_prompt`** / Bewertungs-Zeile — **superseded** durch **§6.3** (2026-04-06): zwei Kacheln **Bereinigung** + **Zu-/Absage**, keine separate Bewertungs-Kachel.

**Aktueller Soll-Zustand** (verbindlich **§6.3**):

1. **Zu erledigen:** (a) **Bereinigung** → **`events.cleanup`** bei **`retro_cleanup_progress.pending > 0`**; (b) **Zu-/Absage** → **`events.detail`** für **`rsvp_prompt_event`** (kommende 30 Tage, frühestes offenes RSVP). Bewertungen vergangener Events nur über **Bereinigung**.
2. **User-Bar:** kein Cleanup-Icon; **`inject_retro_cleanup`**. **`events/cleanup.html`:** Phase-7-Qualität; Logik/Navigation **§6.3**.

Weitere Dashboard-Migration (KPI-Muster, Lucide-Konsolidierung, …) bleibt **Phase 5** gemäß Tracker.

### 8.2 Phase 6 (Verein + Shell) — Abschluss (2026-04-05)

**Ziel laut Masterplan:** Hubs und Navigation an die IA (**§4.2**, **§4.5**) anbinden.

**Umgesetzt (ohne Chat-Kontext nachvollziehbar):**

| Bereich | Dateien / Routen | Inhalt |
| -------- | ---------------- | ------ |
| **Top-Bar** | `templates/partials/_user_bar.html` | **Theme-Toggle**; **`user-menu`** (`<details>`): Profil, Sicherheit (Badge 2FA), App & Benachrichtigungen, Abmelden; Trigger Lucide **`user`**; **kein** Namenstext (Spirit/Rufname); **kein** Admin-Icon. |
| **Navigation** | `_sidebar.html`, `_bottom_nav.html` | Vierter Eintrag **„Verein“**, Icon **`landmark`**; aktiver Tab für `member.*`, `account.*`, `admin.*` — **ohne** `docs.*`. |
| **Verein-Hub** | `templates/member/index.html`, `backend/routes/member.py` → **`index`** | **`settings-nav`**: Sektion **Verein** (eine Zeile **Merch** → `member.merch`, Lucide **`shirt`**, Beschreibung **„Shop und Bestellungen“**); Sektion **Verwaltung** nur **`is_admin()`**: **Mitglieder** (`admin.members`), **Merch-Verwaltung** (`admin.merch`). **`h1` „Verein“**. Route **`member.index`** ohne zusätzlichen Template-Context. |
| **Dashboard-Copy** | `templates/dashboard/index.html` | **Zu erledigen:** Kacheln **Bereinigung** + **Zu-/Absage** (Copy **§6.3**); **GGL**-Meta **ohne** Teilnahme-Zähler; **Erkunden:** Merch-Kachel Titel **„Merch“**, Icon **`shirt`**, Meta **„Shop und Bestellungen“**; Statistiken **„KPIs und Charts“**. |

**`templates/admin/index.html` — bewusst nicht auf `settings-nav` umgebaut:** Die Seite bleibt ein **Legacy-KPI-Hub** (`hub-card`) für direkte Aufrufe von **`admin.index`** (Lesezeichen, alte Links). Die **Hauptnavigation** führt Admins primär über **Verein** (**§4.2**). Status in **§13:** **`done`** mit Begründung im **Entscheidungslog §12** („Exempt“).

**Phase 7** ist der nächste Schwerpunkt (**§10**); konkrete Arbeitspakete **§8.3**.

### 8.3 Phase 7 — Pakete (für Agenten ohne Chat-Kontext)

**Zweck:** Phase 7 ist zu groß für „alles auf einmal“. Jeder Agent bearbeitet **genau ein Paket** pro Session (oder bis Commit), dokumentiert den Abschluss in **§8.3.1** und im **Tracker §10**, dann erst nächstes Paket.

**Vor jeder Änderung:** `.cursor/rules/redesign.mdc`, **§7** (Migrations-Checkliste), **§5** (Komponenten-Katalog). **Branch:** `redesign`. **Nach `components.css`:** `python scripts/fingerprint_assets.py`.

**Reihenfolge:** Pakete **7a → 7f** (7b/7c/7d/7e sind untereinander parallelisierbar, sobald **7a** begonnen wurde; **7f** immer **zuletzt** — siehe Spalte „Blockiert bis“).

#### 8.3.1 Paket-Status (pflegen)

| Paket | Inhalt (Templates) | Status   | Hinweis |
| ----- | -------------------- | -------- | ------- |
| **7a** | `templates/events/cleanup.html`, `edit.html`, `year_planning.html` | erledigt | Lucide, **`.page-back`**, **`cleanup.html`** Copy **§6.3**; **`#rating-card`** in **`components.css`** (2026-04-06) |
| **7b** | `templates/member/profile.html`, `security.html`, `technical.html`, `member/merch/index.html`, `order.html`, `orders.html`, `order_edit.html` | erledigt | **`.page-back`** (Profil/Sicherheit/Einstellungen → **Dashboard**; Merch-Kopf → **Verein**); **`member.merch_order_detail`:** Redirect auf **Merch** `tab=orders` (kein separates **`order_detail`**-Template mehr). **Lucide** u. a. **`shirt`** für Merch; Stand 2026-04-06 |
| **7c** | `templates/admin/members.html`, `create_member.html`, `edit_member_enhanced.html`, `member_sensitive.html`, `member_security_overview.html`, `reset_member_2fa.html`, `reset_member_password.html`, `temp_password.html`, `create_event.html`, `admin/merch/index.html`, `article_form.html`, `article_detail.html`, `admin/merch/order_detail.html` | offen | **`admin/index.html`** bleibt exempt (**§8.2**, **§12**) — nicht migrieren |
| **7d** | `templates/errors/403.html`, `errors/404.html`, `errors/500.html`, `public/landing.html`, `offline.html` | offen | Kurzseiten; Tonalität ruhig; PWA **`offline.html`** |
| **7e** | `templates/auth/*.html` (alle 11: Login, Passwort, 2FA, Step-Up, Backup-Codes, …) | offen | Nach **7d** sinnvoll (öffentliche/Auth-Flows); **C-001** blockiert bis Lucide überall (§16.2) |
| **7f** | Abschluss: **`templates/base.html`** (§13), **`templates/dashboard/index.html`** auf **done** nach PO; **§16** P0/P1; Performance-Sanity; Registry-Totcode; ggf. **§14** | offen | **C-002** (V1 entfernen), **C-003**, **C-004** siehe §16.2 |

**Statuswerte:** nur `offen` | `erledigt` (pro Paket). Bei `erledigt`: **§7** für alle Dateien des Pakets erfüllt, Commit auf `redesign`, **§8.3.1** und ggf. **§13**-Einträge (siehe unten) aktualisieren.

#### 8.3.2 Pro Paket — immer gleiches Vorgehen

1. **Paket in §8.3.1** als „offen“ bestätigen (nicht an einem fertigen Paket weiterarbeiten).
2. **Templates** der Paketliste durchgehen: **V2**-Layout (`page-header`, `page-content`, Tokens, Registry-Klassen), **Lucide** (`url_for` Sprite wie Events/GGL), keine **Font-Awesome**-Neueinführung (Altbestand: §16.2 **C-001**). **Breadcrumb-Navs entfernen** → **`.page-back`** (§3 Breadcrumbs, **§7**).
3. **Formulare:** `.form`, `.form-field`, `.form-actions`; **Tabellen:** `data-table` / `table-responsive` wie in **§5.1**.
4. **Test:** Desktop + schmales Fenster; kritische Flows des Pakets (z. B. ein Login bei **7e**).
5. **Doku:** Tracker **§10** (Session-Notiz **§11** bei Abbruch); **Entscheidungslog §12** nur bei Abweichung vom Katalog oder PO-Entscheidung.
6. **Paket:** Status **erledigt** in **§8.3.1**; nächster Agent nimmt das nächste `offen`-Paket in Reihenfolge **7a→…→7f** (oder nach Absprache ein parallelisierbares Paket aus der Tabelle).

#### 8.3.3 §13 nachziehen

Solange **7f** nicht erledigt ist, bleibt die Zeile **„übrige `templates/`**“ in **§13** auf **pending**. Optional: **pro abgeschlossenem Paket** eine **Session-Notiz §11** oder eine kurze Zeile unter der §13-Tabelle („Paket 7b erledigt: …“), wenn **§13** noch keine Einzelzeilen pro Datei hat — Mindeststandard: **§8.3.1** muss stimmen.

**Ende Phase 7:** **§8.3.1** alle Pakete **erledigt**; **§16.1** erfüllt; **§10** Phase 7 „erledigt“.

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
- **Rate limiting:** In **Development** und **Testing** ist **`RATELIMIT_ENABLED = False`**; der **Flask-Limiter** wird in **`init_extensions`** mit **`enabled=False`** gebaut (**`backend/config.py`**, **`backend/extensions.py`**), damit lokales Arbeiten ohne häufige **429**-Antworten zuverlässig bleibt.

---

## 10. Fortschritts-Tracker


| Phase              | Status   | Anmerkungen                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0a Grundsatz + IA  | erledigt | Option A, IA + Settings-Hubs dokumentiert                                                                                                                                                                                                                                                                                                                                                                                                     |
| 0b Admin-Kontext   | erledigt | Muster `**context-actions**` in IA + Konventionen festgelegt (§4.4); **CSS** gehört zu Phase 1 (nicht mit „0b“ verwechseln)                                                                                                                                                                                                                                                                                                                   |
| 0c Doku            | erledigt | `REDESIGN.md`, `.cursor/rules/redesign.mdc`                                                                                                                                                                                                                                                                                                                                                                                                   |
| 1 Fundament        | erledigt | CSS/Snippets, Shell-Partials, **Head-Partials** (§13.2); Tab-JS für Bereichs-Tabs bleibt **optional** und kann bei Bedarf in späteren Phasen nachgerüstet werden                                                                                                                                                                                                                                                                              |
| 2 GGL-Pilot        | erledigt | Wie zuvor; zusätzlich **Performance-Texte** und Ranglogik in **`backend/services/ggl_rules.py`** (Insights, Tie-Break wie Tabelle, Teilnahme-Nenner, siehe **§11** / **§12** 2026-04-04); **Saison-Filter:** nach **Filtern** einklappen (**§5.2.3**).                                                                                                                                                                                                                    |
| 3 Events-Übersicht | erledigt | Wie zuvor; **Filter-Leiste** + **Tab Statistiken** erweitert: **Top & Flop**, Restaurant-Tabelle + Organisator-Bewertungs-Chart, **`[hidden]`**-Fix — **§5.3**, **§11**, **§12** (2026-04-05). |
| 4 Event-Detail     | erledigt | **`detail.html`:** **`tabs--panel`**, Tab Infos **Summary** + RSVP-Zeile **Deine Teilnahme**; Leiste **Bearbeiten** + **`sessionStorage`**; **`data-table`** (Teilnehmer, **`billbro-guess-ranking-table`**); BillBro **Hinweistext** unter Phasenleiste, **Anker** + Redirects, **`billbro-sync`**-Polling; Tab Bewertungen: Hero **`metrics-spotlight`**, **`events-ratings-others-table`** — Details **§11**. |
| 5 Dashboard        | weitgehend erledigt | Intent-Layout (**Zu erledigen** / **Zur Info** / **Erkunden**), **`dashboard_intent_tile`**, Merch-Kachel-Logik, **`rank_total`** in **`dashboard.py`**; visuelle PO-Freigabe optional (**§13** ggf. **`done`**). |
| 6                  | erledigt | Verein-Hub, Shell-Navigation, User-Menü — **§8.2**; **`admin.index`** Legacy exempt (**§12**). |
| 7                  | offen    | Arbeitspakete **§8.3** (Status **§8.3.1**); Abschluss **§16** + **§8.3.3** §13. |


### NAECHSTER SCHRITT

**Nächster Agent (Reihenfolge):** (1) **§8.3** — aktuelles **Phase-7-Paket** (Status **§8.3.1**) und dort genannte Templates. (2) **§10** Tracker + dieser Abschnitt. (3) **§16** / **§16.2** bei Backlog/Blockern. (4) Umsetzung **nur** für das gewählte Paket; **§7** Checkliste.

**Nächster Phase-7-Block:** Paket **7c** (Admin-Templates), siehe **§8.3.1**.

**Optional:** **`templates/dashboard/index.html`** in **§13** auf **`done`** setzen, wenn der PO das Intent-Dashboard visuell freigibt.

**Technische Anker:** **`backend/routes/member.py`** — **`member.index`** rendert **`member/index.html`** ohne Extra-Context. **`member.merch_order_detail`** (GET `/member/merch/order/<id>`): **kein** Template mehr — **Redirect** auf **`member.merch`** mit **`tab=orders`** und **`order_id`** (Deep-Links/Lesezeichen bleiben gültig). **`merch_order_edit`:** Redirect nach Speichern / bei nicht editierbarer Bestellung ebenfalls dorthin. **Dashboard / Bereinigung:** **`backend/routes/dashboard.py`**, **`backend/services/retro_cleanup.py`**, **`backend/routes/events.py`** (`cleanup`, `cleanup_rsvp`, `cleanup_undo_rsvp`), **`backend/routes/ratings.py`** (Undo-Clear), **`app.py`** (`inject_retro_cleanup`) — Details **§6.3**. **CSS-Fingerprint:** nach Änderungen an **`components.css`** immer **`python scripts/fingerprint_assets.py`**. Branch **`redesign`**.

---

## 11. Letzte Session-Notiz

- **2026-04-06 (Paket 7b):** Member-Unterseiten + Merch: **`profile`**, **`security`**, **`technical`**, **`member/merch/*`** — Breadcrumbs → **`.page-back`**, Lucide wie Events/GGL, Profil/Merch-Tabs **`tabs--panel`**. **`order.html`:** Legacy-Formular/Inline-JS unverändert (nur Kopf + **`card__subtitle`**-Fix). **Nacharbeit 2026-04-06:** Technik-**`h1`** nur «Einstellungen»; Zurück Profil/Sicherheit/Einstellungen → **Dashboard**; Merch **`h1`**/Verein-Kachel/Dashboard-Erkunden: **`shirt`**, Titel «Merch»; Bestellungen nur noch im Merch-Tab; **`order_detail.html`** entfernt, Route leitet auf **`member.merch?tab=orders&order_id=`** um. **Nächster Schritt:** **§8.3.1 Paket 7c**.
- **2026-04-06:** **Dashboard & Bereinigung** — IA: Kacheln **Bereinigung** + **Zu-/Absage**; **`RetroCleanupService`** nur vergangene Events in der Bereinigung; Navigation **`?i=`**, Hinweistexte, **Undo** (`cleanup_rsvp_undo`, `POST /events/cleanup/undo-rsvp`), Ratings löschen Undo bei Speichern. **`REDESIGN.md`:** **§4.1**, **§5.1**, **§6.3** (Handoff), **§8.1**, **§8.2**, **§12**; **`redesign.mdc`** Registry. **`rating_prompt`** nicht mehr für Dashboard.
- **2026-04-06 (Handoff):** **Paket 7a erledigt** — **`events/cleanup.html`** / **`edit.html`** / **`year_planning.html`** (Lucide, **`.page-back`**, **`#rating-card`** + **`components.css`**). **`cleanup`:** Titel **„Bereinigung“**, **`.events-cleanup-intro`** aus **`progress.pending`** (**§6.3**). **Dashboard:** **Zur Info** nur noch **`dashboard-intent__grid`** (einheitlich mit **Zu erledigen** / **Erkunden**). **Doku aktualisiert:** §5.2, §6.3, §8.3.1, §12, §13-Hinweis, **`.cursor/rules/redesign.mdc`**. **Nächster Agent:** Paket **7b** (**§8.3.1**).
- **2026-04-05 (Phase-6-Abschluss):** **Phase 6 erledigt** — Details **§8.2**, Tracker **§10**, Exempt **`admin/index`** **§12**. Dashboard-Untertitel angepasst (**`dashboard/index.html`**: Datenbereinigung „fehlende Angabe(n)“, GGL ohne Teilnahme-Zähler im Meta, Erkunden Merch/Statistiken). **Nächster Schritt:** **Phase 7**, start **`events/cleanup.html`** (**§10 NAECHSTER SCHRITT**).
- **2026-04-05:** **Verein-Hub** **`templates/member/index.html`:** **`settings-nav`** (§4.2), Backend **`member.index`** vereinfacht — siehe **§12** letzte Zeile und **§10 NAECHSTER SCHRITT**.
- **2026-04-05 (Handoff für nächsten Agenten):** **Dashboard** fertig umgesetzt: Intent-Sektionen, **`dashboard_intent_tile`**, Cleanup-Kachel **`brush-cleaning`** / Untertitel **fehlende Angabe(n)** (siehe **§6.3**), **Nächstes Event** ohne RSVP (Detail/Liste), **Dein letzter Anteil**, Merch ohne Nr. und ausgeblendet bei **Geliefert**, **Erkunden** nur Shop + Statistiken. **`dashboard.py`:** **`ggl_stats.rank_total`**. **Datenbereinigung:** **`retro_cleanup.py`** — Fenster **heute … +30 Tage** (nur RSVP), Retro-Past **CUTOFF_DAYS 7** (+ Bewertung), Reihenfolge **`datum` absteigend**; **`events.cleanup`** / **`cleanup_rsvp`** / **`can_rate`** / **`cleanup_upcoming_days`**; **`.events-cleanup-intro`**. **Doku:** **§4.1**, **§5.2**, **§6.3**, **§12**. **Assets:** nach CSS-Änderung immer **`python scripts/fingerprint_assets.py`**. Nächster Schritt: **§10 NAECHSTER SCHRITT**.
- **2026-04-05:** **Dashboard-UX:** Umstellung auf **Intent-Sektionen** (**Zu erledigen** / **Zur Info** / **Erkunden**) mit knappen Kacheln — siehe **§6.3** und **§12** (Intent-Zeile). Weiteres visuelles Feintuning nach PO-Freigabe möglich.
- **2026-04-05:** **Dashboard inhaltlich + IA:** **Nacharbeit**-Card (Cleanup-Zeile + ggf. Bewertungs-Zeile), **nächstes Event** (Hit-Link + RSVP), **letzter Anteil** (BillBro), **GGL**-Kachel, **Merch**-letzte Bestellung; **keine** Shortcuts zur **Bottom-Nav**; klickbare Kacheln (**`dashboard-card-link`**, **`card--dash-tile`**). Backend: **`merch_*`**, **`cleanup_cutoff_days`**. **`REDESIGN.md`** §4.1, §5.2, §8.1, §12; CSS **DASHBOARD**; Fingerprint **`components.*`**.
- **2026-04-05:** **Phase 5 / §8.1 (früher):** Bewertung von Events-Index auf Dashboard; später in **Nacharbeit**-Card mit Cleanup zusammengeführt; **User-Bar** ohne Cleanup-Icon; **GGL** **`season=`**.
- **2026-04-05:** **Events-Index, Tab Statistiken (Erweiterung):** **`details`** **Top & Flop** (Standard **zu**); **`monatsessen_stats.py`:** Aggregation **`restaurantRatings`** (Ø Gesamt/Essen/Getränke/Service, **n** pro Restaurant-Label), **`organizerRatings`** (Mittel der Event-Ø-Gesamtbewertungen je Organisator); **`charts_json`**-Keys; **`events-monatsessen-stats.js`:** sortierbare Tabelle, **Top 10**, Balkenchart **1–5**; Sektion **Bewertungen** ohne Card (**`events-stats-restaurant-block`**); Card-Titel **Teilnahmequote**, **Ø Kosten / Organisator** (**`banknote`**), **Ø Gesamtbewertung** (**`chart-column`**). **`base.css`:** **`[hidden] { display: none !important }`** (Leerzustand vs. **`.empty-state`**). Fingerprint **`components.*`**, JS **`?v=1.1.1`**.
- **2026-04-05:** **Event-Detail, Tab Bewertungen:** Abschnitt **Alle Bewertungen** ohne verschachtelte Card; **`event_ratings`**; Toolbar **Bearbeiten/Löschen**; Anker **`event-ratings-form`** / **`event-ratings-actions`** / **`event-ratings-all`**; **`ratings.py`** Redirects **`_anchor`**; Flash/Formulartexte **Du**-Form (**`ratings.py`**, **`forms/rating.py`**). Registry **§5.2** / **`redesign.mdc`**.
- **2026-04-05:** **Event-Detail, Tab Infos:** Card-Titel **„Summary“**; RSVP-**`chip-select`** aus dem Header in die erste **`info-row`** **„Deine Teilnahme:“** im **`card__body`**. Template **`templates/events/detail.html`**.
- **2026-04-05:** **Event-Detail, Tab BillBro:** **`billbro-workflow-block`** mit **`.billbro-workflow__hint`** (Organisator vs. Mitglied, je Phase). **Schätzungsrangliste:** **`billbro-guess-ranking-table`** + Anker **`billbro-guess-ranking`**; weitere Anker **`billbro-my-guess`**, **`billbro-new-guess`**, **`billbro-attendance`**, **`billbro-enter-bill`**; **`billbro.py`**-Redirects mit **`_anchor`**; **`mark_absent` / `mark_present`** → **`events.detail`** `tab=billbro` + **`#billbro-attendance`**. **`GET …/billbro-sync`** in **`events.py`** + Polling (12 s, nur sichtbarer Tab) für Live-Aktualisierung. **`scroll-margin-top`** für BillBro-Anker. Fingerprint **`components.4967aa7f.css`** (Stand Commit).
- **2026-04-05:** **Event-Detail, Tab Bewertungen:** Gesamtbewertung: **`clipboard-list`** + **`metrics-spotlight`**-Hero (wie GGL-Summary); fremde Bewertungen als **`data-table events-ratings-others-table`** (Mitglied **`display_spirit_rufname`**, Gesamt/Essen/Getränke/Service, Highlight). Registry **§5.1** / **§5.2** / **`redesign.mdc`** angepasst.
- **2026-04-05:** **Events-Index, Tab Statistiken:** Auswertung nur **vergangene, veröffentlichte Monatsessen** (`EventType.MONATSESSEN`). **Filter** oben (**`year`** → Saison, **`organisator_id`**) gilt wie für Kommend/Archiv. **Backend:** **`backend/services/monatsessen_stats.py`** (`get_monatsessen_statistics`), angebunden in **`backend/routes/events.py`** (`tab == 'stats'` → Context **`monatsessen_stats`**). **Teilnahmequote:** pro Event Anteil der **aktiven** Mitglieder mit **Beitritt ≤ Eventdatum** und `teilnahme=True`; fehlender **Participation**-Eintrag zählt wie Absage; Vereins-Ø = Mittel der Event-Quoten; **ganze Prozent** im UI. **Ø Kosten/Person:** Mittel aller **`calculated_share_rappen`** (nur `teilnahme=True`); **ganze CHF** im Hero. **Summary-Card** wie GGL: Titel **„Summary“**, Icon **`clipboard-list`**, **`metrics-spotlight__context`** nur Filterzeile (**Jahr** / **Alle Jahre** · **Organisator** / **Alle Organisatoren**). **Panel:** **Dein Überblick** (Teilnahme in zwei Sätzen, Esstyp-Satz, „pro Essen“-Kosten), **Rekorde** (teuer/günstig/Trinkgeld, Satzbau „… im Restaurant X von Organisator“; **Küche** am Ende des Rekorde-Blocks). **Charts:** Chart.js (CDN wie GGL), **`static/js/v2/events-monatsessen-stats.js`**, JSON-Script **`id="events-monatsessen-charts-data"`**; Balken Teilnahmequote je Mitglied, Balken Ø-Anteil je Organisator, Pie Küchen. **CSS:** **`.events-stats-chart`** in **`components.css`**. Kein **`sessionStorage`** mehr für Rekorde (kein Disclosure). Leerzustand: **`empty-state`** wenn keine Monatsessen im Filter.
- **2026-04-05:** **`metrics-spotlight__hero` (projektweit):** **CSS Grid** **`grid-template-columns: repeat(2, minmax(0, 1fr))`**; **Kacheln** (`__hero > __metric`) mit **Border**, **`min-height`**, Surface-Hintergrund; äußerer Hero **transparent** ohne Panel-Rahmen. **`metrics-spotlight__metric-value--accent` im Hero deprecated** (wird auf Primärtext gemappt); neue Templates ohne diese Klasse im Hero — **§5.1**, **`redesign.mdc`**.
- **2026-04-05:** **Event-Detail Feinschliff:** **`h1`** nur Icon + Datum (Typ **`sr-only`**); Tool-Strip-Titel **„Bearbeiten“** (`**event-detail-edit-disclosure**`, Key **`gourmen:eventDetailEditDisclosureOpen`**); Teilnehmerliste wie **Events-Index** ( **`table-responsive data-table-wrap`** ohne Card, **`data-table events-participants-table`**, Spalte **Teilnahme** mit **Zugesagt/Abgesagt**, Zeile **`__row--current`**). Fingerprint **`components.8ce95763.css`**.
- **2026-04-05:** **Phase 4 — `templates/events/detail.html`:** Breadcrumb durch **`.page-back`** ersetzt; **Lucide**-Makros wie Events-Index; Organisator-Leiste + **`sessionStorage`**; **`tabs tabs--panel`**; Infos: **Teilnehmer** und **Schätzungsrangliste** als **`data-table`**; BillBro: **`billbro-workflow`** (seit 2026-04-05 erweitert, siehe neuere **§11**-Zeilen); Bewertungen: **`metrics-spotlight`** / **`empty-state`** / Tabelle fremde Bewertungen (**`events-ratings-others-table`**); doppelte **Rechnungsübersicht** entfernt; Skripte in **`{% block scripts %}`**. CSS: **`base.css`** (`.page-back`), **`components.css`**.
- **2026-04-05:** **GGL Tab Spielverlauf (`rennen`):** Card **„Ranking“** (Lucide **`trophy`**, kumulierte Punkte); Card **„Differenz“** (Lucide **`target`**, kumulative **signierte** Differenz Schätzung minus Rechnungsbetrag in Rappen, Feld **`cumulative_signed_diff_rappen`** in **`get_season_progression_data`** / **`ggl_rules.py`**). **`static/js/v2/ggl-season.js`:** zwei Liniendiagramme, gemeinsame Farbzuordnung pro Mitglied.
- **2026-04-03:** Phase-1-CSS für `context-actions` und `settings-nav` ergänzt; Tracker 0b/1 präzisiert; §5.2.1 Snippets; `main-v2` Fingerprint + `base.html`-Link aktualisiert.
- **2026-04-03:** §16 Ende-Kriterium + Cleanup-Backlog (P0/P1); Starteinträge C-001/C-002.
- **2026-04-03:** §13.1 — Status nur `pending`  `done`; §7/§16.1 angeglichen.
- **2026-04-03:** Phase 1 — Shell-Partials für `base.html` (`_user_bar`, `_sidebar`, `_bottom_nav`, `_flash_messages`); §13.2; Login-Seite 200 (Smoke).
- **2026-04-03:** Phase 1 — `<head>` in `_head_*.html` Partials; OG/Twitter/Title-Blöcke bleiben in `base.html`; Smoke Login 200.
- **2026-04-03:** Phase 2 — GGL `index.html` Pilot; `stat-tiles` + `ggl-ranking-table`; `main-v2.04743a90.css`; `git tag pre-phase-2`.
- **2026-04-03:** UX — keine verpflichtenden `page-subtitle` mehr (Kontext in `h1` wo nötig); Filter-Cards dezent (`.card.card--filter`); `main-v2` Fingerprint aktualisiert.
- **2026-04-03:** Phase 3 — `events/index.html`: `context-actions` statt Admin-Filter-Card; Tabs-Icons Lucide; Kommend/Archiv als responsive **Tabelle** (§5.3); Statistiken **stat-tiles**; leere Zustände **alert--info**.
- **2026-04-03:** Events-Übersicht — Tab **„Übersicht“** entfernt (Doppelung mit Dashboard); Standard-Tab **Kommend**; `?tab=overview` → Redirect **kommend**; Bewertungs-Hinweis als **Alert** oberhalb der Tabs.
- **2026-04-03:** **§8.1** ergänzt — Phase 5 Dashboard: verbindlicher Klärungsbedarf zu **ausstehenden Bewertungen** und zu `**templates/events/cleanup.html`** (inkl. Entscheidungslog nach Klärung).
- **2026-04-03:** Gemeinsame Tabellen-Hülle `**.data-table-wrap` / `.data-table`** — Events Kommend/Archiv optisch an GGL angeglichen; GGL nutzt dieselbe Basis + `.ggl-ranking-table`-Modifier.
- **2026-04-03:** Events-Tabellen: Spalte **Typ** (Icon statt Text im Raster), **Archiv** ohne Spalte **Küche**; Tracker Phase 3 für nächsten Agent präzisiert — **Phase 4** nächster Schritt: `templates/events/detail.html` (siehe **§10 NAECHSTER SCHRITT**).
- **2026-04-03:** Events **index:** Filter global über Tabs; `**empty-state`** / `**empty-state--filtered**` für Kommend-Leerzustände; §5.2–5.3 und §12 ergänzt.
- **2026-04-03:** IA-Zielbild **Verein** / User-Menü / Theme in Top-Bar / kein Admin-Button in Bar / GV-Icon `**landmark`** / Löschen nur Admin / §4.1–4.5, §5.2.2, §12, §13.2 angepasst.
- **2026-04-03:** **`tool-surface`** implementiert (`context-actions`, alle `card--filter`); Event-Löschen nur Admin im Template; §5.2 / §12 aktualisiert.
- **2026-04-03:** **Tool-Strip §5.2.3** dokumentiert und umgesetzt: Planung und Filter optisch/strukturell gleich (`disclosure` + `tool-strip__actions` bzw. `form` + `form-actions`); **Standard eingeklappt**; **sessionStorage** + Tab-Wechsel; **§4.4**, Registry, Tracker Phase 3, **§12** fortgeschrieben.
- **2026-04-03:** Events-Filter: **Lucide `funnel`** am Primary-Button **Filtern**; Reihenfolge **Filtern** vor **Zurücksetzen** mit **`form-actions--start`**. Tabs: **`.tabs--panel`** (Panel + Lasche) auf **Events-Index**; CSS in **`components.css`**.
- **2026-04-04:** **Light:** Tabellen-**`thead`** (`**.data-table**`, **`.table`**) — Hintergrund wie **`.card__header`** (`--brand-primary-200`).
- **2026-04-04:** **§5.2.2** präzisiert (Light/Dark **`.tool-surface`**, **`--chrome-inactive-pill-bg`**, Filter-**`chip--info`**); **§5.1** / **§5.3** an **`.tabs--panel`**-Istzustand; **§9** Rate-Limiting lokal aus; **§12** Entscheidungslog ergänzt (**thead**, Tabs, Tool-Surface, Dev-Limiter).
- **2026-04-04:** **GGL** (`ggl/index.html`): Filter wie Events (**`funnel`**, **`form-actions--start`**, Lucide **`chevron-down`**), **`tabs--panel`**, **`sessionStorage`**-Key **`gourmen:gglFilterDisclosureOpen`** — **§5.2.3**.
- **2026-04-04:** **Kennzahlen-UI:** neues Muster **`metrics-spotlight`** / **`metrics-insight-panel`** in **`components.css`**; GGL Performance-Tab und Events-Statistiken umgestellt; **`stat-tiles`** für ergänzende KPIs unter dem Spotlight (**`stat-tiles--metrics-follow`**). Registry §5.1, §5.3, Tracker Phase 2/3, **§12** nachgetragen. *(Copy/Titel im GGL-Card-Header z. B. „Summary“ — bei Bedarf später deutsch/konsequent benennen; kein Blocker für Pattern-Doku.)*
- **2026-04-04:** **§5.2.3** — nach **Filtern** (GET-Submit): Filter-**`details`** schließen und **`sessionStorage`** auf zu; **Events-Index** + **GGL**.
- **2026-04-04:** **GGL `ggl_rules.py`:** Insights **„Abstände“** / **„Schätz-Differenzen“** (Abschnitt **„Im Schnitt“** entfernt); Abstandszeilen **„fehlen dir … Punkte“**; **Tie-Break** wie Tab Tabelle **`(total_points, avg_points)`** für Spitze / nächster Block; **Teilnahme an Events** nur gegen **bereits stattgefundene** published Events; **`datetime`**-Import file-level.
- **2026-04-04:** Commit-Bundle: Templates, **`components.css`**, Fingerprint **`components.f4efae83.css`**, Manifest, **`REDESIGN.md`**, **`redesign.mdc`**, Backend GGL/Member — **nächster Schritt unverändert Phase 4** (`events/detail.html`).
- **Bekannte Altlast (nicht in diesem Commit):** Legacy-Route **`ggl.season`** redirectet mit Query **`race_season` / `table_season`**, **`ggl.index`** liest aber nur **`season`** — Deep-Links setzen die Saison ggf. nicht. Fix: überall **`season=`** verwenden; ggf. **§16.2** eintragen.

---

## 12. Entscheidungslog

Jede Zeile muss **ohne Chat-Kontext** verständlich sein (siehe Abschnitt 6.1). Keine alleinigen Verweise auf Arbeitsbezeichnungen ohne Klartext in derselben Zelle.


| Datum      | Phase | Entscheidung                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Begründung                                                                                                 |
| ---------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 2026-04-03 | 0a    | Technischer Ansatz: Custom BEM + Tokens, kein Tailwind/Framework (Konzept „Option A“, vom PO bestätigt)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Kontrolle, bestehende V2-Basis, kein Build-Zwang; Agent-Arbeit über Registry                               |
| 2026-04-03 | 0a    | Member/Admin-Hub: Settings-Liste statt KPI-Karten                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | KPIs unnötig; schnellere Navigation                                                                        |
| 2026-04-03 | 0b    | Kontextleiste `context-actions` für Planung auf Event-Seiten                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Sichtbarkeit, ein Muster statt Disclosure-Cards                                                            |
| 2026-04-03 | 0a/IA | Organisator nur in Events; Admin-Jahresplanung + Backup im Admin-Bereich; eine Bearbeitungslogik, zwei Admin-Einstiege ok                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Rollenklarheit, Merch-Parallele                                                                            |
| 2026-04-03 | 1     | `context-actions` und `settings-nav` sind in `static/css/v2/components.css` umgesetzt; Referenz-Snippets in §5.2.1; Abstandregel `.page-header:has(+ .context-actions)` in `base.css`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Tracker-Klarheit (0b = Spezifikation, 1 = Umsetzung); Agenten können Templates anbinden                    |
| 2026-04-03 | Doku  | Abschluss des Redesigns: verbindliches **Ende-Kriterium** und gemeinsames **Cleanup-Backlog** in §16; Pflege in §6.1 und §7                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Agents ohne Chat-Kontext wissen, wann „fertig“ ist und welche Altlasten dokumentiert abgearbeitet werden   |
| 2026-04-03 | Doku  | **§13 Template-Übersicht:** Status-Spalte normiert auf ausschließlich **pending** | **done** (Legende §13.1); **done** inkl. dokumentierter User-Exempts via §12                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Einheitliche Agent-Handoffs ohne parallele Status-Begriffe                                                 |
| 2026-04-03 | 1     | Layout-Shell aus `base.html` in `templates/partials/` ausgelagert (`_user_bar`, `_sidebar`, `_bottom_nav`, `_flash_messages`); Referenz **§13.2**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Phase-1-Rückbau; kleinere `base.html`, gleiche Laufzeitsemantik                                            |
| 2026-04-03 | 1     | `<head>`-Inhalt (Theme-Script, PWA-Meta, Manifest/Icons, Stylesheets, deferred Scripts) in `_head_*.html`; vererbbare **Blöcke** (`title`, `og_*`, `twitter_*`, `head`) verbleiben in `base.html`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Jinja-`extends` bleibt korrekt; Partials ohne eigene `{% block %}`                                         |
| 2026-04-03 | 2     | GGL-Hauptseite: KPIs als **stat-tiles**; Saison-Ranking als **eine Tabelle** (`ggl-ranking-table`) statt pro Zeile eine Card; Referenz **§5.1**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | REDESIGN §5.3; bessere Mobile/Desktop-Nutzung, weniger visuelles Gewicht                                   |
| 2026-04-03 | UX    | **Page-Header:** kein Standard-`page-subtitle`; nur `h1`, ggf. Kontext in derselben Zeile (z. B. „Bearbeiten · Name“). `**card--filter`:** optisch abgeschwächt (kein Schatten/Hover-Lift, Surface-Hintergrund) — einheitlich mit bestehendem Disclosure-Muster                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Weniger Höhe und Redundanz; Filter bleibt erkennbar, Inhalts-Cards visuell im Vordergrund                  |
| 2026-04-03 | 3     | **Events-Übersicht (`events/index.html`):** Admin-Planung nur noch `**context-actions`** unter dem Page-Header (kein `card--filter`-Disclosure dafür). **Kommend** und **Archiv:** homogene Zeilen in `**.data-table-wrap` / `.data-table`** (`.table-responsive`); **Statistiken:** `**stat-tiles`**. **Lucide** per Sprite (`url_for`) für Tab- und Seiten-Icons.                                                                                                                                                                                                                                                                                                                                                                          | REDESIGN §4.4, §5.3; konsistent mit Phase-2-Pilot; gemeinsame Tabellen-Hülle mit GGL (siehe unten)         |
| 2026-04-03 | 3     | **Tabellen einheitlich:** `.data-table-wrap` und `.data-table` als gemeinsame „Card“-Tabelle (Rahmen, Schatten, Header-Fläche, Zeilenlinien); GGL mit zusätzlich `.ggl-ranking-table` und Spalten-/Zeilen-Modifiern; Events Kommend/Archiv dieselbe Hülle — kein paralleles `ggl-ranking-table-wrap` mehr nötig                                                                                                                                                                                                                                                                                                                                                                                                                              | Gleiche Lesbarkeit und Hierarchie wie GGL; eine Pflegestelle statt divergierender `.table`-Minimalvariante |
| 2026-04-03 | 3     | **Events-Tabellen:** Spalte **Typ** mit Überschrift „Typ“ — sichtbar nur **Lucide-Icon** zum Event-Typ; **Datum** nur Text. **Archiv:** Spalte **Küche** entfernt (Küche bleibt im Event-Detail).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Kompaktere Liste; Typ weiterhin per `sr-only` + Icon für A11y                                              |
| 2026-04-03 | 3     | **Kein Tab „Übersicht“** mehr auf der Events-Hauptseite: Inhalt (aktuelles/nächstes Event) war **redundant zum Dashboard**. Standard-URL `**/events`** lädt **Kommend** (`tab=kommend`). `**tab=overview`** wird nach **kommend** umgeleitet. **Bewertungs-Hinweis** für das letzte besuchte Event ohne Bewertung bleibt als `**alert--info`** oberhalb der Tab-Leiste sichtbar (nicht dashboard-redundant).                                                                                                                                                                                                                                                                                                                                 | Nutzerwunsch; eine klare Rolle pro Seite (Dashboard = persönlicher Einstieg, Events = Listen/Archiv/Stats) |
| 2026-04-03 | 3     | **Events-Übersicht:** Jahr-/Organisator-**Filter** steht **über** den Tabs und wirkt auf **Kommend**, **Archiv** und **Statistiken** (URL `year`, `organisator_id`; Tab-Links und Archiv-Pagination behalten Filter). **Kommend** bei 0 Treffern: ungefiltert `**empty-state`** mit „Keine kommenden Events verfügbar.“ **ohne** Jahresplanung-Link; gefiltert `**empty-state--filtered`** mit kontextualisiertem Text (Jahr und/oder Organisator), **ohne** Filter-Zurücksetzen im Leerzustand. Muster `**empty-state`** in §5.2 / Registry.                                                                                                                                                                                                | Nutzerwunsch; Leerzustand ohne erzwungenen CTA; Filter als globale Seitenkontrolle                         |
| 2026-04-03 | IA    | **Navigation Zielbild:** Hauptbereich **„Member“** → **„Verein“** (Merch-Shop, später Dokumente; Admins zusätzlich Mitgliederverwaltung, Merch-Backoffice, später Buchhaltung). **Persönliches** (Profil, Sicherheit) über **User-Menü** in der oberen Leiste; **Theme-Toggle** bleibt **in der Top-Bar**. **Kein** Admin-Icon in der User-Bar — Admin-Einstiege über **Verein** und **Kontextleisten** am Objekt. **Icon Verein:** Lucide `**landmark`** (wie GV-Event-Typ). **Event löschen:** nur **Admins** in der **UI** (Button nicht für Organisator ohne Admin). Operative Aufgaben weiter in **Leisten** (`context-actions` …). **§5.2.2:** gemeinsame Sekundärleisten-Optik **`tool-surface`**. | Klarere Mental Models (Verein vs. Ich); weniger parallele Admin-Welt; Konsistenz der Werkzeug-Leisten      |
| 2026-04-03 | UX/CSS | **`.tool-surface`:** gemeinsame Optik für **`context-actions tool-surface`** und **`card.card--filter.tool-surface`** (`components.css`). **Event-Detail:** Formular **Event löschen** nur bei **`current_user.is_admin()`** gerendert. | REDESIGN §4.5, §5.2.2; UI entspricht Backend `events.delete` |
| 2026-04-03 | 3/UX | **Sekundärleisten / Tool-Strip:** Verbindliches Muster **`card card--filter tool-surface`** + **`<details class="disclosure">`**. **Kopf:** `summary.disclosure__summary` mit Lucide **`chevron-down`**, Titel in **`--color-interactive-primary`**, **`text-base`**, **`font-semibold`**, **`flex-wrap`**; aktive Filter optional als **`chip chip--info`**. **Inhalt:** nur Schaltflächen → **`tool-strip__actions`**; mit Feldern → **`form`** + **`.form-actions`**. CSS in **`components.css`** unter **`.card--filter`** + **`.tool-strip__actions`**. | Eine Leisten-Sprache für Planung (ohne Felder) und Filter (mit Feldern); ersetzt die frühere abweichende **`context-actions`**-Optik auf der Events-Übersicht für Planung |
| 2026-04-03 | 3/UX | **Events-Index:** Planungs-Card mit Klasse **`events-planning-strip`**; **`base.css`:** **`.page-header:has(+ .events-planning-strip)`** für engen Abstand unter dem Titel. | Gleiche Kartenhülle wie Filter; konsistente vertikale Rhythmik |
| 2026-04-03 | 3/UX | **Eingeklappt-Standard + Tab-Wechsel:** Beide **`details`** (Planung, Filter) starten **geschlossen**, wenn **`sessionStorage`** keinen Wert hat. **Keys:** `gourmen:eventsIndexPlanningDisclosureOpen`, `gourmen:eventsIndexFilterDisclosureOpen`; bei **`toggle`** persistieren. Tab-Wechsel **Kommend / Archiv / Statistiken** = Reload, **`sessionStorage`** bleibt → Zustand bleibt erhalten. | Nutzerwunsch; konsistentes Default-Verhalten |
| 2026-04-03 | 3 | **Event-Detail Planung:** unter **`disclosure__content`** **`tool-strip__actions`** statt **`form-actions`**, wenn keine Formularfelder oberhalb der Buttons (keine irreführende Trennlinie). | Analog Events-Index „nur Aktionen“ |
| 2026-04-03 | 3/UX | **Filter-Submit:** Primary-Button **Filtern** mit Lucide **`funnel`**; **DOM-Reihenfolge** Primary vor Outline; **`form-actions form-actions--start`** für linksbündige Reihenfolge (Abweichung von **`justify-content: flex-end`** der Standard-**`form-actions`**). | Nutzerwunsch; Primary-Icon-Regel aus Diskussion (Tool-Strip) |
| 2026-04-03 | 3/UX | **Tabs Panel + Lasche:** Modifier **`.tabs--panel`** — **Rail**, **aktive Lasche**, **`margin-bottom: -1px`**. Wrapper: **nur unterer** Rand (kein L/R); **jeder Tab** mit **Rand links, oben, rechts**; **`overflow: hidden`** unten abgerundet. Pilot **Events-Index**. | Stärkere Kopplung Tab↔Inhalt |
| 2026-04-04 | UX/CSS | **Light:** **`thead`** von **`.data-table`** und **`.table`** — Hintergrund **`--brand-primary-200`** (wie **`.card__header`**); Dark: **`--color-surface-secondary`**. | Einheitliche Tabellen-Kopfzeile mit Card-Header |
| 2026-04-04 | UX/CSS | **`.tabs.tabs--panel`:** Tab-**Nav** transparent mit **`gap`**; Tabs **oben abgerundet**, **ohne** sichtbaren Einzel-Rand; **inaktiv** Light **`--color-bg-muted`**, Dark **`--chrome-inactive-pill-bg`** — Dark nur mit **`:not(.tabs__tab--active)`**, damit **aktiv** nicht überschrieben wird; **aktiv** und **`tabs__content`** = **`--tabs-panel-body-bg`**. | Lesbarkeit, Dark-Kontrast, Spezifitäts-Fix (supersedes Tab-Rand-Detail aus 2026-04-03-Zeile, sofern abweichend) |
| 2026-04-04 | UX/CSS | **`.tool-surface` / Filter-Chips:** Dark: Leiste **`--color-bg-base`**, Rand **`--color-surface-secondary`**; **`chip--info`** in **`card--filter` Disclosure** Dark = **`--chrome-inactive-pill-bg`**; Light: **`tool-surface`** **`--brand-primary-50`**, Chips **`--color-bg-muted`**. Siehe **§5.2.2**. | Konsistenz Tool-Strip ↔ Panel-Tabs |
| 2026-04-04 | Dev | **`RATELIMIT_ENABLED = False`** auf **Development**- und **Testing**-Config; **Limiter** in **`init_extensions`** mit **`enabled=False`**, wenn ausgeschaltet — lokales/Test-Setup ohne 429-Störungen. | Entwickler-Ergonomie (**§9**) |
| 2026-04-04 | 2/UX | **GGL-Hauptseite:** Filter-**`disclosure`** mit **`id="ggl-filter-disclosure"`**, **`form-actions form-actions--start`**, Primary **Filtern** mit Lucide **`funnel`**; Tabs-Wrapper **`tabs tabs--panel`**; **`sessionStorage`**-Key **`gourmen:gglFilterDisclosureOpen`**, Standard **eingeklappt** — analog **Events-Übersicht** (**§5.2.3**). | Einheitliche Sekundärleisten- und Tab-Sprache |
| 2026-04-04 | 2/3/UX | **Kennzahlen-Darstellung:** **`metrics-spotlight`** (Hero-Metriken, BEM in **`components.css`**) projektweit für 1–2 prominente Wert-Paare; optional **`metrics-insight-panel`** darunter für Einordnungstext/Listen. **GGL** Tab „Deine Performance“ nutzt Spotlight (+ Insights aus **`backend/services/ggl_rules.py`** als Markup). **Events** Tab Statistiken: zwei Spotlight-Blöcke, jeweils mit nachgeschalteten **`stat-tiles stat-tiles--metrics-follow`**. Frühere Formulierung „GGL nur stat-tiles“ für den Performance-Tab ist damit **ersetzt** ( **`stat-tiles`** bleiben für Raster/Folge-KPIs). | Stärkere visuelle Hierarchie Hero vs. Neben-KPIs; konsistent GGL ↔ Events-Statistiken |
| 2026-04-04 | 2/UX | **GGL Performance-Insights (`ggl_rules.py`):** Abschnitt **„Abstände“** (Zum nächsten Rang / Zur Spitze, Namen in Klammern, **„fehlen dir … Punkte“**); **„Schätz-Differenzen“** statt Top & Flop; **„Im Schnitt“**-Abschnitt entfernt. **Rang-/Spitzen-Logik** nutzt dieselben **Tie-Breaks** wie **`get_season_ranking`** / Tab Tabelle: Sortierschlüssel **`(total_points, avg_points)`** für führende Gruppe, Spitzennamen und **nächsten Rangblock** (nicht nur „alle mit max Punkten“). **„Teilnahme an Events“:** Nenner = veröffentlichte Events der Saison mit **`datum < utcnow`**; Zähler = Schätzungen nur zu diesen Events. | Nutzerwunsch; Konsistenz mit Tabelle; laufende Saison ohne künstlich hohen Nenner |
| 2026-04-04 | 3/UX | **Filter-Tool-Strips (GET):** Nach Submit **Filtern** wird das jeweilige **`details`** geschlossen und der **`sessionStorage`**-Eintrag auf **zu** gesetzt — **Events-Index** (`events-index-filter-disclosure`, Key **`gourmen:eventsIndexFilterDisclosureOpen`**) und **GGL** (`ggl-filter-disclosure`, Key **`gourmen:gglFilterDisclosureOpen`**). Tab-Wechsel ohne Filter-Submit: Verhalten wie bisher. Spez **§5.2.3**. | Nutzerwunsch; nach Anwenden des Filters weniger visuelles Rauschen |
| 2026-04-05 | 3 | **Events-Index Tab Statistiken:** Inhalt = nur **vergangene Monatsessen** im Filter (Saison/Jahr, Organisator). Kennzahlen und Texte wie in **`monatsessen_stats.py`** und Template; **Ø Teilnahmequote** und **Ø Kosten/Person** für Nutzer als **ganze Zahlen** (Prozent bzw. CHF). Rekorde-Formulierung: teuer/günstig „… im Restaurant X von **Organisator**“. **Rekorde** als fester Abschnitt (kein Einklappen); Küchen-Satz ans Ende von Rekorde. | Nutzer/Pilot; klare IA; Handoff für weitere Statistik-Seiten |
| 2026-04-05 | UX/CSS | **`metrics-spotlight__hero`:** Immer **zwei Spalten** (Grid); jede Metrik-Kachel mit **Rand** und einheitlicher Mindesthöhe; **keine** orange **Accent**-Farbe für einzelne Hero-Werte — **`.metrics-spotlight__hero .metrics-spotlight__metric-value--accent`** entspricht Primärtext; Klasse im Hero **nicht** mehr verwenden. | Einheitliche KPI-Kacheln; §5.1 / **redesign.mdc** |
| 2026-04-05 | 2 | **GGL Spielverlauf:** Zwei Charts — **Ranking** (Punkte) und **Differenz** (kumulative signierte Schätzdifferenz je Mitglied über Events); Daten aus **`get_season_progression_data`**. | Nutzerwunsch; gleiche Event-Reihenfolge wie Punkteverlauf |
| 2026-04-05 | 4 | **Event-Detail:** Keine Breadcrumb-Kette; **`.page-back`** „Zurück zu Events“. **Tabs** **`tabs--panel`** + Lucide. **Organisator-Leiste:** Titel **„Bearbeiten“**, **`id="event-detail-edit-disclosure"`**, Key **`gourmen:eventDetailEditDisclosureOpen`**, Standard zu. **`h1`:** nur Icon + Datum (Typ nur **`sr-only`**). **Tab Infos:** erste Card **„Event-Summary“** mit **`clipboard-list`**. **Teilnehmer:** **`events-participants-table`**. **BillBro:** **`.billbro-workflow`**. **Bewertungen:** **`metrics-spotlight`**, kein Duplikat **Rechnungsübersicht**. | REDESIGN §3, §5.2.3, §5.3; Konsistenz Events-Index/GGL |
| 2026-04-05 | 4 | **Event-Detail Info-Card:** Bezeichnung **„Event-Informationen“** → **„Event-Summary“**; Icon **`clipboard-list`** statt **`file-text`**, analog GGL Performance-Summary. | Einheitliche Summary-Sprache GGL ↔ Event-Detail; Nutzerwunsch |
| 2026-04-05 | 4/UX | **Tab Infos:** Card-Titel **„Summary“**; RSVP-**`chip-select`** in **`card__body`**, erste Zeile **„Deine Teilnahme:“**. | Klarere Kopfzeile; RSVP gleichwertig zu anderen Summary-Feldern |
| 2026-04-05 | 4/UX | **Tab BillBro:** **`billbro-workflow-block`** + **`.billbro-workflow__hint`** (Organisator vs. Mitglied, je Phase). **Schätzungsrangliste:** **`billbro-guess-ranking-table`**; stabile **`id`-Anker** + **`url_for(..., _anchor=…)`** nach POSTs; **`mark_absent` / `mark_present`** → **`events.detail`** mit **`tab=billbro`**. **Live-Abgleich:** **`GET /events/<id>/billbro-sync`** (JSON, **`no-store`**) + Client-Polling ca. **12 s** nur bei **`tab=billbro`** und sichtbarem Tab; bei geändertem Snapshot **Vollreload** (kein WebSocket). | Restaurant-Nutzung; Orientierung für beide Rollen; frische Daten ohne manuelles Neuladen |
| 2026-04-05 | 4/UX | **Tab Bewertungen:** Gesamtdurchschnitt in Card **Gesamtbewertung** mit **`metrics-spotlight__hero`**. **Alle Bewertungen** als **`data-table events-ratings-others-table`** über volle Breite (inkl. eigener Zeile, **`__row--current`**); Formular-Card nur bei Abgabe/Bearbeiten (**`#event-ratings-form`**); nach Speichern Toolbar **`#event-ratings-actions`** (Bearbeiten/Löschen) oberhalb der Tabelle. Redirects **`ratings.*`** mit **`_anchor`** (**`event-ratings-all`** / **`event-ratings-form`**). CSS: **`event-ratings-all`**, **`event-ratings-toolbar`**, **`scroll-margin-top`**. | Nutzerwunsch; Tabelle nicht in verschachtelter Card; klare Aktionen + Sprungmarken |
| 2026-04-05 | 3/UX | **Events-Index Tab Statistiken:** Rekorde-Bereich umbenannt **Top & Flop**, **`details`** standard **eingeklappt**; Copy Trinkgeld + beste/schlechteste Restaurant mit **Stern** + Note; neue **Restaurant-Bewertungstabelle** (sortierbar, Top 10, ohne Card) + **Balken Ø Gesamtbewertung je Organisator**; **`charts_json`** um **`restaurantRatings`** und **`organizerRatings`** erweitert. | Nutzerwunsch; Übersicht; Daten im JSON für Client-Sortierung |
| 2026-04-05 | 1/UX | **`base.css`:** Selektor **`[hidden] { display: none !important }`**, damit das HTML-Attribut **`hidden`** zuverlässig wirkt, wenn Komponenten (z. B. **`.empty-state`**) **`display: flex`** setzen. | Bugfix: Leerzustand und Tabelle gleichzeitig sichtbar |
| 2026-04-05 | UX    | **Tabellen vs. Cards:** Volle **`data-table`**-Listen **ohne** umschließende **`.card`** im Tab-Inhalt; Cards für Formulare, KPIs, Charts, Summary — Tabelle bringt den Rahmen selbst mit (**§5.1** Prinzip, **§5.3**). | Agent-Handoff; vermeidet doppelte Rahmen und verschachtelte Cards |
| 2026-04-05 | 5     | **Bewertungs-Erinnerung:** Nur noch auf dem **Dashboard**, in der Card **„Nacharbeit zu Events“** als **Zeile** (Link **Event-Detail `tab=ratings`**, nicht mehr separater **`alert--info`**). **`events/index.html`:** kein Bewertungs-Alert. **Backend:** **`get_rating_prompt_event_for_member`** (**`rating_prompt.py`**). **Ersetzt** den **2026-04-03**-Hinweis auf Events sowie die frühere Dashboard-**`alert`**-Variante (siehe **§12** Zeile **Dashboard-Überblick**). | IA; Prinzip 4 |
| 2026-04-05 | 5     | **Datenbereinigung:** Bei **`retro_cleanup_progress.pending > 0`** zeigt das Dashboard eine **Card** (Fortschritt **completed**/**total**, Kurztext, Primär-Link **`events.cleanup`**). **Kein** Cleanup-Warn-Button mehr in **`templates/partials/_user_bar.html`** (keine Doppelung zur Card; Einstieg über Dashboard nach Login). **`inject_retro_cleanup`** bleibt für Templates. Visuelles Redesign **`events/cleanup.html`** = **Phase 7**. | Dashboard als kanonische Stelle; ruhigere User-Bar; Prinzip 1 + 8 |
| 2026-04-05 | 5     | **Dashboard-Überblick (IA):** Eine **Nacharbeit**-Card vereint **Datenbereinigung** (Link **`events.cleanup`**) und **ausstehende Bewertung** jüngstes Event (Link **Event-Detail `tab=ratings`** — kann vor Cleanup-Stichtag liegen). Weitere Kacheln: **nächstes Event** (Klick ins Detail, **RSVP** separat), **letzter Anteil** (BillBro), **GGL** (Rang → Tabelle), **Merch** (letzte Bestellung → Detail). **Keine** generischen Links zu Zielen der **Bottom-Nav** (Events/GGL/Member-Start). Interaktion: überwiegend **klickbare Kacheln** (**`.dashboard-card-link`**, **`.card--dash-tile`**). | Nutzerwunsch; ein mentaler „Daten sauber“-Block neben übrigen Themen; Prinzip 6 + 7 |
| 2026-04-05 | 5     | **Dashboard — Intent-Gruppierung:** Drei Sektionen **Zu erledigen** / **Zur Info** / **Erkunden**; kompakte **`dashboard-intent-tile`**-Kacheln + Makro **`dashboard_intent_tile`**; CSS **`dashboard-intent*`** ( **`dashboard-next-event*`** weiter im CSS für ältere Referenzen / optional). Details zum aktuellen Copy und RSVP siehe **unmittelbar folgende Zeile**. | Nutzerwunsch; Intent-Scan; Prinzip 6 + 7 + 8 |
| 2026-04-05 | 5     | **Dashboard Feinschliff:** **Datenbereinigung**-Kachel: Icon **`brush-cleaning`**, Untertitel zunächst **„Unvollständige Events: n“** — **ersetzt** durch **„fehlende Angabe(n)“** (**§12** Zeile **5/6 Dashboard-Untertitel**, **§6.3**). **Nächstes Event:** Intent-Kachel (**`calendar`**), **„[Typ] am [Datum]“**, **kein RSVP** auf dem Dashboard — Zu-/Absage weiter **Event-Detail** / **Events-Liste**, **nicht** über Datenbereinigung (Cleanup nur **vergangene** Events ab Stichtag, siehe **§6.3**). **BillBro** / **Merch** wie zuvor beschrieben. **Erkunden:** ohne GGL-Duplikat; **Statistiken** mit **`chart-column`**; **Events**-Kachel entfernt (**Bottom-Nav**). | Nutzerwunsch; IA-Klarheit Cleanup vs. kommende Events |
| 2026-04-05 | 5     | **Erkunden:** **Events**-Kachel vom Dashboard entfernt — Einstieg **Events** über **Bottom-Nav**. | Nutzerwunsch; keine Doppelung zur Navigation |
| 2026-04-05 | 5     | **Datenbereinigung (`retro_cleanup.py`):** **`UPCOMING_WINDOW_DAYS = 30`** — kommende Events im Fenster nur **RSVP**, **keine** Bewertung. **Vergangene** (wie bisher **`CUTOFF_DAYS = 7`**) inkl. Bewertung. **Reihenfolge:** **`datum` absteigend** (jüngstes zuerst). **`cleanup_rsvp`:** **`allows_cleanup_rsvp`** (Upcoming oder Retro). **`events/cleanup`:** **`can_rate`** nur außerhalb Upcoming; **`has_rating`** berücksichtigt. Template-Einleitung + **`cleanup_upcoming_days`**. | Nutzerwunsch; nächstes Event zuerst, Retro zeitversetzt |
| 2026-04-05 | 6/IA  | **Verein-Hub (Feinplanung):** **Eine** Navigationszeile **Merch**; Admin-Sektion nur **Mitglieder** und **Merch-Verwaltung**, **ohne** Eintrag **Admin-Übersicht** (`admin.index`). **User-Bar:** kein Spirit/Rufname-Text; **User-Menü** mit Lucide **`user`**; Einträge Profil, Sicherheit, App & Benachrichtigungen, Abmelden. **Hauptnav:** **`docs.*`** nicht mehr für aktiven Tab „Verein“; künftige Dokumente unter Verein. **Sidebar:** Label **Verein** + Icon **`landmark`** wie Bottom-Nav. | PO-Bestätigung Option B; Prinzip 2, 4, 6 |
| 2026-04-05 | 6     | **`templates/member/index.html`:** Verein-Hub als **`settings-nav`** — Sektion **Verein** (Zeile **Merch**); später nur **„Shop und Bestellungen“** als Beschreibung (**Supersedes:** frühere Varianten mit offenen Bestellungen im Untertitel). Sektion **Verwaltung** nur **Admin** (**Mitglieder** → **`admin.members`**, **Merch-Verwaltung** → **`admin.merch`**). **`h1` „Verein“** mit Lucide **`landmark`**. Kein Logout/KPI-Karten; Persönliches nur User-Menü. **`member.index`:** zuletzt **ohne** Template-Context (nur `render_template('member/index.html')`). | §4.2; Phase 6 Hub |
| 2026-04-05 | 6     | **Phase 6 abgeschlossen.** Shell (**`_user_bar`** User-Menü, **`_sidebar`**/**`_bottom_nav`** **Verein**/`landmark`, kein **`docs.*`** im Active-State). **`admin.index`:** **`templates/admin/index.html`** bleibt **KPI-`hub-card`**-Landing für Lesezeichen — **nicht** in der Hauptnav; primärer Admin-Einstieg = **Verein** (**§4.2**). **§13:** `admin/index` = **`done`** (Exempt). **Nächster Schwerpunkt:** **Phase 7** (**§10**). | PO; IA; Agent-Handoff |
| 2026-04-05 | 5/6   | **Dashboard-Untertitel** (`templates/dashboard/index.html`): **Datenbereinigung** „1 fehlende Angabe“ / „n fehlende Angaben“ (**ersetzt** „Unvollständige Events: n“ aus früherer §11/§12-Formulierung). **GGL**-Intent-Kachel: Meta **ohne** „Teilnahme x/x“. **Erkunden:** Merch-Shop **„Shop und Bestellungen“**, Statistiken **„KPIs und Charts“**. | Nutzerwunsch; Copy-Konsistenz mit Verein-Merch |
| 2026-04-06 | 5/UX | **Dashboard (`templates/dashboard/index.html`):** Sektion **Zur Info** — alle Kacheln in **`dashboard-intent__grid`** (wie **Zu erledigen** / **Erkunden**); **kein** **`dashboard-intent__stack`**, kein inneres verschachteltes Grid. | Nutzerwunsch; einheitliche 2-Spalten-Kacheln ab 480px |
| 2026-04-06 | 7 | **`templates/events/cleanup.html`:** **`{% block title %}`** und **`h1`** „**Bereinigung**“ (Lucide **`brush-cleaning`**); **`.events-cleanup-intro`:** ein Satz mit **`progress.pending`** (0 / 1 / n); **`.page-back`** → **`dashboard.index`**. Ausführliche Fenster-/Stichtag-Einleitung im Template entfernt (Logik **§4.1** / **`RetroCleanupService`**). | Nutzerwunsch; klare Kopfzeile und Statuszeile |
| 2026-04-06 | 5/7 | **Dashboard & Bereinigung (IA-Refactor):** Zwei Kacheln **Zu erledigen** — **Bereinigung** (`events.cleanup`) und **Zu-/Absage** (frühestes Event **heute…+30 Tage** ohne RSVP, `get_upcoming_rsvp_prompt_event`). **`RetroCleanupService`:** Bereinigung nur **vergangene** Events (Event-Datum strikt **vor** Tagesbeginn UTC heute); Fortschritt und Liste ohne verschmolzene Upcoming-Queue; Reihenfolge **absteigend** nach **`datum`**; **`cleanup`** mit **`?i=`** und UI **„k von n“**; **`cleanup_rsvp`** / **`allows_cleanup_rsvp`** nur vergangen; **Session-Undo** **`cleanup_rsvp_undo`** + **`POST /events/cleanup/undo-rsvp`**; nach **Bewertungs-Speichern** Undo für dieselbe **`event_id`** löschen. **`rating_prompt`** am Dashboard entfernt. **CSS:** **`.cleanup-step-nav*`**, **`.events-cleanup-hint`**, **`.cleanup-undo-form`**. Doku: **§4.1**, **§6.3**, Registry **§5.1**. | Nutzerwunsch; klare Trennung RSVP kommend vs. Nachpflege vergangen; Rückgängig bei Fehlklick |


---

## 13. Template-Übersicht (Kern)

### 13.1 Status-Spalte (nur diese zwei Werte)


| Wert        | Bedeutung                                                                                                                                                                                                                                 |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pending** | Für diesen Eintrag ist die Migration auf das in der **Phase**-Spalte vorgesehene Redesign-Muster **noch nicht** abgeschlossen.                                                                                                            |
| **done**    | **Entweder:** Migration erledigt und gegen **§7** geprüft. **Oder:** vom User **ausdrücklich** von der visuellen/IA-Migration ausgenommen — dann **zusätzlich** ein Eintrag im **Entscheidungslog §12** (welches Template, warum exempt). |


**Nicht verwenden:** Zwischenstände wie „wip“, „teilweise“, „in Arbeit“ — Details in **§11** Session-Notiz oder **§16.2** Backlog, nicht in dieser Spalte.

### 13.2 Layout-Partials (`templates/partials/`)

Einbindung in `base.html`: `{% include 'partials/_….html' %}`. **Keine** `{% block %}` in Partials — überschreibbare Blöcke nur im Layout (`base.html`), sonst funktioniert `{% extends %}` nicht.

**Body / Shell**


| Datei                  | Inhalt                                                                                                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `_user_bar.html`       | Obere Leiste: Logo, **Theme-Toggle**, **User-Menü** (**§4.5**, **`user-menu`**, Lucide **`user`**, kein Namenstext in der Bar); keine Admin-Schaltfläche. Datenbereinigung nur Dashboard-Card |
| `_sidebar.html`        | Desktop-Sidebar (Hauptnavigation)                                                                                                            |
| `_bottom_nav.html`     | Mobile Bottom-Navigation (4 Tabs)                                                                                                            |
| `_flash_messages.html` | Flask Flash-Messages im `<main>`                                                                                                             |


`**<head>`** (Reihenfolge: Theme-Script zuerst, dann charset/viewport/titel und OG/Twitter-**Blöcke** in `base.html`, danach Includes)


| Datei                         | Inhalt                                                                 |
| ----------------------------- | ---------------------------------------------------------------------- |
| `_head_theme_script.html`     | Inline-Script: `data-theme` + dynamisches `theme-color` vor CSS (FOUC) |
| `_head_pwa_meta.html`         | Statische PWA-/SEO-Basis-Meta (ohne OG/Twitter-Blöcke)                 |
| `_head_manifest_icons.html`   | Manifest, Favicons, Apple-Touch, iOS-Splash                            |
| `_head_stylesheets.html`      | V2/V1-CSS, Lucide-Preload, Font Awesome                                |
| `_head_deferred_scripts.html` | `pwa.js`, `app.js`, CSRF-`meta` (nach `{% block head %}`)              |



| Pfad                             | Phase | Status  |
| -------------------------------- | ----- | ------- |
| `templates/base.html`            | 1     | pending |
| `templates/dashboard/index.html` | 5     | pending |
| `templates/events/index.html`    | 3     | done    |
| `templates/events/detail.html`   | 4     | done    |
| `templates/ggl/index.html`       | 2     | done    |
| `templates/member/index.html`    | 6     | done    |
| `templates/admin/index.html`     | 6     | done    |
| übrige `templates/`**            | 7     | pending |


**Phase 5:** Dashboard-Intent + Bereinigungs-/RSVP-Logik **umgesetzt** (**§6.3**, Stand 2026-04-06); **`templates/dashboard/index.html`** in **§13** Status **pending** bis PO-Freigabe oder explizit **`done`**. Layout: **`dashboard-intent__grid`** für alle Sektionen. **`events/cleanup.html`:** **Phase 7** erledigt (**§8.3.1**); fachliche Details **§6.3** / Entscheidungslog **§12** (2026-04-06).

**Phase 6:** **`templates/member/index.html`** = **`done`** (**`settings-nav`**). **`templates/admin/index.html`** = **`done`** als **Exempt**: KPI-**`hub-card`** bleibt für **`admin.index`**-Deep-Link; kein **`settings-nav`**-Umbau nötig (**§8.2**, **§12**).

---

## 14. Hinweis zu `docs/DESIGN_SYSTEM.md`

Bis zur Konsolidierung dient `DESIGN_SYSTEM.md` als **Referenz** für Farben und Breakpoints. **Verbindliche** Redesign-Regeln und Tracker stehen **hier** in `REDESIGN.md`. Nach Abschluss der Migration kann `DESIGN_SYSTEM.md` durch einen Verweis ersetzt oder entfernt werden.

---

## 15. Git (Kurz)

- Arbeit nur auf Branch `**redesign`**.  
- Kein Push auf `master` aus dem Redesign-Workflow.  
- Vor Phase 2+: `git tag pre-phase-2` usw. setzen.

Notfall-Befehle: siehe `.cursor/rules/redesign.mdc`.

---

## 16. Ende-Kriterium und Cleanup-Backlog (agentschaftlich)

Dieser Abschnitt ist die **einzige verbindliche Stelle** für „wann ist das Redesign fertig“ und **welcher Alt-Code** noch weg muss. Jeder Agent pflegt ihn **ohne** Zugriff auf frühere Chats weiter.

### 16.1 Ende-Kriterium (GO für Abschluss / Merge nach außen)

Das Redesign gilt **nur dann als abgeschlossen**, wenn **alle** folgenden Punkte erfüllt sind **und** der **User** den Abschluss ausdrücklich bestätigt hat (Agent ersetzt keine PO-Freigabe).

1. **Template-Übersicht (§13):** Alle dort genannten Kern-Templates und die Kategorie „übrige `templates/`**“ haben Status **done** (siehe **§13.1**; Ausnahmen nur mit **§12**-Eintrag).
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


| ID    | Priorität | Was entfernen / konsolidieren                                                   | Ort (Pfade, Muster)                                                          | Blockiert bis                                                                                 | Status |
| ----- | --------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------ |
| C-001 | P1        | Font Awesome CDN entfernen, wenn alle Icons auf Lucide/Sprite                   | `templates/base.html`                                                        | Lucide in allen V2-Templates; Agent prüft per Suche `fa-` / `font-awesome`                    | open   |
| C-002 | P0        | V1-CSS und Verzweigung `use_v2_design` / Legacy-Zweig in `base.html` entfernen  | `templates/base.html`, `static/css/main.css`, ggf. `backend/`** Render-Flags | §13 vollständig **done**; §16.1 Punkt 2–3                                                     | open   |
| C-003 | P1        | Alte GGL-Ranking-**Card**-Styles entfernen (ersetzt durch `.ggl-ranking-table`) | `static/css/v2/components.css` (`.ggl-ranking-list`, `.ggl-ranking-card`, …) | Suche im Repo: keine Template-Referenz mehr auf diese Klassen; nach User-Check Layout Phase 7 | open   |
| C-004 | P1        | **GGL Saison-URL:** **`ggl.index`** liest **`season=`**; **`templates/dashboard/index.html`** nutzt **`season=`** (2026-04-05). Offen: **`ggl.season`**-Redirect in **`ggl.py`** mit **`race_season`/`table_season`** → auf **`season=`** umstellen. | `backend/routes/ggl.py` | Kurzer Test Tab Tabelle/Rennen nach **`/ggl/season/<jahr>`** | open   |


*(Weitere Zeilen bei Bedarf fortlaufend nummerieren: C-005 …)*

**Priorität:**

- **P0:** Blockiert das Ende-Kriterium (§16.1) — muss vor Abschluss erledigt oder per §12 vom User befreit werden.
- **P1:** Soll vor Merge erledigt sein; technische oder optische Schulden, die das GO nicht zwingend blockieren, aber dokumentiert abgearbeitet werden sollen.


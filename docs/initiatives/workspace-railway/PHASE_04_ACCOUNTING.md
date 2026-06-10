# Phase 4 – Buchhaltungs-Modul

**Status**: pending  
**Aufwand**: ~1–2 Wochen  
**Branch**: `phase/04-workspace-accounting`  
**Spec**: `docs/capabilities/accounting.md` (autoritativ — bei Konflikten gewinnt das Capability-Doc)

## Ziel

Vollständiges Buchhaltungsmodul für den Verein: Buchungsjournal, Belegverwaltung, Budget-vs-Ist, Revisions-Workflow und Export — alles primär in der App. Belege landen in Google Drive (`Buchhaltung/{Jahr}/`), Strukturdaten in Postgres.

## Pre-Conditions

- Phase 3 (Drive) abgeschlossen: `DriveService` vorhanden und funktioniert
- Phase 1 (Mail) / Phase 2 (Resend) abgeschlossen: für Revision-Notifications
- Branch `phase/04-workspace-accounting` von `master` erstellt
- `scripts/seed_accounting_chart.py` bereit (oder als erster Task erstellen)

## Pre-Flight (Agent liest zuerst)

```
1. AGENTS.md
2. docs/capabilities/accounting.md  ← Haupt-Spec, vollständig lesen
3. docs/ARCHITECTURE.md             ← bestehende Models, Blueprints, Services
4. docs/CONVENTIONS.md              ← Models, Services, Routes, BEM
5. docs/DOMAIN.md                   ← Vereins-Funktionen (SCHATZMEISTER, RECHNUNGSPRUEFER)
6. docs/UI.md                       ← Components, Tokens
7. docs/capabilities/drive.md       ← DriveService-API (Belege-Upload)
8. docs/initiatives/workspace-railway/README.md  ← Status-Tabelle
```

### Pflicht: Bestehende Seiten studieren (vor dem ersten Commit)

**Bevor Code geschrieben wird**, die folgenden Templates und Routes vollständig lesen. Ziel: alle neuen Accounting-Seiten sollen sich nahtlos ins bestehende Projekt einfügen — gleiche Tab-Struktur, gleiche Filter-Muster, gleiche Workflow-Führung, gleiche Tabellen.

**Tab-Seiten und Übersichten:**
```
templates/admin/merch/index.html     ← Tab-Nav, Filter-Disclosure pro Tab, chip--info, Tabellen-Layout
templates/events/index.html          ← Filter-Disclosure mit aktiven Chips, Jahres-Filter, Tab-Parameter in URL
templates/dashboard/index.html       ← dashboard-info-grid, dashboard-info-tile, KPI-Kacheln
templates/admin/index.html           ← admin-hub__hero mit Metriken, page-header, Zurück-Link
```

**Workflows und Schritt-Navigation:**
```
templates/events/cleanup.html        ← cleanup-step-nav: Counter, Zurück/Weiter, Undo-Button
templates/events/detail.html         ← billbro-workflow-block: Schritt-Anzeige, rollen-aware Hinweistext,
                                        dashboard-info-tile in Tabs, info-row in Cards, chip-select
```

**Formulare:**
```
templates/admin/merch/article_form.html  ← form-field__hint, form-row--inline-remove, js-remove,
                                            dynamisches Hinzufügen/Entfernen von Zeilen via vanilla JS
templates/admin/create_event.html        ← Formular-Struktur, _form_macros.html, form-row, form-actions
```

**Mitglieder-Ansichten:**
```
templates/member/merch/orders.html   ← Mitglieder-Listen-Ansicht, Status-Chips
templates/member/index.html          ← settings-nav__row, Platzhalter ersetzen
```

**Routes (Muster für URL-Parameter, Guards, Service-Calls):**
```
backend/routes/admin.py              ← Tab-Parameter (?tab=...), _require_admin(), CSRF-Muster
backend/routes/events.py             ← Filter-Parameter, Jahres-Selektor, Pagination
```

Nach dem Lesen dieser Dateien sollte klar sein: wie Tabs funktionieren, wie Filter mit `disclosure` aufgebaut sind, wie `cleanup-step-nav` verwendet wird, wie `billbro-workflow-block` aufgebaut ist, wie `dashboard-info-tile` aussieht, und wie rollen-abhängige Hinweistexte strukturiert sind. Erst dann beginnt die Implementierung.

## Implementierungs-Reihenfolge

### Commit 1 – Migration: Konten und Geschäftsjahre

Neue Tabellen: `accounts`, `fiscal_years`, `budget_entries`  
Alembic-Migration in eigenem Commit.

Models gemäss `docs/capabilities/accounting.md` Sektion 4.1 / 4.2 / 4.5.

### Commit 2 – Migration: Buchungen, Belege, Revision

Neue Tabellen: `bookings`, `receipts`, `revision_comments`, `revision_approvals`  
Alembic-Migration in eigenem Commit (nach Commit 1).

Models gemäss `docs/capabilities/accounting.md` Sektion 4.3 / 4.4 / 4.6 / 4.7.

**Wichtig**: `Booking.amount_rappen` ist `Integer`, niemals `Float`.

### Commit 3 – Seed-Script und Service-Layer

**`scripts/seed_accounting_chart.py`**  
Legt alle Konten aus `docs/capabilities/accounting.md` Sektion 6 an (Code, Name, Gruppe, Kind, Sort-Order). Idempotent: läuft auch mehrfach ohne Fehler.

Zusätzlich: FiscalYears 2021–2026 anlegen (2021–2025 als `closed`, 2026 als `open`). Budget-Werte 2025 und 2026 aus `vorlagen_buchhaltung/Vereinsfinanzen_2026.xlsx` (nicht committen — nur lokal für Seed). **Keine historischen Einzelbuchungen** (Option A).

**`backend/services/accounting.py`** – `AccountingService`:

```python
# Konten
get_active_accounts(kind=None) -> List[Account]
create_account(code, name, kind, group_name) -> Account
update_account(account_id, **kwargs) -> Account

# Geschäftsjahre
get_or_create_fiscal_year(year) -> FiscalYear
submit_for_review(fiscal_year_id, by_member) -> FiscalYear
approve_year(fiscal_year_id, reviewer) -> FiscalYear  # erzeugt RevisionApproval + PDF

# Budget
set_budget(fiscal_year_id, account_id, amount_rappen, by_member) -> BudgetEntry
get_budget_vs_actual(fiscal_year_id) -> List[dict]  # für Jahresübersicht

# Buchungen
create_booking(fiscal_year_id, date, description, amount_rappen, direction,
               account_id, event_id, member_id, created_by) -> Booking
update_booking(booking_id, **kwargs) -> Booking  # nur wenn Jahr 'open'
get_journal(fiscal_year_id, account_id=None, direction=None) -> List[Booking]
get_year_summary(fiscal_year_id) -> dict  # Einnahmen, Ausgaben, Jahresergebnis

# Belege
upload_receipt(file, uploader, fiscal_year_id, suggested_account_id,
               suggested_event_id, comment) -> Receipt   # via DriveService
attach_receipt_to_booking(receipt_id, booking_id) -> Receipt
get_inbox() -> List[Receipt]  # ungebuchte Belege

# Export
export_csv(fiscal_year_id) -> str       # UTF-8 mit BOM, Semikolon-getrennt
generate_pdf_report(fiscal_year_id) -> bytes

# Revisions-Kommentare
add_revision_comment(booking_id, fiscal_year_id, author, text) -> RevisionComment
resolve_comment(comment_id) -> RevisionComment
```

Drive-Ordner-Logik: beim ersten Upload-Aufruf eines Jahres prüfen ob `Buchhaltung/{Jahr}/` existiert — falls nicht, anlegen via `DriveService`.

### Commit 4 – Routes und Templates: Kern

Blueprint `backend/routes/accounting.py`

Hauptroute:
- `GET /accounting` → Tab-Index (`?year=<id>&tab=journal|belege|budget|abschluss`)
  - Vor den Tabs: Jahres-Selektor + `dashboard-info-grid` (3 KPI-Kacheln)
  - Journal-Tab: `card card--filter` + `disclosure` (Konto, Richtung) + `data-table`
  - Belege-Tab: `card card--filter` + `disclosure` (Status, Event) + Belegliste
  - Budget-Tab: Tabelle Soll/Ist/Abweichung (kein Filter, Jahr oben gewählt)
  - Abschluss-Tab: `billbro-workflow-block` (3 Phasen) + Revisions-Kommentare + Action-Buttons

Weitere Routes:
- `GET /accounting/booking/<id>` → Buchungsdetail
- `POST /accounting/booking/<id>/edit` → Buchung bearbeiten (Guard: Jahr muss `open`)
- `POST /accounting/year/<id>/comment` → Revisionskommentar

Templates: `templates/accounting/index.html`, `booking_detail.html`  
BEM-Klassen, Design-Tokens gemäss `docs/UI.md`.

### Commit 5 – Routes und Templates: Belege und Buchungsworkflow

Beleg-Upload-Workflow (alle aktiven Mitglieder):
- `GET /accounting/receipt/upload` → Schritt 1: Datei + Pre-Tagging / Schritt 2: Vorschau
- `POST /accounting/receipt/upload` → Submit (Upload nach Drive, Receipt anlegen)
- `GET /accounting/receipt/<id>` → Beleg anzeigen / Download via DriveService
- `POST /accounting/booking/<id>/receipt` → Beleg zu bestehender Buchung verknüpfen
- `GET /member/receipts` → Eigene Belege mit Status (Member-Blueprint)

Buchungsworkflow (Schatzmeister):
- `GET/POST /accounting/booking/new` → Schritt 1–3 (Beleg/Daten → Konto → Bestätigen)

Upload-Formular: `<input type="file" accept="image/*,application/pdf" capture="environment">` für Kamera-Support auf Mobile.

Templates: `templates/accounting/receipt_upload.html`, `templates/accounting/booking_new.html`, `templates/member/receipts.html`

### Commit 6 – Revisions-Workflow

Alles läuft im Abschluss-Tab von `accounting/index.html` — keine separate Seite:
- `POST /accounting/year/<id>/submit` → Jahr auf `in_review` setzen (Schatzmeister/Admin)
  - App-Notification an Revisor: `NotifierService.send_push_notification(...)`
  - Journal + Belege werden read-only (Guard in allen Schreib-Routes)
- `POST /accounting/year/<id>/approve` → Jahr bestätigen (nur `Funktion.RECHNUNGSPRUEFER`)
  - `AccountingPdfService.generate_report(fiscal_year)` → PDF-Bytes
  - PDF via `DriveService` in `Buchhaltung/{Jahr}/Revisorenbericht_{Jahr}.pdf` ablegen
  - `RevisionApproval.report_drive_id` setzen → Status auf `closed`

### Commit 7 – Statistik-Seite

Route: `GET /accounting/stats` (Schatzmeister / Revisor / Admin)

Template: `templates/accounting/stats.html` — Vorlage: `templates/events/index.html`

Auswertungen gemäss `docs/capabilities/accounting.md` Sektion 10:
- Saldo-Verlauf (Linienkurve, Chart.js)
- Budget-Auslastung pro Kontengruppe (CSS-Progressbars, kein Chart.js)
- Jahresvergleich alle Jahre (Balkendiagramm, Chart.js)
- Ausgaben nach Kontengruppe (Donut-Chart, Chart.js)
- Ergebnis-Übersicht Tabelle (alle Jahre)
- Mitgliederbeiträge laufendes Jahr (Liste, nur Schatzmeister/Admin)

Chart.js **nur auf dieser Seite** via CDN einbinden:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```
Datenpunkte als JSON im Template (`data-chart='{{ chart_data | tojson }}'`), Initialisierung via inline `<script>` — kein separates JS-File.

Link zur Stats-Seite im Accounting-Index: `settings-nav__row` oder kleiner Button unterhalb der Tabs.

### Commit 8 – Export und Kontenplan-Verwaltung

- `GET /accounting/export/<id>/csv` → CSV-Download
- `GET /accounting/export/<id>/pdf` → PDF-Download (Jahresabschluss ohne Revisions-Bestätigung)
- `GET/POST /accounting/accounts` → Kontenplan-Übersicht (Admin)
- `GET/POST /accounting/accounts/<id>/edit` → Konto bearbeiten (Admin)

### Commit 9 – Navigation, Seed, Doc-Updates

- Sidebar-/Bottom-Nav-Eintrag «Buchhaltung» für Schatzmeister, Revisor, Admin
- `scripts/seed_accounting_chart.py` finalisieren und dokumentieren
- Erster-Start-Check: falls keine Konten vorhanden → Hinweis in `/accounting`
- `docs/ARCHITECTURE.md`: neuer Blueprint + neue Models in den Listen
- `docs/DOMAIN.md`: Sektion «Buchhaltung» mit Kontenplan-Kurzübersicht
- `docs/initiatives/workspace-railway/README.md`: Phase 4 Status auf `done`

## Berechtigungs-Guards (pro Route)

Jede Route muss die Berechtigungen aus `docs/capabilities/accounting.md` Sektion 5 prüfen. Kurzreferenz:

| Route | Mindestberechtigung |
|---|---|
| `receipt/upload`, `member/receipts` | aktives Mitglied |
| `accounting/*` (lesen) | `SCHATZMEISTER` oder `RECHNUNGSPRUEFER` oder `ADMIN` |
| `booking/new`, `booking/edit`, `inbox`, `budget` | `SCHATZMEISTER` oder `ADMIN` |
| `year/submit` | `SCHATZMEISTER` oder `ADMIN` |
| `year/approve` | `RECHNUNGSPRUEFER` |
| `accounts/edit` | `ADMIN` |

Jahr-Guard: Buchungen anlegen/bearbeiten nur wenn `FiscalYear.status == 'open'`.

## Acceptance-Criteria

- [ ] Schatzmeister kann Buchungen anlegen (Einnahme/Ausgabe) mit Konto, Betrag, Datum, Beschreibung
- [ ] Jedes Mitglied kann Beleg hochladen (Foto oder PDF), Pre-Tagging optional
- [ ] Beleg-Inbox zeigt ungebuchte Belege; Schatzmeister kann daraus Buchung erstellen
- [ ] Buchung und Beleg sind verknüpfbar (nachträglich und beim Anlegen)
- [ ] Jahresübersicht zeigt Budget | Ist | Budget nächstes Jahr pro Kontengruppe
- [ ] Buchungsjournal ist filterbar nach Jahr, Konto, Richtung
- [ ] Schatzmeister kann Jahr zur Revision freigeben → Revisor wird benachrichtigt
- [ ] Revisor sieht alle Buchungen + Belege read-only, kann Kommentare hinterlassen
- [ ] Revisor kann Jahr bestätigen → PDF-Revisorenbericht wird generiert und in Drive abgelegt
- [ ] Nach Bestätigung: keine Buchungen mehr möglich im geschlossenen Jahr
- [ ] CSV-Export öffnet korrekt in Excel (UTF-8 BOM, Semikolon)
- [ ] PDF-Export zeigt Jahresabschluss mit allen Kontengruppen
- [ ] Admin kann Kontenplan bearbeiten (Konto hinzufügen, umbenennen, deaktivieren)
- [ ] Mitglied ohne Berechtigung sieht kein Accounting-Modul ausser eigene Belege
- [ ] Beträge werden korrekt in Rappen gespeichert, im UI als CHF angezeigt (Rappen / 100)
- [ ] Alle DB-Migrationen sauber (up + down)
- [ ] Kamera-Upload funktioniert auf iOS Safari und Android Chrome

## Out of Scope für Phase 4

- OCR / AI-Klassifikation (Future, Datenmodell vorbereitet)
- TWINT / ZKB-Integration (`payment_ref` ist vorbereitet, Logik kommt Phase 6)
- Automatischer Kontoauszug-Import (Future)
- Merch-Beleg-Verknüpfung (`suggested_merch_order_id` kommt Phase 10)
- Doppelte Buchführung / MwSt
- Wiederkehrende Buchungen
- React / Tailwind Frontend (Open Decision in STRATEGY_2026.md, aktuell Jinja2)

## Template-Referenzen (WICHTIG: bestehende Muster kopieren, keine neuen erfinden)

Cursor darf **keine neuen CSS-Klassen** erfinden. Alle neuen Templates bauen auf den bestehenden BEM-Klassen der App auf.

### Seitenstruktur (gilt für alle neuen Templates)

```html
{% extends "base.html" %}
{% macro lucide_icon(symbol_id, icon_class='icon') -%}
<svg class="{{ icon_class }}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <use href="{{ url_for('static', filename='icons/lucide-sprite.7e463391.svg') }}#{{ symbol_id }}"></use>
</svg>
{%- endmacro %}
{% block content %}
<div class="container">
    <div class="page-header">
        <p class="page-back"><a href="...">{{ lucide_icon('chevron-left') }}<span>Zurück zu Verein</span></a></p>
        <h1>{{ lucide_icon('calculator') }} Buchhaltung</h1>
    </div>
    <div class="page-content">...</div>
</div>
{% endblock %}
```

### Template-zu-Vorlage-Mapping

| Neues Template | Vorlage kopieren von | Warum |
|---|---|---|
| `accounting/index.html` | `templates/admin/merch/index.html` | Tab-Struktur (`tabs__nav`, `tabs__panel`), Filter-Disclosure pro Tab |
| `accounting/booking_new.html` | `templates/events/cleanup.html` | `cleanup-step-nav` Schritt-Navigation |
| `accounting/receipt_upload.html` | `templates/events/cleanup.html` | `cleanup-step-nav` Schritt-Navigation |
| `accounting/booking_detail.html` | `templates/events/detail.html` | Detail-Layout mit `info-row` und `dashboard-info-tile` |
| `member/receipts.html` | `templates/member/merch/orders.html` | Mitglieder-Listen-Ansicht |

### Pattern 1: Tab-Index mit KPI-Kacheln vor den Tabs

Vorlage: `templates/admin/merch/index.html` (Tabs) + `templates/dashboard/index.html` (Kacheln)

```html
{# Jahres-Selektor + KPI-Kacheln VOR den Tabs #}
<div class="dashboard-info-grid">
    <div class="dashboard-info-tile dashboard-info-tile--static">
        <span class="dashboard-info-tile__content">
            <span class="dashboard-info-tile__label">Saldo</span>
            <span class="dashboard-info-tile__value">
                <span class="dashboard-info-tile__line">CHF {{ saldo_chf }}</span>
            </span>
        </span>
    </div>
    <div class="dashboard-info-tile dashboard-info-tile--static">
        <span class="dashboard-info-tile__content">
            <span class="dashboard-info-tile__label">Offene Belege</span>
            <span class="dashboard-info-tile__value">
                <span class="dashboard-info-tile__line {% if offene_belege == 0 %}dashboard-info-tile__line--subtle{% endif %}">
                    {{ offene_belege }}
                </span>
            </span>
        </span>
    </div>
</div>

<div class="tabs">
    <nav class="tabs__nav" role="tablist">
        <a href="{{ url_for('accounting.index', year=year_id, tab='journal') }}"
           class="tabs__tab {{ 'tabs__tab--active' if active_tab == 'journal' else '' }}"
           role="tab" aria-selected="{{ 'true' if active_tab == 'journal' else 'false' }}">
            {{ lucide_icon('book-open') }} Journal
        </a>
        {# weitere Tabs: belege, budget, abschluss #}
    </nav>
    <div class="tabs__content">
        <div class="tabs__panel {{ 'tabs__panel--active' if active_tab == 'journal' else '' }}" role="tabpanel">
            {# card card--filter + disclosure nur in diesem Tab #}
        </div>
    </div>
</div>
```

### Pattern 2: Abschluss-Tab mit BillBro-Workflow-Block

Vorlage: `templates/events/detail.html` — der BillBro-Workflow-Block ab `<div class="billbro-workflow-block">`.

```html
<div class="billbro-workflow-block">
    <ol class="billbro-workflow" aria-label="Jahresabschluss-Ablauf">
        {% for label in ['Offen', 'In Prüfung', 'Abgeschlossen'] %}
        {% set i = loop.index %}
        <li class="billbro-workflow__step{% if i < abschluss_phase %} billbro-workflow__step--done{% elif i == abschluss_phase %} billbro-workflow__step--current{% endif %}"
            {% if i == abschluss_phase %}aria-current="step"{% endif %}>
            <span class="billbro-workflow__index">{{ i }}</span>
            {% if i == abschluss_phase %}<span>{{ label }}</span>{% endif %}
        </li>
        {% endfor %}
    </ol>
    <p class="billbro-workflow__hint" role="status">
        {% if current_user.has_funktion('SCHATZMEISTER') or current_user.is_admin() %}
            {% if abschluss_phase == 1 %}Erfasse alle Buchungen und weise Belege zu. Sobald alles vollständig ist, gib das Jahr zur Prüfung frei.
            {% elif abschluss_phase == 2 %}Das Jahr ist gesperrt. Beantworte Kommentare des Revisors falls nötig.
            {% else %}Abschluss {{ fiscal_year.year }} ist genehmigt und archiviert.{% endif %}
        {% elif current_user.has_funktion('RECHNUNGSPRUEFER') %}
            {% if abschluss_phase == 1 %}Warte, bis der Schatzmeister das Jahr freigibt.
            {% elif abschluss_phase == 2 %}Prüfe Journal und Budget, hinterlasse Kommentare bei Klärungsbedarf und bestätige das Jahr.
            {% else %}Abschluss {{ fiscal_year.year }} ist genehmigt und archiviert.{% endif %}
        {% endif %}
    </p>
</div>
```

`abschluss_phase`: 1 = `open`, 2 = `in_review`, 3 = `closed`.

### Pattern 3: Schritt-Navigation (Upload + Buchungsworkflow)

Vorlage: `templates/events/cleanup.html` — `cleanup-step-nav`-Block.

```html
<nav class="cleanup-step-nav" aria-label="Schritte">
    <p class="cleanup-step-nav__counter">{{ step }} von {{ total_steps }}</p>
    <div class="cleanup-step-nav__actions">
        {% if step > 1 %}
        <a class="btn btn--outline btn--sm" href="{{ url_for('accounting.receipt_upload', step=step-1) }}">Zurück</a>
        {% else %}
        <button type="button" class="btn btn--outline btn--sm" disabled>Zurück</button>
        {% endif %}
        {# Weiter via Submit-Button im Formular, nicht als direkter Link #}
    </div>
</nav>
```

### Pattern 4: Filter-Disclosure (pro Tab, nicht global)

Filter nur im jeweiligen Tab — gleiche Klassen wie `templates/admin/merch/index.html`:

```html
<div class="card card--filter tool-surface">
    <div class="card__body">
        <details class="disclosure">
            <summary class="disclosure__summary">
                {{ lucide_icon('chevron-down') }}
                Filter
                {% if active_filter %}<span class="chip chip--info">{{ active_filter }}</span>{% endif %}
            </summary>
            <div class="disclosure__content">
                <form method="GET" class="form">
                    <input type="hidden" name="tab" value="journal">
                    <div class="form-row">...</div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn--primary btn--sm">{{ lucide_icon('funnel') }} Filtern</button>
                        <a class="btn btn--outline btn--sm" href="...">Zurücksetzen</a>
                    </div>
                </form>
            </div>
        </details>
    </div>
</div>
```

### Alle CSS-Klassen auf einen Blick

| Pattern | Klassen |
|---|---|
| KPI-Kachel statisch | `dashboard-info-tile dashboard-info-tile--static` → `__content` → `__label` + `__value` → `__line` |
| KPI-Kachel leer | `dashboard-info-tile__line--subtle` für Platzhaltertext |
| Workflow-Block | `billbro-workflow-block` → `billbro-workflow` (ol) → `billbro-workflow__step --done/--current` → `__index` + Label + `billbro-workflow__hint` |
| Schritt-Nav | `cleanup-step-nav` → `cleanup-step-nav__counter` + `cleanup-step-nav__actions` |
| Tab-Nav | `tabs` → `tabs__nav` → `tabs__tab tabs__tab--active` (role="tab") |
| Tab-Panel | `tabs__panel tabs__panel--active` (role="tabpanel") |
| Filter-Disclosure | `card card--filter tool-surface` → `card__body` → `details.disclosure` → `summary.disclosure__summary` → `div.disclosure__content` |
| Aktiver Filter-Chip | `chip chip--info` im Summary |
| Formular-Zeile | `form-row` → `form-field` → `form-field__label` + `form-field__input` / `form-field__select` |
| Hilfetext | `form-field__hint` unter dem Input |
| Inline-Entfernen | `form-row form-row--inline-remove` → `js-remove` auf dem Button |
| Info-Zeile | `info-row` → `info-row__label` + `info-row__value` |
| Admin-Hub-Hero | `admin-hub__hero` → `admin-hub__hero-inner` → `admin-hub__metrics` → `admin-hub__metric` |
| Settings-Zeile | `settings-nav__row` → `settings-nav__icon` + `settings-nav__meta` → `__label` + `__description` + `settings-nav__chevron` |
| Buttons | `btn btn--primary` / `btn btn--outline` / `btn btn--sm` |
| Zurück-Link | `page-back` > `a` mit `chevron-left` |
| Pflichtfeld | `{% from 'partials/_form_macros.html' import required_mark, field_errors %}` |

### Einstiegspunkt: Verein-Hub (KEIN Bottom-Nav-Eintrag)

Die Buchhaltung bekommt **keinen eigenen Bottom-Nav-Eintrag**. Der Einstieg läuft über «Verein» → «Vereinsverwaltung».

In `templates/member/index.html` gibt es bereits einen Platzhalter (`settings-nav__row--soon`). Diesen **ersetzen** durch:

```html
{% if current_user.has_funktion('SCHATZMEISTER') or current_user.has_funktion('RECHNUNGSPRUEFER') or current_user.is_admin() %}
<a href="{{ url_for('accounting.index') }}" class="settings-nav__row">
    <span class="settings-nav__icon" aria-hidden="true">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <use href="{{ _sprite }}#calculator"></use>
        </svg>
    </span>
    <span class="settings-nav__meta">
        <span class="settings-nav__label">Buchhaltung</span>
        <span class="settings-nav__description">Journal, Belege und Jahresabschluss</span>
    </span>
    <svg class="icon settings-nav__chevron" viewBox="0 0 24 24" aria-hidden="true">
        <use href="{{ _sprite }}#chevron-right"></use>
    </svg>
</a>
{% endif %}
```

### Was Cursor NICHT tun darf

- Keine neuen CSS-Klassen wie `accounting-table`, `receipt-card`, `booking-form__wrapper` erfinden
- Kein Inline-CSS (`style="..."`) ausser für dynamische Werte (z.B. Prozentbalken-Breite)
- Kein Tailwind, kein Bootstrap, kein CDN-CSS
- Keine neuen Icon-Libraries — ausschliesslich der bestehende Lucide-Sprite
- Kein eigenes JavaScript-Framework — vanilla JS wie in den bestehenden Templates
- Kein Feature-Flag `ACCOUNTING_FEATURE_ENABLED` einbauen

## Hinweise für Cursor

- `amount_rappen` ist **immer Integer**, niemals Float. Im UI immer `betrag_rappen / 100` anzeigen.
- Drive-Ordner `Buchhaltung/{Jahr}/` wird beim ersten Upload auto-angelegt — kein neuer Config-Eintrag, aus `DRIVE_ROOT_FOLDER_ID` ableiten via `DriveService`.
- Seed-Script ist idempotent (mehrfach ausführbar ohne Fehler). Datei `vorlagen_buchhaltung/` niemals committen.
- PDF: `reportlab` verwenden. Implementierung in `backend/services/accounting_pdf.py` (`AccountingPdfService`) isolieren.
- Forms: alle Accounting-Forms als `FlaskForm` in `backend/forms/accounting.py`. Reine State-Mutations (Jahresfreigabe, Genehmigen) als einfache HTML-Forms mit `{{ csrf_token() }}`.
- Berechtigungen: `_require_funktion(*funktionen)` im Blueprint, Admin kommt immer durch.
- UX-Texte: Deutsch, schweizerische Schreibweise, Doppel-S statt Eszett. BEM-Klassen + Tokens gemäss `docs/UI.md`.
- Migrationen: zwei separate Alembic-Commits (erst Konten/Jahre/Budget, dann Buchungen/Belege/Revision).
- Nach jedem Commit lokal mit Test-Daten verifizieren.

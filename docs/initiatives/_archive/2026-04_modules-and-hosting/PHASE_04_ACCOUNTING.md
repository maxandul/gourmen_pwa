# Phase 4 – Buchhaltung

**Status**: pending  
**Aufwand**: ~1-2 Wochen (je nach Tiefe)  
**Branch**: `phase/04-modules-accounting`

## Ziel

Eigenes Buchhaltungs-Modul für den Verein. Einnahmen-/Ausgaben-Rechnung mit Belegen, Jahresabschluss, Export für Revisor. Belege liegen via Phase-3-StorageService in R2.

## Pre-Conditions

- Phase 3 (Files) abgeschlossen, `StorageService` funktioniert
- Phase 1 (Mail) abgeschlossen für optionale Buchungs-Bestätigungen
- Branch `phase/04-modules-accounting` von `master` erstellt
- Mit User vorab geklärt: einfache Einnahmen-/Ausgaben-Rechnung **oder** doppelte Buchführung

## Tasks

### 1. Models

Datei `backend/models/accounting.py` (oder mehrere Dateien):

- [ ] `Account` (Konto)
  - `id`, `code` (z.B. `1000`), `name`, `kind` (Enum: `ASSET`, `LIABILITY`, `INCOME`, `EXPENSE`, `EQUITY`), `parent_id` (FK self, optional für Hierarchie)
  - `is_active`, `created_at`, `updated_at`
- [ ] `FiscalYear` (Geschäftsjahr)
  - `id`, `year`, `start_date`, `end_date`, `is_closed` (bool), `closed_at`
- [ ] `Booking` (Buchung)
  - `id`, `fiscal_year_id` (FK), `booking_date`, `description`, `amount_rappen` (int), `direction` (Enum: `IN`/`OUT` für E/A-Rechnung – oder `debit_account_id`/`credit_account_id` bei doppelter Buchführung)
  - `category_id` (FK Account)
  - `created_by` (FK Member), `created_at`, `updated_at`
  - `event_id` (FK Event, nullable – z.B. wenn Beleg zu Event gehört)
  - `member_id` (FK Member, nullable – z.B. Mitgliedsbeitrag)
- [ ] `Receipt` (Beleg)
  - `id`, `booking_id` (FK), `document_id` (FK Document) – Wiederverwendung des Document-Modells aus Phase 3
- [ ] Alembic-Migration in **separatem Commit**

### 2. Service-Layer

Datei `backend/services/accounting.py`:

- [ ] `AccountingService`
  - [ ] `create_booking(...)` – Buchung anlegen mit optionalem Beleg
  - [ ] `attach_receipt(booking_id, file)` – Beleg via StorageService hochladen, Document erstellen, Receipt-Eintrag
  - [ ] `close_fiscal_year(year_id)` – Jahresabschluss markieren, danach keine Buchungen mehr in diesem Jahr
  - [ ] `get_balance(account_id, until_date)` – Kontostand
  - [ ] `get_overview(year_id)` – Übersicht Einnahmen/Ausgaben/Saldo
  - [ ] `export_csv(year_id) -> str` – CSV-Export für Revisor
  - [ ] `export_pdf(year_id) -> bytes` – PDF-Jahresabschluss

### 3. Routes

Neuer Blueprint `backend/routes/accounting.py`:

- [ ] `GET /accounting` – Übersicht aktuelles Geschäftsjahr (nur Schatzmeister + Admin)
- [ ] `GET /accounting/year/<id>` – Jahres-Detail
- [ ] `GET/POST /accounting/booking/new` – Buchung anlegen
- [ ] `GET /accounting/booking/<id>` – Buchung anzeigen + Belege
- [ ] `POST /accounting/booking/<id>/receipt` – Beleg hochladen (via Phase-3-Logik)
- [ ] `GET /accounting/export/<year_id>/csv` – CSV-Download
- [ ] `GET /accounting/export/<year_id>/pdf` – PDF-Download
- [ ] `POST /accounting/year/<id>/close` – Jahresabschluss (Admin + Step-Up)

### 4. Permissions

- [ ] Schreib-Zugriff: nur Member mit `Funktion.SCHATZMEISTER` oder `Role.ADMIN`
- [ ] Lese-Zugriff: zusätzlich `Funktion.RECHNUNGSPRUEFER` (Revisor)
- [ ] Anderen Members: keine Sicht auf Buchhaltung

### 5. Initial-Konten-Setup

- [ ] Seed-Skript `scripts/seed_accounting_chart.py`:
  - Standard-Vereins-Kontenplan anlegen
  - Vereinfachter Plan: Bank, Kasse, Mitgliedsbeiträge, Veranstaltungs-Einnahmen, Veranstaltungs-Ausgaben, Merch-Erlöse, Merch-Einkauf, Verwaltung, Sonstige Einnahmen, Sonstige Ausgaben
- [ ] Beim ersten Aufruf der Übersicht: prüfen ob Konten existieren, sonst Hinweis „Bitte initialisieren"

### 6. Frontend

- [ ] `templates/accounting/index.html` – Übersicht mit Stat-Tiles (Einnahmen, Ausgaben, Saldo)
- [ ] `templates/accounting/booking_new.html` – Buchungs-Form mit Beleg-Upload
- [ ] `templates/accounting/booking_detail.html`
- [ ] `templates/accounting/year_detail.html`
- [ ] Sidebar/Bottom-Nav-Eintrag „Buchhaltung" für berechtigte User
- [ ] BEM-Klassen, Tokens (siehe `docs/UI.md`)

### 7. Optional: Auto-Buchung bei Stripe/RaiseNow-Webhook

- [ ] **Verschoben auf Phase 6** (Payments)
- [ ] Hier nur Datenmodell vorbereiten

### 8. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: neuer Blueprint + neue Models in den Listen
- [ ] `docs/DOMAIN.md`: Sektion „Buchhaltung" mit Konten-Plan-Erklärung

## Acceptance-Criteria

- [ ] Schatzmeister kann Buchungen anlegen (Einnahme/Ausgabe)
- [ ] Belege können hochgeladen werden (PDF, JPG) und sind verknüpft
- [ ] Übersicht zeigt aktuelle Salden
- [ ] CSV-Export öffnet sich in Excel/Numbers korrekt (Komma-Zahlen, Datums-Format)
- [ ] PDF-Jahresabschluss listet alle Buchungen + Saldo
- [ ] Jahresabschluss-Mechanismus blockiert weitere Buchungen
- [ ] Revisor (Funktion `RECHNUNGSPRUEFER`) sieht alles, kann nicht ändern
- [ ] Member ohne Berechtigung sieht Modul nicht
- [ ] DB-Migration sauber

## Out of Scope

- **Doppelte Buchführung mit MwSt** – Vorerst nur einfache Einnahmen-/Ausgaben-Rechnung (für kleine Vereine üblich)
- **Externe FIBU-Anbindung** (bexio, Abacus) – falls später gewünscht, separate Mini-Phase
- **Wiederkehrende Buchungen** (z.B. monatliche Beiträge) – kommt später
- **Mahn-Wesen** – kommt später, vermutlich mit Phase 6 verschmolzen
- **Mehrwertsteuer** – Verein meist befreit, nicht im Initial-Scope

## Cursor-Agent-Briefing

```
Branch: phase/04-modules-accounting
Doc: docs/initiatives/modules-and-hosting/PHASE_04_ACCOUNTING.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen
- docs/CONVENTIONS.md lesen (Models, Services, Routes)
- docs/DOMAIN.md lesen (Vereins-Funktionen, Schatzmeister)
- docs/UI.md lesen (Components für UI)
- Phase 3 (Files) abgeschlossen
- Mit User vorab Variante geklärt: einfache E/A-Rechnung oder doppelte Buchführung

Implementiere Phase 4 (Buchhaltung) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- Permissions strikt (Schatzmeister + Admin schreibend, Revisor lesend)
- Beleg-Upload via Phase-3-StorageService
- Folge .cursor/rules/initiatives.mdc

Nach jedem Sub-Task lokal verifizieren mit Test-Daten.

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md, DOMAIN.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Beträge in Rappen** als `int`, niemals Float
- **Rundung** nur bei Display, nicht in Storage
- **Kontenplan** kann später erweitert werden, deshalb `Account.code` flexibel halten
- **PDF-Generierung** mit `reportlab` oder `weasyprint` – beide Optionen ok, mit User abstimmen
- **CSV-Encoding** UTF-8 mit BOM für Excel-Kompatibilität
- **Lokales Testing** mit echtem Test-Beleg (PDF) hochladen

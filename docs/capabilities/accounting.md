# Capability: Buchhaltung

> **Zweck**: Das Buchhaltungsmodul bildet die gesamte Vereinsfinanzverwaltung in der PWA ab — Buchungsjournal, Budget, Belegverwaltung, Jahresabschluss und Revisionsprozess. Ziel ist eine vollständig app-basierte Arbeitsweise: kein Excel-Ping-Pong mehr, kein manuelles Zusammensuchen von Belegen, kein separater Revisoren-Workflow ausserhalb der App.
>
> **Status**: Konzept abgeschlossen, bereit für Phase-4-Implementation. **Owner**: Andreas. **Stand**: 2026-06-08.
>
> **Verwandte Docs**: `docs/STRATEGY_2026.md` (strategischer Rahmen), `docs/initiatives/workspace-railway/PHASE_04_ACCOUNTING.md` (Cursor-Briefing), `docs/capabilities/drive.md` (Belege-Storage via Drive).

---

## 1. Strategie-Anker

Aus `STRATEGY_2026.md`:

- *Belege (Buchhaltung)*: Google Shared Drive (Unterordner) — pragmatisch, kollaborierbar.
- *Strukturierte App-Daten*: Postgres auf Railway — Buchungen, Konten, Geschäftsjahre, Belege-Metadaten.
- *AI-first-Leitlinie*: Für Buchhaltung explizit geprüft. OCR und Klassifikation sind Future Considerations; kein AI im MVP.
- *Offene Entscheide (STRATEGY_2026)*: n8n vs. Flask → **Flask-Modul** (Entscheid 2026-06-08). TWINT-Anbieter offen, ZKB-Integration als Future Consideration.

**Leitprinzip App-first**: Buchungsjournal, Budget, Revisionsworkflow und Jahresübersicht sind primär in der App. PDF- und CSV-Export sind ein Zusatz für Archiv und externe Empfänger — nie die primäre Arbeitsweise.

## 2. User Stories

| Rolle | Story |
|---|---|
| Mitglied | «Ich kann nach einem Event meinen Beleg direkt in der App fotografieren und einreichen, mit Hinweis auf den Event und die Kategorie.» |
| Mitglied | «Ich sehe, ob mein eingereichter Beleg bereits verbucht wurde.» |
| Schatzmeister | «Ich sehe eine Inbox mit allen ungebuchten Belegen und kann sie mit einem Klick in eine Buchung umwandeln.» |
| Schatzmeister | «Ich kann Buchungen manuell anlegen (ohne Beleg) und Belege nachträglich anfügen.» |
| Schatzmeister | «Ich sehe das Buchungsjournal gefiltert nach Jahr und Kategorie, mit Saldo auf einen Blick.» |
| Schatzmeister | «Ich kann das Jahr für die Revision freigeben — ab dann ist es gesperrt für Änderungen.» |
| Schatzmeister | «Ich kann Budget-Werte pro Konto und Jahr hinterlegen und Budget vs. Ist direkt vergleichen.» |
| Revisor | «Ich sehe alle Buchungen und Belege eines Jahres in der App (read-only), ohne Excel-Datei anfordern zu müssen.» |
| Revisor | «Ich kann Kommentare zu einzelnen Buchungen hinterlassen und das Jahr formal bestätigen.» |
| Revisor | «Nach meiner Bestätigung generiert die App automatisch den Revisorenbericht als PDF.» |
| Admin | «Ich kann den Kontenplan in der App bearbeiten — Konten hinzufügen, umbenennen, deaktivieren.» |

## 3. Architektur-Entscheide

### 3.1 Flask-Modul statt n8n

Entschieden für reines Flask-Modul. Begründung: Für ~50 Buchungen/Jahr und eine Person als Schatzmeister bringt n8n keinen echten Mehrwert. Kein weiterer Dienst, kein weiteres Abo, alles im selben Repo.

OCR/Beleg-Klassifikation als zukünftiger optionaler API-Call direkt aus Flask — das Datenmodell ist dafür vorbereitet, aber kein Tag-1-Feature.

### 3.2 Einnahmen-/Ausgaben-Rechnung (E/A)

Keine doppelte Buchführung. Für Schweizer Kleinvereine unter CHF 500k Jahresumsatz gesetzlich und praktisch ausreichend. Der bestehende Kontenplan (2021–2026) wird 1:1 übernommen.

### 3.3 Belege via Google Drive

Belege werden beim Upload in Drive gespeichert (`Buchhaltung/{Jahr}/`). Die App speichert die Drive-File-ID als Referenz in Postgres. Drive ist reiner Speicher; Navigation und Verknüpfung laufen über die App.

### 3.4 Zwei-Stufen-Beleg-Flow

1. **Einreichen** (jedes Mitglied): Beleg hochladen mit optionalem Pre-Tagging → Status «ungebucht»
2. **Buchen** (Schatzmeister): Beleg prüfen, Buchung erstellen, Beleg verknüpfen → Status «gebucht»

Belege können ohne Buchung existieren (Inbox). Buchungen können ohne Beleg existieren (z.B. Kontoführungsgebühren).

### 3.5 Kein Feature-Flag

Das Modul braucht kein `ACCOUNTING_FEATURE_ENABLED`-Flag. Die Berechtigungslogik (Schatzmeister/Revisor/Admin) übernimmt die Zugangskontrolle vollständig. Mitglieder ohne Berechtigung sehen den Eintrag im Verein-Hub schlicht nicht.

### 3.6 PDF-Bibliothek: reportlab

`reportlab` (pure Python, keine System-Abhängigkeiten). Auf Railway problemlos deploybar ohne Cairo/Pango. Die PDF-Logik wird vollständig in `backend/services/accounting_pdf.py` (`AccountingPdfService`) isoliert — kein PDF-Code in Routes oder dem Haupt-Service.

### 3.7 WTForms

Für alle Formular-Seiten: `FlaskForm` aus `flask_wtf` (wie `backend/forms/rating.py`). Für reine State-Mutations via POST-Button (Jahresfreigabe, Revision bestätigen): manueller `csrf_token()` in einem einfachen HTML-Formular (wie in `backend/routes/docs.py`). Alle Accounting-Forms in **`backend/forms/accounting.py`** — kein Inline-Definieren im Route-File.

### 3.8 Berechtigungs-Helper

Generischer Helper im Blueprint, kein separater Helper pro Rolle:

```python
def _require_funktion(*funktionen) -> None:
    if not current_user.is_authenticated:
        abort(403)
    if not current_user.is_admin() and not any(
        current_user.has_funktion(f) for f in funktionen
    ):
        abort(403)
```

Verwendung: `_require_funktion('SCHATZMEISTER')` oder `_require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')`. Admin kommt immer durch (konsistent mit dem Rest der App).

### 3.9 Drive-Ordner-Konfiguration

Kein neuer Config-Eintrag. Der Unterordner `Buchhaltung/{Jahr}/` wird aus dem bestehenden `DRIVE_ROOT_FOLDER_ID` beim ersten Upload automatisch erstellt/gesucht via `DriveService`. Keine separate `ACCOUNTING_DRIVE_FOLDER_ID`-Variable.

### 3.10 Budget: Separate Ansicht (Variante B)

Budget hat einen eigenen Tab im Accounting-Index. Begründung: Budgetpflege ist eine eigenständige Aufgabe (einmal pro Jahr), und der Revisor soll direkt zur Budget-vs-Ist-Ansicht navigieren können ohne durch das Journal zu scrollen. Das Budget-Tab zeigt eine Tabelle Soll / Ist / Abweichung pro Konto, gruppiert nach Kontengruppen.

## 4. Datenmodell

### 4.1 `FiscalYear` (Geschäftsjahr)

```python
id          : Integer PK
year        : Integer UNIQUE (z.B. 2026)
start_date  : Date
end_date    : Date
status      : Enum('open', 'in_review', 'closed')
closed_at   : DateTime nullable
```

Status-Lifecycle: `open` → `in_review` (Schatzmeister gibt frei) → `closed` (Revisor bestätigt).

### 4.2 `Account` (Konto)

```python
id          : Integer PK
code        : String(10) UNIQUE (z.B. '3000')
name        : String(100) (z.B. 'Mitgliederbeiträge')
kind        : Enum('income', 'expense')
group_name  : String(100) nullable  # Kontengruppe für Gruppierung im Report
is_active   : Boolean DEFAULT True
sort_order  : Integer DEFAULT 0
created_at  : DateTime
```

Kontenplan ist editierbar (Admin). Seed aus bestehendem Excel (Sektion 6).

### 4.3 `Booking` (Buchung)

```python
id              : Integer PK
fiscal_year_id  : FK FiscalYear
booking_date    : Date
description     : String(255)
amount_rappen   : Integer  # niemals Float
direction       : Enum('in', 'out')
account_id      : FK Account
event_id        : FK Event nullable
member_id       : FK Member nullable  # zugeordnetes Mitglied (z.B. Beitragszahler)
payment_ref     : String(255) nullable  # für spätere TWINT/ZKB-Integration
created_by      : FK Member
created_at      : DateTime
updated_at      : DateTime
```

**Beträge immer in Rappen als Integer.** Niemals Float. Anzeige mit Division durch 100, Runden nur beim Display.

### 4.4 `Receipt` (Beleg)

```python
id              : Integer PK
booking_id      : FK Booking nullable  # NULL = noch ungebucht (Inbox)
drive_file_id   : String(255)          # Google Drive File-ID
drive_file_name : String(255)
display_name    : String(120) nullable # kurzer Anzeige-Name fuer Listen (zusaetzlich zum langen Dateinamen)
drive_folder_id : String(255)          # Ordner-ID in Drive
file_type       : String(50)           # 'image/jpeg', 'application/pdf', etc.
uploader_id     : FK Member
uploaded_at     : DateTime
suggested_account_id : FK Account nullable   # Pre-Tagging durch Uploader
suggested_event_id   : FK Event nullable     # Pre-Tagging durch Uploader
comment         : Text nullable              # Freitext-Kommentar des Uploaders
ocr_data        : JSON nullable              # Future: OCR-Rohresultat
```

### 4.5 `BudgetEntry` (Budget)

```python
id              : Integer PK
fiscal_year_id  : FK FiscalYear
account_id      : FK Account
amount_rappen   : Integer
created_by      : FK Member
updated_at      : DateTime
UNIQUE(fiscal_year_id, account_id)
```

### 4.6 `RevisionComment` (Revisionskommentar)

```python
id          : Integer PK
booking_id  : FK Booking nullable  # falls zu einer Buchung
fiscal_year_id : FK FiscalYear nullable  # falls allgemein zum Jahr
author_id   : FK Member
text        : Text
created_at  : DateTime
resolved    : Boolean DEFAULT False
```

### 4.7 `RevisionApproval` (Revisionsbestätigung)

```python
id              : Integer PK
fiscal_year_id  : FK FiscalYear UNIQUE
reviewer_id     : FK Member
approved_at     : DateTime
report_drive_id : String(255) nullable  # Drive-ID des generierten PDFs
```

### 4.8 Alembic-Migrationen

Zwei separate Commits:
1. Konten + Geschäftsjahre + Budget (`accounts`, `fiscal_years`, `budget_entries`)
2. Buchungen + Belege + Revision (`bookings`, `receipts`, `revision_comments`, `revision_approvals`)

## 5. Rollen und Berechtigungen

| Aktion | Mitglied | Schatzmeister | Revisor | Admin |
|---|---|---|---|---|
| Beleg einreichen | ✅ | ✅ | – | ✅ |
| Beleg-Inbox sehen | – | ✅ | – | ✅ |
| Buchung anlegen/bearbeiten | – | ✅ (nur offenes Jahr) | – | ✅ |
| Buchungsjournal lesen | – | ✅ | ✅ | ✅ |
| Budget bearbeiten | – | ✅ | – | ✅ |
| Jahr zur Revision freigeben | – | ✅ | – | ✅ |
| Revisionskommentar | – | ✅ | ✅ | ✅ |
| Jahr bestätigen (Revision) | – | – | ✅ | – |
| Kontenplan bearbeiten | – | – | – | ✅ |
| PDF/CSV exportieren | – | ✅ | ✅ | ✅ |

Rollen-Mapping auf bestehende Modelle: `Funktion.SCHATZMEISTER`, `Funktion.RECHNUNGSPRUEFER`, `Role.ADMIN`.

## 6. Kontenplan (Seed)

Aus dem bestehenden Excel 2021–2026 übernommen. Kontonummern bleiben erhalten; im UI werden nur die Namen angezeigt.

### Einnahmen

| Code | Name | Gruppe |
|---|---|---|
| 3000 | Mitgliederbeiträge | Mitgliederbeiträge |
| 3015 | Freiwillige Beiträge von Mitgliedern | Mitgliederbeiträge |
| 3020 | Gönnerbeiträge | Mitgliederbeiträge |
| 3100 | Spenden von Privaten | Erhaltene Zuwendungen |
| 3110 | Legate und Vermächtnisse | Erhaltene Zuwendungen |
| 3120 | Subventionen / Spenden öffentlicher Hand | Erhaltene Zuwendungen |
| 3130 | Einnahmen Sammelaktionen | Erhaltene Zuwendungen |
| 3300 | Erlöse aus Materialverkäufen | Aktivitäten und Leistungen |
| 3310 | Einnahmen aus monatlichen Essen | Aktivitäten und Leistungen |
| 3320 | Erlöse aus Veranstaltungen | Aktivitäten und Leistungen |
| 3340 | Mieteinnahmen | Aktivitäten und Leistungen |
| 3600 | Inserate, Werbe- und Sponsoringeinnahmen | Übrige Erlöse |
| 3610 | Ertrag aus Liegenschaften | Übrige Erlöse |
| 3620 | Sonstige Erlöse (Bussen) | Übrige Erlöse |

### Ausgaben

| Code | Name | Gruppe |
|---|---|---|
| 4000 | Waren und Materialaufwand | Aufwand Aktivitäten |
| 4400 | Aufwand für bezogene Dienstleistungen | Aufwand Aktivitäten |
| 4500 | Leistungen für Vereinszweck (Reisen / Ausflüge) | Aufwand Aktivitäten |
| 5000 | Lohnaufwand | Personalaufwand |
| 6000 | Raumaufwand (Mieten) | Übriger Aufwand |
| 6100 | Ausgaben aus monatlichem Essen | Übriger Aufwand |
| 6200 | Fahrzeug- und Transportaufwand | Übriger Aufwand |
| 6300 | Sachversicherungen, Abgaben und Gebühren | Übriger Aufwand |
| 6400 | Energie- und Entsorgungsaufwand | Übriger Aufwand |
| 6500 | Büromaterial, Drucksachen, Fachliteratur | Übriger Aufwand |
| 6510 | Telefon, Internet, Porti | Übriger Aufwand |
| 6530 | Sekretariats-, Buchführungs- und Revisionsaufwand | Übriger Aufwand |
| 6540 | Entschädigungen und Spesen Vorstand | Übriger Aufwand |
| 6541 | Aufwand Vereinsversammlung | Übriger Aufwand |
| 6542 | Aufwand Vorstandssitzungen | Übriger Aufwand |
| 6570 | Informatik- und Internetaufwand | Übriger Aufwand |
| 6660 | Werbe- und Marketingaufwand | Übriger Aufwand |
| 6700 | Sonstiger Vereinsaufwand | Übriger Aufwand |
| 6800 | Abschreibungen und Wertberichtigungen | Abschreibungen |
| 6900 | Zinsaufwendungen | Finanzergebnis |
| 6940 | Spesen und Gebühren (Kontoführung) | Finanzergebnis |

Seed-Script: `scripts/seed_accounting_chart.py`. Beim ersten Start von `/accounting` prüfen ob Konten existieren — falls nicht, Hinweis «Kontenplan initialisieren» anzeigen.

## 7. Beleg-Upload

### 7.1 Wer kann hochladen

Jedes aktive Mitglied kann Belege einreichen. Schatzmeister und Admin zusätzlich auch direkt beim Buchungsanlegen.

### 7.2 Upload-Formular (Pre-Tagging)

Felder beim Beleg-Upload:
- **Datei** (Pflicht): Foto via Kamera (`<input type="file" accept="image/*,application/pdf" capture="environment">`) oder Datei-Upload. Hinweis: `capture` greift nur auf Mobilgeräten; am Desktop öffnet sich der Datei-Dialog.
- **Anzeige-Name** (optional): kurzer Name für die Beleg-Liste, zusätzlich zum langen Drive-Dateinamen (`Receipt.display_name`)
- **Event** (optional): Dropdown mit kommenden und vergangenen Events des laufenden Jahres
- **Kategorie-Vorschlag** (optional): Vereinfachte Dropdown-Liste der aktiven Ausgaben-Konten (Anzeige: Name, nicht Code)
- **Bestehende Buchung** (optional): Beleg direkt mit einer Buchung eines offenen Jahres verknüpfen → Beleg gilt sofort als «verbucht». Wird auch vom Buchungsdetail («Beleg erfassen») via `?booking=<id>` vorbelegt.
- **Kommentar** (optional): Freitext

Event, Kategorie und Kommentar sind **Vorschläge** für den Schatzmeister, keine Buchungsdaten.

### 7.3 Drive-Speicherung

Ordnerstruktur: `Buchhaltung/{Jahr}/`
Dateiname in Drive: `{YYYYMMDD}_{Kommentar-Prefix}_{OriginalDateiname}` (Kommentar-Prefix max. 30 Zeichen, sanitized)

Die App speichert `drive_file_id` und `drive_folder_id` in Postgres. Der Drive-Ordner `Buchhaltung/` wird beim ersten Upload eines Jahres automatisch angelegt falls nicht vorhanden.

### 7.4 Beleg-Status-Anzeige für Mitglied

Im eigenen Profil: Tabelle aller eingereichten Belege mit Status «Ausstehend» / «Verbucht am {Datum}».

## 8. Seitenstruktur und UI

### 8.1 `accounting/index.html` — Tab-Seite

Die Haupt-URL `/accounting` zeigt eine Tab-Seite (Muster: `templates/admin/merch/index.html`).

**Vor den Tabs** (gilt für alle Tabs):
- Jahres-Selektor (Dropdown, `form-field__select`)
- `dashboard-info-grid` mit drei statischen Kacheln: Saldo des Jahres | Offene Belege | Budget-Auslastung (%)

**Tabs**: Journal | Belege | Budget | Abschluss

**Journal-Tab**:
- `card card--filter tool-surface` mit `disclosure` (Filter: Konto, Richtung, Status) — Filter nur in diesem Tab
- `data-table`: Datum | Beschreibung | Konto | Betrag | Beleg-Icon | Aktionen

**Belege-Tab**:
- `card card--filter tool-surface` mit `disclosure` (Filter: Status, Event) — Filter nur in diesem Tab
- Liste: Uploader, Upload-Datum, Kategorie-Vorschlag, Event-Vorschlag, Kommentar, Aktionen

**Budget-Tab**:
- Tabelle: Konto | Soll | Ist | Abweichung — kein Filter (Jahr schon oben gewählt)
- Editierbar durch Schatzmeister/Admin direkt in der Tabelle

**Abschluss-Tab**:
- `billbro-workflow-block` mit drei Phasen: Offen → In Prüfung → Abgeschlossen
- Kontextueller Hinweistext (`billbro-workflow__hint`, `role="status"`) je nach Phase und Rolle (Schatzmeister vs. Revisor)
- Revisions-Kommentare als Kommentar-Liste unter dem Workflow-Block
- Action-Buttons: Schatzmeister «Zur Prüfung freigeben» / Revisor «Genehmigen»

Phase-Hinweistexte:

| Phase | Schatzmeister | Revisor |
|---|---|---|
| Offen | «Erfasse alle Buchungen und weise Belege zu. Sobald alles vollständig ist, gib das Jahr zur Prüfung frei.» | «Warte, bis der Schatzmeister das Jahr freigibt.» |
| In Prüfung | «Das Jahr ist gesperrt. Beantworte Kommentare des Revisors falls nötig.» | «Prüfe Journal und Budget, hinterlasse Kommentare bei Klärungsbedarf und bestätige das Jahr.» |
| Abgeschlossen | «Abschluss {Jahr} ist genehmigt und archiviert.» | «Abschluss {Jahr} ist genehmigt und archiviert.» |

### 8.2 Workflow-Seiten (eigene Seiten mit Schritt-Navigation)

**`accounting/receipt_upload.html`** — Beleg einreichen (alle Mitglieder):
- Schritt 1: Datei wählen + Pre-Tagging (Event, Kategorie-Vorschlag, Kommentar)
- Schritt 2: Vorschau + Bestätigen
- Muster: `cleanup-step-nav` mit Counter und Zurück/Weiter

**`accounting/booking.html`** — Buchung erfassen (Schatzmeister):
- Schritt 1: Beleg-Vorschau (falls aus Inbox) + Buchungsdaten (Betrag, Datum, Beschreibung)
- Schritt 2: Konto zuweisen
- Schritt 3: Bestätigen
- Muster: `cleanup-step-nav`

### 8.3 Info-Tile-Muster für KPIs

```html
<div class="dashboard-info-grid">
    <div class="dashboard-info-tile dashboard-info-tile--static">
        <span class="dashboard-info-tile__content">
            <span class="dashboard-info-tile__label">Saldo</span>
            <span class="dashboard-info-tile__value">
                <span class="dashboard-info-tile__line">CHF {{ saldo_chf }}</span>
            </span>
        </span>
    </div>
    ...
</div>
```

### 8.4 Hilfetext-Muster bei Formularfeldern

```html
<span class="form-field__hint">Betrag wird vom Schatzmeister geprüft und kann angepasst werden.</span>
```

## 9. Revisions-Workflow

Der gesamte Revisions-Workflow läuft im **Abschluss-Tab** von `accounting/index.html` — keine separate Workflow-Seite. Das Muster ist der BillBro-Workflow-Block aus `templates/events/detail.html`.

```
Schatzmeister: «Zur Prüfung freigeben» (Button im Abschluss-Tab)
       ↓
Status: 'in_review' — Buchungsjournal wird gesperrt
Benachrichtigung an Revisor (App-Notification via NotifierService)
       ↓
Revisor: Buchungen und Belege in App prüfen (Journal-Tab + Belege-Tab, read-only)
Revisor: Kommentare hinterlassen im Abschluss-Tab
       ↓
Schatzmeister: Kommentare beantworten / Korrekturen (wenn Jahr noch in_review)
       ↓
Revisor: «Genehmigen» (Button im Abschluss-Tab)
       ↓
Status: 'closed'
App generiert Revisorenbericht PDF → Upload in Drive ('Buchhaltung/{Jahr}/Revisorenbericht_{Jahr}.pdf')
Jahr vollständig gesperrt — keine Buchungen mehr möglich
```

### 9.1 Revisorenbericht-Inhalt (auto-generiert)

- Vereinsname, Geschäftsjahr, Datum der Bestätigung
- Sparkapital zu Jahresbeginn
- Erfolgsrechnung (Einnahmen / Ausgaben / Jahresergebnis) nach Kontengruppen
- Bestätigung: «Der unterzeichnende Revisor bestätigt, dass die Buchhaltung des Vereins Männliche Frohvollen für das Geschäftsjahr {Jahr} geprüft und für korrekt befunden wurde.»
- Name des Revisors, Datum

PDF-Generierung mit **`reportlab`** (pure Python, keine System-Abhängigkeiten, Railway-kompatibel). Implementiert in `backend/services/accounting_pdf.py`.

## 10. Statistik-Seite

Route: `GET /accounting/stats` (Schatzmeister / Revisor / Admin)

Separate Seite mit Auswertungen der Buchhaltungsdaten. Jahres-Selektor oben (gilt für alle Auswertungen ausser Jahresvergleich).

### 10.1 Auswertungen

**Saldo-Verlauf** (laufendes/gewähltes Jahr)
Linienkurve: kumulierter Saldo über die Monate des Jahres. Zeigt wann Mitgliederbeiträge eingehen und wann grosse Ausgaben anfallen. Datenbasis: alle Buchungen des Jahres, chronologisch summiert.

**Budget-Auslastung pro Kontengruppe** (gewähltes Jahr)
Fortschrittsbalken pro Kontengruppe: Ist-Wert / Budget-Betrag in CHF, plus Prozentzahl. Nur Gruppen mit Budget > 0. Keine Diagrammbibliothek nötig — reines CSS (`style="width: {{ pct }}%"`).

**Jahresvergleich** (alle verfügbaren Jahre)
Balkendiagramm: Einnahmen / Ausgaben / Ergebnis pro Jahr nebeneinander. Ideal für GV-Präsentation und Langzeittrend. Zeigt alle FiscalYears mit Status `closed` oder `in_review` plus laufendes Jahr.

**Ausgaben nach Kontengruppe** (gewähltes Jahr)
Donut-Chart: Anteil jeder Kontengruppe an den Gesamtausgaben. Gibt schnell Überblick worauf das Budget entfällt.

**Ergebnis-Übersicht** (alle Jahre)
Einfache Tabelle: Jahr | Einnahmen | Ausgaben | Ergebnis | Status. Keine Visualisierung — reine Zahlen für den Überblick.

**Mitgliederbeiträge** (gewähltes Jahr)
Liste welche Mitglieder im laufenden Jahr einen Beitrag (Konto 3000, 3015, 3020) gebucht haben. Für den Schatzmeister zum Nachfassen. Zeigt: Mitglied | Betrag | Datum. Nur Schatzmeister/Admin sichtbar.

### 10.2 Diagramm-Bibliothek

**Chart.js** via CDN (`<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js">`). Nur auf der Stats-Seite eingebunden — kein globaler Import. Budget-Auslastung via CSS-Balken (kein Chart.js nötig).

Datenpunkte werden als JSON im Template gerendert (`data-chart='{{ chart_data | tojson }}'`) und via vanilla JS initialisiert — kein separates JS-File nötig.

### 10.3 Template

`templates/accounting/stats.html` — Vorlage: `templates/events/index.html` (page-header, card-Struktur). Kein Tab (Stats ist eine eigene Seite, Link im Accounting-Index).

## 12. Export

PDF und CSV sind **Zusatz**, nicht primäre Arbeitsweise.

- **CSV-Export**: Alle Buchungen des gewählten Jahres, Semikolon-getrennt, UTF-8 mit BOM (Excel-kompatibel), Spalten: Datum;Beschreibung;Konto-Code;Konto-Name;Richtung;Betrag CHF
- **PDF-Jahresabschluss**: Erfolgsrechnung im gleichen Format wie Revisorenbericht, aber ohne Bestätigung — für Archiv oder externe Empfänger
- Download-Buttons in der Jahresübersicht sichtbar für Schatzmeister, Revisor, Admin

## 13. Payments-Vorbereitung (Phase 6)

Das Modell ist für spätere TWINT/ZKB-Integration vorbereitet:

- `Booking.payment_ref` (nullable String) nimmt externe Zahlungs-Referenzen auf (TWINT-UUID, ZKB-Transaktions-ID)
- Ein späterer Webhook (Stripe, RaiseNow oder ZKB Open Banking) kann `Booking`-Records automatisch anlegen und `payment_ref` setzen
- Kein n8n nötig — der Webhook-Handler kommt direkt als Flask-Route in Phase 6

ZKB Open Banking (via SIX bLink) als mögliche Basis für TWINT-Anfragen direkt aus der App: in Phase 6 evaluieren.

## 14. Kassen-Erweiterung (Backlog)

Heute: nur ZKB-Bankkonto. Falls künftig ein Festbetrieb mit Barkasse: ein zweites Konto-Objekt («Kasse») anlegen, Buchungen diesem Konto zuweisen. Das Modell unterstützt das bereits ohne Änderung.

## 15. AI/Automation — geprüft, Future

Aus STRATEGY_2026.md: Buchhaltung ist explizit als Kandidat für AI/Automation gelistet.

| Ansatz | Bewertung |
|---|---|
| Beleg-OCR (Betrag, Datum, Händler erkennen) | Future: optionaler API-Call zu Google Document AI oder OpenAI Vision. Datenmodell (`Receipt.ocr_data` JSON) ist vorbereitet. |
| Buchungssatz-Klassifikation | Future: aus OCR-Daten Konto-Vorschlag ableiten. Ersetzt Pre-Tagging durch Uploader. |
| Automatischer Buchungseingang aus Mail | Nicht geplant — n8n wurde bewusst verworfen. |
| ZKB-Kontoauszug-Import | Future: CSV-Import der ZKB-Transaktionen als Batch-Buchungsvorschläge. |

**Entscheidung MVP**: Kein AI-Einsatz. OCR und Klassifikation kommen wenn der Grundbetrieb stabil ist.

## 16. Routes-Übersicht

Neuer Blueprint `backend/routes/accounting.py`:

```
GET  /accounting                         → Tab-Index (Journal/Belege/Budget/Abschluss)
                                           ?year=<id>&tab=journal|belege|budget|abschluss
GET  /accounting/receipt/upload          → Beleg-Upload-Workflow (alle Mitglieder, Schritt 1–2)
POST /accounting/receipt/upload          → Beleg einreichen (Submit Schritt 2)
GET/POST /accounting/booking/new         → Buchungsworkflow (Schatzmeister, Schritt 1–3)
GET  /accounting/booking/<id>            → Buchungsdetail (Inline-Bearbeitung)
POST /accounting/booking/<id>/edit       → Buchung bearbeiten (Guard: Jahr muss 'open')
POST /accounting/booking/<id>/receipt    → Beleg zur Buchung anfügen
POST /accounting/year/<id>/submit        → Jahr zur Revision freigeben (Schatzmeister)
POST /accounting/year/<id>/approve       → Jahr bestätigen (nur Revisor)
POST /accounting/year/<id>/comment       → Revisions-Kommentar hinzufügen
GET  /accounting/export/<id>/csv         → CSV-Download
GET  /accounting/export/<id>/pdf         → PDF-Download
GET/POST /accounting/accounts            → Kontenplan verwalten (Admin)
POST /accounting/accounts/<id>/edit      → Konto bearbeiten (Admin)
GET  /accounting/receipt/<id>            → Beleg anzeigen / aus Drive herunterladen
```

Alle Accounting-Routes `@login_required`. Berechtigungen gemäss Sektion 5 pro Route prüfen via `_require_funktion(*funktionen)`.

Mitglied-eigene Beleg-Übersicht (im Member-Blueprint):
```
GET /member/receipts                     → Eigene eingereichte Belege mit Status
```

## 17. Decision Log

| Datum | Entscheid | Begründung |
|---|---|---|
| 2026-06-08 | Flask-Modul statt n8n | ~50 Buchungen/Jahr, eine Person als Schatzmeister — n8n-Overhead nicht gerechtfertigt |
| 2026-06-08 | E/A-Rechnung statt doppelter Buchführung | Schweizer Kleinverein unter CHF 500k, gesetzlich ausreichend, bewährtes Format seit 2021 |
| 2026-06-08 | Kontenplan aus Excel 2021–2026 übernehmen | 5 Jahre bewährt, Revisor kennt das Format |
| 2026-06-08 | Budget-Werte in App | Bisher im Excel gepflegt — gehört in die App für Budget-vs-Ist-Vergleich |
| 2026-06-08 | Drive als Beleg-Storage (`Buchhaltung/{Jahr}/`) | Konsistent mit Drive-Strategie; kollaborierbar, n8n-kompatibel falls später |
| 2026-06-08 | Zwei-Stufen-Flow: Einreichen (alle) → Buchen (Schatzmeister) | Spiegelt bisherigen WhatsApp-Workflow; Schatzmeister behält Kontrolle |
| 2026-06-08 | Pre-Tagging beim Upload | Uploader kennt den Kontext; spart Schatzmeister Nachfragen |
| 2026-06-08 | Foto-Funktion via `capture="environment"` | PWA, kein Native-Plugin nötig; funktioniert auf iOS und Android |
| 2026-06-08 | Vollständiger Revisions-Workflow in App | Kein Excel-Ping-Pong mehr; Revisor bestätigt digital, Bericht wird auto-generiert |
| 2026-06-08 | PDF/CSV als Zusatz, App-first | Primäre Arbeitsweise ist die App; Export nur für Archiv und externe Empfänger |
| 2026-06-08 | `payment_ref` nullable in Booking | Vorbereitung Phase 6 (TWINT/ZKB) ohne Umbau |
| 2026-06-08 | Beträge in Rappen als Integer | Kein Float-Rundungsproblem; Standard für CHF-Beträge |
| 2026-06-08 | OCR und AI auf Future gesetzt | Grundbetrieb zuerst; Datenmodell (`ocr_data` JSON) ist vorbereitet |
| 2026-06-08 | Kontenplan editierbar (Admin) | Kontenplan wächst über Jahre; muss nicht via Code-Deployment angepasst werden |
| 2026-06-10 | Kein Feature-Flag | Berechtigungslogik ersetzt Flag vollständig; einfacher |
| 2026-06-10 | reportlab statt weasyprint | Pure Python, keine System-Deps auf Railway (kein Cairo/Pango) |
| 2026-06-10 | FlaskForm + `backend/forms/accounting.py` | Konsistent mit `rating.py`-Muster; bei komplexem Modul separate Forms-Datei |
| 2026-06-10 | Generischer `_require_funktion(*funktionen)` | Ein Helper statt vieler; Admin kommt immer durch (wie im Rest der App) |
| 2026-06-10 | Drive-Unterordner aus Root ableiten | Keine neue Config-Variable; On-the-fly via DriveService |
| 2026-06-10 | Budget als separater Tab (Variante B) | Eigenständige Aufgabe (einmal/Jahr); Revisor soll direkt zur Budget-Ansicht |
| 2026-06-10 | Tab-basierter Index (Journal/Belege/Budget/Abschluss) | Konsistent mit Merch und Events; kein separater Revisions-Workflow-Screen |
| 2026-06-10 | Abschluss-Tab mit billbro-workflow-block | Bestehende Klassen, kein neues Muster nötig; phasenbewusster Hinweistext für jede Rolle |
| 2026-06-10 | Beleg-Upload + Buchung als Workflow-Seiten (cleanup-step-nav) | Geführte Mehrschritt-Abläufe mit bestehendem Schritt-Navigations-Muster |
| 2026-06-10 | Seeding Option A | Kontenplan + FiscalYears 2021–2026 + Budget 2025/2026 aus Excel; keine historischen Einzelbuchungen |

## 18. Offene Punkte

- **Kassen-Konto**: Noch kein Bedarf. Wenn Festbetrieb mit Barkasse kommt, zweites Konto-Objekt anlegen — Modell unterstützt das.
- **ZKB-CSV-Import**: Manueller Import des Kontoauszugs als Buchungsvorschläge wäre nützlich (ZKB-Format bekannt aus `vorlagen_buchhaltung/`). Future Consideration für Phase 4b oder Phase 6.
- **TWINT/ZKB Open Banking**: Tiefere Evaluation in Phase 6. `payment_ref` ist schon vorbereitet.
- **Merch-Verknüpfung**: `Receipt.suggested_event_id` ist vorhanden; eine `suggested_merch_order_id` kann bei Phase 10 ergänzt werden ohne Modell-Bruch.
- **Datenschutz**: Buchungen und Belege enthalten Finanzdaten von Mitgliedern. Zugriff strikt nach Sektion 5. `vorlagen_buchhaltung/` ist in `.gitignore`.
- **Framework-Frage**: React + Tailwind vs. Flask/Jinja2 ist als Open Decision in STRATEGY_2026.md festgehalten. Accounting-Modul wird zunächst in Jinja2 umgesetzt — ein späterer Frontend-Umbau betrifft Routes und Templates, nicht das Datenmodell.

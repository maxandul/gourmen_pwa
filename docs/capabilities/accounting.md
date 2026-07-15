# Capability: Buchhaltung

> **Zweck**: Das Buchhaltungsmodul bildet die gesamte Vereinsfinanzverwaltung in der PWA ab — Buchungsjournal, Budget, Belegverwaltung, Jahresabschluss und Revisionsprozess. Ziel ist eine vollständig app-basierte Arbeitsweise: kein Excel-Ping-Pong mehr, kein manuelles Zusammensuchen von Belegen, kein separater Revisoren-Workflow ausserhalb der App.
>
> **Status**: Phase 4 (Grundmodul) + Phase 4b (ZKB-Import, Offene Posten, BillBro-Zahlweg, Sektion 11) implementiert — Merge + Prod-Migration/Seed offen. **Owner**: Andreas. **Stand**: 2026-07-13.
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
| Schatzmeister | «Ich lade den monatlichen ZKB-Kontoauszug (CSV) hoch und bekomme alle neuen Transaktionen als Buchungsvorschläge — mit erkannten Mitgliedern, Konten und offenen Posten.» |
| Schatzmeister | «Ich sehe pro Mitglied, welche Beträge (Beiträge, Essensanteile, Merch) noch offen sind und was wann bezahlt wurde.» |
| Mitglied | «Ich sehe auf dem Dashboard meine offenen Posten; nach Eingang und Verbuchung meiner Zahlung stehen sie auf 'beglichen'.» |
| Mitglied | «Wenn ich eine Event-Rechnung privat bezahlt habe, bestätige ich in der App die Eingänge der Anteile der anderen.» |
| Organisator | «Beim BillBro-Start gebe ich an, ob mit dem Vereinskonto bezahlt wird oder welches Mitglied die Rechnung übernimmt.» |

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

## 6. Kontenplan (Seed) — verschlankt 2026-07

Der ursprüngliche Kontenplan stammte aus den PDF-Erfolgsrechnungen (veraltete Vorlage) und enthielt viele Konten, die nie eine Buchung gesehen haben — diese sind entfernt. Massgebend für die Verschlankung: die real bebuchten Kategorien aus den ZKB-Kontoauszügen 2021–2026 und die Kostenstellen-Logik des Schatzmeisters in `vorlagen_buchhaltung/Vereinsfinanzen_2026.xlsx` (Sheet «Konto»). Die Kostenstellen dort werden nicht 1:1 übernommen, sondern auf folgende Konten abgebildet. Kontonummern-Schema bleibt (3xxx Einnahmen, 4xxx–6xxx Ausgaben); im UI werden nur die Namen angezeigt.

### Einnahmen

| Code | Name | Gruppe | Herkunft / Beispiele |
|---|---|---|---|
| 3000 | Mitgliederbeiträge | Mitgliederbeiträge | Monatsraten und Jahresbeträge (Sektion 11.7) |
| 3100 | Spenden und Sponsoring | Übrige Einnahmen | Mehrzahlungen als Spende deklariert |
| 3310 | Essensanteile von Mitgliedern | Essen | Rücküberweisungen nach Zahlung mit Vereinskonto («Einzahlung MG für Essen») |
| 3315 | Aufgerundete Essensanteile | Essen | Ausserordentliche Einnahme: Differenz bei aufgerundeten Essensanteilen (Sektion 11.5) |
| 3400 | Merch-Zahlungen von Mitgliedern | Merch | Zahlungen der Mitglieder für Merch-Bestellungen |
| 3410 | Aufgerundete Merchbestellungen | Merch | Ausserordentliche Einnahme: Überzahlung bei Merch (z.B. bewusste Spende beim Rückzahlungsverzicht) |
| 3500 | Einnahmen aus Reisen | Reisen | Kostenbeteiligungen, Rückerstattungen von Anbietern zu Reisen |
| 3620 | Sonstige Einnahmen (Bussen, Rückerstattungen) | Übrige Einnahmen | Bussen, sonstige Gutschriften |

### Ausgaben

| Code | Name | Gruppe | Herkunft / Beispiele |
|---|---|---|---|
| 4500 | Reisen und Ausflüge | Reisen | Hotel, Transport, Essen, Erlebnis auf Vereinsreisen (Kartenzahlungen und eBanking) |
| 6100 | Essen mit Vereinskonto | Essen | Restaurant-Zahlung per Gourmen-Karte (Monatsessen, «Essen für Buchhaltung») |
| 6541 | Generalversammlung | Vereinsanlässe | Raum, Snacks, Verpflegung GV |
| 6542 | Vorstandssitzungen | Vereinsanlässe | Verpflegung Vorstand |
| 6570 | IT, Telefon und Internet | Übriger Aufwand | Hosting, Sunrise, Domains |
| 6650 | Merch-Einkauf bei Lieferanten | Merch | Lieferantenrechnungen der Bestellrunden |
| 6660 | Marketing und Merch-Beitrag des Vereins | Merch | Vereinsbeitrag an Merch der Mitglieder, Werbematerial |
| 6700 | Sonstiger Vereinsaufwand | Übriger Aufwand | Alles ohne eigenes Konto (inkl. Kleinst-Abschreibungen) |
| 6710 | Rückzahlungen an Mitglieder | Übriger Aufwand | Rücküberweisungen vom Vereinskonto (Rabattweitergabe, Auslagenersatz) |
| 6940 | Kontoführung und Kartengebühren | Finanzergebnis | ZKB Kontoführung, Debit-Karten-Gebühren |

Feinere Unterteilung (z.B. Reisen nach Hotel/Transport/Essen/Erlebnis wie in der Excel des Schatzmeisters) ist bei Bedarf jederzeit über die Kontenplan-Verwaltung möglich; das Budget wird auf Gruppenebene ausgewertet. Die Merch-Gruppe wird in der Budget-Ansicht netto ausgewiesen (Sektion 11.8).

Seed-Script: `scripts/seed_accounting_chart.py` — legt die Konten oben an, benennt bestehende Konten aus dem alten Seed um (3310, 6100, 6570, 6660), entfernt Alt-Konten ohne Buchungen, setzt `membership_fee_rappen`, Budget 2025/2026, Ist-Sammelbuchungen 2022–2025 (aus Erfolgsrechnung, eine Buchung pro Konto/Jahr mit `payment_ref=SEED-IST-…`) und Beitrags-Claims für das offene Jahr. Lokale ZKB-CSVs unter `vorlagen_buchhaltung/` werden optional als pending Import eingelesen; 2026-Einzelbuchungen entstehen über den Import-Review, nicht als Seed. Beim ersten Start von `/accounting` prüfen ob Konten existieren — falls nicht, Hinweis «Kontenplan initialisieren» anzeigen.

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

## 11. ZKB-Kontoauszug-Import und Offene Posten (Refokus 2026-07, Phase 4b)

> **Kontext**: Die hauptsächliche Unterstützung des Buchhaltungsmoduls liegt beim monatlichen CSV-Import des ZKB-Kontoauszugs. Fast alle Vereinsbuchungen laufen über das ZKB-Konto — der Import ist damit die primäre Buchungsquelle, nicht die manuelle Erfassung. Referenz-Dateien: `vorlagen_buchhaltung/Kontoauszug 2025.csv` und `Kontoauszug 2026.csv` (echte Exporte aus der ZKB-App). Die aktuelle Kontoführung des Schatzmeisters (`vorlagen_buchhaltung/Vereinsfinanzen_2026.xlsx`, Sheet «Konto» und «Jahresabschluss») liefert die Kostenstellen-Logik und die aktuellen Zahlen — sie muss nicht 1:1 übernommen werden, ist aber die Ideenquelle für den verschlankten Kontenplan (Sektion 6).

### 11.1 CSV-Format (ZKB-App-Export)

Header:

```
"Datum";"Buchungstext";"Whg";"Betrag Detail";"ZKB-Referenz";"Referenznummer";"Belastung CHF";"Gutschrift CHF";"Valuta";"Saldo CHF";"Zahlungszweck";"Details"
```

Eigenschaften und Parsing-Regeln:

- Semikolon-getrennt, alle Felder in Anführungszeichen; Datumsformat `DD.MM.YYYY`; Beträge mit Punkt als Dezimaltrenner. Encoding beim Einlesen tolerant behandeln (UTF-8 mit/ohne BOM und cp1252 versuchen).
- Neueste Zeile zuoberst. Monatliche Exporte können sich mit früheren Importen überlappen → **Dedup über `ZKB-Referenz`** (eindeutig pro Transaktion).
- **Sammelbuchungen**: Zeilen wie `"Belastungen eBanking (7)"` haben Detail-Zeilen direkt darunter mit **leerem Datum**, Gegenpartei im `Buchungstext`, Betrag in `Betrag Detail` (+ `Whg`) und Verwendungszweck in der `Zahlungszweck`-Spalte (Position variiert — die Detail-Zeilen haben keine eigene ZKB-Referenz). Detail-Zeilen werden dem Parent zugeordnet (Schlüssel: Parent-Referenz + Laufindex) und einzeln verbuchbar gemacht.
- **Fremdwährung**: Detail-Beträge können in EUR sein, während der Parent-Betrag in CHF belastet wird (z.B. `"Belastungen eBanking (2), EUR 1762.25"` → CHF 1626.01). Der CHF-Betrag wird proportional auf die Detail-Zeilen verteilt; im Review-Schritt manuell korrigierbar.
- `Gutschrift CHF` = Einnahme, `Belastung CHF` = Ausgabe. `Auftraggeber`-Name und -Adresse stehen im `Buchungstext` (Prefix `Gutschrift Auftraggeber:`) bzw. in `Details`.

### 11.2 Datenmodell (neu, Phase 4b)

```python
BankStatementImport:
    id, fiscal_year_id FK, filename, imported_by FK Member, imported_at,
    row_count, new_count, duplicate_count

BankTransaction:
    id, import_id FK, zkb_ref String UNIQUE nullable  # NULL bei Detail-Zeilen
    parent_id FK BankTransaction nullable             # Detail-Zeile einer Sammelbuchung
    line_key String UNIQUE                            # zkb_ref bzw. '{parent_ref}#{index}' für Dedup
    booked_date Date, valuta Date nullable
    amount_rappen Integer, direction Enum('in','out')
    currency String(3) default 'CHF', amount_original String nullable  # z.B. 'EUR 922.25'
    buchungstext String, zahlungszweck String nullable, details String nullable
    status Enum('pending', 'booked', 'ignored')
    booking_id FK Booking nullable                    # gesetzt nach Verbuchung
    suggested_account_id FK Account nullable          # Auto-Vorschlag
    suggested_member_id FK Member nullable            # Auto-Vorschlag via Alias
    raw_json JSON                                     # Original-Zeile

MemberBankAlias:
    id, member_id FK, alias_text String  # normalisierter Auftraggeber-Name
    # Namen/Adressen im CSV stimmen nicht zwingend 1:1 mit der Mitglieder-DB überein
    # (Zweitnamen, GROSSSCHREIBUNG, Umlaut-Transkription «Mueller»/«Müller», alte Adressen).
    # Beim ersten manuellen Zuordnen wird der Alias gelernt; künftige Importe matchen automatisch.

MemberClaim (Forderung / offener Posten):
    id, member_id FK                                  # Schuldner
    creditor_member_id FK Member nullable             # NULL = Verein (läuft über Buchhaltung);
                                                      # gesetzt = privates Auslegen (läuft NICHT über Buchhaltung)
    claim_type Enum('MITGLIEDERBEITRAG', 'ESSENSANTEIL', 'MERCH', 'REISE', 'SONSTIGES')
    fiscal_year_id FK nullable, event_id FK nullable, merch_order_id FK nullable
    expected_rappen Integer, paid_rappen Integer default 0
    status Enum('offen', 'teilweise', 'beglichen', 'erlassen')
    settled_at DateTime nullable, created_at, note String nullable
```

Zusätzlich auf bestehenden Modellen:

- `Booking.bank_transaction`-Rückreferenz (via `BankTransaction.booking_id`) — Buchungen aus dem Import sind als solche erkennbar.
- `Event`: `bill_paid_by` Enum(`'vereinskonto'`, `'mitglied'`) nullable + `bill_payer_member_id` FK nullable (Sektion 11.6).
- `FiscalYear`: `membership_fee_rappen` Integer nullable (Jahresbeitrag pro Mitglied, 2026: CHF 840).

### 11.3 Import-Ablauf (Schatzmeister/Admin)

```
1. Upload: CSV-Datei hochladen (neuer Tab «Import» im Accounting-Index oder Workflow-Seite)
2. Parsing: Zeilen einlesen, Sammelbuchungen aufsplitten, Beträge in Rappen wandeln
3. Dedup: bereits importierte line_keys überspringen (Zähler «X neu, Y bereits vorhanden»)
4. Auto-Vorschläge pro Transaktion:
   - Konto-Vorschlag (Regeln, Sektion 11.4)
   - Mitglied-Vorschlag (Alias-Matching, Sektion 11.2)
   - Offene-Posten-Matching: passt eine Gutschrift zu einer offenen MemberClaim?
5. Review-Screen: Liste aller pending-Transaktionen; pro Zeile Konto/Mitglied/Event/Claim
   bestätigen oder anpassen; einzelne Zeilen ignorieren (z.B. interne Umbuchungen)
6. Verbuchen: pro bestätigter Zeile eine Booking anlegen (payment_ref = zkb_ref),
   Claims fortschreiben (Sektion 11.5), Status → 'booked'
```

Der Import ist idempotent: dieselbe Datei mehrfach hochladen erzeugt keine Duplikate. Teilweise verarbeitete Importe können später weiterbearbeitet werden (pending-Transaktionen bleiben in der Import-Inbox).

**Import löschen**: Solange noch keine Zeile verbucht ist, kann der Schatzmeister den gesamten Import löschen (falsche Datei / erneuter Test-Upload). Dabei werden pending- und ignored-Transaktionen entfernt und die Dedup-Schlüssel (`line_key`) freigegeben — derselbe CSV kann danach erneut importiert werden. Sobald mindestens eine Zeile verbucht ist, ist Löschen gesperrt (verbuchte Bookings bleiben unangetastet).

### 11.4 Auto-Matching-Regeln (Konto-Vorschlag)

| Muster | Vorschlag |
|---|---|
| `Kontoführung`, `Gebühr Kontoführung`, `Gebühr ZKB Visa Debit Card`, `Jahresgebühr … Debit Card` | Konto «Kontoführung und Kartengebühren», ohne Mitglied |
| Gutschrift + Mitglied erkannt + offener Beitrag (Claim `MITGLIEDERBEITRAG`) | Konto «Mitgliederbeiträge» + Claim-Zuordnung |
| Gutschrift + Mitglied erkannt + offener Essensanteil (Claim `ESSENSANTEIL`, Betrag ≈) | Konto «Essensanteile von Mitgliedern» + Claim-Zuordnung |
| Gutschrift + Mitglied erkannt + offene Merch-Forderung | Konto «Merch-Zahlungen von Mitgliedern» + Claim-Zuordnung |
| `Einkauf ZKB Visa Debit Card` + Datum ≈ Event mit `bill_paid_by = vereinskonto` | Konto «Essen mit Vereinskonto» + Event-Zuordnung |
| Belastung an erkanntes Mitglied | Konto «Rückzahlungen an Mitglieder» |
| Sonst | kein Vorschlag — manuell im Review |

Vorschläge sind immer nur Vorschläge; der Schatzmeister bestätigt jede Zeile. Bestätigte Mitglied-Zuordnungen erzeugen/aktualisieren `MemberBankAlias` (lernendes Matching).

### 11.5 Forderungen und Offene-Posten-Übersicht

`MemberClaim` bildet ab, wer dem Verein (oder einem auslegenden Mitglied) wieviel schuldet. Quellen:

- **Mitgliederbeiträge** (Sektion 11.7): pro Mitglied und Jahr eine Claim über den Jahresbeitrag.
- **BillBro-Essensanteile** (Sektion 11.6): wenn mit dem Vereinskonto bezahlt wurde, pro teilnehmendem Mitglied eine Claim über den berechneten Anteil.
- **Merch-Bestellungen** (Sektion 11.8): pro Bestellung eine Claim über den Mitglieder-Preis.
- **Reisen** (Sektion 11.9): optional, z.B. Kostenbeteiligungen.

Verbuchung von Zahlungseingängen gegen Claims:

- Zahlungen können **gesplittet** eingehen (z.B. Beitrag in Monatsraten) → `paid_rappen` kumuliert, Status `offen` → `teilweise` → `beglichen`.
- **Aufrunden**: Zahlt ein Mitglied mehr als die offene Forderung, wird die Differenz als **ausserordentliche Einnahme** verbucht — Konto «Aufgerundete Essensanteile» bzw. «Aufgerundete Merchbestellungen» (Sektion 6). Die Claim gilt als beglichen.
- Nach Verbuchung sieht das Mitglied den Posten auf dem Dashboard als «beglichen».

**Übersicht in der Buchhaltung** (neuer Tab «Offene Posten»): pro Mitglied alle offenen und beglichenen Posten — welcher Zahlungsausgang vom Vereinskonto noch offen ist, wieviel wann bereits bezahlt wurde; dasselbe für die erwarteten Mitgliederbeiträge. Filter: Typ, Status, Mitglied.

### 11.6 BillBro-Integration (Zahlweg)

Am Anfang des BillBro-Workflows (beim Organisator) gibt es neu die Angabe, **wie die Rechnung bezahlt wird**:

- **Vereinskonto** (`bill_paid_by = 'vereinskonto'`): Nach Abschluss der Anteilsberechnung entsteht pro teilnehmendem Mitglied eine `MemberClaim` (Typ `ESSENSANTEIL`, Gläubiger = Verein). Die Kartenzahlung erscheint später im ZKB-Export (Konto «Essen mit Vereinskonto»), die Rücküberweisungen der Mitglieder werden per Import den Claims zugeordnet. Aufgerundete Beträge → «Aufgerundete Essensanteile» (Beispiel: Memuzin 2025 — Zahlung CHF 700 mit Vereinskarte, Rückzahlungen 677.40 in Anteilen von 82.00–92.00). Nach Zahlungseingang und Verbuchung wechselt der offene Betrag auf dem Dashboard des Mitglieds auf «beglichen».
- **Mitglied zahlt** (`bill_paid_by = 'mitglied'` + `bill_payer_member_id`): Ein teilnehmendes Mitglied wird als Zahler zugewiesen; die anderen überweisen ihre Anteile direkt an dieses Mitglied. **Läuft nicht über die Vereinsbuchhaltung** — es entstehen Claims mit `creditor_member_id` = Zahler, ohne Bookings. Das zahlende Mitglied bestätigt die Eingänge in der App (pro Teilnehmer «erhalten» markieren); die Schuldner sehen den Status auf ihrem Dashboard.

### 11.7 Mitgliederbeiträge (Soll-Stellung und Splittung)

- Der Jahresbeitrag pro Mitglied ist pro Geschäftsjahr hinterlegt (`FiscalYear.membership_fee_rappen`, 2026: CHF 840). **Beitragssoll des Jahres = Anzahl aktive Mitglieder × Jahresbeitrag.**
- Beim Eröffnen des Geschäftsjahres wird pro aktivem Mitglied eine `MemberClaim` (Typ `MITGLIEDERBEITRAG`) über den Jahresbeitrag erzeugt; der Betrag ist pro Mitglied überschreibbar (Sonderfälle).
- **Splittung**: Nach aktueller Bestimmung kann der Beitrag bis Ende Juni des laufenden Jahres als Gesamtbetrag oder in 6 gleichen Monatsraten beglichen werden. Diese Regel existierte nur, um dem Schatzmeister Verbuchungsaufwand zu ersparen — mit automatischer Verbuchung über die App sind **beliebige Splittungen** unproblematisch. Das Modell schreibt deshalb keine Raten vor: jeder Zahlungseingang reduziert die offene Forderung (Sektion 11.5).
- Die reale Zahlungspraxis aus den Kontoauszügen (monatlich 50/70/98, Jahresbeträge 600/840, Nachzahlungen 240) wird damit vollständig abgedeckt.

### 11.8 Merch-Integration

Ablauf: Der Marketingchef eröffnet eine Bestellrunde mit **Listenpreis** → Mitglieder bestellen → Marketingchef bestellt bei den Lieferanten und kennt dann den **effektiven Preis** → Rechnung wird mit dem Vereinskonto beglichen und erscheint im ZKB-Export.

- Lieferanten-Zahlung: Konto «Merch-Einkauf bei Lieferanten» (Import, Zuordnung zur Bestellrunde).
- Mitglieder-Zahlungen: pro `MerchOrder` eine `MemberClaim` (Typ `MERCH`) über den Mitglieder-Preis; Eingänge via Import zuordnen. Überzahlung → «Aufgerundete Merchbestellungen».
- Rückzahlungen an Mitglieder (z.B. Rabattweitergabe wie im Mai 2026) → Konto «Rückzahlungen an Mitglieder», reduziert bzw. schliesst die Claim.
- Es gibt ein **Budget für Merch-Beiträge des Vereins** an die Mitglieder: in der Budget-Ansicht wird die Kontengruppe «Merch» **netto** ausgewiesen (Ausgaben − Mitglieder-Einnahmen) und gegen das Budget gestellt.

### 11.9 Reisen (Vereinsausflüge)

- Der Reisekommissar erfasst eine **Vorab-Buchung**, wenn er z.B. ein Hotel bucht — den Rechnungsbeleg entweder sofort oder später. Kommt danach der ZKB-Eintrag per Import, wird er der bestehenden Buchung zugeordnet (Betrag/Datum-Matching im Review) statt doppelt verbucht.
- Vergisst er die Vorab-Erfassung, entsteht die Buchung erst beim CSV-Import — beides ist gültig.
- Für Reisen gibt es ein **Budget** (Kontengruppe «Reisen», Sektion 6); der Budget-Wert wird auf Gruppenebene ausgewiesen.

### 11.10 Neue Event-Kategorie: «Essen für Buchhaltung»

Neuer `EventType.ESSEN_BUCHHALTUNG`:

- Läuft wie die Vorstandssitzung **ohne GGL-Teile** (kein Schätzspiel, keine Rangliste, keine Punkte), aber mit `audience = ALL` — offen für alle Mitglieder.
- Zweck: auf Reisen oder bei sonstigen Ad-hoc-Essen mit der Vereinskarte zahlen zu können und die ZKB-Einträge später über die App dem Event (und den Teilnehmer-Anteilen) zuzuordnen.
- Kein 3-Wochen-RSVP-Reminder (Ad-hoc-Charakter); BillBro-Anteilsberechnung inkl. Zahlweg-Angabe (Sektion 11.6) verfügbar.

### 11.11 Budget-Vorschlag bei Jahreseröffnung

Wenn ein neues Geschäftsjahr eröffnet wird, schlägt die App das Budget pro Konto vor:

- **Mitgliederbeiträge**: Anzahl aktive Mitglieder × Jahresbeitrag (`membership_fee_rappen`).
- **Übrige Konten**: Ist-Werte des Vorjahres (gerundet auf CHF 10).
- Alle Vorschläge sind editierbar, bevor sie gespeichert werden (Budget-Tab).

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
| ZKB-Kontoauszug-Import | **Kern-Feature (Refokus 2026-07)** — Sektion 11, Umsetzung Phase 4b. Regelbasiertes Matching, kein AI. |

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

Neu in Phase 4b (Sektion 11):
```
GET/POST /accounting/import              → ZKB-CSV hochladen + Import-Historie
GET  /accounting/import/<id>/review      → Review-Screen (pending-Transaktionen zuordnen)
POST /accounting/import/<id>/delete      → Import löschen (nur ohne verbuchte Zeilen; freigibt Dedup)
POST /accounting/import/tx/<id>/book     → Transaktion verbuchen (Konto/Mitglied/Event/Claim)
POST /accounting/import/tx/<id>/ignore   → Transaktion ignorieren
GET  /accounting/claims                  → Offene-Posten-Übersicht (Tab, Filter: Typ/Status/Mitglied)
POST /accounting/claims/<id>/settle      → Claim manuell abschliessen/erlassen
POST /billbro/<event_id>/payment_method  → Zahlweg setzen (Vereinskonto / Mitglied)
POST /billbro/<event_id>/confirm_payment/<member_id> → Privatzahler bestätigt Eingang
GET  /member/claims (bzw. Dashboard)     → Eigene offene Posten mit Status
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
| 2026-07-13 | **Refokus: ZKB-CSV-Import als Kern-Workflow** | Fast alle Buchungen laufen über das ZKB-Konto; monatlicher Export aus der ZKB-App ist die primäre Buchungsquelle, manuelle Erfassung der Sonderfall |
| 2026-07-13 | Kontenplan verschlankt | Alte PDF-Vorlage enthielt nie bebuchte Konten; neue Liste orientiert sich an real bebuchten Kategorien und den Kostenstellen aus `Vereinsfinanzen_2026.xlsx` |
| 2026-07-13 | `MemberClaim` als Offene-Posten-Modell | Beiträge, Essensanteile, Merch und Reisen einheitlich als Forderungen; Teilzahlungen und Aufrundungen (→ ausserordentliche Einnahme) abgedeckt |
| 2026-07-13 | `MemberBankAlias` für Mitglied-Matching | CSV-Namen/Adressen stimmen nicht 1:1 mit der DB überein (Zweitnamen, Umlaute, Umzüge); lernendes Alias-Matching statt fixer Regeln |
| 2026-07-13 | BillBro-Zahlweg (Vereinskonto vs. Mitglied) | Privat ausgelegte Rechnungen laufen nicht über die Vereinsbuchhaltung; Bestätigung der Eingänge durch das auslegende Mitglied |
| 2026-07-13 | Beitrags-Splittung frei | 6-Monatsraten-Regel existierte nur wegen manuellem Verbuchungsaufwand; mit App-Verbuchung sind beliebige Teilzahlungen möglich |
| 2026-07-13 | Neuer EventType `ESSEN_BUCHHALTUNG` | Ad-hoc-Essen mit Vereinskarte (z.B. auf Reisen) ohne GGL, offen für alle — für saubere ZKB-Zuordnung |
| 2026-07-13 | Budget-Vorschlag bei Jahreseröffnung | Mitgliederbeiträge = aktive Mitglieder × Jahresbeitrag; übrige Konten = Vorjahres-Ist; alles editierbar |

## 18. Offene Punkte

- **Kassen-Konto**: Noch kein Bedarf. Wenn Festbetrieb mit Barkasse kommt, zweites Konto-Objekt anlegen — Modell unterstützt das.
- **ZKB-CSV-Import**: ~~Future Consideration~~ → **Kern-Feature**, spezifiziert in Sektion 11, Umsetzung in Phase 4b (`docs/initiatives/workspace-railway/PHASE_04B_ACCOUNTING_BANK_IMPORT.md`).
- **TWINT/ZKB Open Banking**: Tiefere Evaluation in Phase 6. `payment_ref` ist schon vorbereitet.
- **Merch-Verknüpfung**: `Receipt.suggested_event_id` ist vorhanden; eine `suggested_merch_order_id` kann bei Phase 10 ergänzt werden ohne Modell-Bruch.
- **Datenschutz**: Buchungen und Belege enthalten Finanzdaten von Mitgliedern. Zugriff strikt nach Sektion 5. `vorlagen_buchhaltung/` ist in `.gitignore`.
- **Framework-Frage**: React + Tailwind vs. Flask/Jinja2 ist als Open Decision in STRATEGY_2026.md festgehalten. Accounting-Modul wird zunächst in Jinja2 umgesetzt — ein späterer Frontend-Umbau betrifft Routes und Templates, nicht das Datenmodell.

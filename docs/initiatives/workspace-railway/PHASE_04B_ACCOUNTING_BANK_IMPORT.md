# Phase 4b – ZKB-Import und Offene Posten (Buchhaltung Refokus)

**Status**: done (Code; Merge + Prod-Migration/Seed offen)  
**Aufwand**: ~1–2 Wochen  
**Branch**: `phase/04b-workspace-bank-import`  
**Spec**: `docs/capabilities/accounting.md` Sektion 11 (autoritativ — bei Konflikten gewinnt das Capability-Doc)

## Ziel

Phase 4 hat das Buchhaltungs-Grundmodul geliefert (Journal, Belege, Budget, Revision, Export). Der Fokus war aber nicht ganz richtig gesetzt: Die **hauptsächliche Unterstützung** des Moduls ist der **monatliche CSV-Import des ZKB-Kontoauszugs**. Fast alle Vereinsbuchungen laufen über das ZKB-Konto — der Import ist die primäre Buchungsquelle, die manuelle Erfassung der Sonderfall.

Phase 4b liefert:

1. **ZKB-CSV-Import** mit Dedup, Sammelbuchungs-Splitting, Auto-Vorschlägen und Review-Screen
2. **Offene Posten** (`MemberClaim`): Mitgliederbeiträge, BillBro-Essensanteile, Merch, Reisen — mit Teilzahlungen, Aufrundungs-Verbuchung und Übersicht pro Mitglied
3. **BillBro-Zahlweg**: Vereinskonto vs. privat auslegendes Mitglied (inkl. Eingangs-Bestätigung durch den Privatzahler)
4. **Kontenplan-Verschlankung** (neuer Seed, Alt-Konten-Cleanup)
5. **Neue Event-Kategorie** «Essen für Buchhaltung» (`ESSEN_BUCHHALTUNG`)
6. **Budget-Vorschlag** bei Jahreseröffnung (Mitgliederbeiträge = aktive Mitglieder × Jahresbeitrag; Rest = Vorjahres-Ist)

## Pre-Conditions

- Phase 4 gemergt und in Production (Migrationen `e1a2c7b4d905` + Seed gelaufen)
- Branch `phase/04b-workspace-bank-import` von `master` erstellt
- Referenz-CSVs lokal vorhanden: `vorlagen_buchhaltung/Kontoauszug 2025.csv`, `Kontoauszug 2026.csv` (echte ZKB-App-Exporte, **niemals committen**)

## Pre-Flight (Agent liest zuerst)

```
1. AGENTS.md
2. docs/capabilities/accounting.md          ← Sektion 6 (neuer Kontenplan) + Sektion 11 (Import/Claims) vollständig
3. docs/initiatives/workspace-railway/PHASE_04_ACCOUNTING.md  ← UI-Patterns, Template-Vorlagen, Tabu-Liste (gelten weiter)
4. docs/ARCHITECTURE.md / CONVENTIONS.md / DOMAIN.md / UI.md
5. backend/models/accounting.py             ← bestehende Models
6. backend/services/accounting.py           ← bestehender Service
7. backend/routes/billbro.py + templates/events/detail.html   ← BillBro-Workflow (für Zahlweg-Integration)
8. backend/models/event.py                   ← EventType/Audience-Muster (Vorstandssitzung als Vorlage)
9. vorlagen_buchhaltung/Kontoauszug 2025.csv + 2026.csv       ← echtes Format inkl. Sonderfälle
```

## Wichtige Format-Sonderfälle (aus den echten CSVs)

- **Dedup**: `ZKB-Referenz` ist der eindeutige Schlüssel; monatliche Exporte überlappen sich.
- **Sammelbuchungen**: `"Belastungen eBanking (7)"` → Detail-Zeilen darunter mit leerem Datum, Betrag in `Betrag Detail`, Gegenpartei im `Buchungstext`, Zweck in der `Zahlungszweck`-Spalte, **ohne eigene ZKB-Referenz** → `line_key = '{parent_ref}#{index}'`.
- **Fremdwährung**: Parent in CHF, Details in EUR (`"Belastungen eBanking (2), EUR 1762.25"` → CHF 1626.01) → CHF proportional verteilen, im Review korrigierbar.
- **Namens-Varianten**: `Roman Müller` vs. `Roman Mueller`, `DAVID NUNZIO CATALDO` (Zweitname, Grossschreibung), Adress-Wechsel im Jahresverlauf → `MemberBankAlias`-Matching, beim ersten manuellen Zuordnen lernen.
- **Beitragsmuster**: Monatsraten (50/70/98), Jahresbeträge (600/840), Nachzahlungen (240), Zahlungszweck mal aussagekräftig («JAHRESBEITRAG»), mal leer.

## Implementierungs-Reihenfolge

### Commit 1 – Migration: Import, Claims, Aliase, Event/FiscalYear-Erweiterungen

Neue Tabellen: `bank_statement_imports`, `bank_transactions`, `member_claims`, `member_bank_aliases`  
Erweiterungen: `events.bill_paid_by` + `events.bill_payer_member_id`, `fiscal_years.membership_fee_rappen`, neuer Enum-Wert `ESSEN_BUCHHALTUNG` in `eventtype`.  
Modelle gemäss Spec Sektion 11.2. Alembic-Migration in eigenem Commit (up + down).

### Commit 2 – Seed-Update: Kontenplan verschlanken

`scripts/seed_accounting_chart.py` gemäss Spec Sektion 6:
- Neue/umbenannte Konten anlegen (3000, 3100, 3310, 3315, 3400, 3410, 3500, 3620, 4500, 6100, 6541, 6542, 6570, 6650, 6660, 6700, 6710, 6940)
- Alt-Konten **ohne Buchungen** deaktivieren oder löschen (nie bebuchte Konten aus der PDF-Vorlage)
- Budget-Werte auf die neuen Codes remappen
- `FiscalYear.membership_fee_rappen` setzen (2026: 84000)
- Idempotent bleiben

### Commit 3 – Service: `BankImportService` + Claims im `AccountingService`

`backend/services/bank_import.py`:

```python
parse_csv(file) -> ParsedStatement            # Zeilen, Sammelbuchungs-Split, Rappen-Konvertierung
import_statement(file, member) -> BankStatementImport  # inkl. Dedup + Auto-Vorschläge
suggest_for_transaction(tx) -> dict           # Konto/Mitglied/Event/Claim-Vorschlag (Spec 11.4)
book_transaction(tx_id, account_id, member_id, event_id, claim_id, by) -> Booking
ignore_transaction(tx_id) -> BankTransaction
learn_alias(member_id, auftraggeber_text)     # MemberBankAlias pflegen
```

`AccountingService`-Erweiterung (Claims):

```python
create_claims_for_fiscal_year(fy)             # Beitrags-Claims pro aktivem Mitglied
create_claims_for_billbro(event)              # Essensanteil-Claims (nur bill_paid_by='vereinskonto')
create_claim_for_merch_order(order)
apply_payment_to_claim(claim, amount_rappen, booking)  # inkl. Aufrundungs-Split → 3315/3410
get_open_claims(member_id=None, claim_type=None) -> List[MemberClaim]
propose_budget(fy) -> dict                    # Spec 11.11
```

Aufrundungs-Logik: Zahlung > offener Rest → Rest auf Ursprungs-Konto, Differenz als zweite Buchung auf «Aufgerundete Essensanteile» (3315) bzw. «Aufgerundete Merchbestellungen» (3410).

### Commit 4 – Routes/Templates: Import-Tab und Review-Screen

- `GET/POST /accounting/import` → Upload + Import-Historie (neuer Tab «Import» im Accounting-Index)
- `GET /accounting/import/<id>/review` → Review-Liste der pending-Transaktionen (`data-table`, pro Zeile: Datum, Text, Betrag, Vorschläge als vorbelegte Selects)
- `POST /accounting/import/tx/<id>/book` / `.../ignore`
- Guard: `_require_funktion('SCHATZMEISTER')`, Jahr muss `open` sein

### Commit 5 – Routes/Templates: Offene Posten

- `GET /accounting/claims` → Tab «Offene Posten»: pro Mitglied offene/beglichene Posten, Filter Typ/Status/Mitglied (Filter-Disclosure-Muster)
- `POST /accounting/claims/<id>/settle` → manuell abschliessen/erlassen
- Dashboard-Integration: eigene offene Posten des Mitglieds mit Status («offen» / «teilweise» / «beglichen»)

### Commit 6 – BillBro-Zahlweg

- Zahlweg-Angabe am Anfang des BillBro-Workflows (Organisator): Vereinskonto oder zahlendes Mitglied (Dropdown der Teilnehmer)
- Bei Abschluss der Anteilsberechnung: Claims erzeugen (Vereinskonto → Gläubiger Verein; Mitglied → `creditor_member_id`, **keine** Bookings)
- Privatzahler-Ansicht: Eingänge pro Teilnehmer bestätigen (`POST /billbro/<event_id>/confirm_payment/<member_id>`)

### Commit 7 – EventType «Essen für Buchhaltung»

- `EventType.ESSEN_BUCHHALTUNG`: wie Vorstandssitzung ohne GGL (`GGL_EVENT_TYPES` unverändert), aber `audience = ALL`; kein RSVP-Reminder (`RSVP_REMINDER_EVENT_TYPES` unverändert)
- Formulare (`create_event`/`edit`), Anzeige-Labels, BillBro-Workflow inkl. Zahlweg verfügbar

### Commit 8 – Budget-Vorschlag, Doc-Updates, Nav

- Jahreseröffnung: Budget-Vorschläge vorbelegen (editierbar) + Beitrags-Claims erzeugen
- `docs/ARCHITECTURE.md` (neue Models/Service), `docs/DOMAIN.md` (Offene Posten, Essen für Buchhaltung, Zahlweg), `docs/UI.md` falls nötig
- Initiative-README Status-Tabelle

## Berechtigungs-Guards

| Route | Mindestberechtigung |
|---|---|
| `accounting/import*`, `accounting/claims*` (schreiben) | `SCHATZMEISTER` oder `ADMIN` |
| `accounting/claims` (lesen) | `SCHATZMEISTER`, `RECHNUNGSPRUEFER` oder `ADMIN` |
| BillBro-Zahlweg setzen | Organisator (wie übriger BillBro-Workflow) |
| Privatzahler-Eingang bestätigen | nur `bill_payer_member_id` (oder Admin) |
| Eigene Posten sehen (Dashboard) | aktives Mitglied |

## Acceptance-Criteria

- [ ] ZKB-CSV der Referenzdateien 2025 und 2026 importiert fehlerfrei: alle Zeilen geparst, Sammelbuchungen in Detail-Zeilen gesplittet, EUR-Details proportional in CHF verteilt
- [ ] Doppelter Upload derselben Datei erzeugt 0 neue Transaktionen (Dedup über `line_key`)
- [ ] Kontoführung/Kartengebühren werden automatisch dem Gebühren-Konto vorgeschlagen
- [ ] Mitglied-Zuordnung lernt: nach einmaligem manuellem Zuordnen von «Roman Mueller» wird «Roman Müller» beim nächsten Import automatisch vorgeschlagen
- [ ] Verbuchen einer Transaktion erzeugt Booking mit `payment_ref = zkb_ref` und schreibt zugeordnete Claims fort (`paid_rappen`, Status)
- [ ] Überzahlung erzeugt automatisch die Aufrundungs-Buchung (3315/3410) und schliesst die Claim
- [ ] Jahreseröffnung erzeugt pro aktivem Mitglied eine Beitrags-Claim (Betrag überschreibbar) und Budget-Vorschläge (editierbar)
- [ ] Teilzahlungen in beliebiger Stückelung reduzieren die Beitrags-Claim korrekt (Monatsraten und Einmalzahlung getestet)
- [ ] BillBro fragt den Zahlweg ab; Vereinskonto → Claims gegen Verein, Mitglied → Claims gegen Privatzahler ohne Bookings
- [ ] Privatzahler kann Eingänge pro Teilnehmer bestätigen; Schuldner sieht Status auf dem Dashboard
- [ ] Tab «Offene Posten» zeigt pro Mitglied offen/teilweise/beglichen mit Beträgen und Zahlungsdaten; Mitgliederbeiträge separat filterbar
- [ ] Event-Typ «Essen für Buchhaltung» anlegbar, für alle sichtbar, BillBro ohne GGL-Teile
- [ ] Seed verschlankt den Kontenplan; nie bebuchte Alt-Konten sind weg, Budgets remappt
- [ ] Alle Beträge Integer-Rappen; Migrationen sauber (up + down); bestehende Phase-4-Funktionen unverändert

## Out of Scope

- Automatischer Abruf des Kontoauszugs (ZKB Open Banking / bLink) — Phase 6
- TWINT-Zahlungsanstoss aus der App — Phase 6
- OCR/AI-Klassifikation — Future
- Mahnwesen/automatische Zahlungserinnerungen (manuelles Nachfassen via Offene-Posten-Übersicht reicht vorerst)

## Hinweise für Cursor

- UI-Regeln, Template-Vorlagen und die Tabu-Liste aus `PHASE_04_ACCOUNTING.md` gelten unverändert (BEM, keine neuen CSS-Klassen, `data-table`, Filter-Disclosure, `cleanup-step-nav`).
- CSV-Parsing tolerant: UTF-8 mit/ohne BOM und cp1252 versuchen; Spalten über den Header mappen, nicht über Positionen.
- `vorlagen_buchhaltung/` ist in `.gitignore` — Testdaten für Unit-Tests als **anonymisierte** Fixtures unter `tests/fixtures/` anlegen (fiktive Namen, echte Struktur inkl. Sammelbuchung + EUR-Fall).
- Migrationen als separate Commits, nie mit Feature-Code mischen.
- Enum-Erweiterung `eventtype` in Postgres braucht `ALTER TYPE ... ADD VALUE` (nicht transaktional — Migration entsprechend aufbauen, Muster: Migration `f2c8a1b9d047` für `VORSTANDSSITZUNG`).

# Domain – Gourmen-Verein

Vereinsspezifische Begriffe. Wenn ein Begriff im Code oder Frontend auftaucht und nicht hier steht: ergänzen.

## Der Verein

**Gourmen** ist ein Schweizer Verein. Schwerpunkt: gemeinsame kulinarische Events ("Monatsessen"), Geselligkeit, Mitglieder-Wettbewerbe. Sitz Schweiz, deutschsprachig.

Aktueller Status: nicht im Handelsregister eingetragen – das ist für einen einfachen Verein zulässig (Statuten + Vereinsbeschluss reichen).

## Mitglieder-Rollen

### `Role` (Berechtigung im System)

| Wert | Bedeutung |
|---|---|
| `MEMBER` | Standard-Mitglied; Vereinsbereich inkl. **Lesen** von Admin-Übersicht, Mitgliederliste und Merch-Übersicht (Organisation, Kontakte) |
| `ADMIN` | Zusätzlich: Mitglieder bearbeiten/anlegen, sensible/verschlüsselte Daten, Sicherheit (Passwort/2FA), Events erfassen, Merch pflegen, Mail-Test |

### `Funktion` (Vereinsfunktion, ehrenamtlich)

| Wert | Bedeutung |
|---|---|
| `MEMBER` | normales Mitglied ohne spezielle Funktion |
| `VEREINSPRAESIDENT` | Vereinspräsident (Vorstand) |
| `KOMMISSIONSPRAESIDENT` | Kommissionspräsident (Vorstand) |
| `SCHATZMEISTER` | Kassenwart, Buchhaltung (Vorstand) |
| `MARKETINGCHEF` | Aussen-Kommunikation, Merch (Vorstand) |
| `REISEKOMMISSAR` | Organisation Ausflüge (Vorstand) |
| `RECHNUNGSPRUEFER` | Revisor, prüft Buchhaltung |

`vorstandsmitglied`-Bool im Member-Model markiert Vorstandsmitglieder unabhängig von der Funktion.

## Event-Typen (`EventType`)

| Wert | Bedeutung |
|---|---|
| `MONATSESSEN` | Monatliches Restaurant-Event, Hauptaktivität |
| `AUSFLUG` | Mehrtägige oder Tages-Ausflüge |
| `GENERALVERSAMMLUNG` | Jährliche Mitgliederversammlung |
| `VORSTANDSSITZUNG` | Sitzung des Vorstands; immer `audience=board` |
| `ESSEN_BUCHHALTUNG` | «Essen (Buchhaltung)»: Ad-hoc-Essen (z.B. auf Reisen), das mit der Vereinskarte bezahlt wird – nur damit der ZKB-Eintrag später zugeordnet und via BillBro gesplittet werden kann. Offen für alle Mitglieder, ohne GGL, ohne Erinnerungen |

### Event-Sichtbarkeit (`EventAudience`)

| Wert | Bedeutung |
|---|---|
| `all` | Für alle aktiven Mitglieder sichtbar (App + iCal) |
| `board` | Nur Vorstandsmitglieder (`Member.vorstandsmitglied`), Admins und der Organisator |

`VORSTANDSSITZUNG` setzt `audience` serverseitig immer auf `board`. Push-/RSVP-Erinnerungen (3 Wochen vor Termin, Montag vor Event) laufen für Monatsessen, GV und Vorstandssitzung; bei `board` nur an Vorstandsmitglieder.

Bei Monatsessen wird in der Regel BillBro inkl. GGL-Schätzspiel angewendet. Bei **Vorstandssitzungen** und **Essen (Buchhaltung)** läuft BillBro abgespeckt (Ess-Typ + Rechnungssplit, ohne Schätzung/Rangliste/GGL). Bei Ausflügen und Generalversammlung ist BillBro nicht zwingend.

## BillBro

**Was es ist**: Bill-Splitting-System, das den Rechnungsbetrag fair auf Teilnehmende aufteilt – nicht stumpf gleichmässig, sondern nach **Verzehrs-Rolle** (Ess-Typ).

### Rollen pro Teilnahme (`Participation.esstyp`)

Bei BillBro wählt das Mitglied eine Rolle, die das geschätzte Verzehr-Verhalten abbildet:

| Rolle | Gewicht (default) | Bedeutung |
|---|---|---|
| **sparsam** | 0.7 | wenig Essen/Trinken, einfaches Menü, keine teuren Getränke |
| **normal** | 1.0 | durchschnittlicher Konsum |
| **allin** | 1.3 | viel/teuer, Wein, Dessert, mehrere Gänge |

Gewichte sind pro Event in `Event.weights_used_json` konfigurierbar (Default: 0.7/1.0/1.3).

### Berechnung

```
1. Rechnungsbetrag erfassen (rechnungsbetrag_rappen)
2. Trinkgeld berechnen nach tip_rule (z.B. "7pct_round10" = 7% auf 10er gerundet)
3. Gesamtbetrag = Rechnung + Trinkgeld
4. Gewichte aller Teilnehmenden summieren (z.B. 3×0.7 + 5×1.0 + 2×1.3 = 9.7)
5. Anteil pro Rolle = Gesamtbetrag × (Gewicht / Summe)
6. Rundung nach rounding_rule (z.B. "ceil_10" = aufrunden auf 10er Rappen)
```

Resultat-Felder am Event: `betrag_sparsam_rappen`, `betrag_normal_rappen`, `betrag_allin_rappen`.

### BillBro-Schätzspiel (nur Monatsessen / GGL)

`Event.supports_ggl` ist `True` nur für `EventType.MONATSESSEN`. Nur dann:

- Teilnehmende geben zusätzlich einen Schätzbetrag ab (`guess_bill_amount_rappen`)
- Organisator sieht die Schätzungsrangliste
- Beim Erfassen der Rechnung vergibt `GGLService.calculate_event_points` GGL-Punkte

Bei Vorstandssitzungen (und anderen Nicht-GGL-Events) wählen Teilnehmende nur den Ess-Typ; der Organisator erfasst Rechnung, bestätigt/passt den vorgeschlagenen Gesamtbetrag (inkl. Trinkgeld) an und BillBro berechnet die Anteile – ohne Rangliste und ohne GGL-Punkte.

### BillBro-Zahlweg (Phase 04b)

Der Organisator gibt an, wie die Rechnung beglichen wird (`Event.bill_paid_by`):

- **Vereinskonto** (`VEREINSKONTO`) – bei Finalisierung entstehen pro Teilnehmer offene Posten (`MemberClaim`, Typ `ESSENSANTEIL`); Rücküberweisungen werden über den ZKB-Import den Posten zugeordnet, Aufrundungen landen auf Konto `3315`.
- **Mitglied** (`MITGLIED`) – ein teilnehmendes Mitglied legt privat aus (`Event.bill_payer_member_id`); die Anteile laufen **nicht** über die Vereinsbuchhaltung. Der Auslegende bestätigt eingegangene Zahlungen der anderen direkt in der App (Dashboard).

## GGL – Gourmen Guessing League

**Was es ist**: Saisonaler Wettbewerb. Wer am besten den Rechnungsbetrag eines **Monatsessens** schätzt, kriegt Punkte. Über die Saison entsteht ein Ranking.

### Punkte-Vergabe pro Event

```
1. Differenz ermitteln: |Schätzung - tatsächlicher Rechnungsbetrag|
2. Sortiere nach Differenz (kleinste = bester Tipp)
3. Fractional Ranking bei Gleichstand:
   - 2 Personen mit gleicher Differenz auf Platz 3 → beide Rang 3.5
4. Punkte = N - rank + 1, wobei N = Anzahl Teilnehmender mit gültigem Tipp
```

Beispiel mit 5 Tippenden:

| Rank | Punkte |
|---|---|
| 1 | 5 |
| 2 | 4 |
| 3.5 (Gleichstand) | 2.5 |
| 3.5 (Gleichstand) | 2.5 |
| 5 | 1 |

### Saison

Eine Saison entspricht einem Kalenderjahr (`Event.season` = Jahr aus `datum`). Saisonsieger ist, wer am Saisonende die meisten GGL-Punkte hat.

## Spirit Animal

Optionale "Tier-Persönlichkeit" pro Mitglied (`Member.spirit_animal` = String). Wird bei Display-Namen mit angezeigt: "🐺 Wolf Max" statt nur "Max".

Reine Vereins-Folklore, keine technische Bedeutung.

## Rufname

Spitzname, optional, in `Member.rufname`. Wird im Display bevorzugt vor Vorname verwendet, wenn gesetzt.

## Zimmerwunsch

Bei Ausflügen: Präferenz für Zimmer-Aufteilung (`Member.zimmerwunsch`):

- `Einzelzimmer`
- `Zweierzimmer`
- `Egal`

## Nationalitaet

Feldwerte: `CH`, `IT`, `Andere`, leer. Hat sich historisch auf diese Werte beschränkt – keine generische ISO-Nationalitäts-Liste.

## Kleider / Körper-Daten

Für Vereins-Merch und Ausflüge erfasst (alle optional):

| Feld | Inhalt |
|---|---|
| `koerpergroesse` | Körpergrösse in cm |
| `schuhgroesse` | EU-Schuhgrösse als Float (39, 39.5, 40, ...) |
| `koerpergewicht` | Gewicht in kg |
| `kleider_oberteil` | Konfektionsgrösse (S, M, L, XL, ...) |
| `kleider_hosen` | Konfektionsgrösse |
| `kleider_cap` | Konfektionsgrösse |

## Führerschein

Komma-separierte Liste der Führerscheinklassen (z.B. `"B,A1"`). Praktisch für Ausflug-Organisation (wer kann fahren?).

## Beitritt

`beitrittsjahr` als `Integer` plus `beitritt` als `Date` (Monatsbeginn). Letzteres ist neuer und genauer.

## Sensitive Daten

In `MemberSensitive` werden potentiell sensitive Felder verschlüsselt abgelegt (z.B. AHV-Nr., IBAN falls erfasst). Lese-Zugriff erfordert **Step-Up-Auth** (frische Passwort-Bestätigung).

## Vereins-Drive (Phase 03 / Phase 09 Browser)

Der Verein nutzt ein **Google Shared Drive** als zentralen Dokumentenspeicher fuer Statuten, Protokolle, Belege, Fotos und Marketing-Material. Die App folgt der **Drive-Ordnerstruktur** (rekursiv ab Shared-Drive-Root); Ordner pflegen die Vereinsmitglieder in Drive. Authoritatives Spec: `docs/capabilities/drive.md`.

### Begriffe

- **Vereins-Drive** – das eine Shared Drive `gourmen.ch` (`GOOGLE_DRIVE_ID`). Jedes verifizierte Mitglied wird als `content_manager` eingeladen.
- **Google-Login-Adresse** (`Member.google_email`) – die E-Mail-Adresse, mit der ein Mitglied sich bei Google einloggt. Muss nicht zwingend Gmail sein. Wird im Profil getrennt von der Kontakt-Mail (`Member.email`) gepflegt und per Token-Mail (`AuthTokenPurpose.GOOGLE_EMAIL_VERIFY`, 7 Tage gueltig) verifiziert.
- **Service-Account** – eigener Google-Account fuer die App-Backend-Zugriffe (kein Mensch). Authentifiziert via Base64-encoded JSON-Key in `GOOGLE_SERVICE_ACCOUNT_KEY`.
- **`drive_parent_id`** – in der DB gecachter Google-Folder, in dem die Datei liegt; bei Abweichung zu Drive korrigiert Auto-Sync still.
- **Archiv-Ordner** – dedizierter Folder im Shared Drive; seine Drive-File-ID steht in `DRIVE_ARCHIVE_FOLDER_ID`. *Archivieren* verschiebt die Datei dorthin (kein separates DB-Status-Feld).
- **Auto-Sync** – pro Detail-Aufruf (und verwandte Pfade): prueft Existenz der Datei und Obsoleszenz von `drive_parent_id`; Import/Removal bei Resync.
- **Admin-Re-Sync** – rekursiver Walk ab Root: neue Drive-Dateien mit DB-Zeilen verknuepfen, verschwundene Eintraege bereinigen.

### Audit-Aktionen (zusaetzlich zu Sektion «Audit-Aktionen»)

- `GOOGLE_EMAIL_VERIFY_REQUESTED`, `GOOGLE_EMAIL_VERIFIED`
- `DOCUMENT_UPLOADED`, `DOCUMENT_RENAMED`, `DOCUMENT_MOVED`, `DOCUMENT_ARCHIVED`, `DOCUMENT_RESTORED`, `DOCUMENT_PERMANENTLY_DELETED`, `DOCUMENT_DOWNLOADED`
- `DOCUMENT_AUTO_SYNCED`, `DOCUMENT_AUTO_IMPORTED`, `DOCUMENT_AUTO_REMOVED`
- `DRIVE_MEMBER_INVITED`, `DRIVE_MEMBER_REMOVED`
- `DRIVE_RESYNC_TRIGGERED`, `DRIVE_AUTO_SYNC_DRIFT_FIXED`, `DRIVE_HARD_DELETE_CONFIRMED`

## Audit-Aktionen

Im `AuditAction`-Enum definiert. Beispiele:

- `LOGIN`, `LOGOUT`
- `ENABLE_2FA`, `DISABLE_MFA`, `USE_BACKUP_CODE`
- `CHANGE_PASSWORD`, `RESET_PASSWORD`
- `REQUEST_2FA_RESET`, `RESET_2FA`
- `READ_SENSITIVE_DATA`
- `CALENDAR_FEED_ENABLED`, `CALENDAR_FEED_REGENERATED`, `CALENDAR_FEED_DISABLED` — persönlicher iCal-Feed (`docs/capabilities/calendar.md`); **ohne** Token-Wert im Audit-`extra_json`
- weitere bei Bedarf

## Buchhaltung (Phase 04 + 04b)

Einnahmen-/Ausgaben-Rechnung (E/A) des Vereins in der App. Authoritatives Spec: `docs/capabilities/accounting.md`.

### Begriffe

- **Geschäftsjahr** (`FiscalYear`) – Kalenderjahr mit Status-Lifecycle `open → in_review → closed`. Nur in offenen Jahren sind Buchungen möglich.
- **Konto** (`Account`) – Position aus dem Kontenplan (z.B. `6100 Ausgaben aus monatlichem Essen`), Art `income`/`expense`, gruppiert per `group_name` (Kontengruppe).
- **Buchung** (`Booking`) – einzelner Geldfluss: Datum, Beschreibung, Betrag (Rappen, Integer), Richtung `in`/`out`, Konto, optional Event/Mitglied/`payment_ref`.
- **Beleg** (`Receipt`) – Quittungs-Datei im Vereins-Drive unter `Buchhaltung/{Jahr}/`. Jedes aktive Mitglied kann Belege einreichen (Foto/PDF, optionales Pre-Tagging). `booking_id NULL` = ungebucht («Inbox» des Schatzmeisters).
- **Budget** (`BudgetEntry`) – Soll-Wert pro Konto und Jahr; Vergleich Budget vs. Ist im Budget-Tab.
- **Revision** – der Rechnungsprüfer prüft das freigegebene Jahr in der App (read-only), hinterlässt `RevisionComment`s und bestätigt formal (`RevisionApproval`). Danach generiert die App den **Revisorenbericht** als PDF und legt ihn in Drive ab.
- **Sparkapital** – kumuliertes Ergebnis aller Vorjahre («zu Jahresbeginn» im Bericht).
- **ZKB-Import** (`BankStatementImport`/`BankTransaction`, Phase 04b) – monatlicher CSV-Export des ZKB-Vereinskontos wird hochgeladen, dedupliziert (ZKB-Referenz), Sammelbuchungen werden in Detailzeilen gesplittet; der Schatzmeister verbucht die Zeilen im Review-Screen. Der Import ist die **primäre Buchungsquelle**, manuelle Buchungen der Sonderfall. Solange noch nichts verbucht ist, kann ein Import komplett gelöscht werden (falsche Datei / erneuter Upload).
- **Offener Posten** (`MemberClaim`, Phase 04b) – erwartete Zahlung eines Mitglieds an den Verein: Mitgliederbeitrag, BillBro-Essensanteil, Merch-Bestellung, Reise. Kennt Teilzahlungen (`OFFEN → TEILWEISE → BEGLICHEN`); Überzahlungen werden als ausserordentliche Einnahme (aufgerundeter Anteil) verbucht.
- **Bank-Alias** (`MemberBankAlias`, Phase 04b) – gelernte Schreibweise eines Mitglieds im Kontoauszug (Zweitnamen etc.); verbessert die Auto-Zuordnung bei künftigen Importen.

### Rollen

- **Schatzmeister** (`Funktion.SCHATZMEISTER`) – bucht, verwaltet Budget, gibt das Jahr zur Revision frei.
- **Rechnungsprüfer / Revisor** (`Funktion.RECHNUNGSPRUEFER`) – read-only-Zugriff, Kommentare, formale Bestätigung des Jahres.
- **Admin** – kommt überall durch; verwaltet zusätzlich den Kontenplan.
- **Aktives Mitglied** – darf Belege einreichen und die eigenen Belege sehen (`/member/receipts`); sieht eigene offene Posten auf dem Dashboard und bestätigt dort Eingänge, wenn es privat ausgelegt hat.

### Kontenplan (Kurzübersicht)

Vierstellige Konto-Nummern, angelehnt an KMU-Kontenrahmen. Seit dem Refokus (Phase 04b) verschlankt auf 18 real bebuchte Konten:

- **3xxx Einnahmen**: `3000` Mitgliederbeiträge, `3100` Spenden/Sponsoring, `3310/3315` Essensanteile (inkl. Aufrundungen), `3400/3410` Merch-Zahlungen (inkl. Aufrundungen), `3500` Reisen, `3620` Sonstiges (Bussen, Rückerstattungen)
- **4xxx Aufwand Aktivitäten**: `4500` Reisen und Ausflüge
- **6xxx übriger Aufwand**: `6100` Essen mit Vereinskonto, `6541/6542` GV/Vorstandssitzungen, `6570` IT/Telefon, `6650/6660` Merch-Einkauf/-Beitrag, `6700` Sonstiges, `6710` Rückzahlungen, `6940` Konto-/Kartengebühren

Seed: `python scripts/seed_accounting_chart.py` (idempotent; Kontenplan + FiscalYears 2021–2026 inkl. `membership_fee_rappen` + Budget 2025/2026 + Ist-Sammelbuchungen 2022–2025 aus den Erfolgsrechnungen + Beitrags-Claims für 2026; optional lokale ZKB-CSVs unter `vorlagen_buchhaltung/` als pending Import; entfernt/deaktiviert Alt-Konten ohne/mit Buchungen). 2026-Einzelbuchungen kommen bewusst über den ZKB-Import-Review, nicht als Seed.

## Merchandise

Vereins-Shop-Logik mit Preis-Strukturen:

- **`MerchArticle`**: ein Artikel-Typ (z.B. "Vereins-T-Shirt")
- **`MerchVariant`**: konkrete Variante (Farbe + Grösse, z.B. "Schwarz/M")
- **`MerchOrder`**: Bestellung eines Members
- **`MerchOrderItem`**: einzelne Position einer Bestellung

Preis-Felder unterscheiden zwischen `supplier_price_rappen` (was der Verein an den Lieferanten zahlt) und `member_price_rappen` (was das Mitglied zahlt). Differenz = Vereinsmarge.

## Status / Workflows

### `MerchOrder.status`

Default `BESTELLT`, weitere Werte je nach Workflow (`AUSGELIEFERT` etc. – im Code nachschauen).

### `Event.published`, `Event.allow_ratings`, `Event.billbro_closed`

- `published` = Event sichtbar für alle Members
- `allow_ratings` = Bewertungen aktiviert (default true)
- `billbro_closed` = BillBro-Eingabe gesperrt (nach Abschluss/Auswertung)

## Saisonbegriff

`Event.season` ist das Jahr des Events. Aggregationen (GGL-Ranking, Stats) gruppieren nach Saison.

## Was es **nicht** gibt (potenziell verwirrend)

- **Keine Family-/Gast-Mitglieder**: jeder Member ist gleich strukturiert
- **Keine automatische Beitrags-Einforderung**: Mitgliederbeiträge entstehen als offene Posten (`MemberClaim`) und werden über den ZKB-Import abgeglichen; es gibt aber kein aktives Mahnwesen und keine Payment-Integration (TWINT kommt erst in Phase 6)
- **Keine externen Auth-Provider**: Login ist Eigenbau (Email + Passwort + 2FA)
- **Keine native App**: nur PWA (installierbar, aber HTML/JS unter der Haube)

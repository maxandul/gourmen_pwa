# Domain – Gourmen-Verein

Vereinsspezifische Begriffe. Wenn ein Begriff im Code oder Frontend auftaucht und nicht hier steht: ergänzen.

## Der Verein

**Gourmen** ist ein Schweizer Verein. Schwerpunkt: gemeinsame kulinarische Events ("Monatsessen"), Geselligkeit, Mitglieder-Wettbewerbe. Sitz Schweiz, deutschsprachig.

Aktueller Status: nicht im Handelsregister eingetragen – das ist für einen einfachen Verein zulässig (Statuten + Vereinsbeschluss reichen).

## Mitglieder-Rollen

### `Role` (Berechtigung im System)

| Wert | Bedeutung |
|---|---|
| `MEMBER` | Standard-Mitglied, kann Events sehen/teilnehmen |
| `ADMIN` | Vollzugriff (Events erstellen, Members verwalten) |

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

Bei Monatsessen wird in der Regel BillBro angewendet, bei Ausflügen und Generalversammlung nicht zwingend.

## BillBro

**Was es ist**: Bill-Splitting-System für Monatsessen, das den Rechnungsbetrag fair auf Teilnehmende aufteilt – nicht stumpf gleichmässig, sondern nach **Verzehrs-Rolle**.

### Rollen pro Teilnahme (`Participation.role` o.ä.)

Bei der Anmeldung wählt das Mitglied eine Rolle, die das geschätzte Verzehr-Verhalten abbildet:

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

### BillBro-Schätzspiel

Vor jedem Monatsessen schätzt jedes teilnehmende Mitglied den Rechnungsbetrag. Diese Schätzung wird in `Participation.guess_bill_amount_rappen` gespeichert und ist Grundlage für die GGL-Punkte (siehe unten).

## GGL – Gourmen Guessing League

**Was es ist**: Saisonaler Wettbewerb. Wer am besten den Rechnungsbetrag eines Monatsessens schätzt, kriegt Punkte. Über die Saison entsteht ein Ranking.

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

## Audit-Aktionen

Im `AuditAction`-Enum definiert. Beispiele:

- `LOGIN`, `LOGOUT`
- `ENABLE_2FA`, `DISABLE_MFA`, `USE_BACKUP_CODE`
- `CHANGE_PASSWORD`, `RESET_PASSWORD`
- `REQUEST_2FA_RESET`, `RESET_2FA`
- `READ_SENSITIVE_DATA`
- weitere bei Bedarf

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
- **Keine Mitgliedsbeiträge im Code** (heute): Beitragslogik kommt mit Buchhaltungs-Modul
- **Keine externen Auth-Provider**: Login ist Eigenbau (Email + Passwort + 2FA)
- **Keine native App**: nur PWA (installierbar, aber HTML/JS unter der Haube)

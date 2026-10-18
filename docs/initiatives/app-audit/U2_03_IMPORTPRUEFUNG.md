# U2-03: Sichere Importvorstufe

## Zuschnitt und Vertrag vor Code

A-064/A-065 werden als U2-03a zuerst lokal abgeschlossen; A-063 (Referenz-/
Dateiidentitaet) folgt als U2-03b mit eigenem Altbestandsvertrag. Quellen:
FINDINGS, B01, FINANZ_ERGAENZUNG_ENTWURF, Accounting-Capability und Anchor-Docs.

a: CSV-Struktur und benoetigte Spalten eindeutig, Datensaetze vollstaendig.
Ein-/Ausgang genau einmal je Hauptzeile, positive exakte Betraege in Rappen,
keine abgeschnittenen Nachkommastellen oder mehrfache Vorzeichen. Ungueltige
Werte melden Datensatz und Feld als BankImportError; kein Teilimport.
Details ohne Sammelkopf oder ohne Betrag sind Fehler, keine stillen Auslassungen.

Sammelkopf nennt Detailanzahl, die exakt stimmen muss. CHF-Details summieren
exakt zum Bankbetrag, keine Hochrechnung fehlender Teilzahlungen. Fremdwaehrung
nur als einheitliche, im Kopf mit Originalgesamtbetrag ausgewiesene Gruppe;
Details muessen genau diesem Originalbetrag entsprechen. Erst dann proportional
auf den vorgegebenen CHF-Bankbetrag verteilen, Integer-Rappen mit deterministischem
Rest auf letzter Zeile; keine Mischung oder Null-/Negativanteile. Andere/unklare
Formate zur Korrektur ablehnen, keinen Wechselkurs oder Betrag erfinden.

Keine historischen Zeilen korrigieren. b folgt separat; Parseraenderung allein
loest Referenzlosigkeit nicht. Keine Migration fuer a.

## Nachweise

a am 18.10.2026 lokal geprueft: isolierter Runner mit test_bank_csv_validation,
test_bank_import, test_bank_booking_atomicity, test_payment_allocations:
**71 bestanden, 560 Warnungen, 18.45 s**. Original-Datei-POST mit fehlerhafter
zweiter Zeile liefert Importmeldung und keinen Teilbestand. Ungueltige Zahlen,
fehlende/doppelte Spalten, Quotes, fehlende/ueberzaehlige Details, CHF-Differenz,
fehlender/falscher Fremdwaehrungsgesamtbetrag und valide exakte Verteilung
abgedeckt. Kein dotenv/Netz, synthetische Daten. `git diff --check` ohne Fehler.
Keine Migration oder UI-Aenderung. Referenzidentitaet b bleibt offen; keine
PostgreSQL-/echte Bankexport-Abnahme.


## b: Identitaetsvertrag vor Code

Jeder neue Import speichert einen SHA-256-Dateifingerprint (keine Dateiinhalte
zusätzlich). Referenzlose Hauptzeilen erhalten eine neue H2-Identitaet aus allen
vorhandenen Originalspalten und ihrem Vorkommen innerhalb derselben Datei.
Unterschiedliche Zahlungszwecke/Details und auch mehrfach identische legitime
Zeilen bleiben getrennt. Detailidentitaeten bleiben an ihren Sammelkopf gebunden.

Exakt dieselbe Datei darf erneut als Duplikat erkannt werden. Eine referenzlose
Kollision aus anderer Datei oder mit altem H-Ersatzschluessel bleibt mehrdeutig:
Datei ohne Teilimport mit Klartextgrund ablehnen, keine Zeile still verwerfen oder
automatisch doppelt anlegen. Der Nutzer muss den konkreten Bestand abgleichen;
keine Bankidentitaet aus bloss gleichem Datum/Betrag behaupten. Identische Dateien
sind derselbe Importbeleg; falls zwei echte Bewegungen sogar in vollstaendig
identischen Dateien stehen, ist eine manuelle Klaerung statt automatischer
Unterscheidung erforderlich. Keine heuristische Altdatenreparatur.

Vorhandene Bankreferenz nur bei identischem gespeicherten Originaldatensatz und
identischen Details als Duplikat behandeln; Widerspruch verlangt Klaerung.
Neue Importzeilen, Importkopf/Zaehlwerte und gegebenenfalls neues Jahr in einer
Transaktion, Fehler rollt alles zurueck. Unique line_key bleibt letzte DB-Grenze;
PostgreSQL-Konkurrenz separat. Additive Fingerprint-Migration ohne Backfill separat.


## b Abschlussnachweis 18.10.2026

Migration separat **b8e38ec**, ohne Backfill; Upgrade/Downgrade/Upgrade bewahrt
Legacy-Import, Downgrade verweigert benutzte Fingerprints. Isolierter Runner:
test_import_fingerprint_migration, test_bank_import_identity,
test_bank_csv_validation, test_bank_import, test_bank_booking_atomicity,
test_payment_allocations: **78 bestanden, 590 Warnungen, 21.03 s**.

Unterschiedlicher Zahlungszweck, zweimal identische Zeile, exakter Wiederimport,
Kollision mit anderer Datei/Altkey, widerspruechliche Bankreferenz, echter
Flushfehler beim zweiten Insert und Commitfehler ohne Teiljahr/-kopf/-zeilen
abgedeckt. Nach Fehler erfolgreich genau einmal importierbar. Keine UI-Aenderung.
`git diff --check` ohne Fehler. Synthetische SQLite-Daten, kein dotenv/Netz.
Echte Bankexportvarianten und PostgreSQL-Konkurrenz offen; keine historischen
Dubletten oder verlorenen Zahlungen repariert. Mehrdeutige Datei ist bewusst
abgewiesen und nicht als erfolgreich dedupliziert gemeldet.

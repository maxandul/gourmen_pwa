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

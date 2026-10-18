# U2-02a: Atomare Importverbuchung

## Vertrag vor Code

A-060, B01/F5 und vorhandene Buchungsgrenzen aus U2-01. Eine ausdrueckliche
Importverbuchung speichert Haupt-/gegebenenfalls Zusatzbuchung, Forderungsstand,
Alias und Bankstatus in genau einer Transaktion. Auch ein dabei neu angelegtes
Geschaeftsjahr gehoert dazu. Fehlende Voraussetzungen, Fehler im zweiten Schritt
oder Commitfehler hinterlassen keine Teilbuchung. Erfolg erst nach Commit.

Importkopf vor Zeile sperren und frisch lesen; Ignorieren/Wiederaufnehmen/Loeschen
verwenden dieselbe Sperrreihenfolge. Forderung und Jahr beim Buchen ebenfalls
frisch sperren. Bereits verbuchte Zeile ablehnen, keine doppelte Fortschreibung.
Kein pauschaler Unique-Index auf payment_ref: echte Aufteilungen brauchen mehrere
Buchungen pro Bankbewegung. Fehlerstatus ist keine Bestaetigung, dass eine Bank-
oder DB-Antwort sicher erfolglos war; bei unklarem Commit zuerst Status abgleichen.

Dieses Teilpaket aendert die Speichergrenze. Die bisher automatische Behandlung
von Ueberzahlungen wird anschliessend in U2-02b durch explizite F5-Auswahl ersetzt;
Richtung/Schuldner und Importkorrektur folgen b/c. Keine historische Reparatur,
keine Migration, kein echter Bank-/Mail-/Drivezugriff. PostgreSQL-Sperrverhalten
bleibt separat nachzuweisen; SQLite beweist nur lokale Transaktionsfaelle.

## Nachweis

18.10.2026, isolierter Runner (kein dotenv/Netz, SQLite im Speicher):
`test_bank_booking_atomicity`, `test_bank_import`, `test_booking_values`:
**61 bestanden, 584 Warnungen, 23.74 s**. `git diff --check` ohne Fehler.

Konkrete Regression: fehlendes Aufrundungskonto zweimal ueber Original-POST und
Service, danach erfolgreiche Wiederholung; echte NOT-NULL-Verletzung nach
beiden Inserts; Fehler nach Forderungsfortschreibung/Alias-Flush und beim Commit;
kein neues Jahr/keine Buchung/keine Zahlung/kein Alias nach Fehler. Erfolgreiche
Aufteilung summiert exakt zur Bankbewegung. Erneute Verbuchung sowie Ignorieren,
Wiederaufnahme oder Loeschen eines verbuchten Vorgangs abgewiesen. Bestehende
Import- und Datums-/Rappenregression bestanden. Keine Migration oder UI-Aenderung.

Keine parallele PostgreSQL-Ausfuehrung, keine historischen Daten korrigiert.
U2-02b/c und U1-Revisions-/externe Abnahmen bleiben offen.

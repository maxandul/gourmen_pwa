# U2-04: Revisionsgrenzen und erhaltene Pruefstaende

## a: Vertrag vor Code

A-059/A-066, bestaetigte F6/R13-Regeln aus ROLLEN_ENTSCHEIDUNGEN und
REVISION_KORREKTUR_ENTWURF. Budget nur im offenen Jahr bearbeiten. Belegumhaengen
prueft sowohl bisherige als auch neue Buchung: beide Jahre muessen offen sein;
ungebundener Beleg braucht nur offenes Ziel. Rollen-/Event-/Belegrechte erhalten.

Betroffene Mutationen und Revisionszustandswechsel sperren denselben frischen
Jahresdatensatz vor Pruefung/Schreiben. Bei zwei Jahren nach ID sortiert sperren;
Beleg danach frisch sperren, zwischenzeitlich geaenderte Zuordnung ablehnen.
Buchungsanlage/-edit und direkte Belegverknuepfung verwenden dieselbe Jahresgrenze.
Budgeteingaben rappengetreu, Null erlaubt, nichtendliche/negative/zu grosse Werte
abweisen. Keine stille Fuenf-Rappen-/Float-Rundung.

a liefert diese Sperrgrenze, noch keine versionsgebundene Revisionshistorie.
b folgt mit erhaltenem Pruefstand/Bestätigung und begruendeter Wiederöffnung;
c mit stabilem Abschluss und Bericht. Keine fachliche Rollenlockerung in a,
keine Historie loeschen oder Altdaten korrigieren, keine neue Migration.

## Nachweise

U2-04a: 103 Python-Tests bestanden, 1229 Warnungen, 40.07 s:
test_accounting_year_guards, test_booking_values,
test_upload_selection_permissions, test_payment_allocations, test_bank_import.
Isolierter Runner, synthetische SQLite-Daten, dotenv/Netz gesperrt.
19 Service-Worker-Tests bestanden; git diff --check sauber.
PWA 3.16.22 / pwa.73705b99.js. Keine Migration.
Der Windows-pyreadline-Destruktor meldete nach erfolgreichem pytest-Ende einen
ignorierten Handlefehler. PostgreSQL-Sperrwirkung und Browserabnahme bleiben offen.
Revisionshistorie folgt in b, stabile Abschlusszahlen/Berichte in c. U1 bleibt offen.

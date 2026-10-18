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

## b: Vertrag vor Code

Eigene unveraenderliche Einreichungsdaten in AccountingRevision, je Jahr
fortlaufende Version; bisherige RevisionApproval-Zeilen bleiben unangetastet.
Ein Snapshot enthaelt Journal, Kontobezeichnungen, Budget und Belegreferenzen.
Jahressperre serialisiert Vorlage, Kommentare, Erledigung und Bestaetigung;
Formulare senden die erwartete Version. Alte Formulare duerfen keine neue
Fassung bestaetigen oder zuruecknehmen. Fehler rollen die ganze Transaktion zurueck.

Nur aktiver Schatzmeister/Systemadmin legt vor oder nimmt mit Pflichtgrund
zurueck (auch CLOSED nach OPEN). Nur Rechnungspruefer/Systemadmin bestaetigt,
Admin immer sichtbar stellvertretend. Keine neuen Rechte fuer Finanzdelegation.
Offene explizite Beanstandungen blockieren; Kommentare und fehlende Belege sind
Hinweise. Bestehende Kommentare werden nicht nachtraeglich zu Beanstandungen.
Neue Kommentare erhalten Versionsbezug, Beanstandungswahl nur Revisor/Admin;
Erledigung speichert Person/Zeit. Alte Beanstandungen bleiben bis Erledigung offen.

Alte IN_REVIEW-Jahre ohne Snapshot koennen nicht als neue Fassung bestaetigt
werden: begruendet zuruecknehmen und neu vorlegen. Bei Alt-Wiederoeffnung wird
kein historischer Pruefstand erfunden; alte Bestaetigung/Bericht bleiben lesbar.
Historienansicht zeigt Fassungen, Gruende, Handelnde, Kommentare und Snapshots.
Berichts-Fertigstellung ist versionsgebunden; stabile Berechnung/Retry folgt c.
Migration separat; kein produktiver Backfill, keine realen Drive-Zugriffe.

### Nachweise b

Isolierter Runner ohne dotenv/Netz: erster Lauf 72 bestanden, 503 Warnungen,
25.53 s (Revisionsregression, Jahresgrenzen, Buchungswerte). Erweiterter Lauf
60 bestanden, 1050 Warnungen, 22.89 s (Revisionsregression einschliesslich
Originalrouten/Rollen, Finanzfreigaben, Belegauswahl, Zahlungszuordnungen).
Keine Summe daraus als Gesamtlauf. SQLite-Migration Upgrade/Downgrade/Upgrade
mit Altkommentar sowie verweigertem Historienverlust im Test enthalten.
19 Worker-Tests bestanden, git diff --check sauber. PWA 3.16.23 / pwa.f5ad7d83.js.
Keine neuen CSS-Klassen. PostgreSQL-Parallelitaet, reale Drive-Dateiinhalte
und Browser/visuelle Abnahme offen. Berichtsberechnung und Retry bleiben c.

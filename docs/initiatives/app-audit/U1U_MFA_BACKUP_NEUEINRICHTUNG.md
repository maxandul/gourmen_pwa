# U1u / A-080: Backup-Codes bei erneuter MFA-Einrichtung

Stand: 13.10.2026. Lokale Fortsetzung auf «ok weiter», Basis `27f8b04`,
Branch `codex/u1u-mfa-backup-reenrollment`.

## Vertrag und Umsetzung

Neue und wiederholte MFA-Einrichtung liefern nach gültigem TOTP zehn neue
Backup-Codes. Alte Zeilen bleiben erhalten, werden jedoch widerrufen. Unter
der vorhandenen Mitgliedssperre werden Faktor, Codehashes und MFA-Linkwiderruf
gemeinsam committed. Andere Mitglieder bleiben unberührt. Kein neues Schema.

Die bestehende Backup-Code-Ansicht wird direkt im bestätigten POST ausgegeben,
mit `Cache-Control: no-store` und `Referrer-Policy: no-referrer`. Kein Klartext
in Session, Cookie, Datenbank oder Logs. Die Antwort wird vor Commit gerendert,
aber erst nach Erfolg zurückgegeben. Fehler rollen zurück; der Einrichtungsschlüssel
bleibt für Wiederholung erhalten. GET/HEAD erzeugen weder Codes noch MFA-Zeilen.
Erneuter POST bei bereits aktivem Faktor ersetzt nichts und zeigt keine Codes.

Die bisherige ausdrückliche Erneuerung über Passwortbestätigung zur Deaktivierung
und anschliessende TOTP-Neueinrichtung bleibt erhalten. Verlorene Anzeige oder
vollständig verbrauchte Codes lösen keine automatische Ausgabe per GET aus.
Keine separate Erneuerungsoberfläche hinzugefügt. Vorlage, Styles und Assets
unverändert; kein PWA-Bump nötig. Die HTTP-Vertragsänderung 302 → 200 bei
erfolgreicher Einrichtung ist in bestehenden Regressionstests nachgeführt.

## Nachweise und Grenzen

Gezielte Tests liefen mit dem isolierten `run_existing_tests.py`: synthetische
Daten, SQLite im Speicher, kein dotenv und keine ausgehenden Verbindungen.

- 48 Tests bestanden: neue Datei `test_mfa_backup_enrollment.py` (15 Fälle),
  bestehender MFA-Linkwiderruf, Auth-Logging und Backup-Code-Login; 452,48 Sekunden.
- Die fünf abschliessend erweiterten Fälle für echte Anmeldung nach Neueinrichtung
  und erfolgreiche Wiederholung nach Fehler separat bestanden; 86,72 Sekunden.
- 77 angrenzende Tests bestanden: MFA-Resetbestätigung, Step-Up-Sitzungsbindung
  und verpflichtender Passwortwechsel; 184,04 Sekunden.
- `git diff --check` ohne Fehler. Kein erneuter Gesamtlauf aller Fachtests;
  die vollständige Suite des Vorgängerpakets bleibt dessen separater Nachweis.

Die neuen Fälle prüfen Erst-/Neueinrichtung mit aktiven, verbrauchten und
widerrufenen Altzeilen, Nutzbarkeit und Einmalverbrauch neuer Codes, Ablehnung
alter Codes, Mitgliedstrennung, wiederholte POSTs, lesende GET/HEAD-Aufrufe,
CSRF/Anmeldung, Cache-Header und Klartextfreiheit von Cookies/Logs sowie
Rollback bei Render-/Commitfehlern mit anschliessender Wiederholung.

Der erfolgreiche Serverantwortversand beweist nicht, dass Codes tatsächlich
gesichert wurden. Bei verlorener Antwort ist der bestehende Erneuerungsweg nötig.
`no-store` ersetzt keine Kontrolle über Browserhistorie oder vom Nutzer gesicherte
Kopien. PostgreSQL-Parallelabnahme und echte Geräte bleiben separat. Allgemeiner
Sitzungs-/Gerätewiderruf A-077/A-082 und aktionsgebundene erneute Bestätigung
bleiben eigene Pakete. Keine Produktion, kein Push, Merge oder Deploy.

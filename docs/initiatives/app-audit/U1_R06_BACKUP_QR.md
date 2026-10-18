# U1-R06: Backup-Code-Ausgabe ohne Schein-QR

## Vertrag vor Umsetzung

A-121 wird durch Entfernung des funktionslosen QR-Angebots geschlossen. Die
Einmalanzeige nach bestaetigter MFA-Einrichtung, Drucken, Kopieren und die
Sicherungsbestaetigung bleiben erhalten. Keine neue Exportform, kein externer
Dienst, keine Speicherung von Klartextcodes. U1u bleibt verbindlich.

## Pruefung und Grenzen

18.10.2026: Isolierter Runner (kein dotenv, Netz gesperrt),
`tests/routes/test_mfa_backup_enrollment.py` und `test_backup_code_login.py`:
**26 bestanden, 502 Warnungen, 77.09 s**. Bestehende Erfolgsregression prueft
Drucken/Kopieren/Bestaetigen und Abwesenheit des QR-Angebots; weiterhin
Einmalanzeige, fehlende Klartextpersistenz, Einmalverbrauch, Widerruf und Fehler.
Windows-pyreadline meldet beim Prozessende einen ignorierten Handlefehler;
Exitcode 0. `node --test tests/js/sw_cache_isolation.test.cjs`: **19 bestanden**.
`git diff --check` ohne Fehler. PWA-Version 3.16.18, Hash 8dd61da7.
Keine neue UI-Klasse, keine Migration. Echte Browser-, Drucker- und
Zwischenablageabnahme bleiben separat; U1 bleibt insgesamt offen.

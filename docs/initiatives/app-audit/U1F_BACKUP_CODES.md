# U1f – MFA-Backup-Codes korrekt prüfen und einmalig verbrauchen

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1f-backup-code-login`, Basis U1e-Commit `627e697`.
Vorhandener A-079, bestehender bestätigter MFA-Wiederherstellungsweg.
A-076 wurde zu Beginn gelesen, bleibt wegen des zusammenhängend festzulegenden
Pflichtwechsel-/Zwischenzielablaufs ein späteres Paket. Kein neuer Gesamtaudit.

## Änderung

Die bisherige Gleichheitssuche nach einem frisch gesalzenen Hash wird durch
den vorhandenen Hash-Verifikator ersetzt. Der Service betrachtet nur aktive
Backup-Codes des Mitglieds, dessen Passwort bereits geprüft wurde.
Gross-/Kleinschreibung wird wie bisher normalisiert. Hashverfahren und gespeicherte
Hashes bleiben unverändert; keine neuen Codes oder Schlüssel erzeugt.

Ein passender Code wird durch bedingtes UPDATE nur dann verbraucht, wenn er
weiterhin unbenutzt und nicht widerrufen ist. Genau eine geänderte Zeile und
erfolgreicher Commit sind Voraussetzung für die Anmeldung. Zwischenzeitlicher
Verbrauch oder Widerruf führt zur Ablehnung. Bei Schreibfehlern erfolgt Rollback
vor Anmeldung. Audit protokolliert weiterhin lediglich die Code-ID.

Keine Änderung am Passwort-/TOTP-Schritt, an Gerätevertrauen, Sessionfristen,
Backup-Code-Erzeugung oder MFA-Neueinrichtung. Andere Lifecycle-Befunde bleiben offen.

## Nachweise

`tests/routes/test_backup_code_login.py` verwendet echte Login-/MFA-Routen,
synthetische Konten und den originalen gesalzenen Hash-Prüfer. Datenbankzustand
wird in neuer Session geprüft, nicht nur anhand eines Redirects.

Erster Lauf: **3 fehlgeschlagen, 5 bestanden**; gültiger Code wird abgelehnt,
Schreibfehlerpfad wird wegen der falschen Hashsuche gar nicht erreicht.
Nach Fix: diese **8 Tests bestanden**. Ergänzt sind zwei deterministische
Zwischenänderungen nach Hashprüfung (Verbrauch/Widerruf) und die Auswahl unter
mehreren aktiven Codes.

Abdeckung: gültiger Code in Gross-/Kleinschreibung, einmaliger Gebrauch,
falscher/verbrauchter/widerrufener/fremder Code, fehlender Passwortschritt,
Commitfehler mit Rollback ohne Anmeldung, zwischenzeitliche Zustandsänderung,
nur passender Code verbraucht, Code und Hash nicht in Logs.

Ausführung über bestehenden isolierten Audit-Teststarter mit gebündeltem Python,
SQLite im Speicher, ohne dotenv oder ausgehendes Netzwerk. Keine echten
Zugangsdaten verwendet. Testing-CSRF/Rate-Limits deaktiviert.

Abschlusslauf: **221 Tests bestanden**, darunter **11 neue Regressionstests**,
in 93,65 Sekunden; 1636 Warnungen. `git diff --check` ohne Fehler.

## Grenzen

Die Zwischenänderungstests simulieren die relevante Reihenfolge deterministisch;
sie sind keine PostgreSQL-Prüfung mit gleichzeitig laufenden Transaktionen.
Die bedingte Schreiboperation ist die technische Sicherung; eine echte
PostgreSQL-Nebenläufigkeitsabnahme bleibt vor produktiver Freigabe erforderlich.
Ein nach Verbrauch unterbrochener HTTP-Ablauf kann einen Code verbrauchen, ohne
dass der Browser die neue Anmeldung erhält; keine Exactly-once-Zustellung behauptet.
Keine Code-Erneuerung, Migration, Schlüsselrotation, Produktionsänderung,
Veröffentlichung, Push oder Merge auf master. Fremde Dateien und Planung erhalten.

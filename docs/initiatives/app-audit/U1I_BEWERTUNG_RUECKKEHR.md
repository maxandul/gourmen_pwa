# U1i – Sichere Rückkehr nach Event-Bewertungen

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1i-rating-return-target`, Basis U1h-Commit `1c162a8`.
Umfang: ursprünglicher Bewertungsbefund A-035, keine neue Audit-Runde.

## Änderung

`ratings.rate_event` prüft Query- und Formular-`next` mit dem vorhandenen
`SecurityService.local_return_target()`. Das erste erlaubte interne Ziel gewinnt
(Query vor Formular). Damit verwenden alle bestehenden Erfolgs-/Fehlerzweige
ein geprüftes Ziel. Externe und protokollrelative Adressen führen zu den bereits
vorhandenen Event-Tabs und Ankern. Gültige interne Rückkehrziele zur Cleanup-Liste
bleiben mit Query und Fragment erhalten.

Keine Änderung an Teilnahme-, Bewertungs- oder Kategorienregeln. Insbesondere
sind die bestätigten künftigen optionalen Kategorien hier noch nicht umgesetzt.
Auch der getrennte Eingabeerhalt-Befund A-036 wird hier nicht behoben.

## Regression

`tests/routes/test_rating_return_target.py`: 40 neue Tests.
Matrix aus Query/Formular, externem/protokollrelativem/internem Ziel und sechs
Abläufen: deaktiviert, ohne Teilnahme, bestehende Bewertung, Erfolg,
Validierungsfehler, GET. Zusätzlich Anmeldung, Event-Sichtbarkeit, CSRF und
gültiges Formularziel bei ungültiger Query. Datenbankzustand wird unabhängig
von der Weiterleitung geprüft: Erfolg speichert genau eine Bewertung mit den
erwarteten Werten, vorhandene Bewertung bleibt gleich, Fehler schreiben nichts.

Vorher-Lauf der ursprünglichen 37 Fälle: **24 fehlgeschlagen, 13 bestanden**.
Die interne Testadresse wurde danach auf den echten Cleanup-Pfad `/events/cleanup`
berichtigt; drei zusätzliche Schutztests ergänzt. Externe Ziele werden nie
aufgerufen. Synthetische Mitglieder/Events, SQLite im Speicher, isolierter
Audit-Teststarter ohne dotenv und mit gesperrtem ausgehendem Netzwerk.
CSRF ist für den gezielten Ablehnungstest aktiviert, ansonsten Testing-Konfiguration.
Abschluss: **325 Tests bestanden**, darunter **40 neue Regressionstests**,
in 181,40 Sekunden bei 2351 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups unverändert.

## Grenzen

A-035 bleibt für Merch-/Dokument-Einstiege offen; kein appweiter Abschluss.
Keine Oberflächenänderung, Migration, neue Abhängigkeit oder Änderung von
Produktionsdaten und Schlüsseln. Kein Push, Deploy oder Merge auf master.
Planung, Mockups und fremde lokale Dateien bleiben erhalten.

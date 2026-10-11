# U1h – Sichere Rückkehr nach erneuter Passwortbestätigung

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1h-step-up-return-target`, Basis U1g-Commit `6c5cf29`.
Umfang: Step-Up-Anteil des gemeinsamen Redirect-Vertrags A-035.

## Änderung

Die Step-Up-Route verwendet den in U1g eingeführten Prüfer
`SecurityService.local_return_target()` für sämtliche Rückkehrquellen:
Query-`next`, Formular-`next`, Formular-`next_url` und gespeichertes
`step_up_next`. In dieser Reihenfolge gewinnt das erste zulässige interne Ziel.
Ungültige gespeicherte Altwerte werden sofort entfernt und erscheinen auch bei
falschem Passwort nicht mehr im Formular.

Das geprüfte Ziel bleibt während Wiederholungen erhalten. Nach erfolgreicher
Passwortbestätigung oder bei bereits gültiger Freigabe wird es entfernt und
direkt verwendet. Ohne zulässiges Ziel führt die Route zum Dashboard.
Die bestehenden Anforderungen an Passwort, Mitgliedsbindung und Freigabedauer
bleiben unverändert. Keine neue Fachregel oder zusätzliche Passwortabfrage.

## Regression

20 neue Tests in `tests/routes/test_step_up_return_target.py`:
vier Quellen, zwei problematische URL-Formen und jeweils mit/ohne bestehende
Freigabe; ausserdem Wiederholung nach falschem Passwort, gültiges gespeichertes
Ziel trotz ungültigem Query-Wert, Entfernung unsicherer Altwerte bei Fehlversuch
und direkte interne Rückkehr bei bestehender Freigabe.

Vorher: **18 fehlgeschlagen, 2 bestanden**. Die Tests verfolgen keine externen
Weiterleitungen, sondern prüfen Antwort und Sitzungszustand. Nur synthetische
Konten und Passwörter; keine echten Benutzerdaten. Gesamtlauf über den isolierten
Audit-Teststarter mit SQLite im Speicher, ohne dotenv und ausgehendes Netzwerk.
Testing-CSRF/Rate-Limits sind deaktiviert.

Abschluss: **285 Tests bestanden**, darunter **20 neue Regressionstests**,
in 150,41 Sekunden bei 1927 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups unverändert.

## Grenzen

A-035 ist weiterhin nicht appweit abgeschlossen: Event-, Merch- und
Dokument-Einstiege bleiben separat. Keine Änderung an MFA-Reset, Gerätevertrauen,
Pflichtwechsel oder globalem Sitzungswiderruf. Die Zielroute prüft ihre eigenen
Zugriffsrechte weiterhin selbst. Keine Templates, Assets, Migrationen, Schlüssel
oder Produktionsdaten geändert. Kein Push, Deploy oder Merge auf master.
Planungsunterlagen und fremde lokale Dateien bleiben erhalten.

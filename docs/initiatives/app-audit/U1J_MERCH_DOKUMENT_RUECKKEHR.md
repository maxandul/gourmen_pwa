# U1j – Sichere Rückkehr bei Merch und Dokumenten

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1j-merch-docs-return-target`, Basis U1i-Commit `ff67223`.
Umfang: verbleibende konkret dokumentierte A-035-Einstiege. Keine neue Audit-Runde.

## Änderung

`admin.update_order_status` und die Dokumentaktionen `rename`, `move`, `archive`
und `restore` prüfen Formular-`next` mit `SecurityService.local_return_target()`.
Externe/protokollrelative Ziele werden verworfen. Die bisherigen internen
Fallbacks bleiben erhalten: Bestelldetail, Dokumentordner bzw. Dokumentdetail.
Gültige interne Ziele behalten Query und Fragment. Erfolgreiches Archivieren
und Wiederherstellen führen weiterhin in den festgelegten Archiv-/Zielordner.

Zusammen mit U1g, U1h und U1i sind damit die in A-035 dokumentierten Einstiege
lokal korrigiert. Das ist kein Nachweis über jede denkbare App-Weiterleitung
oder ein vollständiger Abschluss des Gesamtpakets U1.

## Regression

62 neue Tests in `tests/routes/test_merch_docs_return_target.py`:

- Vier Dokumentaktionen mit Erfolg, Validierungs-/Servicefehler und fehlendem
  Zielordner; externe, protokollrelative und interne Rückkehradressen.
- Originale CSRF-Prüfung mit gültigem Testtoken; ohne Token keine Serviceaktion.
- Merch-Erfolg, ungültiger Status und abgefangener Fehler des Buchhaltungsservices;
  internes Ziel und sichere Fallbacks. Bestellstatus aus neuer DB-Session geprüft.
- Mitglied ohne Adminrolle kann den Bestellstatus nicht ändern.

Vorher: **29 fehlgeschlagen, 33 bestanden**. Nach Fix: **62 bestanden**.
Drive- und Buchhaltungsaufrufe sind simuliert; keine echten Dateien, Bestellungen
oder externen Dienste berührt. Originalrouten und synthetische DB-Datensätze;
SQLite im Speicher über isolierten Audit-Teststarter ohne dotenv und Netzwerk.
Gesamtlauf: **387 Tests bestanden**, darunter **62 neue Regressionstests**,
in 241,08 Sekunden bei 2805 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups unverändert.

## Grenzen

Keine Änderung der bestehenden Datei-/Merchrechte, Status- oder Geldflussregeln.
Der aktuelle Merch-Pfad speichert den Status bereits vor der Folgeaktion in der
Buchhaltung. Der simulierte Folgefehler prüft hier nur sichere Rückkehr und hält
dieses bestehende Verhalten fest; atomare Geldflüsse sind weiter Aufgabe von U2.
Der separate Merch-v2-Branch wurde nicht integriert. Keine Live-Drive-Abnahme
und keine neue Lösch-/Archivfreigabe. Templates, Assets, Mockups, Produktionsdaten
und Schlüssel bleiben unverändert. Kein Push, Deploy oder Merge auf master.
Fremde lokale Dateien und Planungsunterlagen erhalten.

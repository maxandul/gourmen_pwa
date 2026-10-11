# U1a – Daten bei Lesefehlern bewahren (A-086)

Stand: 11. Oktober 2026. Ausschliesslich lokale Umsetzung des separat
beauftragten Einstiegspakets; keine Gesamtabnahme von U1.

## Geprüfte Basis

- Ausgangspunkt: Planungsbranch `codex/app-audit-handoff-2026-10-10`, `551e1ef`.
- Lokaler `master`: `bf4d84a`; frisch abgerufener `origin/master`: `d5aa4d5`.
  Die sieben neueren Commits betreffen Icons/Assets und zugehörige Dokumentation/
  Tests. Keine Unterschiede in den betroffenen Backend-Lesepfaden.
- Feature-Branch `codex/u1a-preserve-sensitive-data` von `551e1ef`, darauf
  `origin/master` konfliktfrei integriert: lokale Basis `bc03b51`.
  Beide Vorgänger sind enthalten; master und Planungsbranch unverändert.
  Kein Einmischen von `phase/10-merch-wip`.
- Fremde unversionierte Dateien erhalten: `build_logs.txt`, drei Game-Dokumente,
  `static/js/pwa.6af171c6.js` und `static/js/pwa.fa8699c7.js`.

## Änderung

Eigene sensible Profildaten und Admin-Zugriff lesen den vorhandenen Payload
jetzt vor GET **und POST** über denselben Service-Helfer. Nicht entschlüsselbare
oder strukturell unbrauchbare Daten brechen den Vorgang ab. Datensatz, Payload
und Zeitstempel bleiben erhalten. Es gibt weder automatische Löschung noch ein
leeres Ersatzformular, auch nicht bei direktem POST oder wiederholtem Versuch.

Die bestehende technische Fehlerseite antwortet mit HTTP 500 und erklärt per
Flash-Meldung, dass nichts gespeichert wurde und erneutes Öffnen bzw. Klärung
mit dem Administrator möglich ist. Warnlog und Meldung enthalten keine
ursprünglichen Exceptions, Schlüssel, verschlüsselten oder entschlüsselten Inhalte.
Nur ein wirklich fehlender Datensatz erlaubt weiterhin eine Ersterfassung.

Audit-Logging liegt ausserhalb der Lesefehlerbehandlung: ein Protokollfehler
darf ebenfalls keine Löschung auslösen. Der bestehende allgemeine Umgang mit
Audit-Ausfällen wird nicht neu gestaltet. Für den gesunden Admin-Lesepfad wird
das bereits vom Template erwartete `FlaskForm` übergeben (minimal notwendige
Korrektur des in A-087 belegten Renderfehlers für den U1a-Positivtest).
Keine Templates, Assets, Rechte, MFA-Logik oder Datenbankschemata geändert.

## Regression und Reproduktion

`tests/routes/test_sensitive_data_preservation.py` prüft echte Routen und
Templates mit synthetischen Konten und jeweils neuem Testschlüssel im Prozess.
SQLite nur im Speicher; Datenbankzustand wird in neuer Session nachgelesen.

- Vor dem Fix: erster Lauf 20 fehlgeschlagen, 2 bestanden. Gezielte Folgeprobe
  zeigt Löschung beim eigenen GET, Admin-Templatefehler nach dem defekten Lesepfad
  und tatsächliches Überschreiben bei direkten POSTs beider Routen.
- Fehlervarianten: beschädigter Payload, unpassender/fehlender/ungültiger
  Testschlüssel, ungültiges JSON/UTF-8, JSON ohne Objektstruktur und injizierte
  Exception mit synthetischem Geheimnis. Jeweils GET und POST als erster Versuch,
  Wiederholung, unveränderte ID/Payload/Zeitstempel und keine Geheimnisse in
  Antwort/Logs.
- Positiv: vorhandene Daten lesen/ändern, fehlende Daten neu erfassen und
  Wiederholung nach vorübergehendem Lesefehler.
- Zusätzlich: Audit-Ausfall erhält den Bestand; GET/POST ohne frische
  Passwortbestätigung erreichen die Entschlüsselung weiterhin nicht.

Ausführung mit gebündeltem Python und vorhandenen Projektpaketen, weil der
lokale venv-Starter auf eine hier nicht verfügbare Python-Installation zeigt.
Der vorhandene Audit-Teststarter verhindert dotenv-Laden und ausgehendes Netzwerk:

```python
import runpy
runpy.run_path('docs/initiatives/app-audit/run_existing_tests.py', run_name='setup')
import pytest
raise SystemExit(pytest.main([
    'tests/routes/test_sensitive_data_preservation.py', '-q',
    '--disable-warnings', '-p', 'no:cacheprovider',
]))
```

Für die gesamte vorhandene Suite stattdessen `tests` als Testpfad verwenden.

Abschlusslauf: **118 Tests bestanden**, einschliesslich **44 gezielter U1a-Fälle**,
in 64,44 Sekunden. Keine fehlgeschlagenen oder übersprungenen Tests.
Der Lauf meldete 1065 Warnungen (unter anderem bestehende SQLAlchemy-
Legacy-API- und `datetime.utcnow()`-Deprecations); keine Warnungsbereinigung in U1a.
`git diff --check` bestanden. Templates/Assets entsprechen unverändert
`origin/master`; gesicherte Mockups entsprechen unverändert `551e1ef`.

Der U1a-Code-/Dokumentationsdiff wird als lokaler Commit über `bc03b51`
gesichert, einschliesslich der neuen Test- und Nachweisdateien. Kein Push erfolgt.

## Grenzen

Keine Produktions-/Postgres-/Browser- oder Nebenläufigkeitsabnahme. CSRF und
Rate-Limits sind in der vorhandenen Testing-Konfiguration deaktiviert.
Kein Zugriff auf echte Mitgliederdaten, keine produktive Reparatur, Migration,
Schlüsselrotation, Veröffentlichung, Deployment oder Zusammenführung auf master.
Der Fix repariert keinen unlesbaren Inhalt; er bewahrt ihn für eine gesonderte
Ursachenklärung. Historische Auditdateien bleiben als ursprüngliche Nachweise erhalten.

# U1d – Cron-Testzugang absichern

Stand: 11. Oktober 2026. Fortsetzung auf Nutzerauftrag «ok weiter».
Branch `codex/u1d-cron-test-access` über geprüftem U1c-Commit `f31c688`.
Vorhandener Befund A-113; kein neuer Gesamtaudit, keine Fremdbranch-Integration.

## Umfang und Abnahme

`/cron/test` darf ohne explizite Freischaltung keinen Versandservice erreichen.
Auch bei Freischaltung muss ein konfiguriertes Cron-Token gültig mitgegeben werden.
Die bisherige Abhängigkeit von `ENV == production` entfällt: Flask setzt diesen
Wert in der vorhandenen ProductionConfig nicht, daher war die Sperre unwirksam.

- `Config.CRON_TEST_ENABLED=False` sperrt Basis-, Production- und TestingConfig.
  `DevelopmentConfig` setzt explizit `True`. Nur der boolesche Wert `True` öffnet
  den Pfad, keine wahrheitsähnlichen Strings oder Zahlen.
- Nach Freischaltung verwendet der Testpfad die bestehende Cron-Token-Prüfung,
  ausdrücklich ohne lokale Ausnahme für ein fehlendes Token. Fehlende/falsche
  Berechtigung ergibt HTTP 401, nicht freigeschalteter Endpunkt HTTP 403.
- Die bisherigen drei Token-Transportwege bleiben verfügbar: `X-Cron-Auth`,
  Bearer-Header und Query-Fallback. Für lokale Aufrufe Header bevorzugen.
- Reguläre Cron-Endpunkte behalten ihre bisherige Prüfung einschliesslich der
  lokalen Ausnahme ohne konfiguriertes Token. Keine Änderung an Auswahl,
  Ausführung oder fachlichem Ergebnis der Reminder-Services.
- Kein neuer ENV-Schalter: Freischaltung über die Python-Konfigurationsklasse,
  bestehendes `CRON_AUTH_TOKEN` unverändert. Keine Hosting-Konfiguration geändert.

## Regression

`tests/routes/test_cron_test_access.py` verwendet echte Konfigurationsklassen
in einer isolierten Flask-App mit Original-Blueprint. Kein Produktions-Appstart
und keine Produktions-DB-Verbindung; der Versandservice ist vollständig gemockt.

Vor Fix: **17 fehlgeschlagen, 8 bestanden**. Nach Fix: **25 bestanden**.
Abdeckung: Standardsperre mit/ohne Token; fehlende, falsche und nicht-boolesche
Freischaltung; DEBUG/ENV/TESTING als unzulässiger Ersatz; lokale Ablehnung ohne
oder mit falschem Token; alle drei gültigen Tokenwege; lokale erfolgreiche
Ausführung; unveränderter regulärer Cron-Vertrag; GET führt nichts aus.
Neben HTTP-Antworten wird geprüft, dass der Versandservice bei Ablehnung nie
und bei Freigabe genau einmal aufgerufen wird. Synthetisches Token, keine Mail
und keine Push-Nachricht versendet.

Gesamtlauf über den vorhandenen isolierten Audit-Teststarter mit gebündeltem
Python: dotenv und Netzwerk blockiert, SQLite im Speicher, keine Secrets aus
lokalen ENV-Dateien.

Abschlusslauf: **180 Tests bestanden**, einschliesslich **25 neuer U1d-Tests**,
in 71,32 Sekunden; keine fehlgeschlagenen oder übersprungenen Tests.
1273 bestehende Legacy-/Deprecation-Warnungen; keine Warnungsbereinigung in U1d.
`git diff --check` bestanden. Templates/Assets unverändert gegenüber `f31c688`,
Mockups unverändert gegenüber `551e1ef`. Code, Tests und Dokumentation werden
gemeinsam als lokaler Commit gesichert.

## Grenzen

Keine Aussage über bisherige tatsächliche Aufrufe in Railway. Kein globaler
Reminder-/Cron-Audit, keine Änderung am öffentlichen Statuspfad oder den
separaten Befunden A-043/A-111/A-112. CSRF-Ausnahme des Scheduler-Testpfads bleibt
bestehen; dessen Zugriff ist jetzt durch Freischaltung plus Cron-Token geschützt.
Keine neuen Fachregeln, Migrationen, Dependencies, Schlüsselrotation oder
Produktionsdatenänderung. Kein Push, Deployment oder Merge auf master.
Planung, Mockups und fremde lokale Dateien bleiben erhalten.

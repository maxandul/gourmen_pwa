# U1b – Geheimnisse aus Logs entfernen

Stand: 11. Oktober 2026. Separat beauftragte lokale Fortsetzung nach U1a.
Grundlage: vorhandene Befunde A-081 und A-110, kein neuer Gesamtaudit.
Branch `codex/u1b-secret-safe-logging`, Basis `9cf5126` (geprüfter U1a-Commit).
Der Planungsstand `551e1ef` und der zuvor abgeglichene `origin/master`-Stand
`d5aa4d5` sind enthalten; keine neue Übernahme fremder Änderungen.

## Umfang und Verhalten

- MFA-Einrichtung protokolliert weder neue noch wiederverwendete Secrets oder
  Mailadressen. TOTP-Prüfung protokolliert nur das Ergebnis und berechnet keinen
  zusätzlichen aktuellen Code mehr für Debug-Ausgaben.
- Places-Autocomplete und Details protokollieren Vorgang, HTTP-Status und
  gegebenenfalls Ergebnisanzahl. Keine Parameter, Suchwerte, vollständigen
  Antworten, freien API-Status-/Fehlertexte oder Exceptions: diese können
  API-Schlüssel, Sitzungstokens oder vollständige Anfrage-URLs enthalten.
  Request-Parameter und fachliche Rückgaben bleiben unverändert.
- Im direkt betroffenen Auth-Code war zusätzlich die vollständige
  Passwortbestätigungs-Anfrage einschliesslich Passwort geloggt. Diese Ausgabe
  sowie Rückkehr-URL-/Query-Logs in Step-up und dessen Decorator sind entfernt.
  Der unmittelbare Logging-Nachtrag wird hier dokumentiert, keine neue
  fachliche Zugangsregel eingeführt.
- Bestehende Audit-Ereignisse bleiben bestehen. Keine Änderung an Rollen,
  Sitzungsfristen, MFA-Akzeptanzfenster, Datenbankschema, Templates oder Assets.

## Prüfung

Neue Regressionen in `tests/services/test_secret_safe_logging.py` und
`tests/routes/test_auth_secret_logging.py` verwenden ausschliesslich synthetische
Werte. Sie kontrollieren formatierte Logs **und rohe LogRecord-Argumente**.

Der erste Lauf vor dem Fix scheiterte in allen 18 anfänglichen Fällen an den
Logging-Prüfungen. Nach dem Fix bestanden diese 18 Tests. Zusätzlich ergänzt:
Step-up-Decorator mit Token in der URL und beide bestehenden Places-Fallbacks
ohne konfigurierten Schlüssel.

Abdeckung: neue/fortgesetzte MFA-Einrichtung mit ungültigem und gültigem Code,
erfolgreicher/abgelehnter MFA-Login, Passwortbestätigung samt Rückkehrziel,
TOTP-Service, Places-Erfolg, API-Ablehnung, HTTP-/Verbindungs-/JSON-Fehler.
Auch Funktionsresultate, MFA-Datenbankzustand, Sitzungszustand und unveränderte
API-Parameter werden geprüft. Places ist gemockt, keine Google-Anfrage.

Ausführung wie bei U1a: gebündeltes Python mit vorhandenen Projektpaketen;
`run_existing_tests.py` wird mit `run_name='setup'` geladen, danach `pytest.main`
mit den beiden Testpfaden bzw. `tests` für den Gesamtlauf aufgerufen.
Der Starter unterbindet dotenv-Laden und ausgehendes Netzwerk. SQLite im Speicher,
Testing-CSRF und Rate-Limits aus. Keine echten Schlüssel oder Logbestände gelesen.

Abschlusslauf: **139 Tests bestanden**, darunter **21 neue U1b-Regressionen**,
in 67,91 Sekunden. Keine fehlgeschlagenen oder übersprungenen Tests.
1122 Warnungen, insbesondere bestehende SQLAlchemy-Legacy- und datetime-
Deprecations; keine Warnungsbereinigung in diesem Paket.
`git diff --check` bestanden. Templates/Assets unverändert gegenüber `9cf5126`,
Mockups unverändert gegenüber `551e1ef`. Code, Tests und Dokumentation werden
gemeinsam als lokaler U1b-Commit gesichert.

## Grenzen

Kein Nachweis, ob historische Produktionslogs Geheimnisse enthalten; keine
Log-Löschung, Schlüsselrotation oder Änderung am Hosting. Keine Garantie für
separat konfigurierte Proxy-, HTTP-Wire- oder Fremdbibliotheks-Debuglogs.
U1b sichert die beschriebenen Anwendungslogs, keine Gesamtabnahme aller Logquellen.
Keine Behebung anderer MFA-/Widerrufs-/Cachebefunde in diesem Paket.
Keine Veröffentlichung, kein Push, kein Deploy, kein Merge auf master.
Fremde lokale Dateien, Planungsunterlagen und historische Auditbelege erhalten.

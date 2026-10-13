# U1t / A-076: ersten Passwortwechsel durchsetzen

Stand: 13.10.2026. Lokale Fortsetzung auf «ok weiter», Basis `de095b0`,
Branch `codex/u1t-required-password-change`.

## Technischer Vertrag

`password_changed_at IS NULL` bleibt das bestehende Kriterium. Nach Passwort
und gegebenenfalls MFA wird die Sitzung eingeschränkt: zentrale Request-Prüfung
vor allen Fachseiten, Adminaktionen, APIs, Step-Up und MFA-Verwaltung. Kein neues
Schema oder neues Rollenmodell. Passwortwechsel und Logout bleiben möglich.
Öffentliche Seiten, statische Assets/SW/Health, unabhängig authentifizierte
Cron-/Kalenderzugriffe und bestehende tokengebundene Passwort-/Aktivierungs-/
MFA-Resetwege behalten ihre eigenen Prüfungen. Anonyme Anmeldung/MFA unverändert.

Alle erfolgreichen Loginzweige priorisieren den Pflichtwechsel vor `next`.
Das geprüfte ursprüngliche Ziel wird kontogebunden in der Sitzung aufbewahrt;
Login/Logout/Cookie-Wiederanmeldung entfernen es. Auth-Zwischenziele werden nicht
gespeichert. Direkte spätere GETs ersetzen ein vorhandenes gültiges Ziel nicht.
POSTs werden weder als Rückkehrziel gespeichert noch nach dem Wechsel wiederholt.
HTML wird zum Passwortwechsel umgeleitet (303 bei Mutation), JSON/API bekommt
403 mit festem Fehlercode und Ziel. Antworten der Sperre sind `no-store`.
Ungültige Passwörter oder fehlgeschlagener Commit lassen Pflicht und Ziel bestehen.
Erst erfolgreicher Passwortwechsel verbraucht das Ziel; sonst Dashboard. Normaler
freiwilliger Passwortwechsel behält den bisherigen Profil-Rückweg.

## Nachweise und Grenzen

Die gezielte Regression bestand zunächst mit 46 Tests. Zwei zusätzliche gezielte
Prüfungen bestätigen das unveränderte Rückkehrziel bei direkter Navigation,
einschliesslich eines abschliessenden Fragezeichens im Query-Wert. Die Datei
`tests/routes/test_required_password_change.py` enthält damit 47 Testfälle.
Abgedeckt sind alle fünf Loginzweige, direkte Fach-/Adminzugriffe, HTML-/JSON-
Mutationen, CSRF, Cookie-Wiederanmeldung, kontogebundene Ziele sowie Passwort-
und Commitfehler. Der vollständige Testlauf bestand mit **628 Tests** in
715,22 Sekunden (5726 Warnungen, keine Fehler). Er wurde vor dem zusätzlichen
Query-Grenzfall gestartet; die abschliessende Korrektur am Erhalt des Query-Werts
ist separat mit **2 bestandenen Tests** nachgewiesen (45 abgewählt).

Alle Tests laufen über `run_existing_tests.py`: SQLite im Speicher, dotenv
deaktiviert und ausgehende Socket-Verbindungen gesperrt. Synthetische Testkonten
für andere Fachtests markieren einen bereits abgeschlossenen Passwortwechsel
ausdrücklich; keine Ausnahme von der Sperre für Testing und keine abgeschwächten
fachlichen Assertions. Keine Schema- oder UI-Änderung, kein PWA-Bump erforderlich.
Kein allgemeiner Sitzungs-/Gerätewiderruf, kein neuer Recovery-Vertrag, keine
Produktion, kein Push, Merge oder Deploy. Echte Geräte und PostgreSQL separat.

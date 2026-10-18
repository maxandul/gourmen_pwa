# U1-R04b1 – Grundlage gezielter Bereichsfreigaben

18.10.2026, Basis a0cb070. Schnitt aus U1-R04b vor Implementierung:

Persistente Freigaben je Mitglied und Scope mit Vergabe-/Widerrufsperson und
Zeitpunkt. Eine aktive Zeile je Mitglied/Scope; erneute Vergabe erzeugt neuen
Verlaufseintrag. Admin verwaltet mit eigener Aktion area_permissions und frischem
Passwort; Ziel-Zugangsversion rotiert atomar (alte Sitzungen/Step-Up/Token weg).
Keine Auto-Vergabe, keine neue Adminrolle, kein Ersetzen vorhandener Funktionsrechte.
Unbekannte Scopes werden abgelehnt. Erste konkret durchgesetzte Freigabe:
travel_documents (sechs Pass-/ID-Felder aus R04a, weiterhin Step-Up).
Weitere Scopes erst mit ihrem getrennten Durchsetzungspaket in der UI anbieten.
GET eigener Freigaben fuer das Mitglied, fremde Verwaltung nur Admin.

Migration getrennt; SQLite Upgrade/Downgrade/Upgrade mit synthetischer Mitgliedzeile
und Unique-Negativtest. PostgreSQL-Parallelitaet bleibt externe Abnahme.
Folge: R04b2 Finanzbereich, R04b3 Reisen, R04b4 Merch; R04c Dokumentbereiche separat.

## Abschlussnachweis

Migration separat `ee39355`. Erste isolierte Regression 23 bestanden; Abschlusslauf
56 bestanden, 1177 bestehende Warnungen (Exit 0), dazu 19 Worker-Tests bestanden.
Python-Dateien: tests/models/test_member_area_grant_migration.py,
tests/routes/test_member_area_permissions.py, test_travel_sensitive_fields.py,
test_action_confirmation.py; Runner per runpy wie U1z mit -q --disable-warnings
--tb=short -p no:cacheprovider. Ignorierte pyreadline-Destruktorwarnung beim Ende.
SQLite-Migrationszyklus und aktiver Unique-Index geprueft; keine PostgreSQL-
Parallelitaetsbehauptung. CSRF, falsches Passwort, falsche Aktion/Ziel, Replay,
Rollback nach Commitfehler, alte Sitzung und minimale Rechte abgedeckt.
Cacheversion 3.16.11, PWA-Fingerprint aktualisiert, keine neue UI-Klasse.
`git diff --check` ohne Fehler. Kein dotenv, kein ausgehendes Netz, keine Produktion.
Browserabnahme und PostgreSQL bleiben offen. Core lokal fertig, weitere
Bereichsdurchsetzung separat als R04b2–R04b4; U1 bleibt offen.

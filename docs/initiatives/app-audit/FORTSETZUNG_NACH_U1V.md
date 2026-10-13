# Fortsetzung nach U1v

Stand: 13.10.2026. Einstieg: aktueller Nachtrag in `AGENT_HANDOFF.md`, danach
`RESTABDECKUNG_GESAMTVORLAGE.md` und `U1V_SITZUNGS_GERAETEWIDERRUF.md`.
Nach dem zusammenhängenden Auth-Paket ist ein Agentwechsel sinnvoll. Kein neuer
Chat oder Agent wurde automatisch gestartet und keine Nachricht dorthin gesendet.

## Lokale Basis

- `C:/gourmen_pwa`, Branch `codex/u1v-auth-revocation`. HEAD mit Git prüfen.
- Basis U1u: `f756240`; additive Migration separat: `24e68fc`.
- Die bisherige U1-Branchkette bleibt erhalten. Nicht von master neu starten.
- Nur lokal gesichert, kein Push, Merge, Deploy, Produktionszugriff oder Schlüsselwechsel.
- Fremde unversionierte Dateien erhalten: `build_logs.txt`,
  `docs/GDD_FOOD_POKEMON.md`, `docs/GDD_FOOD_POKEMON_REVIEW.md`,
  `docs/capabilities/game.md`, `static/js/pwa.6af171c6.js`, `static/js/pwa.fa8699c7.js`.

## Nächste zusammenhängende U1-Arbeit

Die bestätigte aktionsgebundene erneute Identitätsbestätigung aus F1 in einen
konkreten technischen Vertrag übersetzen: betroffene Passwort-/MFA-/Berechtigungs-
aktionen, Konto- und Sitzungsbindung, Einmalverbrauch und Verhalten bei Abbruch,
Fehler oder paralleler Änderung. Vorhandenes Step-Up-Fenster aus U1c allein
erfüllt diesen vollständigen Vertrag noch nicht. Bestätigte Fachregeln nicht
erneut pauschal abstimmen; konkrete ungeklärte Fachentscheidung bei Bedarf benennen.
Nicht gleichzeitig das gesamte Rollenmodell und alle Oberflächen umbauen.

Rollen-/Feldmatrix R13, technischer Admin-Notfallweg, Cache-Nutzertrennung und
spätere U2–U6-Pakete bleiben separat. Kein neuer umfassender Audit-/Mockup-Zyklus.

## Offene Abnahmen

- U1 insgesamt ist nicht abgeschlossen.
- PostgreSQL-Parallelität und echte Geräte sind durch SQLite-Tests nicht bewiesen.
- U1v ändert die Login-ID: vorherige Cookies werden abgewiesen. Migration/Appwechsel
  und Rollback vor Veröffentlichung koordinieren, keine ungeprüften Mischversionen.
- Widerruf stoppt bereits laufende Requests nicht rückwirkend.
- Aktuelle Testnachweise und gegebenenfalls Einschränkungen im U1v-Paket lesen.

## Isolierter Testlauf

Interpreter:
`C:/Users/ulric/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Vor pytest `runpy.run_path('docs/initiatives/app-audit/run_existing_tests.py',
run_name='setup')` laden: Projektpakete, kein dotenv, SQLite im Speicher,
ausgehende Verbindungen blockiert. Danach pytest mit `--tb=short`,
`--show-capture=no`, `--disable-warnings` und `-p no:cacheprovider` ausführen.
Keine echten Datenbanken zum Testen verwenden. Testfixtures nutzen versionierte
IDs aus `tests.conftest.auth_id`; Legacy-IDs ausschliesslich in Ablehnungstests.

Git benötigt `git -c safe.directory=C:/gourmen_pwa ...`; nur eigene Dateien stagen.
Migrationen weiterhin als separater Commit. AGENTS.md und relevante Anchor-Docs
vor Änderungen lesen, Code/Tests/Paketnachweis und README zusammen pflegen.

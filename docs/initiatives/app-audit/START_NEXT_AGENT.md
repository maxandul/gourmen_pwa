# Neuer Agent: Startauftrag und reproduzierbarer Einstieg

Stand: 10.11.2026. B02-Anwendungsabschluss: `4bc210e`; separate Migration: `b9727e4`. Repository: https://github.com/maxandul/gourmen_pwa
Branch: `codex/app-audit-implementation-plan`. **Nicht master verwenden.**
Dieser Branch enthaelt Code, separat committete Migrationen, Fachentscheidungen,
Tests und Paketnachweise. Kein vorheriger Chat ist erforderlich.

## Kopierbarer Startauftrag

Arbeite im Repository Gourmen PWA auf `codex/app-audit-implementation-plan`
(lokal bisher `C:\gourmen_pwa`). Lies zuerst AGENTS.md,
docs/initiatives/app-audit/AGENT_HANDOFF.md, README.md und IMPLEMENTATION_PLAN.md.
Pruefe Branch, HEAD und lokale Aenderungen. Bewahre die bestehende Branchkette
mit Vorfahr 5b6d28d und fremde Dateien; nicht von master neu beginnen.
Lies vor Code die relevanten Anchor-Docs und Paketquellen.

Setze das naechste bereite Paket U3-02 – GGL-Dashboard-Rangabgleich gemaess Plan
vollstaendig um. Danach selbststaendig am naechsten bereiten Paket weiterarbeiten.
Jedes Paket mit passenden Regressionstests, Dokumentation, aktualisiertem Plan
und Handoff sowie lokalen Commits abschliessen. Migrationen separat committen.
Nur synthetische Daten, kein dotenv oder ausgehende App-Verbindungen.
Kein Push, Merge, Deploy, Produktionszugriff oder Schluesselwechsel. Die einmalige
GitHub-Veroeffentlichung vom 10.11.2026 war nur die Uebergabe, keine allgemeine
Freigabe. Keine anderen Agenten/Chats automatisch starten.
U1 bleibt insgesamt offen. Tatsaechliche Ergebnisse und verbleibende Abnahmen
regelmaessig kurz berichten. Nur konkrete fehlende Fachentscheidungen erfragen;
bestaetigte Regeln nicht erneut abstimmen. Unabhaengige lokale Arbeit fortsetzen,
auch wenn einzelne externe Abnahmen fehlen.

## Checkout und Tests

Bei vorhandenem Checkout zuerst `git status --short`, `git branch --show-current`
und `git log -5 --oneline`; keine fremden Aenderungen zuruecksetzen.
Bei frischem Checkout genau diesen GitHub-Branch auswaehlen. Python 3.11 laut
Architektur, Abhaengigkeiten in requirements.txt (inklusive pytest); Node fuer
JS-Tests. Eine frische Testumgebung braucht diese Abhaengigkeiten vorab aus
einem erlaubten Paketcache/Setup. Venv, dotenv, echte Daten und Schluessel
sind absichtlich nicht im Repository und fuer synthetische Tests nicht noetig.
Keine App normal starten, keine lokale DB migrieren, keine Secrets beschaffen.

Vollstaendige isolierte Regression aus Repository-Wurzel:

```text
python docs/initiatives/app-audit/run_existing_tests.py
node --test tests/js/sw_cache_isolation.test.cjs tests/js/merch_order_edit.test.cjs
```

Der Runner entfernt Umgebungswerte, sperrt dotenv und ausgehende Sockets und
nutzt synthetische Fixtures. Er fuegt den bisherigen Windows-venv-Pfad hinzu;
auf einem frischen System muss der verwendete Python-Interpreter die
requirements.txt-Abhaengigkeiten installiert haben. Keine Installation durch
den Testlauf. Tests pruefen SQLite, keine echten PostgreSQL-Sperren.

Gezielter letzter B02-Abschlusslauf (122 bestanden):

```text
python -c "import runpy,sys; runpy.run_path('docs/initiatives/app-audit/run_existing_tests.py',run_name='audit_bootstrap'); import pytest; sys.exit(pytest.main(['tests/services/test_private_reminders.py','tests/services/test_private_reminder_migration.py','tests/services/test_billbro_private_clarification.py','tests/services/test_billbro_finance.py','tests/services/test_billbro_correction.py','tests/services/test_bank_import.py','tests/routes/test_event_visibility.py','-q','--disable-warnings','--tb=short','-p','no:cacheprovider']))"
```

122 Python- und 24 JS-Tests am 10.11.2026 bestanden. Historischer Gesamtlauf
1510 Tests war vor c1b2/B02 und ist kein aktueller Gesamtbeleg. Bei Windows
trat nach Testende ein ignorierter pyreadline3-Handlefehler auf (Exit 0).
Weitere konkrete Ergebnisse stehen in den jeweiligen Paketnachweisen.

## Grenzen und Orientierung

- U1z ist bereits umgesetzt; nicht dort erneut beginnen. Genau ein naechstes
  Paket im IMPLEMENTATION_PLAN ist massgeblich. Alte datierte Fortsetzungen
  und Audit-CSV sind Verlauf, keine konkurrierende Warteschlange.
- B02 ersetzt private Zahlungsbestaetigung durch eigene Anzeige-Praeferenz;
  Altwerte bleiben Historie. Migration b9727e4 ist separat und nicht live
  angewandt. Verwendete Praeferenzen sperren ihren Downgrade.
- Bezahlter Glaeubigerwechsel G1, Merch-Runden/Zuschuesse/Korrekturen und
  weitere U2-U6-Arbeit bleiben offen. Bereits bestaetigte Regeln stehen
  im Handoff und in den dort verlinkten Fachvertraegen.
- PostgreSQL, echte Browser/PWA/Geraete, Mail/Drive und Hosting-Recovery
  brauchen externe Nachweise. D-01 Google-Mehrfachzuordnung bleibt fachlich offen.
- Fremde lokale unversionierte Dateien laut Handoff wurden nicht veroeffentlicht.
  Sie gehoeren nicht zur App-Audit-Uebergabe; keine Testabhaengigkeit davon.
- Kein Merge auf master: dieser kann Railway-Deployment ausloesen.

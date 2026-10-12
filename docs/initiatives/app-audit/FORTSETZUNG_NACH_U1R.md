# Fortsetzung nach U1r – vorbereiteter Agentwechsel

Stand: 12. Oktober 2026. Diese Datei ergänzt den aktuellen Einstieg in
`AGENT_HANDOFF.md`; ältere Planungsstände bleiben als Verlauf erhalten.
Der Nutzer hat um eine Mitteilung gebeten, sobald ein Agentwechsel sinnvoll ist.
Nach den zusammenhängenden Passwort-/MFA-Linkkorrekturen ist dies ein geeigneter
Schnitt. Es wurde kein neuer Chat/Agent gestartet und keine Nachricht dorthin gesendet.

## Gesicherte lokale Basis

- Arbeitsverzeichnis `C:/gourmen_pwa`, Branch `codex/u1r-mfa-link-revocation`.
- Basis von U1r: `0c9543a` (U1q). Den aktuellen U1r-HEAD vor Fortsetzung mit Git
  prüfen; den Branch fortsetzen bzw. einen neuen Feature-Branch davon erstellen.
- Die vorherigen Pakete U1a–U1q sind in der lokalen Branchkette enthalten.
  Planung `551e1ef` ist Vorfahr. Nicht von master neu beginnen oder lokale
  Planungsunterlagen durch einen anderen Checkout ersetzen.
- Code, Regressionstests und Paketnachweise sind lokal gesichert. Nicht gepusht,
  nicht auf master gemergt, nicht deployed. Testergebnis in `U1R_MFA_LINK_WIDERRUF.md`.
- Fremde unversionierte Dateien erhalten: `build_logs.txt`,
  `docs/GDD_FOOD_POKEMON.md`, `docs/GDD_FOOD_POKEMON_REVIEW.md`,
  `docs/capabilities/game.md`, `static/js/pwa.6af171c6.js`, `static/js/pwa.fa8699c7.js`.
  Nicht löschen, verändern oder pauschal mit committen.

## Nächster zusammenhängender Arbeitsblock: A-089

Bestätigt in `KONTO_ZUGANG_ENTWURF.md`: Bei Google-Adresswechsel und Deaktivierung
müssen alte Drive-Rechte entzogen werden. Externe Fehler bleiben als konkrete,
offene Adminaufgabe sichtbar. Ein zusätzlicher synchroner API-Aufruf allein
reicht dafür nicht; den Block nicht mit einer solchen Teilkorrektur abschliessen.

Vor Codeänderung den technischen Vertrag konkretisieren und vorhandene Muster
lesen: dauerhaft gespeicherter Widerrufsauftrag mit altem Adress-/Permission-Bezug,
atomare Erfassung zusammen mit Adresswechsel/Deaktivierung, Status und sicherer
Wiederholungsweg, sichtbare Adminaufgabe, Behandlung von Teilfehlern und bereits
fehlender Berechtigung. Zusammenspiel mit laufenden Einladungen aus U1o sowie
mehrmaligem Adresswechsel berücksichtigen. Neue Migration separat committen.
Keine echten Drive-Rechte oder Produktionsdaten während lokaler Umsetzung ändern.

## Nicht als erledigt voraussetzen

- Kein Gesamtabnahme- oder vollständiger U1-Abschluss.
- PostgreSQL-Paralleltests insbesondere für U1o/U1p/U1q/U1r noch offen.
- U1k ist funktional geprüft, die visuelle Browserabnahme bleibt offen.
- A-076 Pflichtwechsel, allgemeiner Sitzungs-/Gerätewiderruf und umfassende
  Recovery-/Berechtigungsverträge sind nicht durch Linkwiderruf ersetzt.
- Bestätigte Fachregeln nicht erneut abstimmen, kein neuer Gesamtaudit oder Mockup-Zyklus.

## Lokale Tests

Der venv-Starter verweist auf eine hier nicht verfügbare Python-Installation.
Verwendet wurde der gebündelte Interpreter:
`C:/Users/ulric/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.

Vor pytest den vorhandenen `docs/initiatives/app-audit/run_existing_tests.py`
mit `runpy.run_path(..., run_name='setup')` laden. Er bindet Projektpakete ein,
verhindert dotenv und blockiert ausgehendes Netzwerk. Gesamtlauf:
`pytest.main(['tests', '-q', '--tb=short', '--show-capture=no', '--disable-warnings',
'-p', 'no:cacheprovider'])`. Synthetische Daten, SQLite im Speicher; externe Dienste
gezielt ersetzen. Keine lokalen oder produktiven Datenbanken für diese Tests verwenden.
Git benötigt hier `git -c safe.directory=C:/gourmen_pwa ...`; nur eigene Dateien stagen.

## Kopierbarer Einstieg für den nächsten Chat

Arbeite lokal in C:/gourmen_pwa. Übernimm den gesicherten Stand auf
codex/u1r-mfa-link-revocation. Lies AGENTS.md, den aktuellen Einstieg in
docs/initiatives/app-audit/AGENT_HANDOFF.md, diese Fortsetzungsdatei und die dort
verlinkte Gesamtvorlage. Prüfe Branch, HEAD und lokale Dateien vor Änderungen.
Bearbeite als nächsten zusammenhängenden Schritt A-089: dauerhaften Drive-Widerruf
bei Adresswechsel und Deaktivierung mit sichtbarer offener Adminaufgabe und
sicherer Wiederholung. Konkretisiere den technischen Vertrag vor der Umsetzung;
Code, gezielte Regressionstests und Dokumentation gehören zusammen. Migrationen
separat committen. Bewahre Planungsunterlagen und fremde Dateien. Kein neuer
Gesamtaudit, keine erneute Abstimmung bestätigter Fachregeln, kein Push, Deploy,
Merge auf master, Produktionsdatenzugriff oder Schlüsselwechsel. Berichte ehrlich
über lokale Nachweise und verbleibende PostgreSQL-/Geräteabnahmen.

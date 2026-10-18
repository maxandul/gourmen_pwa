# Agenteneinstieg: App-Audit-Umsetzung

Stand: 18.10.2026. **U1 ist insgesamt offen.**

1. `AGENTS.md` und [README](README.md) lesen, danach den
   [verbindlichen Umsetzungsplan](IMPLEMENTATION_PLAN.md). Dieser enthält die
   aktuelle Reihenfolge, Restarbeit, Fachquellen und Abschlusskriterien.
2. Bestehende Kette auf `codex/app-audit-implementation-plan` erhalten. Einstieg
   war `5b6d28d`; U1z baut darauf auf. Branch/HEAD/Status pruefen, nicht zuruecksetzen.
3. Naechstes Paket: **U1-R06 – irrefuehrenden Backup-QR entfernen** nach U1_R04_RECHTEMATRIX.md. U1z, U1-R02 und U1-R03 sind
   lokal geprueft (Nachweise im README). Interne Einzelbewertungen sind nach
   bestaetigter Entscheidung fuer alle Mitglieder mit Eventzugriff lesbar.
4. Vor Codeänderungen relevante Anchor-Docs und Paketquellen lesen. Bestätigte
   F1/F2/R13-Regeln gelten; nur konkret fehlende Entscheidungen erfragen.
   Kein gleichzeitiger Gesamtumbau der Rollen und kein neuer Gesamtaudit.
5. Isolierten [Testrunner](run_existing_tests.py) mit synthetischen Daten verwenden,
   ohne dotenv und ausgehende Verbindungen. Versionierte Login-Identitäten aus
   [U1v](U1V_SITZUNGS_GERAETEWIDERRUF.md) beachten. Tatsächliche Testergebnisse
   berichten; PostgreSQL, reale Zustellung, Drive und Geräte nicht als geprüft ausgeben.
6. Paket vollständig mit Regression und Dokumentation lokal sichern. Migrationen
   separat committen. README als Nachweisregister, Plan als aktuelle Restfolge
   pflegen. Genau ein nächstes Paket priorisieren; diese Übergabe kurz halten.

Kein Push, Merge auf master, Deploy, Produktionsdatenzugriff oder Schlüsselwechsel.
Keine fremden unversionierten Dateien anfassen. Beim Einstieg in die Konsolidierung
waren dies `build_logs.txt`, `docs/GDD_FOOD_POKEMON.md`,
`docs/GDD_FOOD_POKEMON_REVIEW.md`, `docs/capabilities/game.md`,
`static/js/pwa.6af171c6.js` und `static/js/pwa.fa8699c7.js`; zusätzlich aktuellen
Git-Status prüfen. Keine Chats oder Agenten automatisch starten.

U1a–U1y samt Prüfnachweisen: [README](README.md). Ältere Übergabe vollständig
bewahrt in [Übergabeverlauf](AGENT_HANDOFF_HISTORY_20261016.md); dessen damalige
Startanweisungen und offene Punkte sind keine aktuellen Arbeitsaufträge.

R04c-Altbestand am 18.10. bestaetigt: noch nicht klassifizierte Dateien in der App
nur fuer Systemadmin. Direkte Drive-Freigaben bleiben bis separater Abnahme unveraendert.

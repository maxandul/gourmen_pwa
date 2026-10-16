# Agenteneinstieg: App-Audit-Umsetzung

Stand: 16.10.2026. **U1 ist insgesamt offen.**

1. `AGENTS.md` und [README](README.md) lesen, danach den
   [verbindlichen Umsetzungsplan](IMPLEMENTATION_PLAN.md). Dieser enthält die
   aktuelle Reihenfolge, Restarbeit, Fachquellen und Abschlusskriterien.
2. Tatsächlichen Branch, HEAD und lokale Änderungen prüfen. App-Basis ist
   `3b85caa` (U1y), separate Migration `9405a7a`; die Dokumentationskonsolidierung
   folgt auf `codex/app-audit-implementation-plan`. Bestehende Kette erhalten,
   nicht von master beginnen und nicht auf einen alten Übergabe-Commit zurücksetzen.
3. Nächster lokaler Umsetzungsschritt: **U1z – Cache-Nutzertrennung (A-010)**.
   Vertrag, Quellen und Abnahmekriterien stehen im Plan. Diese Übergabe entstand
   in einem reinen Dokumentationsauftrag; U1z wurde hier noch nicht implementiert.
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

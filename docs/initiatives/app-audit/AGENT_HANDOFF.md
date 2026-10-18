# Agenteneinstieg: App-Audit-Umsetzung

Stand: 18.10.2026. **U1 ist insgesamt offen.**

1. `AGENTS.md` und [README](README.md) lesen, danach den
   [verbindlichen Umsetzungsplan](IMPLEMENTATION_PLAN.md). Dieser enthält die
   aktuelle Reihenfolge, Restarbeit, Fachquellen und Abschlusskriterien.
2. Bestehende Kette auf `codex/app-audit-implementation-plan` erhalten. Einstieg
   war `5b6d28d`; U1z baut darauf auf. Branch/HEAD/Status pruefen, nicht zuruecksetzen.
3. Naechstes Paket: **U2-10 – Organisatorwechsel (A-033)**. U1z, U1-R02 und U1-R03 sind
   lokal geprueft (Nachweise im README). R08 gleicht die U1-Nachweise ab;
   U1 bleibt wegen externer Abnahmen offen; R04d ist lokal in U2-04b/c umgesetzt. Interne Einzelbewertungen sind nach
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

U2-02c1 ist lokal geprueft; Ruecknahmejournal und alte Buchungen bleiben erhalten.
Fuer c2 ist die Fachentscheidung bestaetigt: ausdruecklich zur Rueckzahlung
bestaetigter Eingangsueberschuss auf 3620, tatsaechlicher Ausgang auf 6710.
Keine automatische Ueberweisung. Vertrag/Nachweise: U2_02C_ZUORDNUNGSKORREKTUR.md.

U2-02c2a lokal geprueft: bestaetigter Ueberschuss auf 3620; BankRefundConfirmation
verknuepft Vormerkung und Buchung. U2-02c2b verknuepft den tatsaechlichen Ausgang auf 6710, mit Teilbetraegen,
Jahreswechsel und beidseitigen Ruecknahmegrenzen; 64 Python-/19 Worker-Tests gruen.

U2-05 lokal geprueft (88 und anschliessend 23 Tests): historische inaktive
Konten, Richtungssummen und Budgetvorschlag. Alte Prueffassungen erhalten.

U2-06 lokal geprueft: optionaler Audit-INSERT mit Savepoint, True/False-Ergebnis;
Fachfehler weitergegeben. Erfolgscommit fuer Altaufrufer bleibt, A-046 separat.

U2-07 lokal geprueft: Eventloeschung mit verpflichtendem Audit in einem Commit;
Abhaengigkeiten und BillBro/GGL-Fachhistorie bleiben erhalten (65 Regressionen).

U2-08 lokal geprueft (63 Python-/19 Worker-Tests): strikte BillBro-Betraege,
Feldfehler ohne Teilmutation. A-031 Rundungsregel beim Nutzer angefragt;
Antwort steht noch aus, unabhaengige Pakete weiterfuehren.

U2-09 lokal geprueft (67 Regressionen): Undo vergleicht eigenen Nachzustand
und bewahrt spaetere Fachwerte; technische Fehler erlauben sicheren Retry.

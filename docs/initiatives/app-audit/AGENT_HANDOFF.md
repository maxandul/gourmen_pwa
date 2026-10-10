# Übergabe für die Fortsetzung in ChatGPT Work

Stand: 10. Oktober 2026. Der Nutzer wechselt von der bisherigen App in die neue ChatGPT-App und arbeitet dort ausdrücklich in **Work**, nicht in Codex, weiter. Technische Aufgaben können im zugänglichen Projekt erledigt werden; die Kommunikation bleibt verständlich und auf Ergebnisse ausgerichtet.

## Einstieg und Auftrag

Repository: `maxandul/gourmen_pwa`. Lokaler Projektordner auf dem bisherigen Computer: `C:\gourmen_pwa`.

Zuerst `AGENTS.md` im Repository lesen, danach in diesem Ordner:

1. `GESAMTBEURTEILUNG.md` – erste Gesamtbeurteilung und vorläufiges Zielbild.
2. `README.md` – Auftrag, Entscheidungen und Prüfstand.
3. `COMPLETION_PLAN.md` – offene Prüfbereiche und Abschlusskriterien.
4. `PAKETREGISTER.csv` und bei Bedarf `FINDINGS.md` – Zuordnung aller 141 Befunde zu sechs vorgeschlagenen Umsetzungspaketen und Detailbelege.

Die Analyse soll eine verständliche Entscheidungsgrundlage für die Weiterentwicklung der gesamten App liefern. Sie ist in wiederholte Detailprüfungen abgedriftet. Der Nutzer hat deshalb die Zusammenführung und frühe Zielbildarbeit bestätigt. Die erste Gesamtbeurteilung liegt vor; sie ist keine vollständige Abnahme der App.

## Nächste konkrete Arbeit

Das vorläufige Zielbild anhand der vorhandenen App konkretisieren: grafische Entwürfe für **Dashboard, Eventdetail und Buchhaltung**, jeweils Mobile und Desktop, ergänzt um Tablet-Regeln. Vorhandene Gestaltung und Seitenfamilien berücksichtigen. Dazu die entscheidungsrelevanten Fachfragen für Zugang und Geldflüsse vorbereiten.

Die Entwürfe sollen als Vorschläge beurteilbar sein. Keine neue umfassende Befundsuche beginnen. Zusätzliche Prüfungen brauchen eine konkrete offene Frage und eine Konsequenz für Zielbild, Entscheidung oder Abnahme. Die verbliebenen Abdeckungslücken bleiben im Abschlussplan sichtbar.

## Entscheidungen und Grenzen

- Die vier Hauptbereiche und die Überarbeitung der bestehenden Technik sind vorgeschlagen, noch nicht als endgültiges Design beschlossen.
- Die sechs Umsetzungspakete sind Vorschläge; App-Änderungen, Auth-Änderungen, Migrationen und Deployment sind noch nicht freigegeben.
- Game/Essens-Pokemon bleibt ausgeschlossen. Seine vorhandenen lokalen Dokumente nicht verändern oder löschen.
- Alte Merch-Bestellseiten sollen später entfallen. Die noch vom aktuellen Shop genutzte Bestellverarbeitung muss erhalten oder gezielt umgezogen werden.
- Die Auditbelege beziehen sich auf Codebasis `bf4d84a`. Lokale Reproduktionen sind keine Produktions- oder Geräteabnahme. Neue Codeänderungen erfordern einen erneuten Abgleich der betroffenen Befunde.
- Vorhandene lokale Dateien bewahren. Keine produktiven Daten, Schlüssel oder externen Dienste durch die Entwurfsarbeit verändern.

## GitHub-Sicherung

Für die Übergabe wird ein eigener Branch `codex/app-audit-handoff-2026-10-10` verwendet. Der Name ist nur ein Git-Branchname und legt den Arbeitsmodus nicht fest: Fortsetzung ausdrücklich in **Work**.

Die Sicherung umfasst diesen Auditordner mit Berichten, Prüfskripten, Ergebnisdateien und Browserbelegen sowie den Eintrag in `docs/initiatives/README.md`. Andere bereits vorhandene lokale Dateien, insbesondere `build_logs.txt`, Game-Dokumente und die beiden unversionierten PWA-Hashkopien, gehören nicht zur Sicherung.

Für eine neue Projektkopie den Sicherungsbranch auswählen; die Unterlagen sind nicht durch diese Sicherung automatisch auf `master`. Keine Zusammenführung auf `master` nur für den App-Wechsel, da dies einen Railway-Deploy auslösen kann. Der tatsächliche Upload-Erfolg und der Link zur Sicherung werden nach dem Push in der bisherigen Aufgabe bestätigt.

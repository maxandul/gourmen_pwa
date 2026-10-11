# Merch: Zielversion und Umgang mit Altbestand

Stand: 11. Oktober 2026. Gezielte Versionsklärung, keine neue umfassende Befundsuche.

## Nutzerentscheidung und Ergebnis

Der Nutzer möchte das jüngere, von ihm überarbeitete Merch-System verwenden.
Das alte System darf für den aktiven Betrieb stillgelegt werden; es wurde als
mögliche Quelle für die Übernahme alter Daten behalten. Dies wird als Ziel für
die spätere Umsetzung festgehalten. Im jetzigen Gestaltungsauftrag werden weder
Systeme deaktiviert noch Daten migriert oder gelöscht.

Die Überarbeitung ist **Merch v2 mit Bestellrunden**. Sie liegt in den lokal
vorhandenen Git-Referenzen auf `phase/10-merch-wip` und
`origin/phase/10-merch-wip`, Stand `c90082ea9ef3d686299ddd68b2012ee9e430a11e`
vom 27. Mai 2026. Dieser Commit ist nicht im aktuellen Auditbranch enthalten.
Ein aktueller Server-/Produktionsstand oder frischer Remote-Abgleich wurde damit
nicht nachgewiesen. Der Arbeitsbranch bleibt unverändert.

«Jünger» bezeichnet die neue Systemgeneration. Spätere Wartungscommits am alten
Merch-System machen dieses nicht zur vom Nutzer gemeinten Überarbeitung.

## Konkrete Belege

| Commit | Beleg |
|---|---|
| `8e1ea0b` / `938bee5`, 15.05.2026 | Legacy-Umbenennung/neue Tabellen sowie neues Cockpit, Shop und Warenkorb. |
| `a19797b`, 16.05.2026 | Neuer Merch-Hub unter `/admin/merch-v2/`. |
| `7946b2e` / `13a06cd`, 25.05.2026 | Bestellrunden-Workflow und Überarbeitung der Rückschritte. |
| `c90082e`, 27.05.2026 | Mitgliederworkflow, mehrere Lieferantenbelege, Beleg-Upload und Admin-Fixes. |

Relevante Quellen werden mit `git show phase/10-merch-wip:<Pfad>` gelesen,
ohne Branchwechsel oder Übernahme von App-Code:

- `docs/capabilities/merch.md`
- `docs/initiatives/workspace-railway/PHASE_10_MERCH.md`
- `backend/services/merch_member_workflow.py`
- `backend/services/merch_round_workflow.py`
- `backend/services/merch_round_service.py`
- Bei gezieltem Bedarf weitere v2-Services und Templates derselben Version.

Die Capability beschreibt den Rundenprozess mit Sortiment, Warenkorb pro Runde,
vorläufigen/effektiven Preisen, Subvention, Lieferantenbestellung und getrennter
Abholung/Bezahlung. Der Mitgliederworkflow nennt vier Phasen: Bestellen,
Eingereicht/Preise folgen, Bezahlen, Abgeschlossen. Der Verwaltungsworkflow nennt
acht Phasen von Vorbereitung bis Abschluss. Diese Strukturen sind die Grundlage
des folgenden Darstellungsentwurfs, keine neu erfundenen Anforderungen.

Innerhalb dieser älteren Unterlagen können Entwicklungsstände voneinander
abweichen, etwa bei Rückschritten und Preisbindung. Keine pauschale fachliche
Freigabe aus Dokumenttext ableiten; relevante Unterschiede am festgelegten Commit
gezielt einordnen. F7 bleibt als fachliche Abstimmung offen.

## Auswirkung auf bisherigen Audit- und Gestaltungsumfang

MERCH_REVIEW.md untersuchte das alte System auf Baseline `bf4d84a`. Seine Befunde
bleiben Belege für diese Version. Die bisher als ungeklärte Dokumentationsabweichung
beschriebenen v2-Komponenten existieren auf dem separaten Entwicklungsbranch.
Sie dürfen weder als fehlendes neues Feature noch als bereits im Audit geprüft
bezeichnet werden.

Die 83 Templates in GESTALTUNGSZUORDNUNG.csv bleiben ein Register der Auditbaseline,
keine vollständige Inventarliste der neuen Merch-Zielversion. Auf dem Zielbranch
liegen 15 zusätzliche v2-Templatepfade unter `templates/admin/merch_v2/` und
`templates/merch/`, darunter Teilansichten. Für die Gestaltung ergänzen sie folgende
bereits bekannte Muster:

| Zielbereich | Muster |
|---|---|
| Shop, Rundenshop, Bestellfuss | M08 Shop, M04 Formulare, M05 Prozess |
| Merch-Hub / Rundenübersichten | M02 Einstieg, M06 Listen/Tabellen |
| Rundendetail / Abschluss / Schrittaktionen | M03 Detail, M05 Prozess, M06 Tabellen |
| Artikel-, Lieferanten-, Rundenformular | M04 Formulare |
| Farben-/Grössenpflege | M04 Inline-Bearbeitung, M06 Listen |
| Navigation / weitere Aktionen | M01 Rahmen, M12 Dialog-/Aktionsmuster |

Dies ist eine gezielte Ergänzung der Zielbasis, kein Abschluss eines v2-Audits.
Der kommende Entwurf muss die Mitglieder- und Verwaltungsansicht dieser Version
zeigen. Die alte Shopstruktur wird nicht weiter als Ziel gestaltet.

## Altbestand und spätere Umstellung

Altbestand erhalten, operative Nutzung später deaktivieren. Eine technische
Migrations-/Stilllegungsplanung muss alte Daten, offene Forderungen, Zuordnungen,
Links und gemeinsame Aufrufpfade berücksichtigen. Erst dann entscheiden, welche
historischen Daten ins neue System übernommen werden. Keine Löschfreigabe für
Tabellen oder historische Bestellungen aus der aktuellen Aussage ableiten.

Die v2-Phasendokumentation trennt bereits Legacy-Tabellen und eine spätere
Datenübernahme. Ob diese Migrationen in einer bestimmten Umgebung gelaufen sind,
ist hier ausdrücklich nicht geprüft.

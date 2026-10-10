# Konsolidierter Pruefstand und Weg zum Auditabschluss

Stand: 2026-10-10. Baseline unveraendert bf4d84a. **Gesamtaudit offen.**
Der inhaltliche Einstieg ist die [Gesamtbeurteilung mit vorlaeufigem Zielbild](GESAMTBEURTEILUNG.md).
Dieser Plan bewahrt den Pruefumfang und die Abschlusskriterien der Restarbeit.
Die Teilberichte behalten ihre Belege und historischen Grenzen. Eine alte
Formulierung «offen» ist nicht automatisch der heutige Stand; neuere Nachweise
werden bei der Bearbeitung unten zugeordnet. Keine App-Aenderung beschlossen.

## Was die bisherige Arbeit traegt

141 nummerierte Befunde sind dokumentiert. Die Zahl ist weder Fehlerquote noch
Fortschrittsprozent. Die Nachweise reichen von Strukturbeobachtung bis lokaler
Reproduktion; sie sind keine vollstaendige Produktions- oder Geraeteabnahme.

- Alle 83 Templates strukturell erfasst; sieben Standard-Tab-Systeme und 13
  Filter-Fundstellen verglichen. Grundlage fuer gemeinsame UI-Bausteine liegt vor.
- 150 UI-Registry-Zeilen mit Teilpruefverweisen: 122 teilweise gepruefte Codepfade,
  5 Dokuabweichungen, 18 fehlende dokumentierte Merch-Komponenten, 5 CSS-Kandidaten.
  Alle 117 Rueckwaertsfamilien eingeordnet; daraus folgt keine Variantenfreigabe.
- Browserbelege B-01 bis B-58 pruefen konkrete Interaktionen/Geometrien. Das sind
  keine 58 vollstaendig abgenommenen Seiten und keine geraeteuebergreifende Matrix.
- Lokale Fach-, Rechte- und Fehlerproben fuer alle grossen Module liegen vor.
  SQL-Skalierung: 120 Render-Messungen; diese messen Abfragen, keine realen Ladezeiten.
- Dokumentationsregister aktuell nachgezaehlt: 30 teilweise geprueft, 14 nur am
  Einstieg eingeordnet, 3 ausdruecklich ausgeschlossen. D-01 bis D-03 sind als
  begrenzte Namens-/Feldabgleiche abgeschlossen, nicht als komplette Domain-Abnahme.

Quellen: [README](README.md), [Komponenten](COMPONENT_REVIEW.md),
[UI-Registry](UI_REGISTRY_REVIEW.md), [Browser](BROWSER_REVIEW.md),
[Dokumentationspakete](DOCUMENT_CLOSURE_MATRIX.md). Zaehler am 2026-10-10 aus
FINDINGS.md und den drei CSV-Registern gegengeprueft. FILE_INVENTORY.csv bleibt
ein Rohinventar; seine Startstatus bilden die spaeteren Reviews nicht ab.

## Aktuelle Abdeckung und verbleibende Arbeit

Alle Zeilen sind Teilabdeckung. «Entscheidungsreif» gilt unten nur fuer konkret
belegte Ursachen, nicht fuer ein vollstaendiges Modul. K bezeichnet die folgenden Pakete.

| Bereich | Belastbarer vorhandener Teilumfang | Konkreter Rest / Abschlussnachweis | Paket |
|---|---|---|---|
| Shell, Bereiche, Tabs, Pfeile, Filter | Strukturvergleich, Tab-/Filterinventar, Public-Drawer- und Archivnavigation-Proben | Jede aktive Seitenfamilie ihrem Navigations-/Aktionsmuster zuordnen; aktive Zustaende, Rueckweg und Rollen pruefen. Eventwechsel, Listenpagination und Formularschritte semantisch trennen. | K1 |
| Formulare, Cards, Tabellen, Dialoge, Charts | Wiederverwendbare Strukturen verglichen; Formularschritte, Tabellen und Dialoge punktuell im Browser | Aktive Varianten mit Leer-/Lang-/Fehlerdaten, Fokus, Tastatur, Zoom und Breitenmatrix; GGL mit Verlaufsdaten, Kalenderdialoge und weitere Chartzustaende noch gezielt offen. | K1 |
| CSS, JS, Assets, Altlasten | 77 Dateien erfasst, Token-/Theme-Proben, Registry vorwaerts/rueckwaerts eingeordnet | Dynamische Consumer und Ladewege, Kaskade der aktiven Varianten, globale Handler und Drittinhalte; Loeschkandidaten samt verbleibenden Verbrauchern/Weiterleitungen. | K1 |
| Public und Dashboard | Sieben Fachszenarien, ausgewaehlte Browser- und SQL-Belege | Asynchrone Suche/History/Fehler; Restaurantidentitaet und Gewichtung; Summen, Hinweisprioritaet, Lang-/Leerdaten und Zeitgrenzen. | K2 |
| Events, BillBro, GGL, Bereinigung | 44 lokale Szenarien plus Kalender-/Audit-Nachtraege; Rechte, Sichtbarkeit, Rang-/Typgrenzen teilweise | Zustands- und Rollenmatrix; bezahlte Claims bei Aenderungen, Wiedereroeffnung/Fehlerwiederholung; Queue Skip/Back/Undo; Altpfade und Diagramme. PostgreSQL-Rangtypen separat. | K2 |
| Aktueller Merch | 18 Szenarien, Struktur- und Query-Nachtraege | Preis-/Variantenhistorie, Statusruecknahme bei Zahlung, Summen und Formularfehler; aktuelle Shop-/Admin-Ablaeufe als Kette. Alte Seiten nur Abhaengigkeiten/Weiterleitung, kein Redesign. | K2 |
| Buchhaltung und Revision | 31 Szenarien, Rollen-Teilmatrix, Tabellen-/Skalierungsbelege | Importvarianten, Ignore/Reopen/Wiederimport; Zuordnung/Korrektur; Abschluss und Wiedereroeffnung; Beleg-Teilfehler; Budget/Historie; gleiche Daten in Journal/Export/Chart, Berichtsrendering. | K2 |
| Dokumente | Suche, Picker, Aktionsdialoge, Service-Erfolg und externe/DB-Teilfehler mit Fakes | Rechte je Aktion und direktem Einstieg; Upload/Download/Trash/Hard-Delete/Sync-Restfaelle, Kollisionen, Dateigrenzen; Detail-/Mobil-/Fehlerwiederaufnahme. Reale Drive-Semantik separat. | K2 |
| Mitglieder, Profil, Anmeldung | 29 Anfangsszenarien plus zahlreiche Folgeproben; A-140/A-141 ueber Originalablaeufe belegt | Rollen-/Funktionswechsel, Deaktivierung waehrend MFA, sensible Formulare/Step-Up-Ablauf; CSRF und Rate-Limits gezielt aktiviert pruefen; Cookie-/Session-Konfiguration. | K3 |
| Audit und Transaktionen | Gemeinsame Fehlerursache A-137 und Auswirkungen in mehreren Modulen belegt; 64 Aufrufstellen inventarisiert | Aufrufer nach Transaktionsverantwortung klassifizieren; finanzielle oder sonst abweichende Pfade gezielt pruefen. Nicht 64 identische Fehlerproben. | K3 |
| Performance, PWA, Kalender, Integrationen | Algorithmus-/Offline-/Transportproben, 120 SQL-Messungen, 20 Kalendergruppen | Browsercache/Update/Accountwechsel, kalter/warmer Seitenaufruf mit definierten Daten; Payload/CPU/Netzwerk; verbleibende Zeit-/Fehlergrenzen. Reale Dienste/Geraete getrennt ausweisen. | K4 |
| Doku, Betrieb, historische Bereiche | 44 Dokumente im Umfang, D-01..03 begrenzt erledigt, Betriebsnachweisregister | D-04..09: verbleibende Aussagen und Archiv/Hamburg abgleichen; behalten/aktualisieren/archivieren mit Nachfolger; jede externe Behauptung mit Nachweisbedarf. | K5 |

Detailquellen: [Public](PUBLIC_DASHBOARD_REVIEW.md), [Events](EVENT_WORKFLOW_REVIEW.md),
[Merch](MERCH_REVIEW.md), [Buchhaltung](ACCOUNTING_REVIEW.md), [Dokumente](DOCS_REVIEW.md),
[Zugang](AUTH_REVIEW.md), [Auditfehler](AUDIT_FAILURE_REVIEW.md),
[Frontend](FRONTEND_REVIEW.md), [PWA](PWA_PERFORMANCE_REVIEW.md),
[Integrationen](INTEGRATION_OPERATIONS_REVIEW.md), [SQL](QUERY_SCALING_REVIEW.md).

## Veraltete Restlisten: konkret aufgeloeste Ueberschneidungen

| Aelterer offener Punkt | Spaeterer Nachweis | Heutige Einordnung |
|---|---|---|
| Verschachtelter Drive-Picker noch offen in Komponentenbericht | B-41 bis B-54, DOCS_REVIEW.md | Konkrete Fokus-/Fehler-/Hierarchie-/Rennfaelle untersucht; Rollen/Breiten und Restvarianten bleiben. Nicht denselben Einstieg wiederholen. |
| Befuellte Buchhaltungstabellen noch offen | B-37 bis B-40 | Vier Tabellen gezielt geprueft; kein allgemeiner Touch-/Browserabschluss. |
| Fuenf Registry-Restpunkte aus Durchlauf 12 | Registry-Durchlaeufe 13/14 | PWA-Status, Flash-Schliessen, Backup-Code-QR, Archivpagination, Warnstil geklaert; alte CSV-Kategorien sind historische Triage, keine neue To-do-Liste. |
| Mehrere Reset-Tokens/Admin-Wege/MFA-Kombination noch offen | Letzte vier Auth-Nachtraege und zugehoerige JSON-Proben | A-140/A-141 entscheidungsreif; Zeitgrenzen/Parallelitaet/Produktivbestand nicht mit erledigt. |
| Rename/Move/Archive/Restore-Erfolgsservice noch offen | DOCS_LIFECYCLE_CHECKS.json und DOCS_PARTIAL_FAILURE_CHECKS.json | Lokale Originalservices mit Fake-Drive geprueft; realer Drive und verbleibende Aktionen offen. |
| Merch-Query-Skalierung noch offen | QUERY_SCALING_REVIEW.md, zweiter Durchlauf | Order-/Claim-Skalierung lokal gemessen; Admin-Statistiken und reale Laufzeiten nicht pauschal abgedeckt. |

## Reihenfolge und klare Ergebnisse pro Paket

**Refokus nach Nutzerzustimmung am 2026-10-10:** K6 wird frueh als vorlaeufige
Vorlage bearbeitet und mit den Erkenntnissen aus K1 bis K5 fortgeschrieben.
Die erste Gesamtbeurteilung ist erstellt. Naechster Meilenstein sind repraesentative
grafische Entwuerfe fuer Dashboard, Eventdetail und Buchhaltung sowie die Vorbereitung
der Fachentscheidungen fuer Zugang und Geldfluesse. Die folgenden K-Pakete sind
Pruefbereiche, keine starre serielle Reihenfolge. Die U-Pakete in der Gesamtbeurteilung
bezeichnen dagegen die vorgeschlagene spaetere Umsetzung.

| Paket | Ergebnis, an dem der Abschluss erkennbar wird | Status |
|---|---|---|
| K0 Pruefstand konsolidieren | Dieser belegte Ueberblick, priorisierte Restarbeit, Regeln gegen redundante Pruefungen | erledigt als Meta-Konsolidierung; keine neue Funktionspruefung |
| K1 Oberflaeche und gemeinsame Bausteine | Seiten-/Komponentenmatrix mit Nachweisen je aktiver Variante; begruendetes Ziel fuer Navigation, Filter, Bearbeitung, Formulare, Cards, Tabellen, Dialoge; CSS-/Altlastenkarte | gezielt zur Konkretisierung und Absicherung des vorlaeufigen Zielbilds |
| K2 Fachablaeufe | Je Modul Zustands-/Rollenmatrix, zusammenhaengender Erfolgsweg und relevante Fehler-/Ruecknahmewege; offene Daten-/Integrationsgrenzen explizit | offen |
| K3 Technische Querschnitte | Verbleibende Rechte-/Sicherheitsgrenzen und Transaktionsklassen; bekannte Ursachen zu gemeinsamen Reparaturpaketen gebuendelt | offen |
| K4 Performance und Betriebsverhalten | Lokale Messungen getrennt von Hypothesen und externen Nachweisen; PWA-/Integrationsrestmatrix | offen |
| K5 Dokumentation und Inventarabschluss | Jede relevante Datei/Route/Komponentenvariante einem Nachweis, Ausschluss oder konkreten Restgrund zugeordnet; 44 Doku-Eintraege nachvollziehbar bewertet | offen |
| K6 Zielbild und Entscheidungsvorlage | Konsolidierte Ursachen, empfohlene Reihenfolge, Nutzen/Aufwand/Risiko und Abnahmekriterien; Optionen fuer Refactoring/Redesign; Entscheidungen fuer Nutzerfeedback | erste Vorlage erstellt am 2026-10-10; grafische Entwuerfe, Feedback und abschliessende Absicherung offen |

Pakete koennen mehrere Durchlaeufe benoetigen. Kein Zeit- oder Prozentversprechen
ohne belastbare Restmengenerfassung. K1 beginnt mit dem Abgleich der 83 Templates
zu aktiven Seitenfamilien und vorhandenen Browserbelegen. Gemeinsame Komponenten
werden einmal gruendlich geprueft; abweichende Verbraucher erhalten eigene Proben.
Die urspruengliche Breiten-/Zustandsmatrix im README bleibt der Pruefmassstab.

## Begrenzung weiterer Vertiefung und Abschlussregel

- A-140/A-141: Ursache, regulaere Erreichbarkeit und Nutzerwirkung ausreichend
  belegt. Keine weitere Serie bloss aehnlicher Linkkombinationen ohne neue Frage.
- A-126..134: dokumentierte Picker-/Such-/Dialogprobleme nicht nochmals identisch
  reproduzieren. Restarbeit auf andere Aktionen, Rechte, Daten und Breiten richten.
- A-137: gemeinsamen Mechanismus nicht fuer jeden Aufrufer neu beweisen;
  Unterschiede bei Commit, Geld, Versand und Wiederaufnahme gezielt bewerten.
- Ein geplanter Test braucht eine offene Frage und eine Konsequenz fuer Befund,
  Zielbild oder Abnahme. Ergebnisse «positiv» und «nicht entscheidbar» sind ebenso
  zu dokumentieren wie Fehler; Befundzahl ist kein Erfolgskriterium.
- Gleichartige Befunde zusammenfuehren, IDs als nachvollziehbare Verweise erhalten.
  Ein Befund kann entscheidungsreif sein, obwohl seine Reparaturabnahme noch aussteht.

Das Audit ist als Entscheidungsvorlage abgeschlossen, wenn alle lokalen
Pruefobjekte nachvollziehbar behandelt, Risiken/Empfehlungen konsolidiert und
verbleibende Grenzen einzeln benannt sind. Ein unbekannter Produktionszustand
darf weder als Fehler noch als Freigabe ausgegeben werden. Lokale Luecken werden
nicht allein zur Verkuerzung der Arbeit zu externen Grenzen umetikettiert.

[Externe Nachweise](OPERATIONS_EVIDENCE_REGISTER.md) bleiben separat: reale
Geraete/Safari, Deployment und Scheduler, PostgreSQL, Zustellung, Drive-Freigaben,
Backup/Restore und Monitoring. Kein Versand, Produktivschreiben oder Restore
im Rahmen dieses Plans. Ein spaeterer externer Pruefschritt braucht einen konkret
festgelegten Umfang; bis dahin lautet sein Status «nicht verifiziert».

Game bleibt ausgeschlossen. Alte Merch-Seiten sind zur Entfernung vorgemerkt;
gemeinsame Bestellverarbeitung und vorhandene Einstiege muessen erhalten bzw.
gezielt umgeleitet werden. Feedback erfolgt anhand der vorlaeufigen Vorlage
und ihrer Konkretisierung. Umsetzung folgt erst auf die entsprechenden
Paketentscheidungen; das Gesamtaudit ist durch die erste Vorlage nicht abgeschlossen.

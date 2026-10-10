# App-Audit und Zielbild fuer Refactoring / Redesign

Stand: 2026-10-10. Status: **in_progress**. Auftrag: vollstaendiges, mehrstufiges Audit;
danach User-Feedback zu den Empfehlungen, erst anschliessend Umsetzung.

**Aktueller Einstieg ab 2026-10-10:** [Gesamtbeurteilung und vorlaeufiges Zielbild](GESAMTBEURTEILUNG.md).
**App-Wechsel:** [Uebergabe fuer ChatGPT Work](AGENT_HANDOFF.md). Fortsetzung in der
neuen ChatGPT-App ausdruecklich in **Work**, nicht in Codex; Sicherung auf eigenem Branch.
Die erste Entscheidungsvorlage buendelt alle 141 Befunde in sechs vorgeschlagene
Umsetzungspakete; die Einzelzuordnung steht im [Paketregister](PAKETREGISTER.csv).
Der Nutzer hat die Zusammenfuehrung und fruehe Zielbildarbeit beauftragt, keine
App-Umsetzung. Als Naechstes das Zielbild an repraesentativen Ansichten konkretisieren
und entscheidungsrelevante Fachfragen vorbereiten. Restpruefungen bleiben im
[Pruefstand und Abschlussplan](COMPLETION_PLAN.md); K1 bis K5 sind keine Voraussetzung
mehr fuer eine erste Gesamtbeurteilung. Aeltere Fortsetzungsnotizen sind Verlauf.

## Auftrag und Entscheidungsrahmen

**Nutzerentscheidung im Audit:** Die alten Merch-Bestell-/Bestelllistenseiten
werden nicht mehr benoetigt und sind fuer die spaetere Entfernung vorgesehen.
Aktueller Shop postet noch auf member.merch_order; gemeinsame Bestellverarbeitung
erhalten oder umziehen, Links/Rueckleitungen anpassen. Audit wird fortgesetzt,
in diesem Schritt keine App-Loeschung. Details: UI_REGISTRY_REVIEW.md, Durchlauf 10.

Die gesamte App wird untersucht: oeffentlicher und geschlossener Bereich,
alle Module, Tabs, Navigation, Filter-/Bearbeitungsbereiche, Formulare, Cards,
Tabellen, Diagramme sowie Bereinigung, BillBro, Merch und Buchhaltung als Workflows.
Auch CSS-Wachstum, Altlasten, Backend, Performance, PWA, Sicherheit, Betrieb,
Tests und veraltete Dokumentation gehoeren dazu. Ein umfassendes Refactoring
und ein Frontend-Redesign sind moegliche Ergebnisse, noch keine beschlossene Umsetzung.

**Ausgeschlossen auf ausdruecklichen Nutzerwunsch:** das pausierte Sideprojekt
Essens-Pokemon/Game einschliesslich `docs/GDD_FOOD_POKEMON.md`,
`docs/GDD_FOOD_POKEMON_REVIEW.md` und `docs/capabilities/game.md`.
Diese Dateien bleiben unangetastet. Das Rohinventar behaelt seine 47 Dokumente;
der aktuelle Dokumentations-Pruefumfang umfasst **44 Dokumente**.

Bewertung nach Nutzen, fachlicher Korrektheit, Konsistenz und Wartbarkeit fuer
einen kleinen Verein. Bestehende Regeln duerfen begruendet infrage gestellt werden.
Unterschiede werden in fachlich notwendige Varianten und historisch entstandene
Abweichungen eingeordnet. Gemeinsame Ursachen erhalten einen Befund mit mehreren
betroffenen Stellen, statt einer Vielzahl redundanter Einzelprobleme.

## Verbindliche Pruefmethode

- **Inventar ist kein Review.** Eine Datei, Route oder Seite gilt durch Auflisten,
  Suchtreffer, Syntaxpruefung oder einen erfolgreichen GET nicht als durchgeprueft.
- Status je Pruefobjekt: inventarisiert, Code gelesen, Verhalten verifiziert,
  Befund dokumentiert, abgeschlossen; alternativ offen mit konkretem Grund.
- Befunde trennen: bestaetigter Fehler, bestaetigte Strukturbeobachtung mit
  Empfehlung, Verdacht, Produkt-/Designentscheidung. Beleg und Unsicherheit angeben.
- Keine Loeschfreigabe allein durch fehlende Textreferenzen: dynamische Verwendung,
  registrierte Routes, Redirects, alte Links, Cron und externe Clients beruecksichtigen.
- Performance getrennt als Code-Hypothese, lokale Messung oder Produktionsmessung
  ausweisen. Dateigroessen sind keine gemessenen Ladezeiten.
- Kein pauschales Versprechen absoluter Fehlerfreiheit: Ziel ist nachvollziehbare
  Vollstaendigkeit des Pruefumfangs mit offen ausgewiesenen Grenzen.
- Keine App-Aenderungen, Migrationen, Deploys oder produktiven Schreibaktionen im Audit.
  Bestehende lokale, nicht versionierte Dateien bleiben erhalten.
- User-Feedback folgt auf den konsolidierten Befundkatalog; Zwischenberichte sind
  Fortschrittsstaende und keine neue Freigabeanforderung fuer jeden Durchlauf.

## Durchlaeufe und Status

| Nr. | Durchlauf | Status | Abschlussbeleg / naechste Arbeit |
|---|---|---|---|
| 00 | Pruefkonzept, Repository-Inventar, Baseline | done | 442 Dateien, 83 Templates, 172 Deklarationen; 168 registrierte Regeln in Testing; 69 bestehende Tests bestanden. Grenzen unten. |
| 01 | Querschnitt: Shell, Navigation, Tabs, Komponenten, Assets | in_progress | Alle 83 Templates strukturell erfasst; 7 Standard-Tab-Systeme und 13 Filter-Fundstellen eingeordnet. COMPONENT_REVIEW.md. Vollstaendige Interaktionsmatrix offen. |
| 02 | Alle Module und fachlichen Workflows | in_progress | 44 Event-/Workflow-, 18 Merch-, 31 Buchhaltungs-, 29 Auth/MFA/Profil/Zugangs-, 51 Dokument- und 7 Public/Dashboard-Szenarien plus dokumentierte Folgeproben, 141 Befunde insgesamt. Restfaelle in den Modul-Teilberichten. Kein Modul vollstaendig abgeschlossen. |
| 03 | CSS-/JS-Abhaengigkeiten und Altlasten | in_progress | 77 CSS-/JS-Dateien, 4 gerenderte Ladelisten, CSS-Build textlich konsistent. FRONTEND_REVIEW.md trennt Quellen, aktive Einbindungen und Bereinigungskandidaten. Komponentenvergleich, Token-Abgleich und 5 isolierte Theme-Proben ergaenzt. Vollstaendige Kaskade und Browser-Coverage offen. |
| 04 | Responsive UX und Barrierefreiheit | in_progress | Erste lokale Browser-Reproduktionen, Event an 8 und Buchhaltung an 5 Viewports; Desktop-Clipping, Tab-/Dialog-/Labelprobleme bestaetigt. BROWSER_REVIEW.md; B-14 bis B-58 ergaenzen Formulare, 320px, sechs Buchungs-Viewports sowie Public-/Chartdialoge. Echte Geraete und Restmatrix offen. |
| 05 | Backend, Datenintegritaet und Sicherheit | in_progress | Isolierte Rechte-/Integritaetspruefungen in Modulberichten und AUTH_REVIEW.md; A-141 ueber normale Reset-Anfragen, administrativen Passwortreset und alte MFA-Reset-Links nach Neueinrichtung bestaetigt. Keine vollstaendige Sicherheitsabdeckung; CSRF, Rate-Limits, reale Konfiguration und weitere Grenzen offen. |
| 06 | Performance, PWA, Integrationen und Betrieb | in_progress | 10 SW-/Update-, 5 Offline-, 6 Service-Vertrags- und 9 Versand-/Cron-Grenzproben, 5 Zeitfenster-/Transport- und 6 Legacy-Notifier-Proben sowie 120 Render-Messungen zur SQL-Skalierung in 3 Durchlaeufen, einschliesslich historischer Saisons/Geschaeftsjahre. PWA_PERFORMANCE_REVIEW.md / QUERY_SCALING_REVIEW.md; echte Ladezeiten, weitere Grenzen und Betrieb offen. |
| 07 | Dokumentationsabgleich | in_progress | 47 Inventareintraege, davon 3 Game-Dokumente ausgeschlossen; 44 im Pruefumfang: 30 teilweise abgeglichen, 14 nur am Einstieg eingeordnet; 5 lokale Dokumentationsproben. DOCUMENTATION_REVIEW.md; Betriebsnachweise separat erfasst. |
| 08 | Gegenpruefung, Lueckenschluss und Zielbild | in_progress | K0 konsolidiert; am 2026-10-10 erste Gesamtbeurteilung mit vorlaeufigem Zielbild und sechs Paketen erstellt. Alle 141 Befunde zugeordnet. Grafische Entwuerfe, Einzelobjektabschluss und gezielter Lueckenschluss offen. |
| 09 | User-Feedback und Umsetzungspakete | in_progress | Erste Vorlage mit Nutzen, relativem Aufwand, Risiko, Abhaengigkeiten und Abnahmekriterien vorhanden. Fach-/Gestaltungsfeedback und endgueltige Paketentscheidungen offen; keine Umsetzungsfreigabe. |

## Abdeckungsmatrix fuer vertiefte Durchlaeufe

Alle folgenden Bereiche sind **noch nicht vollstaendig geprueft**:

| Bereich | Zusaetzlich zum normalen Anzeigen/Bedienen zu pruefen |
|---|---|
| Public / Login | Einstieg, Rueckkehr zur App, Suche/Sortierung/Pagination, SEO, Drittinhalte, Session-Zustaende |
| Dashboard | Relevanz, Priorisierung, zeitliche Hinweise, Links, offene Posten, rollenabhaengiger Inhalt |
| Events | Kommend/Archiv/Statistik, Erstellung/Bearbeitung, Planung, Sichtbarkeit, Vorher/Weiter, Teilnahme, Ratings, Hamburg-Sonderseite |
| BillBro / GGL | Phasen, Teilnehmerrollen, Schaetzung, Rundung, Finalisierung, Ruecknahme, Zahlweg, Ranggleichheit, Saison, Diagramme |
| Verein / Mitglieder | Profil, sensible Felder, Administration, Onboarding, Rollen/Funktionen, Deaktivierung |
| Technik / Sicherheit | Installation, Push, Kalender, 2FA, Reset, Backup-Codes, Step-Up, Logout und Accountwechsel |
| Dokumente | Ordnernavigation, Suche, Upload, Rename/Move, Archiv/Restore, Hard-Delete, Synchronisierung, externe Fehler |
| Merch | Sortiment, Varianten, Bestellung/Bearbeitung, Admin-Verarbeitung, Zahlung/Lieferung; dokumentierte vs. implementierte Workflows |
| Buchhaltung | Journal, Belege, Konten, Budget, Import/Dedup, Teilzahlung, Jahresabschluss, Revision, Exporte, Korrekturen |
| Bereinigung | Schrittfolge, Vorschlaege, Ueberspringen, Zurueck/Undo, Abbruch und Wiederaufnahme |
| Hintergrund/Betrieb | Reminder, Mail, Push, ICS, Health, Deployment, Migrationen, Backups, Konfiguration, verwaiste Helfer |

Fuer jede Seite: Rollen und Berechtigungen; leer/ein/viele/lange Inhalte;
Erfolg/Validierungsfehler/Serverfehler; Links und Browser-Zurueck; Speichern,
Doppelklick, Abbruch und Wiederaufnahme soweit anwendbar.

Visuelle Zielmatrix: 360/390 px Mobile, 768/820 px Tablet hochkant,
1024 px Tablet quer bzw. Uebergang, 1280/1440 px Desktop; ausserdem direkt
unter/auf/ueber tatsaechlichen CSS-Breakpoints. Reflow bei 320 CSS-px,
200%-Zoom, Hell/Dunkel, reduzierte Bewegung, Tastatur und Touch.
Simulation und echte Geraete strikt unterscheiden; Safari/iOS/PWA-Pruefungen
bleiben offen, solange kein entsprechender Testnachweis vorliegt.

## Baseline und Grenzen

- Code: `bf4d84aad2725070cf77f6d9fc5bc818a5e0a43f`, Branch `master`.
- 436 versionierte + 6 vorhandene nicht ignorierte lokale Dateien. Audit-Ausgaben
  selbst sind aus dem Inventar ausgeschlossen. Ignorierte Laufzeitdaten, venv,
  Datenbanken und private Schluessel gehoeren nicht zum Quellcodeinventar.
- Vorhandene lokale Dateien: build_logs.txt, drei Game-Konzeptdokumente,
  zwei pwa-Hashkopien. Sie sind nicht als produktiv eingesetzte Features gewertet.
- 172 AST-Route-Deklarationen sind **nicht** 172 produktive Endpunkte.
  Testing registriert 168 Regeln inkl. Static; Fallback-App und nicht registrierte
  Demo-/Stats-Blueprints erklaeren unterschiedliche Erfassungsmengen mit.
- Lokaler venv-Launcher funktioniert in dieser Sitzung nicht (referenzierter
  Python-Pfad nicht verfuegbar). Bestehende venv-Pakete laufen mit gebuendeltem
  Python 3.12.14. Kein Nachinstallieren von Dependencies.
- Testumgebung: `.env`-Laden unterbunden, Anwendungs-ENV entfernt, SQLite nur
  im Arbeitsspeicher, ausgehende Sockets gesperrt. Bestehende Tests unveraendert.
- **69 passed, 287 warnings**, 37.76 Sekunden. Kein Coverage-Prozent gemessen;
  kein Beleg fuer vollstaendige Fach-/Sicherheitsabdeckung. SQLite ersetzt keine
  PostgreSQL-Migrations-/Constraint-Pruefung. CSRF/Rate-Limit sind in Testing aus.
- 18 zusaetzliche GET-Aufrufe mit einem synthetischen Mitglied/Organisator:
  Routing/Rendering-Baseline, keine vollstaendigen Workflow- oder Browser-Tests.
- Erste lokale Browser-JavaScript-/Viewport-Pruefungen sind dokumentiert.
  Production-Commit, produktive Konfiguration, echte Geraete, reale Ladezeiten
  und externe Integrationen bleiben ungeprueft.

## Dateien / Fortsetzung

- [Dokumentationsabgleich](DOCUMENTATION_REVIEW.md), [47 Dokument-Pruefstaende](DOCUMENT_REVIEW_REGISTER.csv) und [offene Betriebsnachweise](OPERATIONS_EVIDENCE_REGISTER.md).

- [Wiederverbindung, Integrationen und Betrieb](INTEGRATION_OPERATIONS_REVIEW.md):
  [5 Offline-Proben](OFFLINE_RETURN_CHECKS.json) und
  [6 Service-Vertragsproben](INTEGRATION_CONTRACT_CHECKS.json) sowie [9 Versand-/Cron-Grenzproben](NOTIFICATION_BOUNDARY_CHECKS.json) und [5 Zeitfenster-/Transportproben](REMINDER_WINDOW_CHECKS.json) sowie [6 Legacy-Notifier-Proben](LEGACY_NOTIFIER_CHECKS.json); A-107 bis A-118.

- [Erste Befunde](FINDINGS.md): vorlaeufig, kein abschliessender Auditbericht.
- [PWA und Performance](PWA_PERFORMANCE_REVIEW.md): Cache-/Offline-/Update-Vertrag,
  [10 isolierte Algorithmus-Szenarien](SW_STRATEGY_CHECKS.json), `check_sw_strategies.cjs`.
- [Datenbank-Skalierung](QUERY_SCALING_REVIEW.md): vier Datenbestaende, sechs Seiten,
  je zwei frische Sessions; [48 Messungen](QUERY_SCALING_CHECKS.json), `check_query_scaling.py`.
  Zweiter Durchlauf: [48 weitere Messungen](COMMERCE_SCALING_CHECKS.json) fuer
  Bestellungen, Claims und Buchung-/Belegpaare, `check_commerce_scaling.py`.
  Dritter Durchlauf: [24 Historien-Messungen](HISTORY_SCALING_CHECKS.json) fuer
  mehrere Saisons/Geschaeftsjahre, `check_history_scaling.py`.
- [Frontend-Quellen und Altlasten](FRONTEND_REVIEW.md): Ladewege, Build-Gegenpruefung,
  Controller und Bereinigungskandidaten; [Asset-Nachweise](FRONTEND_ASSET_CHECKS.json).
- [Public und Dashboard](PUBLIC_DASHBOARD_REVIEW.md): Sichtbarkeit, Suche,
  Datumsgrenzen; [7 Szenarien](PUBLIC_DASHBOARD_CHECKS.json), `check_public_dashboard.py`.
- [Dokumentverwaltung](DOCS_REVIEW.md): erste Rechte-/Fehlerpfade,
  [7 isolierte Szenarien](DOCS_CHECKS.json), `check_docs_workflows.py`.
  [7 Upload-/Sync-Grenzfaelle](DRIVE_BOUNDARY_CHECKS.json), `check_drive_boundaries.py`.
- [Anmeldung und Profil](AUTH_REVIEW.md): erste Sitzungs-/Resetpruefungen,
  [7 isolierte Szenarien](AUTH_CHECKS.json), `check_auth_workflows.py`.
  [7 weitere MFA-Szenarien](MFA_CHECKS.json), `check_mfa_workflows.py`.
  [8 Profil-/Admin-Szenarien](PROFILE_CHECKS.json), `check_profile_workflows.py`.
  [7 Zugangs-/Verwaltungsszenarien](ACCESS_CHECKS.json), `check_access_lifecycle.py`.
- [Komponentenvergleich](COMPONENT_REVIEW.md): Tab-/Filter-/Formular-/Dialog-/Workflow-Muster.
- [Merch-Teilbericht](MERCH_REVIEW.md): Bestellung, Varianten, Status und Claims;
  [18 isolierte Szenarien](MERCH_CHECKS.json), `check_merch_workflows.py`.
- [Buchhaltungs-Teilbericht](ACCOUNTING_REVIEW.md): Betraege, Jahreszuordnung,
  Sperren, Belegzuordnung und erste Rechtepruefung;
  [7 isolierte Szenarien](ACCOUNTING_CHECKS.json), `check_accounting_workflows.py`.
  Dazu [12 Import-/Zuordnungsszenarien](BANK_CHECKS.json), `check_bank_workflows.py`.
  [7 Revisions-/Berichtsszenarien](REVISION_CHECKS.json), `check_revision_workflows.py`;
  darin eine Matrix mit 16 Rollen-/Aktionskombinationen.
  [5 Beleg-/Korrekturszenarien](RECEIPT_CHECKS.json), `check_receipt_workflows.py`.
- [Browserprotokoll](BROWSER_REVIEW.md): Reproduktionen, Viewport-Messungen und Screenshots.
- [Events und Workflows](EVENT_WORKFLOW_REVIEW.md): vertiefter Teilbericht,
  mit [18 isolierten Szenarien](EVENT_WORKFLOW_CHECKS.json); reproduzierbar via
  `check_event_workflows.py`. Fehlerbelege sind keine bestandenen Regressionstests.
  [Weitere 17 Szenarien](EVENT_FOLLOWUP_CHECKS.json) via `check_event_followup.py`
  erfassen Bewertungen, Event-Erstellung/Planung und GGL-Vergleiche.
  [9 Grenzfallpruefungen](EVENT_BOUNDARY_CHECKS.json) via `check_event_boundaries.py`
  erfassen Public-/Statistik-Datenfluss, Reminder und Loesch-/Ownership-Regeln.
- [Praezisierte Template-Erfassung](UI_PATTERN_SURVEY.csv): exakte Klassentokens;
  Details in UI_PATTERN_LOCATIONS.json, Zusammenfassung in UI_SURVEY_SUMMARY.json.
- [Dateiinventar](FILE_INVENTORY.csv): gesamter erfasster Repository-Bestand.
- [Route-Inventar](ROUTE_INVENTORY.csv): Deklarationen mit Decorators und Code-Ort.
- [Template-Matrix](TEMPLATE_MATRIX.csv): Suchmuster fuer vergleichbare Oberflaechen.
- [CSS-Inventar](CSS_INVENTORY.csv), [Dokumente](DOC_INVENTORY.csv), [Asset-Pruefungen](ASSET_CHECKS.csv).
- [Zusammenfassung](INVENTORY_SUMMARY.json), [Runtime-Pruefungen](RUNTIME_CHECKS.json), [Testergebnis](TEST_RESULTS.txt).
- `collect_inventory.py` erzeugt Rohinventare neu; dabei gesetzte Review-Status sind
  Startwerte. Manuelle Review-Fortschritte hier und im Befundkatalog pflegen,
  bis ein eigenes, beim Regenerieren erhaltenes Pruefregister eingefuehrt ist.
- `run_existing_tests.py` und `check_runtime.py` dokumentieren die isolierten Pruefungen.

Historische Fortsetzungsnotiz (aktuelle Reihenfolge: COMPLETION_PLAN.md): Paket D-05,
[UI-Registry-Abgleich](UI_REGISTRY_REVIEW.md)
erfasst alle 150 Tabellenzeilen als Suchstellenkarte und dokumentiert erste
manuelle Gegenpruefungen. Zweiter Durchlauf verfolgt Body/ID/Makros,
BEM-Kurzformen, Topbar/Dialogpause, Tool-Strip und sechs Legacy-CSS-Familien nach.
Dritter Durchlauf: Cards/Formulare/Tabellen/Hub weiter nachverfolgt;
Rueckwaertssuche mit 117 Kandidatenfamilien und ersten manuellen Einordnungen
(keine Fehlerzahl). Vierter Durchlauf: Bereichskomponenten und gemeinsame
Workflow-Bausteine nachverfolgt. Fuenfter Durchlauf: Public-Navigation und
Fehler-/Offline-Ladewege statisch abgeglichen. Einzelne Child-/Modifier-/
Basisdetails und Rueckwaertskandidaten bleiben offen. Sechster Durchlauf:
[Abdeckungsmatrix](UI_REGISTRY_COVERAGE.csv) fuer alle 150 Zeilen erstellt;
Siebter Durchlauf: auch 038/057/058/068 nachverfolgt, keine rein kartierte Zeile
mehr. 122 Codepfade teilweise geprueft, 5 Dokuabweichungen, 18 fehlende Merch-
Eintraege, 5 CSS-Kandidaten. Achter Durchlauf: alle 117 Rueckwaertskandidaten
in UI_REGISTRY_REVERSE_TRIAGE.csv eingeordnet; 64 Detailpruefungen explizit offen,
Rest auf Teil-Dokumentation, Hooks, Hilfsstile, 6 Registry-Luecken, 2 Suchartefakte
und 20 historische Hamburg-Familien verteilt. Weitere Registry-Varianten offen.
Neunter Durchlauf: zehn alte Merch-Kandidaten mit erreichbaren Routen und
lokalem CSS/Struktur nachverfolgt; aktuell noch 54 offene Detailfamilien im
Rueckwaertsregister. Alte Seiten sind keine verwaisten Dateien.
Zehnter Durchlauf: Places-/Formhilfen-Gruppe nachverfolgt, aktuell 44 offene
Detailfamilien. Nutzerentscheidung zum Entfall alter Merch-Seiten oben erfasst.
Elfter Durchlauf: Chart-/Navigations-/Statusgruppe nachverfolgt, 30 noch nicht
eingeordnete Detailfamilien; zusaetzlich zwei Statusanker mit gezielter offener
Browserfrage (hidden gegen display:block), siehe UI_REGISTRY_REVIEW.md.
Zwoelfter Durchlauf: alle 117 Rueckwaertsfamilien erstmals eingeordnet;
gezielte Restliste statt unspezifischer Kandidaten: PWA-Status, Event-Paginierung,
Flash-Schliessen, Warnstil, Backup-Code-QR. Keine Funktionsfreigabe; weitere
Registry-Varianten offen. Details im zwoelften Registry-Durchlauf.
D-01/D-02 als Namensabgleich und D-03 als statischer Feld-/Seed-Vertragsabgleich abgeschlossen, siehe DOCUMENT_CLOSURE_MATRIX.md; echte PWA-Update-/Offline-Gegenpruefung im Rahmen
der verfuegbaren Browserfunktionen bleibt offen.
B-21 bis B-25 ergaenzen Datei-Pflichtfeld,
Public-Drawer und Accounting-Chart; GGL mit Verlaufsdaten sowie verschachtelte
Drive-/Kalenderdialoge bleiben fuer spaetere Browserdurchlaeufe offen.
Systemtheme-Wechsel im Browser weiter offen. Offene fachliche Grenzen
aus allen Modul-Teilberichten bleiben fuer gezielte Gegenpruefung erfasst;
kein Modul ist durch die bisherigen Szenarien pauschal abgeschlossen.
Pro Modul Rollen, Fehler-/Leer-/Langdatenzustaende,
Formularschritte und Rueckleitungen pruefen. Die Browser-Testbasis hat vier Rollen;
bisherige Browser-Interaktionen erfolgten hauptsaechlich als Admin sowie ausgeloggt.
Die neuen Workflow-Reproduktionen nutzen Organisator und regulaeres Mitglied.
Alle Befunde einschliesslich Layoutproblem A-014 bleiben unveraendert im App-Code.

Dreizehnter Registry-Durchlauf: B-26 bis B-28 bestaetigen PWA-Status,
Flash-Schliessen und QR-Platzhalter (A-119 bis A-121). Belege in
BROWSER_REVIEW.md und browser/registry-followup.json. Event-Paginierung,
Warnstil und weitere Child-/Modifier-Pruefungen bleiben offen.

Vierzehnter Registry-Durchlauf: Archivnavigation und Warnzustand mit B-29/B-30
geprueft. A-122 zur fehlenden Paginierungsgestaltung; Seitennavigation und
Suchfiltererhalt positiv. Basisvarianten btn/alert/empty-state statisch
vertieft (ATOM_VARIANTS.json); Ghost/Secondary ohne CSS-Definition, Warntext
bleibt lesbar. Die gezielten Restpunkte aus Durchlauf 12 sind eingeordnet;
weitere Komponentenvarianten und die umfassende Interaktionsmatrix bleiben offen.

Fuenfzehnter Registry-Durchlauf: Namens-/Definitionsabgleich von sechs
Karten-/Formular-/Tabellenfamilien abgeschlossen (47 Definitionen,
36 verwendete Varianten). STRUCTURAL_VARIANTS_REVIEW.md trennt sinnvolle
Varianten, Inkonsistenzen und 13 Kandidaten ohne Consumer-Nachweis.
Weiterhin 122 Befunde; Interaktionsabdeckung bleibt separat offen.

Sechzehnter Registry-Durchlauf: B-31 bis B-33 pruefen Merch-Karten als
regulaeres Mitglied und Tabellen als Mitglied/Admin. Tastaturbedienung und
Erhalt lokaler Artikelauswahl positiv; generische Toggle-Namen und horizontaler
Fokussprung in der Mitgliederliste als Orientierungsthemen dokumentiert.
Weiterhin 122 Befunde. GGL-/Buchhaltungstabellen, andere Browser und
Screenreader bleiben offen. Beleg: browser/keyboard-followup.json.

Siebzehnter Registry-Durchlauf: B-34 bis B-36 bestaetigen Tastatur-Scroll
in GGL (Mitglied) und Budget (Admin/Revisor). GGL haelt Rang/Name sticky;
Budget-Konto scrollt entgegen dem Registry-Beispiel mit (Erweiterung A-012).
Weiterhin 122 Befunde. Journal/Belege/offene Posten/Import-Historie sowie
Langdaten und weitere Browser bleiben explizit offen.

Achtzehnter Registry-Durchlauf: B-37 bis B-40 schliessen die gezielte lokale
Tastaturprobe fuer befuelltes Journal, Belege, offene Posten und Import-Historie
als Admin ab. Neuer A-123: lange sticky Import-Dateispalte verdeckt weitere
Spalten/Aktion auf schmalem Display. Insgesamt 123 Befunde. Rollen-/Browser-/
Langdatenmatrix bleibt offen; Belege in browser/accounting-tables-keyboard.json.

Kalender-Vertragsdurchlauf: fuenf isolierte Proben zu Cache und SEQUENCE;
A-124/A-125, insgesamt 125 Befunde. CALENDAR_CONTRACT_REVIEW.md trennt
bestaetigte Service-Abweichungen von ungeprueftem Client-/Produktivverhalten.
Dokumentations-Abschlussmatrix auf aktuellen UI-Pruefstand nachgezogen.

Zweiter Kalenderdurchlauf: CAL-06 bis CAL-12 (sieben Gruppen) pruefen
Datumsgrenze, Board-Sichtbarkeit, Entpublizieren, sieben einzelne Felder,
Organisator-Rufname, vier Zeitumstellungsdaten und ungueltigen/inaktiven Zugang.
Positive Inhalts-/Zugangsproben; A-125 um abhaengigen Profilnamen erweitert.
Weiterhin 125 Befunde; echte Kalender-Clients und komplette Mutationsrouten offen.

Dritter Kalenderdurchlauf: CAL-13 bis CAL-20 pruefen originale Event-Edit-/
Delete-POSTs. A-125 (Notiz-Version) und A-026 (ignorierte Sichtbarkeit) bestaetigt;
stabile UID, einmaliges Hochzaehlen bei Mehrfachaenderung und ein Rechtefall
positiv. 20 Kalender-Pruefgruppen insgesamt, weiterhin 125 Befunde.

Dokumentdialog-Durchlauf: B-41 bis B-44 pruefen Upload/verschachtelten
Ordnerpicker an 390px, Rueckkehr/Abbruch und simulierten Ladefehler. A-126
zu fehlenden semantischen Aufklapp-/Auswahlzustaenden; insgesamt 126 Befunde.
Kein Upload; sichtbarer Zielname und Entwurfserhalt positiv.

Upload-Fehlerdurchlauf: B-45/B-46 bestaetigen Entwurfsverlust ohne Datei
(A-127) und fehlende Root-Picker-Fehlermeldung (A-128). Insgesamt 128 Befunde.
Originalcontroller mit lokal simuliertem 503, kein echter Upload.

Picker-Wiederaufnahme: B-47 bis B-49 bestaetigen erfolgreichen erneuten
Versuch nach Root-Fehler, fehlerhafte Hierarchiereihenfolge (A-129) und
unsichtbare Auswahl nach Zuklappen. Insgesamt 129 Befunde. Kein Upload;
weitere Zweig-/Daten-/Rollenvarianten bleiben offen.

Zweig-Durchlauf: B-50 bis B-52 pruefen unabhaengiges Zuklappen, erneuten
Ladeversuch bei anhaltendem Unterordnerfehler und fehlende Leerzustandsmeldung.
A-126 ergaenzt, weiterhin 129 Befunde. Zwei befuellte Nachbarzweige und
verzoegerte Antworten bleiben offen; keine App-Aenderung und kein Upload.

Asynchroner Picker-Durchlauf: PICK-01 bis PICK-04 am Originalcontroller mit
synthetischem DOM und kontrollierter Antwortreihenfolge. Zwei befuellte Zweige
und veraltete Unterordnerantwort positiv; parallele Root-Anfragen duplizieren
Zeilen und fordern nach Schliessen erneut Oeffnen an (A-130). Insgesamt 130
Befunde. Echte Browser-Bestaetigung dieser Rennen bleibt offen. Belege:
PICKER_ASYNC_CHECKS.json und DOCS_REVIEW.md.

Root-Rennen im Browser: B-53/B-54 bestaetigen A-130 mit nativen Dialogen,
zwei Root-Zeilen und Wiederoeffnen nach Schliessen samt Fokuswechsel. Lokale
synthetische Verzoegerung, kein Upload. Weiterhin 130 Befunde. Browserbeleg
fuer PICK-03/04 ergaenzt; andere Ablaufvarianten und Browser bleiben offen.

Dokumentensuche: acht isolierte Gruppen zu leeren/fehlgeschlagenen Suchen,
Mindestlaenge, Ordnerlinks und Suchpaginierung. A-131 (globale Begrenzung vor
Ordnerfilter) und A-132 (widerspruechliche Leerzustaende), insgesamt 132 Befunde.
Originalservice mit synthetischen API-Seiten; Suchbegriff bei Fehler erhalten.
DOCS_SEARCH_CHECKS.json und DOCS_REVIEW.md; reale Google-Suche/Browser offen.

Zweiter Suchdurchlauf: sechs Gruppen zu verschachtelten Suchbereichen,
Sonderzeichen, leerer API-Seite mit Fortsetzung, Folgefehlern und Pfadaufwand.
A-091 um Suchfehler erweitert; A-133 zu 100 redundanten Pfadabfragen bei 50
Treffern im gleichen zweistufigen Pfad. Insgesamt 133 Befunde. API-Aufrufe
isoliert gezaehlt, keine gemessene Produktionslatenz. DOCS_SEARCH_BOUNDARY_CHECKS.json.

Dateiaktionen: gemeinsame Dialoge von Liste/Detail quellenbasiert verglichen;
zehn Routenproben zu Erfolg, behandeltem Fehler und fehlendem Ziel. A-134 zum
fehlenden Dateikontext; A-127 um Entwurfserhalt erweitert. Insgesamt 134 Befunde.
DOCS_ACTION_CHECKS.json und DOCS_REVIEW.md. Mutationsservices ersetzt; keine
echte Dateiaenderung, Browser-/Service-Erfolgsabnahme weiterhin offen.

Aktionsdialoge im Browser: B-55 bis B-58 als regulaeres Mitglied mit zwei
synthetischen Dateien. A-134 bestaetigt; Abbruch/Escape und Dateizuordnung beim
Wechsel positiv. Weiterhin 134 Befunde. Kein Submit, Detail-/Mobil-/Fehlerpfade
weiter offen. browser/docs-actions-followup.json und BROWSER_REVIEW.md.

Dokument-Lifecycle: acht Originalservice-Proben mit zustandsbehaftetem Fake-Drive
und In-Memory-DB. Vier normale Erfolgswege mit passendem Audit-Eintrag positiv.
A-135 (Restore innerhalb Archiv) und A-136 (veralteter DB-Ordner bei bereits
erreichtem Ziel), insgesamt 136 Befunde. DOCS_LIFECYCLE_CHECKS.json; externe
Teil-/DB-Fehler und Parallelitaet weiterhin offen.

Dokument-Teilfehler: fuenf Gruppen nach externem Erfolg, bei DB-Commit-/Audit-
Insertfehlern. Wiederholung erweitert A-136; neuer A-137 zur fehlgeschlagenen
Session nach unterdruecktem Audit-Fehler. Insgesamt 137 Befunde. Original-
Services, Fake-Drive und In-Memory-DB; globale Audit-Aufrufer/Produktion offen.
DOCS_PARTIAL_FAILURE_CHECKS.json und DOCS_REVIEW.md.

Audit-Querschnitt: fuenf weitere Originalrouten-Gruppen ausserhalb Dokumente.
Login-/Event-Fehler erweitern A-137; Kalender und Login mit next bleiben
funktionsfaehig ohne Protokoll. Neuer A-138 zur RSVP-Umkehr bei Wiederholung
nach bereits gespeichertem Zustand. Insgesamt 138 Befunde. AUDIT_FAILURE_REVIEW.md
und AUDIT_FAILURE_ROUTE_CHECKS.json; weitere Audit-Aufrufer/Produktion offen.

Audit-Transaktionen: 64 direkte Aufrufstellen in sieben Dateien inventarisiert,
drei Originalhelfer-Proben zu offenen Fachaenderungen/Commit/Rollback. A-137
um die Transaktionsgrenze praezisiert, weiterhin 138 Befunde. Keine pauschale
Verhaltensfreigabe aller Aufrufer. AUDIT_CALL_INVENTORY.json,
AUDIT_TRANSACTION_CHECKS.json und AUDIT_FAILURE_REVIEW.md.

Mitgliederanlage: fuenf Originalrouten-Proben mit abgefangenem Versand.
A-139 zur Mailbeauftragung vor dauerhaftem Aktivierungstoken; A-137 um beide
Audit-Fehlerstellen erweitert. Normaler Versandfehler zeigt korrekt Warnung.
Insgesamt 139 Befunde. ONBOARDING_FAILURE_CHECKS.json / AUTH_REVIEW.md; kein
echter Versand. Projektbasis weiterhin bf4d84a, App-Code unveraendert.

Onboarding-Wiederaufnahme: drei Gruppen mit je zwei Original-POSTs. Duplikat-
schutz verhindert zweites Konto, aber erneute Anlage scheitert unbehandelt und
sendet keine Einladung neu. A-084/A-139 erweitert, weiterhin 139 Befunde.
ONBOARDING_RETRY_CHECKS.json / AUTH_REVIEW.md. Kein eigener Neusendepfad im
untersuchten Code; keine echte Mail und keine produktive Aenderung.

Aktivierungslink: sechs Originalrouten-Gruppen zu Erfolg/Wiederverwendung, Ablauf,
Zweck, deaktiviertem Mitglied, Passwortvalidierung und Auditfehler. Schutzfaelle
positiv; A-137 um bereits gespeichertes Passwort bei gescheitertem Abschluss
erweitert. Weiterhin 139 Befunde. ACTIVATION_BOUNDARY_CHECKS.json / AUTH_REVIEW.md.
Keine echten Accounts/Mails, Parallelitaet/MFA-/Browservarianten offen.

Aktivierungs-Sessions: drei Gruppen mit normalem Login nach Teilfehler, bereits
angemeldetem anderem Konto und MFA/Onboarding-Kombination. A-140: Aktivierung
umgeht vorhandene MFA-Pruefung bei gueltigem Link; normale Erreichbarkeit der
kombinierten Zustaende noch offen. Insgesamt 140 Befunde. ACTIVATION_SESSION_CHECKS.json
und AUTH_REVIEW.md. Keine echten Accounts oder MFA-Daten veraendert.

Onboarding/MFA-Folgeprobe, Abschluss 2026-10-10: Admin-Anlage, Anfangspasswort-
Login und originales MFA-Setup lassen den Aktivierungslink unbenutzt. Dieser
meldet anschliessend ohne MFA an; normaler Kontrolllogin verlangt MFA. A-140
ueber regulaere Routen erreichbar, weiterhin 140 Befunde. ONBOARDING_MFA_SEQUENCE_CHECKS.json
und AUTH_REVIEW.md. Keine echten Konten/Mails oder Produktionsschluessel beruehrt.

Token-Lebenszyklus, 2026-10-10: vier Originalrouten-Folgen zu alten Aktivierungs-
und Reset-Links nach normalem Passwortwechsel oder Reset mit anderem Link.
A-141: alle vier alten Links koennen das Passwort erneut setzen; anschliessende
Wiederverwendung wird korrekt abgelehnt. Insgesamt 141 Befunde.
CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json / AUTH_REVIEW.md. Ausgabehelfer direkt,
keine Mail-/Produktionspruefung; weitere Ausgabe-/Admin-/Tokenzweck-Grenzen offen.

Reset-Anfragefolgen, 2026-10-10: zwei Gruppen mit originaler Linkausstellung
ueber Passwort vergessen und abgefangenem Versand. Aelterer Link wirkt nach
Reset mit neuerem Link sowie nach administrativem Passwortreset weiter.
Admin-Login und Step-Up original durchlaufen. A-141 erweitert, weiterhin 141
Befunde. RESET_REQUEST_SEQUENCE_CHECKS.json / AUTH_REVIEW.md. Weitere
Tokenzwecke, Parallelitaet und Produktionsbestand offen; App unveraendert.

MFA-Link-Lebenszyklus, 2026-10-10: zwei Originalablauffolgen ueber Mail- und
Admin-Reset mit anschliessender echter lokaler MFA-Neueinrichtung. Alter Link
deaktiviert neue 2FA und entfernt deren Backup-Codes; verbrauchter Link bleibt
nach dritter Einrichtung gesperrt. A-141 erweitert, weiterhin 141 Befunde.
MFA_RESET_LINK_LIFECYCLE_CHECKS.json / AUTH_REVIEW.md. Keine echten Mails,
Konten oder Produktionsschluessel beruehrt; Parallelitaet/Produktion offen.

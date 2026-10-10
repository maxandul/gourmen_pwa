# Frontend: Ladewege, CSS-Quellen und Altlasten

Stand: 2026-09-20. Baseline und Auftrag siehe [README](README.md).
Erster vertiefter Durchlauf; keine Umsetzung oder Loeschfreigabe.

## Methode und belastbare Ergebnisse

77 lokale CSS-/JS-Dateien erfasst, davon 38 mit Hash im Dateinamen.
Enthalten sind auch die zwei bereits vorhandenen unversionierten PWA-Kopien;
die Zahl beschreibt den lokalen Bestand, nicht 77 produktiv geladene Dateien.
Literalreferenzen aus Templates, Backend und Service Worker sowie Erwaehnungen
zwischen Assets wurden erfasst. Erwaehnungen koennen Kommentare enthalten und
sind kein vollstaendiger Abhaengigkeitsgraph.

Vier Seiten wurden mit Flask in der isolierten Testumgebung tatsaechlich
gerendert (alle HTTP 200). Keine externe Verbindung, keine Browserausfuehrung.
Belege: [FRONTEND_ASSET_CHECKS.json](FRONTEND_ASSET_CHECKS.json),
[Ausfuehrungsprotokoll](FRONTEND_ASSET_RUN.txt), `check_frontend_assets.py`.

| Seite | Lokale externe JS-Dateien | CSS-Dateien | Weitere externe Scripts | Lokale CSS-/JS-Bytes |
|---|---:|---:|---|---:|
| `/` | 13 | 2 | Instagram embed.js | 356'011 |
| `/auth/login` | 13 | 1 | keine | 341'519 |
| `/restaurants` | 13 | 2 | keine | 356'011 |
| `/ueber-uns` | 13 | 2 | keine | 356'011 |

Bytes sind die Summe einmalig referenzierter lokaler Dateien auf der Festplatte,
unkomprimiert. HTML, Bilder, Fonts und nachgeladene Ressourcen fehlen darin.
Das sind weder gemessene Netzwerktransfers noch Ladezeiten oder Einsparpotenziale.

## Tatsaechlicher Ladeweg

`base.html` bindet ueber `_head_stylesheets.html` das Bundle
`main-v2.fa47ba3e.css` ein. Die Public-Seiten ergaenzen `public.604da1b3.css`.
Das aktuelle Bundle besteht in dieser Reihenfolge aus `v2/tokens.css`,
`v2/base.css`, `v2/layout.css`, `v2/components.css`.

**Positive Gegenpruefung:** Die reine Build-Funktion erzeugt denselben Text wie
das vorhandene Bundle und seine aktuell referenzierte Hashkopie. Dabei wurden
Zeilenenden durch Textlesen normalisiert; Byte-/Hash-Portabilitaet bleibt A-008.
Der Build wurde nicht ausgefuehrt und keine App-Datei neu geschrieben.
Alte Hashkopien mit `@import`-Ketten belegen keinen solchen Wasserfall im
aktuellen Bundle.

`_head_deferred_scripts.html` liefert `pwa.df1b3f63.js` und `app.6763c8b3.js`.
`base.html` liefert zusaetzlich elf v2-Dateien: theme, theme-toggle, toast,
scroll-to-top, accordion, search, focus-trap, tabs, topbar-scroll,
public-drawer und restaurants-table-scroll. Diese Einbindung ist seitenunabhaengig.
Eine Aufteilung darf gemeinsame Voraussetzungen wie Theme oder Toast nicht
versehentlich entfernen. 13 Dateien allein beweisen kein Performanceproblem.

## CSS-Verantwortlichkeiten

| Quelle | Zeilen | Bytes | `!important` ausserhalb Kommentaren | `@media` ausserhalb Kommentaren |
|---|---:|---:|---:|---:|
| v2/tokens.css | 325 | 11'336 | 0 | 0 |
| v2/base.css | 458 | 10'441 | 1 | 3 |
| v2/layout.css | 584 | 13'631 | 0 | 9 |
| v2/components.css | 6'758 | 156'642 | 6 | 30 |
| public.css | 652 | 14'492 | 0 | 4 |

Die gemeinsame Komponentenquelle traegt den groessten Umfang; das vertieft
A-007, ohne einen zweiten Befund fuer dieselbe Ursache zu erzeugen.
Die wenigen `!important`-Stellen rechtfertigen keine pauschale Diagnose einer
dadurch dominierten Kaskade. Selektorueberschneidungen, Spezifitaet und
Breakpoint-Konflikte sind damit noch nicht geprueft.

## Altlasten nach Belegstaerke

| Gruppe | Einordnung und naechste Pruefung |
|---|---|
| v2-Quellen, public.css, app.js, pwa.js | Fehlender direkter HTML-Link ist kein Altlastenbeleg: Build-/Fingerprint-Quellen von eingebundenen Dateien. |
| main-v2.css | Generiertes Zwischenprodukt; kein unabhaengiges zweites Designsystem. |
| accordion.js / search.js | Global eingebunden. Keine passenden `data-accordion`-/`data-search`-Hooks oder externen direkten Konstruktor-/Initialisierungsaufrufe in Templates, Backend oder anderen JS-Dateien gefunden. Eigene Auto-Initialisierung ist vorhanden. Starker Kandidat fuer ungenutzte gemeinsame Controller, siehe A-097. |
| animations, components, core, features, layout, mobile-touch, notifications, pwa, responsive, utilities unter static/css | Kein direkter aktueller Template-/Backend-/SW-Link im Inventar. Manche Namen stehen in alten Kommentaren; nicht im aktuellen CSS-Build. Historische und dynamische Consumer vor Entfernung pruefen. |
| google-maps.js / places-autocomplete.js | Keine direkte Laufzeit-Dateireferenz gefunden. Aehnlicher Autocomplete-Code steht in Event-Erstellung und -Bearbeitung. Funktionsvergleich und globale Callback-Namen vor Konsolidierung pruefen. |
| Historische Hashkopien | Ein Teil enthaelt fruehere Importketten. Aufbewahrung fuer alte HTML-/SW-Versionen und Rollback explizit festlegen; nicht nach Alter oder fehlender aktueller Template-Referenz loeschen. |

Die UI-Dokumentation stellt mehrere der oben nicht eingebundenen CSS-Dateien
weiterhin als funktionale Bestandteile dar. Das ergaenzt den Dokumentationsabgleich
A-012; daraus folgt keine automatische Aktivierung dieser Dateien.

## Empfehlung und Abnahme

Zuerst eine verbindliche Zuordnung Quelle → Build → ausliefernde Seite → Verhalten
festhalten. Anschliessend gemeinsame Controller mit den tatsaechlichen
Seitenimplementierungen vergleichen (A-005/A-006/A-097). CSS nach nachgewiesenen
Verantwortlichkeiten gliedern; die Anzahl Dateien ist dabei kein Qualitaetsziel.

Fuer den Nutzungsnachweis CSS-/JS-Coverage waehrend definierter Interaktionen
erheben. Das Werkzeug misst die Nutzung waehrend einer Aufzeichnung;
ein einzelner Seitenaufruf reicht fuer unsere Rollen-/Zustandsmatrix nicht.
Referenz: [Chrome DevTools Coverage](https://developer.chrome.com/docs/devtools/coverage).

Vor einer Bereinigung muessen Dialoge, Validierungsfehler, Filter, Tabs, Theme,
PWA-Installations-/Updatehinweise und mobile Navigation in die Messung einbezogen
werden. Danach visuelle Gegenpruefung der betroffenen Seiten sowie Update von
Build, Service Worker und Dokumentation als zusammenhaengendes Paket empfehlen.

## Offene Arbeit

### Vertiefung: Komponenten und Zustandsverantwortung

Zusaetzlicher Quellvergleich am 2026-09-20; keine Browsermessung:

| Bereich | Gepruefte Ueberlagerung / Ergebnis |
|---|---|
| Cards | Grundregeln um Zeile 495, interaktive Variante und pauschales `.card:active` um 3141, Filtervariante ab 4005 in components.css. Auch nicht interaktive Cards erhalten den Pressed-Transform. Verhalten beim Bedienen von Eingaben innerhalb der Card im Browser pruefen; vorerst kein neuer Fehlerbefund. |
| Filter/Aktionen | `.card--filter .disclosure__content .btn` verkleinert Buttons ueber die Elternstruktur. Mobile Regeln setzen Aktionsbuttons auf volle Breite; Event-/Buchhaltungsaktionen haben weitere kontextabhaengige Regeln. Das vertieft A-005/A-007: Einbauort veraendert Komponentenoptik. |
| Formulare | Allgemeine `.form-row`-Gridregeln stehen nach frueheren Inline-Flexvarianten; diese erzwingen `grid-template-columns: none !important`. Das ist eine nachvollziehbare Variantenregel, allein kein nachgewiesener Konflikt. |
| Tabellen | `.table-responsive` und `.data-table-wrap` neben Public-Tabellencontroller: verschiedene Familien. Vollstaendiger Vergleich mit breiten Inhalten, Sticky-Spalten und Touch bleibt offen. |
| Dialoge | Gemeinsames DIV-Modal-CSS verwendet `data-open`, waehrend native Dialogfamilien eigene Controller haben. `focus-trap.js` wird global geladen, aber ausser seiner eigenen Definition keine Aufrufe von `createFocusTrap`/`new FocusTrap` gefunden. Ergaenzt A-016/A-097, kein Beleg fuer funktionierendes Fokusmanagement. |
| Toast | `app.js` delegiert `showToast` an `Toast.show` aus v2/toast.js. Diese zwei Namen belegen keine doppelte aktive Anzeige. Lokale Sonderfunktionen, z.B. temporaeres Admin-Passwort, bleiben gesondert zu pruefen. |
| Theme | Originalskripte zeigen DOM-/Schalter-Divergenz nach simuliertem Systemwechsel, A-098. Hamburg besitzt eine eigene Umschaltung und eigenen Speicherschluessel; deren Einbindung separat pruefen. |

Die Token-Gegenpruefung erfasst 167 verschiedene Definitionsnamen in den fuenf
Quellen. Sechs nicht definierte Namen ohne Fallback kommen an sieben Stellen vor,
darunter die gemeinsam verwendete Schrittanzeige (A-099). Definierte Namen
beweisen noch keine korrekte Vererbung oder Gueltigkeit in jedem Kontext.
`--rating-hue` und `--budget-meter-fill` werden nachweislich in Templates gesetzt;
weitere optionale Werte haben Fallbacks. Diese Faelle sind keine Tokenfehler.

Nachweise: [CSS_TOKEN_CHECKS.json](CSS_TOKEN_CHECKS.json) und
[THEME_STATE_CHECKS.json](THEME_STATE_CHECKS.json). Die fuenf Theme-Proben sind
isolierte Zustandsbelege, keine Browser- oder fachlichen Workflow-Tests.

### Noch nicht abgeschlossen

Browser-Ergaenzung: B-14 bis B-20 in [BROWSER_REVIEW.md](BROWSER_REVIEW.md)
bestaetigen A-099 an zwei Formularen und A-014 am Buchungsformular bei 1024px.
Manueller Theme-Schalter und Eingabenerhalt beim Schrittwechsel positiv geprueft.
Systemwechsel und gedrueckter Card-Zustand bleiben mit dieser Browsersteuerung
nicht reproduziert. Damit ist die unten genannte Gesamtmatrix weiter offen.

- Vollstaendiger Consumer-Graph inklusive dynamischer Klassen und globaler Callbacks.
- CSS-Kaskade an wiederkehrenden Cards, Filtern, Formularen, Tabellen und Dialogen.
- Handler-Zustaendigkeit und Initialisierungsreihenfolge, insbesondere Theme/Toast.
- Modulbezogene Assets, Diagrammbibliotheken und Drittinhalte aller privaten Seiten.
- Browser-Coverage, Netzwerk-/CPU-Messungen mit kaltem und warmem Cache sowie
  weitere Viewports, Themes und Tastatur-/Touchzustaende.
- Historische Assets mit SW-Update-/Offline-Lebenszyklus abgleichen.

Phase 03 bleibt **in_progress**. Bestehende 143 Workflow-Szenarien werden durch
diese vier HTML-Ladelisten nicht zu weiteren Workflow-Tests umetikettiert.

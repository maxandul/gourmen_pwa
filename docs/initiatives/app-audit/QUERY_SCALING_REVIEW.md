# Datenbankarbeit bei wachsenden Datenmengen

Stand 2026-09-20. Originalrouten und Templates, SQLite nur im Speicher,
synthetisches regulaeres Mitglied, ausgehende Sockets gesperrt. Keine App-Aenderung.

## Methode und Abdeckung

Vier voneinander getrennte Datenbestaende, sechs Seiten, je zwei Aufrufe mit
frischer ORM-Session und zurueckgesetztem Login-Cache: **48 Render-Aufrufe**.
Alle antworten mit HTTP 200. Die beiden Wiederholungen liefern je Kombination
identische SQL-Zaehler und ORM-Ladeereignisse. Keine INSERT/UPDATE/DELETE waehrend
der gemessenen GETs; das widerlegt A-051 mit inaktiven Varianten nicht.

Gezahlt wurden SQL-Ausfuehrungen und geladene ORM-Objekte einschliesslich
Template-/Kontextarbeit. Keine Zeitmessung, keine PostgreSQL-Queryplaene,
keine Zahl untersuchter DB-Zeilen und kein Browser-Performance-Test.
ORM-Ladeereignisse sind nicht zwingend eindeutige Datensaetze innerhalb eines
Requests. SQL-Parameter werden nicht ausgegeben.

Baseline: 5 vergangene Events der aktuellen Saison, 5 aktive Mitglieder,
3 aktive Merch-Artikel mit je einer aktiven Variante. Jedes Mitglied nimmt
an jedem Event teil, mit Schaetzung/Punkten. Keine Bewertungen, Bestellungen,
Claims oder zukuenftigen Events. Je Vergleich wird nur eine Dimension erhoeht.

Belege: [QUERY_SCALING_CHECKS.json](QUERY_SCALING_CHECKS.json),
[Ausfuehrungsprotokoll](QUERY_SCALING_RUN.txt), `check_query_scaling.py`.

## SQL-Ausfuehrungen pro Seitenaufruf

| Seite | Baseline | 30 Events | 30 Mitglieder | 30 Artikel |
|---|---:|---:|---:|---:|
| Dashboard | 29 | 104 | 29 | 29 |
| Kommende Events (hier leer) | 16 | 66 | 16 | 16 |
| Event-Archiv, erste Seite | 32 | 97 | 32 | 32 |
| GGL, Tabelle | 46 | 171 | 71 | 46 |
| Merch-Shop | 20 | 70 | 20 | 74 |
| Public-Restaurants | 2 | 2 | 2 | 2 |

Die Zahlen zeigen nicht, dass eine Seite um denselben Faktor langsamer wird.
Sie zeigen nachweisbare zusaetzliche Datenbankarbeit bei wachsendem Bestand.

## Ursachen und Empfehlungen

**Bereinigung wird global berechnet, nur im Dashboard verwendet (A-030).**
`backend/app.py:236` fuehrt `get_progress` fuer jedes authentifizierte Template
aus. Die Textsuche nach `retro_cleanup_progress` findet als Template-Consumer
nur `dashboard/index.html`. Im Shop erzeugen 25 weitere vergangene Events
50 weitere SELECTs: je Event Teilnahme und Bewertung. Das ausgegebene Shop-HTML
bleibt dabei bei 41'324 Bytes; auch die leere kommende Eventliste kostet mehr.
Empfehlung: Fortschritt nur bei Bedarf ermitteln und Kandidaten/Teilnahmen/
Bewertungen gemeinsam laden. Keine nutzeruebergreifende Zwischenspeicherung
ohne explizite Schluessel und Aktualisierungsregeln einfuehren.

**GGL-Rangliste wird wiederholt berechnet (A-104).**
`ggl.index` berechnet Ranglisten fuer Saisonwerte, fuer den Tabellen-Tab und
nochmals im immer aufgerufenen Performance-Kontext. `get_season_ranking` fragt
pro Event die Teilnahmen einzeln ab. Bei 30 Events erscheint diese Queryform
90-mal. Weitere 60 SELECTs kommen aus der globalen Bereinigung; die Ursache
ist also nicht ausschliesslich die GGL selbst. Mit 30 Mitgliedern kommen zudem
25 Abfragen hinzu; `_attach_member_to_ranking` laedt Mitglieder einzeln.
Empfehlung: pro Request/Saison ein Ergebnis wiederverwenden, Daten fuer den
gewaehlten Tab gezielt aufbereiten und benoetigte Relationen gesammelt laden.

**Shop-Varianten werden zweimal je Artikel abgefragt (Ergaenzung A-051).**
3 → 30 Artikel ergibt 20 → 74 SQL-Ausfuehrungen. Zwei Varianten-Queryformen
kommen jeweils 3 bzw. 30-mal vor: aktive Varianten explizit laden und bestehende
Relation fuer deren Zuweisung laden. Die bereits empfohlene Trennung von
Anzeige-Daten und persistenter Relation sollte diese Mehrarbeit gleich mit
beseitigen; keine zweite unabhaengige Reparatur derselben Stelle.
Das Shop-HTML waechst dabei von 41'324 auf 202'706 Bytes. Das ist lokale
unkomprimierte HTML-Groesse, kein gemessener Netzwerktransfer. Ob Filterung,
Seitenteilung oder kleinere Darstellung sinnvoll sind, braucht realistische
Artikel-/Variantenmengen und eine Produktentscheidung.

Geeignete gebuendelte Ladestrategien dokumentiert
[SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html).
Nicht pauschal alle Relationen zusammenjoinen: Das kann seinerseits sehr grosse
Zwischenergebnisse erzeugen. Die Wahl muss zur benoetigten Datenform passen.

## Gegenbeispiele und verbleibende Risiken

- Public-Restaurants bleibt bei zwei Queries, laedt aber 5 bzw. 30 Events.
  Der Service laedt alle passenden Events und Ratings vor Sortierung/Seitenteilung.
  Konstante Queryzahl ist damit kein Nachweis konstanter Arbeit oder Laufzeit.
- Das Event-Archiv paginiert seine Hauptliste auf zehn Eintraege. Trotzdem
  waechst die globale Hintergrundarbeit mit der gesamten Eventhistorie.
- Mehr Mitglieder erhoehen auf mehreren Seiten die geladenen Objekte, ohne
  die Zahl der Queries zu erhoehen. Nur Queries zu zaehlen waere unvollstaendig.

## Naechste Messungen / Abnahme fuer spaetere Aenderungen

Offen: kuenftige Events, umfangreiche Ratings, gemischte
Order-/Claim-Zustaende, weitere Accounting-Daten und Rollenvarianten. Danach Queryplaene/Indizes und
Zeit-/Speicherprofile auf repraesentativer PostgreSQL-Testbasis pruefen.

Spaetere Optimierungen muessen gleiche sichtbare Daten, Rechte, Rangfolge und
Bereinigungsregeln liefern. Abfragen sollen nicht einzeln pro Event/Artikel/
Mitglied anwachsen, wo dieselben Daten gesammelt geladen werden koennen.
Eine absolute Abfragezahl ist erst nach diesen Entscheidungen als Budget sinnvoll.

Diese 48 Aufrufe sind Skalierungsproben, keine 48 neuen fachlichen Workflowtests.

## Zweiter Durchlauf: Bestellungen, Claims und Buchhaltung

Weitere **48 Render-Aufrufe**: vier Bestaende, sechs URLs, je zwei Wiederholungen
mit frischer ORM-Session. Alle HTTP 200, keine DML, wiederholte SQL-/ORM-Zaehler
identisch. Rollen diesmal synthetischer Admin, fuenf Mitglieder, keine Events,
ein Geschaeftsjahr und ein Konto. Die Baseline unterscheidet sich deshalb vom
ersten Durchlauf; die absoluten Zahlen nicht quer zwischen beiden vergleichen.

Baseline: je fuenf Bestellungen, Claims und Buchungen mit je einem zugeordneten
Beleg. Ein Artikel/eine Variante, eine Position je Bestellung. Alle Bestellungen
und Claims gehoeren Mitglied 1. Je Vergleich nur Orders, Claims oder gekoppelte
Buchung-/Belegpaare auf 40 erhoeht. Drive-Metadaten sind erfunden, keine Dateien
hochgeladen. Reale Services blieben gesperrt.

Belege: [COMMERCE_SCALING_CHECKS.json](COMMERCE_SCALING_CHECKS.json),
[Ausfuehrung](COMMERCE_SCALING_RUN.txt), `check_commerce_scaling.py`.
Aktive Tabs wurden aus dem gerenderten HTML gegengeprueft, einschliesslich
`tab=posten` fuer Offene Posten.

| Seite | Baseline | 40 Bestellungen | 40 Claims | 40 Buchungen + Belege |
|---|---:|---:|---:|---:|
| Dashboard | 15 | 15 | 15 | 15 |
| Meine Bestellungen | 7 | 7 | 7 | 7 |
| Admin-Bestellungen | 15 | 50 | 15 | 15 |
| Buchhaltung Uebersicht | 32 | 32 | 32 | 67 |
| Buchhaltung Journal | 32 | 32 | 32 | 67 |
| Buchhaltung Offene Posten | 32 | 32 | 32 | 67 |

### Nachgewiesene Ursachen

- **A-105:** Buchhaltung laedt Journal, Belege, Claims und Statistik fuer alle
  Tabs. Die Panels werden serverseitig voll gerendert und per CSS ausgeblendet.
  Damit wachsen auch beim Einstieg in Uebersicht oder Offene Posten Abfragen
  und HTML mit dem Journal. `booking.receipts` im Journal fuehrt eine zusaetzliche
  Belegabfrage je Buchung aus, obwohl die Belegliste bereits separat geladen ist.
  5 → 40 Paare: 32 → 67 Queries und Uebersichts-HTML 92'691 → 205'504 Bytes.
- **A-106:** Admin-Merch fragt Bestellpositionen einzeln ab, um pro Bestellung
  `get_item_count()` anzuzeigen. 5 → 40 Orders: 15 → 50 Queries; dieselbe
  Positions-Queryform erscheint 5 bzw. 40 Mal. HTML 43'297 → 155'697 Bytes.
- **Gegenbeispiel:** Meine Bestellungen laedt zwar 5 bzw. 40 Bestellkoepfe,
  aber jeweils nur eine Position fuer die ausgewaehlte Bestellung. Kein
  Positions-N+1 fuer diesen konkret geprueften persoenlichen Tab.
- **Wachstum ohne mehr Queries:** Das Dashboard laedt alle 5 bzw. 40 eigenen
  Bestellungen, obwohl es nur letzte Bestellung und Zahl offener Orders verwendet.
  Bei mehr Claims laedt und rendert es dagegen auch entsprechend mehr Inhalt.
  Kleine Queryzahl sagt nichts ueber Nutzdatenmenge oder Renderkosten aus.
- 5 → 40 Claims laesst die Buchhaltungs-Uebersicht bei 32 Queries, vergroessert
  aber deren HTML von 92'691 auf 155'442 Bytes. Der gesamte Claims-Tab wird
  bereits mit ausgeliefert; das ist Teil A-105, kein eigener doppelter Befund.

Alle Bytezahlen sind unkomprimiertes lokal gerendertes HTML, keine gemessenen
Transfers oder Ladezeiten. Buchungen und Belege wurden gemeinsam vergroessert;
die Einzelquery-Ursache ergibt sich aus SQL-Profil und Templatezugriff, nicht
allein aus dem Vergleich zweier Summen.

### Empfehlung / verbleibende Grenzen

Fuer Buchhaltung bewusst zwischen sofort verfuegbaren Client-Tabs und gezielter
serverseitiger Bereitstellung abwaegen. Kleine Kennzahlen gemeinsam laden,
umfangreiche Listen begrenzen oder erst bei Bedarf bereitstellen; URL-/Filter-
Verhalten und Rechte dabei erhalten. Buchungsbelege gebuendelt laden oder einen
gezielten Existenzindikator fuer die Liste bereitstellen. Admin-Bestellmengen
gesammelt aggregieren, ohne fuer reine Zaehler alle Positionen zu instanziieren.

Weitere Abdeckung fehlt fuer viele verschiedene Schuldner/Glaeubiger, private
Claims, Teilzahlungen, mehrere Artikel/Positionen je Order, inaktive Varianten,
Filterkombinationen, Bankimporte und Kommentare. Mehrere Geschaeftsjahre siehe unten.
Zusammen umfassen beide Durchlaeufe **96 Render-Messungen**, weiterhin keine
zusaetzlichen fachlichen Workflow-Szenarien und keine Produktionsmessung.

## Dritter Durchlauf: historische Saisons und Geschaeftsjahre

Weitere **24 Render-Aufrufe**: drei Bestaende, vier URLs, je zwei frische
ORM-Sessions. Fuenf Mitglieder, fuenf Januar-Events je Saison und zwei
Aufwandsbuchungen je Geschaeftsjahr. Baseline eine Saison/ein Geschaeftsjahr;
danach getrennt sechs Saisons oder sechs Geschaeftsjahre. Aktuell ausgewaehltes
Jahr bleibt 2026, dessen Daten bleiben unveraendert. Alle Jahre sind in dieser
Fixture offen; keine Revisions-, Beleg-, Claim- oder Importszenarien.

Belege: [HISTORY_SCALING_CHECKS.json](HISTORY_SCALING_CHECKS.json),
[Ausfuehrung](HISTORY_SCALING_RUN.txt), `check_history_scaling.py`.
Alle 24 Antworten HTTP 200, keine DML, SQL-/ORM-Zaehler je Wiederholung identisch.
Ausgewaehlte Saison, Geschaeftsjahr und GGL-Rangprojektion wurden mit erfasst;
die aktuelle Rangliste bleibt ueber alle drei Bestaende gleich.

| Aktuelle Ansicht | Baseline | 6 Saisons | 6 Geschaeftsjahre |
|---|---:|---:|---:|
| Dashboard | 29 | 79 | 29 |
| GGL Tabelle | 46 | 141 | 46 |
| GGL Performance | 46 | 141 | 46 |
| Buchhaltung Uebersicht | 39 | 89 | 39 |

- **A-030 bestaetigt:** 25 zusaetzliche historische Events verursachen 50
  weitere Abfragen durch den globalen Bereinigungs-Kontext. Dies trifft auch
  die Buchhaltung, deren HTML dabei unveraendert 69'975 Bytes umfasst.
- **A-104 vertieft:** GGL verarbeitet in der Saisonschleife auch die alten
  Saisons. Beide aktuellen Tabs steigen um 95 Queries; darin sind die 50
  globalen Bereinigungs-Abfragen enthalten. Die beiden Ursachen nicht doppelt
  als Einsparung zaehlen. Historische Detailberechnungen am sichtbaren Bedarf
  ausrichten und benoetigte Saisonkennzahlen gesammelt bereitstellen.
- **Positives Gegenbeispiel:** Sechs Geschaeftsjahre bleiben bei 39 Queries.
  `AccountingService.get_year_comparison` aggregiert die Jahre gemeinsam;
  auch der Anfangssaldo wird aggregiert. Geladen werden sechs statt eines
  Jahresobjekts, weiterhin nur zwei Buchungsobjekte des ausgewaehlten Jahres.
  Das HTML waechst auf 72'545 Bytes, unter anderem durch Jahresauswahl und
  Vergleich. Kein Nachweis eines Einzelabfrage-Problems pro historischem Jahr.

Konstante Queryzahl bedeutet keine konstante Datenbankarbeit: SQL-Scanmengen,
Indizes, PostgreSQL-Laufzeit und Speicher wurden nicht gemessen. Der Befund
A-105 zur unbedingten Verarbeitung aller Tabs im ausgewaehlten Jahr bleibt
vom positiven Jahresvergleich unberuehrt. Die drei Durchlaeufe umfassen jetzt
**120 Render-Messungen**. Keine neuen fachlichen Workflow-Szenarien und keine
neuen Befundnummern fuer bereits dokumentierte Ursachen.

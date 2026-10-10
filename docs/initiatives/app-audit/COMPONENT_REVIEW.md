# Querschnittsreview: Oberflaechenmuster und Konsistenz

Stand 2026-09-07. Original-App-Code unveraendert. Die strukturelle Erfassung
umfasst **alle 83 Templates**. Das ist kein vollstaendiges Code-/Workflow-Review
jedes Templates. Ausfuehrliche Einzelfehler: FINDINGS.md; Browserbelege: BROWSER_REVIEW.md.

## Erfassungsmethode und korrigierte Zaehler

`survey_ui_patterns.py` erfasst HTML-Tags und **exakte Klassentokens** in allen
Templates. Jinja-Bedingungen werden dabei nicht ausgewertet. Die JSON-Datei
`UI_PATTERN_LOCATIONS.json` nennt Tag, Attribute und Zeile je Fundstelle;
`UI_PATTERN_SURVEY.csv` hat fuer jedes der 83 Templates einen Eintrag.

| Muster | Dateien mit dem Muster | Einordnung |
|---|---:|---|
| Standard-Tabnavigation `.tabs__nav` | 7 | gemeinsame Optik, gemischte Navigationslogik |
| Eigene Hamburg-Tabnavigation | 1 | separates CSS/JS |
| Native `<details>` | 16 | Filter, Aktionen, Hinweise, optionale Felder |
| Native `<dialog>` | 6 | darunter Partials, nicht sechs alleinstehende Seiten |
| Exakte `.modal`-Klasse | 4 | Events, GGL, Buchhaltungs-Statistik zweimal |
| `.card--filter` | 13 | unterschiedliche semantische Aufgaben |
| `.card--collapsible` | 2 | Merch-Shop/Bestellformular |
| Formulare | 45 | inklusive kleiner Aktionsformulare |
| Canvas-Diagramme | 4 | inklusive Statistik-Partial und altem Volltemplate |
| Lokales Lucide-Makro | 43 | Kopien trotz gemeinsamem Partial |
| Import gemeinsamer Formular-Makros | 9 | Mehrheit baut Felder/Fehler selbst |
| Lokaler `bindDisclosure` | 5 | Events-Liste/-Detail, GGL, Buchhaltung Index/Stats |

Die grobe Erstinventur zaehlte Hamburg zu den Standard-Tabs und
`docs-action-modal` zu `.modal`. Diese Zaehler sind hiermit korrigiert.
Inline-Styles sind insbesondere bei E-Mails gesondert zu beurteilen;
Anzahl allein ist keine Zahl von Fehlern.

## Shell und Hauptnavigation

| Aufgabe | Bestand | Bewertung / Vorschlag |
|---|---|---|
| Public vs. App | Body-Attribut aus `public.*`; gemeinsames base.html | Zwei bewusste Shells sind sinnvoll. Login/Fehlerseiten als dritte Situation explizit behandeln. |
| Hauptbereiche | Sidebar + Bottom-Nav mit kopierten Endpoint-Bedingungen | Zentraler Bereichskatalog; gleiche Labels/aktive Zuordnung fuer beide Darstellungen. A-002. |
| Sidebar-Breite | 200px Margin ab 1024, Main weiterhin 100% | Bestaetigtes Abschneiden rechts, einschliesslich Login ohne Sidebar. A-014. |
| Seiten-Zurueck | oft `.page-back`, Texte/Ziele seitenlokal | Fachliches Elternziel vs. Browser-Zurueck unterscheiden; Filter-/Tab-Kontext bewusst erhalten. |
| Vorher/Weiter | Event-ID-Wechsel; Bereinigung wechselt offenen Eintrag | Aehnliche Optik moeglich, semantisch andere Aufgabe als Formular-Schritte. |
| Kontomenue | Profil/Sicherheit/Technik ausserhalb Hauptnavigation | Im Zielbild die Zuordnung zu persoenlichen Einstellungen vs. Vereinsfunktionen klaeren. |

## Saemtliche Tab-Systeme

| Template | Verhalten im Bestand | Beurteilung / verbleibende Pruefung |
|---|---|---|
| `events/index.html` | Tablinks erzwingen Navigation; Filter/Tab-URLs serverseitig | Ereignisabhaengiger Heute-Tab; Servernavigation bewusst erhalten oder vollwertig ersetzen. |
| `events/detail.html` | Client-Umschalten mit History; Ratings bedingt | Browser-Zurueck und Event-Pfeile fehlerhaft, A-003/A-015. |
| `ggl/index.html` | `data-force-navigation=true`, Charts bedingt | Kommentar erklaert Script-Initialisierung als Grund; nicht blind auf Client-Umschalten umstellen. |
| `accounting/index.html` | Client-Umschalten, bis zu neun Tabs, Rechte abhaengig | A-015 bestaetigt. Navigation ist auf 390px 1196px breit bei 311px sichtbarem Bereich; Produktentscheidung zur Bereichsstruktur noetig. |
| `member/profile.html` | Profildaten clientfaehig; sensible Daten erzwingen Servernavigation | Sicherheitspruefung darf durch Komponentenumbau nicht umgangen werden; ungespeicherte Eingaben spaeter testen. |
| `member/merch/index.html` | Zwei Tabs; Bestellauswahl bringt weiteren Queryparameter | Parameter beeinflussen, ob Controller umschaltet oder Seite neu laedt; Fehler-/Leerzustand pruefen. |
| `admin/merch/index.html` | Zwei Tabs, Bestell-Filterparameter nur teilweise weitergegeben | Verhalten abhaengig vom URL-Kontext; reproduzierbare Auswahl-/Filter-Regeln definieren. |
| `events/hamburg2026.html` | Eigenes `hamburg-tabs__nav` und eigenes Script | Bewusste Sonderseite vs. wartbarer Standardbaustein entscheiden; hier nur strukturell erfasst. |

Alle sieben Standard-Dateien verwenden dasselbe Tab-Script und aehnliches
ARIA-Markup. Ein gemeinsamer Vertrag muss Auswahl, URL, Tastatur, Panel-ID,
Fokus, Initialisierung versteckter Inhalte und abhaengige Aktionen abdecken.
Gleiche CSS-Klasse allein gewaehrleistet das nicht. Siehe A-003/A-004/A-015.

## Saemtliche Fundstellen der Filter-Flaeche

| Template | Tatsaechliche Aufgabe | Sichtbarkeit / Variante |
|---|---|---|
| `events/index.html` | Jahr/Organisator plus Erfassen/Planung | gemeinsames Disclosure vor Tabs, eigener Speicher-/Reset-Controller |
| `events/detail.html` | Bearbeiten, Ratings erlauben, Loeschen | kein Datenfilter; Berechtigungen steuern Inhalt |
| `ggl/index.html` | Saison | Disclosure vor Tabs, Kontext-Chip, eigener Controller |
| `accounting/index.html` | Jahr/Export/Jahreseroeffnung; weitere Journal-/Belegfilter | globale und tablokale Filter mischen sich; eigener Controller |
| `accounting/_tab_kontenplan.html` | neues Konto erstellen | schreibende Aktion, kein Filter |
| `accounting/accounts.html` | Kontoerstellung, historisches Volltemplate | Route `/accounts` leitet GET inzwischen in Tab um; Verwendung weiter verifizieren |
| `accounting/stats.html` | Jahr | Volltemplate neben Statistik-Partial, aktiven Aufrufpfad klaeren |
| `admin/merch/index.html` | Status/Mitglied/Sortierung | tablokal; Chips, native Disclosure-Variante |
| `admin/merch/order_detail.html` | Bestellstatus aendern | schreibende Administration, kein Filter |
| `member/merch/index.html` | konkrete Bestellung auswaehlen | Detailauswahl statt Listenfilter; Reset vor Filtern, anders als GGL |
| `docs/index.html` | Volltextsuche und Hochladen | oeffnet bei Suchquery; Hauptaktion sonst verborgen; role=search |
| `docs/folder.html` | Volltext im Ordnerbaum | oeffnet bei Suchquery; Upload separat im Ordnerkopf |
| `member/profile.html` | Hinweis auf verschluesselte Daten | keine Interaktion; Filter-Styling ohne Filter |

Vorschlag: gemeinsame Oberflaechen fuer **Seitenaktionen**, **Listenfilter**,
**Datensatzauswahl**, **Administration** und **Hinweise**. Nur diejenigen
zusammenfassen, deren Aufgabe und Verhalten tatsaechlich identisch sind.
Ob eine Aktion eingeklappt sein soll, folgt ihrer Wichtigkeit und Nutzung.

## Formulare, Cards und Status

- Gemeinsame Feldmakros bieten bisher Pflichtstern/Fehlertext, aber keinen
  kompletten Vertrag fuer ID, Label, Hilfe, Fehler und Fokus. A-017/A-018.
- Event-Erstellen/Bearbeiten teilen 466 identische Zeilen bei 494/505 Zeilen.
  Diese Doppelspurigkeit ist wesentlich groesser als ein wiederholtes Icon. A-020.
- Merch-Variantenfelder haben im geprueften Shop unbenannte Controls; zukuenftige
  Komponenten muessen auch dynamisch hinzugefuegte Zeilen korrekt behandeln.
- Cards dienen gleichzeitig als Eingabegruppen, Kennzahlen, Listenpositionen,
  Inhaltssektionen und aufklappbare Bestellartikel. Ein Zielsystem braucht
  wenige definierte Varianten, nicht zwingend eine Card um jeden Inhalt.
- Die Bestell-Card ist ein aufklappbarer Abschnitt, kein Dialog. Ein nativer
  Disclosure-Baustein kann passen; die fachliche Variantenlogik bleibt eigenstaendig.
- Fehler-/Leer-/Erfolgszustaende und Tabellen/Diagramm-Alternativen sind noch
  nicht ueber alle 45 Formular-Templates bzw. alle Datenzustaende geprueft.

## Dialoge und Diagramme

| Familie | Umsetzung | Befund |
|---|---|---|
| Drive-Upload/Aktionen/Ordnerpicker | native Dialoge, einzelne Controller | Upload: initialer Fokus, Escape und Rueckgabe an Trigger positiv geprueft. Verschachtelung offen. |
| Kalender-Bestaetigungen | native Dialoge | nur strukturell gelesen; Aktivierung/Regeneration/Deaktivierung offen |
| Public-Drawer | nativer Dialog | Escape/Fokusrueckgabe bei 390px positiv; Wechsel mit offenem Drawer auf 1024px blockiert Seite unsichtbar, A-100/B-23 |
| Events-Charts | DIV mit role=dialog + hidden/data-open | Fokus bleibt ausserhalb; Tastatur bedient Hintergrund, A-016 |
| GGL-/Accounting-Charts | eigene DIV-Modal-Logik | Accounting-Fokusfehler bestaetigt, A-016/B-24; GGL-Dialog wegen leerer Verlaufsdaten noch offen |

Vorschlag: ein Dialog-Baustein mit definiertem Fokus-/Close-/Scroll-Verhalten,
inhaltlich unterschiedliche Varianten fuer Chart, Formular und Bestaetigung.
Diagramme zusaetzlich auf passende Datenalternative, Resize in versteckten Tabs,
Vollbild und Touch-Lesbarkeit pruefen. Ein zugreifbarer Titel ersetzt keine
zugaengliche Wiedergabe der dargestellten Daten.

## Workflows: Gemeinsame Bausteine mit verschiedenen Bedeutungen

| Ablauf | Typ | Was gleich sein kann / was getrennt bleiben muss |
|---|---|---|
| Bereinigung | Warteschlange offener Eintraege | Positionszaehler/Vorher/Weiter; Weiter speichert nicht automatisch. Undo und Abnahmezustand fachlich separat. |
| BillBro | fachlicher Prozess mit mehreren Rollen | gemeinsame Schrittanzeige; Regeln fuer Oeffnen/Schliessen, Anwesenheit, Rechnung und Zahlung serverseitig. |
| Buchung erfassen | lokales Formular mit drei Schritten | Schrittanzeige, Validierung, Fokus, Vorschau; aktuell eigener Inline-Controller. |
| Beleg einreichen | lokales Formular mit zwei Schritten | gleiche Formular-Navigation; Kamera/Datei, Vorschau und Upload bleiben spezielle Eingaben. |
| Jahresabschluss | Statusprozess offen → in Pruefung → abgeschlossen | verwendet BillBro-Klassen; neutrale Fortschrittskomponente moeglich, Rechte/Revision getrennt. |
| Merch | Bestellung plus Statusverwaltung | im erfassten aktuellen Code kein entsprechender achtstufiger Runden-Workflow; Docs nennen noch Merch-Runden-Klassen. Code-/Doku-Abgleich in Modulreview vertiefen. |

Bereinigung und Formularschritte verwenden beide `cleanup-step-nav`, obwohl
Vorher/Weiter unterschiedliche Bedeutung hat. Ziel ist konsistente Darstellung
mit expliziter Semantik, nicht eine einzige universelle Workflow-Engine.

## Pruefabschluss dieses Teilpakets

Abgeschlossen: strukturelle Erfassung aller Templates, Vergleich der sieben
Standard-Tabdateien, Einordnung der 13 Filter-Fundstellen, erste Dialog-/Formular-
und Breakpoint-Reproduktionen. Daraus folgen noch keine Loeschfreigaben.

Offen: vollstaendige Formular-/Tab-Interaktionen fuer alle Rollen und Zustaende,
alle Cards/Tabellen/Diagramme mit umfangreichen Inhalten, Hamburg, GGL-Charts,
weitere Accounting-Chartzustaende, verschachtelte Dialoge, mobile Tastatur, Kontraste,
Screenreader, echte Geraete, browseruebergreifende Vergleiche.

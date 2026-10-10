# Karten, Formulare und Tabellen – Variantenabgleich

Stand 2026-09-20, unveraenderter App-Code. Statischer Durchlauf, keine neuen
Browser-Reproduktionen. Beleg: [STRUCTURAL_VARIANTS.json](STRUCTURAL_VARIANTS.json).
Reproduktion: `check_atom_variants.py --structural`.

## Abgeschlossener Teilumfang

Fuer sechs Familien wurden konkrete Unterelemente/Modifier in ungehashten
V2-CSS-Quellen mit Templates und V2-JS abgeglichen und Auffaelligkeiten im
Quellkontext gelesen. 47 definierte Namen, 36 lexikalisch verwendete Namen;
zwei verwendete Namen ohne Definition, 13 Definitionen ohne Treffer in den
gescannten Consumern. Basisklassen sind in diesen Zahlen nicht enthalten.
Kommentare koennen Suchtreffer erzeugen; keine automatische Loeschfreigabe.
Historische Hash-Dateien sind bewusst nicht als aktuelle Definition gezaehlt.

| Familie | Definiert | Verwendete Namen | Ergebnis des statischen Abgleichs |
|---|---:|---:|---|
| card | 21 | 12 | Alle gefundenen Consumer-Namen definiert; neun Definitionen ohne Consumer-Treffer. |
| card-section | 7 | 4 | Alle gefundenen Consumer-Namen definiert; accent/info/footer ohne Treffer. |
| form-field | 8 | 9 | checkbox/hint ohne Definition; no-margin ohne Consumer-Treffer. |
| form-actions | 1 | 1 | start definiert und verwendet. |
| data-table | 6 | 6 | Alle gefundenen Unterelemente/Modifier definiert und verwendet. |
| info-row | 4 | 4 | Alle gefundenen Unterelemente/Modifier definiert und verwendet. |

## Karten: sinnvolle Varianten und Altlastenkandidaten

- `card--collapsible` wird im aktuellen Merch-Shop und Admin-Sortiment verwendet.
  Diese Nutzung ist nicht durch die Entscheidung zum Entfall separater alter
  Bestellseiten erledigt. Controller `collapsible-card.js` bindet echte Buttons,
  setzt aria-expanded und toggelt is-collapsed. CSS verbirgt den Inhalt per
  display:none. Titelbereich hat cursor:pointer, aber keinen eigenen Handler.
  Empfehlung: klickbare Flaeche und sichtbaren Bedienhinweis angleichen;
  Toggle-Namen um den jeweiligen Artikelnamen ergaenzen. Aktuell heissen sie
  wiederholt nur „Abschnitt umschalten“ und haben kein aria-controls.
  Kein neuer nummerierter Fehler ohne zusaetzliche Verhaltensreproduktion;
  bestehende Disclosure-/Konsistenzbefunde A-005/A-019 werden praezisiert.
- `card__footer--wrap` hat eine konkrete Aufgabe: mobile Spalte, ab 640px
  flexible Reihe, umbrechende Aktionen. Das ist eine begruendete responsive
  Variante (components.css:750 ff.), kein Duplikat allein wegen aehnlicher Namen.
- `card__title-group`/`card__subtitle` sind reale Titelstrukturen. Eine
  Card-Unterzeile ist nicht mit dem untersagten Page-Header-Subtitle gleichzusetzen.
- Neun reine Definitionskandidaten: interactive, dash-tile mit vier
  Unterelementen, actions--split-toggle, actions-chips, body--stacked.
  Ergaenzende Suche in Backend/Templates/ungehashtem JS ohne Consumer-Treffer.
  Keine Entfernung im Audit; vor Bereinigung dynamische/externe Nutzung pruefen.
- card-section--subtle wird in der Sicherheitsuebersicht verwendet; accent/info
  und section-footer sind hier nur definierte Moeglichkeiten. Registry nennt
  accent, aber nicht subtle/info. Erweiterung von A-012, kein eigener Fehler.

## Formulare: zwei unterschiedliche Arten fehlender Definition

`form-field__hint` steht in Event-Erstellung/-Bearbeitung und Merch-Artikelform
(create_event.html:394, edit.html:397, admin/merch/article_form.html:60/73/195).
Keine Definition in den ungehashten CSS-Quellen gefunden. Vorhandenes
`form-field__help` liefert dagegen Blockdarstellung, Abstand, kleinere Schrift
und Hilfetextfarbe (components.css:2244 ff.). Empfehlung: einen gemeinsamen
Hilfetextnamen verwenden und den Text dem Feld explizit zuordnen. A-007/A-018.

`form-field__checkbox` wird bei Login „Angemeldet bleiben“ verwendet
(auth/login.html:52). Fehlende eigene Regel bedeutet nicht fehlende Funktion:
WTForms rendert den nativen Checkbox-Typ samt zugehoerigem Label; der Wrapper
ordnet beide per inline flex/gap an. Empfehlung: native Checkbox bewusst
beibehalten und den Stilnamen entfernen oder ein gemeinsames Checkbox-Muster
mit Focus-/Touch-Zustaenden definieren. Keine nachgewiesene Bedienblockade.

Der Fehler-Makrovertrag bleibt uneinheitlich: _form_macros.html zeigt den
ersten Fehler ohne id; Login zeigt alle Fehler. Das ist eine bewusste
Produktentscheidung fuer die Vereinheitlichung, kein Anlass, Meldungen blind
abzuschneiden. Feldzuordnung/aria-describedby bleiben Teil von A-018.

## Tabellen: Darstellung und Scroll-Verhalten getrennt dokumentieren

`data-table-wrap` allein ist kein horizontaler Scroll-Container:
components.css:1106 setzt overflow:hidden. Die spaetere Klasse
`table-responsive` setzt overflow-x:auto (components.css:2395).
Events, Mitglieder und Buchhaltung kombinieren beide mit
data-table-scroll-inner. Die Registry-Kurzbeschreibung „Scroll-Container“
verschweigt diese notwendige Kombination. Erweiterung A-012.

`data-table-scroll-outer` liefert den Randverlauf. Der Controller
restaurants-table-scroll.js verwaltet Overflow, ResizeObserver und Cleanup;
sein alter Name bedeutet nicht, dass er nur Restauranttabellen bedient.
Er misst ausserdem fuer GGL die Breite der Rangspalte. Zwei sticky Spalten
bei GGL und eine in der Buchhaltung sind fachlich begruendete Varianten.
Die gesichteten Accounting-/Event-/Mitglieder-Wrapper besitzen Regionsnamen,
der GGL-Wrapper an index.html:121 nicht. Tastaturzugang zum horizontalen Scrollen
ist hier nicht im Browser getestet; aus fehlendem tabindex allein folgt kein
browseruebergreifend nachgewiesener Fehler.

## Folgeschritte und Abnahme

- Statischer Namens-/Definitionsabgleich dieser sechs Familien abgeschlossen.
  Quellenabgleich ist keine allgemeine Freigabe aller Interaktionen.
- Spaetere Bereinigung: hint/help vereinheitlichen; native Checkbox bewusst
  gestalten; Kartenvarianten dokumentieren oder begruendet entfernen.
- Tabellenvertrag als vollstaendiges Markup-Muster dokumentieren und mit
  langen Daten, Tastatur, Touch, Hell/Dunkel und schmaler Breite pruefen.
- Wiederholte Merch-Toggles mit mehreren Artikeln per Tastatur pruefen,
  einschliesslich eindeutiger Namen und erhaltenem Formularzustand.
- Weitere Registry-Familien bleiben separat offen; dieser Durchlauf erzeugt
  keine neue Befundnummer. Insgesamt weiterhin 122.

## Browser-Nachtrag

B-31 bis B-33 schliessen die konkrete lokale Gegenpruefung fuer zwei
Merch-Karten und Archiv-/Mitglieder-Scroll ab: Tastatursteuerung funktioniert,
Werte bleiben erhalten. Generische Namen bzw. Fokussprung bleiben
Orientierungsempfehlungen. Kein Screenreader-/Mehrbrowsernachweis;
GGL-/Buchhaltungstabellen weiterhin offen. Siehe BROWSER_REVIEW.md.

### Praezisierung nach B-34 bis B-36

GGL haelt Rang und Name im Browser korrekt fixiert. Die generische sticky-
Variante ist vorhanden, wird aber von der Budgettabelle nicht genutzt:
dort position:static und horizontal mitwandernde Kontozelle. Die obige
Aussage ueber eine sticky Buchhaltungsspalte ist daher kein Nachweis fuer
Budget oder jede Buchhaltungstabelle. Registry-Beispiel Budget korrigieren
(A-012); fachliche Entscheidung zur Orientierung separat festhalten.
Tastatur-Scroll fuer GGL sowie Admin-/Revisor-Budget positiv, andere
Buchhaltungstabellen und Browser bleiben offen.

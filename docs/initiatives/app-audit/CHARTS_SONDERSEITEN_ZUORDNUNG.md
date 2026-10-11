# Charts und Sonderseiten – gezielte Zuordnung

Stand: 11. Oktober 2026. Ergänzung R06/R12, keine neue Befundsuche.
Bestand im Branch `codex/app-audit-handoff-2026-10-10` gezielt gelesen.
Die Darstellungsregeln sind mit «ok» am 11. Oktober 2026 bestätigt.
Keine Änderung der App oder Fachberechnung; Geräteabnahme bleibt offen.

## Bestehende Diagramme

Zehn aktive Diagrammpositionen in den drei Bereichen: zwei GGL, fünf Monatsessen,
drei Buchhaltung. Das alte Statistik-Volltemplate zählt nicht zusätzlich.
Die Restaurantbewertungstabelle ist eine Tabelle, kein elfter Chart. Die Funktion
`pieChart` im Event-Script wird dort nicht aufgerufen; daraus entsteht kein
zusätzlicher aktiver Kuchendiagramm-Entwurf.

| Bestand / Quelle | Mobile-Ziel | Tablet / Desktop |
|---|---|---|
| GGL: kumulative Punkte, `ggl-progression-chart` | Verlauf ausgewählter Personen; darunter alle elf mit exaktem Punktestand zum gewählten Event. Vergleichsauswahl siehe unten. Punkte bleiben Punkte, kein Rangverlauf. | Grössere Zeichenfläche, gleiche Auswahl und vollständige Wertetabelle. |
| GGL: durchschnittliche absolute Schätzabweichung, `ggl-diff-chart` | Dasselbe Vergleichsmuster, Einheit CHF, Erklärung «kleiner ist besser». Anzahl gültiger Tipps im Wertekontext ergänzen. | Gleiches Muster. Nicht als Punktestand oder Rang beschriften. |
| Monatsessen: Teilnahmequote je Mitglied, `events-stats-chart-members` | Elf horizontale Balkenzeilen, Namen und Prozentwerte ausgeschrieben; Skala 0–100 %. Höhe wächst mit den Zeilen, normale vertikale Seitennavigation. | Gleiche vollständige Liste, keine elf schmalen Säulen. |
| Monatsessen: durchschnittlicher Anteil je Organisator, `events-stats-chart-organizers` | Horizontale Balken, Name und CHF; alle vorhandenen Organisatoren. Bezugszeitraum sichtbar. | Dasselbe Muster, mehr Platz für Namen. |
| Monatsessen: Gesamtbewertung je Organisator, `events-stats-chart-organizer-ratings` | Horizontale Balken mit fester Skala 0–5 und exaktem Wert «… / 5». Keine Bewertung nicht als null behandeln. | Dasselbe Muster. Bewertungsgrundlage bleibt F8. |
| Monatsessen: Küchen, `events-stats-chart-kitchens` | Horizontale Balken mit absoluter Anzahl; keine Umdeutung in Prozent. Lange Küchennamen umbrechen. | Dasselbe Muster. |
| Monatsessen: durchschnittliche Kosten im Verlauf, `events-stats-chart-avg-share-trend` | Einzelverlauf plus deutlich beschriftete gestrichelte Gesamtdurchschnittslinie; Eventauswahl mit Datum, Restaurant und CHF. | Gleicher Verlauf, mehr Achsenbeschriftungen bei mehr Platz. |
| Buchhaltung: kumulierter Saldo, `chart-saldo` | Ein Linienverlauf, Monat und CHF, Nullpunkt/Vorzeichen sichtbar; negative Salden nicht abschneiden. | Gleiches Muster. Bedeutung des Saldos im Praxisabgleich B01 bestätigen. |
| Buchhaltung: Jahresvergleich, `chart-years` | Gruppierte Balken für Einnahmen, Ausgaben, Ergebnis; bei vielen Jahren nur Diagrammbereich horizontal verschieben, vollständige Wertetabelle bleibt erreichbar. Keine automatische Addition der drei Reihen. | Gruppierte Balken über mehrere Jahre, Ergebnis mit eigenem Muster/Label und sichtbaren negativen Werten. |
| Buchhaltung: Ausgaben nach Kontengruppe, `chart-donut` | Beschriftete horizontale Betragsbalken mit CHF und Anteil; alle Gruppen. Damit entfällt die kleine Ringlegende auf dem Telefon. | Dasselbe Balkenmuster als Empfehlung statt geräteabhängigem Wechsel der Aussage. Berechnungsbasis und Umgang mit Korrektur-/Negativbeträgen unter B01 klären; keine ungeprüften Prozentanteile. |

Quellen: `templates/ggl/index.html`, `static/js/v2/ggl-season.js`,
`templates/events/index.html`, `static/js/v2/events-monatsessen-stats.js`,
`templates/accounting/_tab_statistik.html`, Chartinitialisierung in
`templates/accounting/index.html`.

## GGL mit elf Personen: konkrete Ergänzung

Empfehlung: zunächst den eigenen Verlauf zeigen, mit «Personen vergleichen»
weitere hinzufügen. Ohne eigene auswertbare Reihe zunächst Auswahl anbieten,
keine willkürlich ausgezeichnete andere Person. Zwei bis drei Reihen sind der
bevorzugte Detailvergleich, **keine harte Auswahlgrenze**. «Alle 11» bleibt
explizit erreichbar; die Oberfläche nennt die aktuell sichtbare Anzahl.

Die Liste aller Personen bleibt unabhängig davon vollständig. Eine gemeinsame
Eventauswahl liefert für alle elf den Wert zu genau diesem Event. So muss man
auf Mobile keine elf überlappenden Linien antippen, um Ergebnisse zu vergleichen.
Auswahl ist eine reine Anzeigeoption und verändert weder Rang noch Berechnung.

Jede Vergleichsreihe erhält neben Farbe einen Namen und ein unterscheidbares
Linien-/Punktmuster. Bei «Alle» hebt die Auswahl einer Person deren Linie hervor;
alle Werte bleiben in der Tabelle erreichbar. Touch öffnet eine stabile
Werteansicht zum Event, Tastatur und beschriftete Auswahl bieten denselben Weg.
Kein Hover als einziger Zugriff. Vergrössern erhält Personen- und Eventauswahl,
Schliessen kehrt mit Fokus und Scrollposition zum Auslöser zurück.

Der Bestand zeigt kumulative Punkte und laufende durchschnittliche Abweichung,
keinen eigenständigen Rangverlauf. Vor dem ersten gültigen Tipp kann die
Abweichung fehlen; fehlend ist nicht null. Ein fortgeführter kumulativer Stand
ist wiederum nicht automatisch eine Datenlücke. Teilnahme, fehlender Tipp und
echte Nullabweichung müssen im Kontext unterscheidbar bleiben; Fachdetails F8.
Ranggleichheit nicht aus der blossen Sortierposition einer Legende ableiten.

Tablet verwendet dieselben bedienbaren Auswahlen. Zwei Diagrammkarten erst
nebeneinander, wenn beide inklusive Namen, Achsen und Bedienelementen lesbar
bleiben; Breite des Inhalts entscheidet, nicht allein der Gerätetyp.

## Sonder- und Altseiten

| Seite | Gezielter Befund | Einordnung in die Gesamtvorlage |
|---|---|---|
| `accounting/accounts.html` | `/accounts` GET leitet zum Tab `kontenplan`; POST verarbeitet weiterhin Kontoanlage. Keine Referenz auf das Volltemplate in den gezielt durchsuchten Backend-/Template-/Testdateien gefunden. | Kein eigener neuer Seitenentwurf. Tab + Formular-/Inline-Muster; Verarbeitung beim späteren Aufräumen erhalten. `account_edit.html` ist weiterhin eine echte Bearbeitungsseite. |
| `accounting/stats.html` | `/stats` leitet mit Geschäftsjahr zum Tab `statistik`; ohne Jahr zur Übersicht. Keine Referenz auf das Volltemplate im gleichen Suchumfang gefunden. | Drei Charts im aktuellen Tab zählen; historische Doppelvorlage ist späterer Bereinigungskandidat, keine jetzige Löschung. |
| `events/hamburg2026.html` | Eigene Reiseoberfläche; Guard endet am 1. Juni 2026, 06:00. Nach dieser Grenze liefert die Route laut gelesenem Code 404. Keine Live-/Produktionsprüfung. | Historische Sonderseite ausserhalb des aktuellen Navigationsentwurfs. Inhalt erhalten. Wiederveröffentlichung als Reise-Archiv oder übertragbares Reisetool wäre ein eigener Auftrag, nicht stillschweigend Teil des Redesigns. |
| Alte Merch-Seiten | Gewähltes Ziel ist v2 auf `phase/10-merch-wip`; siehe `MERCH_ZIELVERSION.md`. | Kein zusätzlicher Entwurf für alten Shop. Spätere operative Stilllegung samt Links/Verarbeitung planen; Daten und mögliche Migrationsquelle bewahren. |
| Game | Ausdrücklich ausgeschlossen. | Keine Prüfung oder Änderung. |

Route-Belege: `backend/routes/accounting.py`, Funktionen `accounts`,
`account_edit`, `stats`; `backend/routes/events.py`, `hamburg2026_is_visible`
und `hamburg2026`.

## Abnahmegrenze und nächster Schritt

R06: Bestandszuordnung abgeschlossen; Mehrpersonenvergleich und Ersatz des
Ausgabenrings als konkrete Darstellungsempfehlungen vorgelegt. Kein neues Mockup
erzwungen; die bisherige Einzelkurve beweist diese Varianten nicht. Bei Umsetzung
mit elf Namen, identischen Werten, fehlenden Tipps, negativen Salden, langen
Zeiträumen und Hell/Dunkel testen: schmale 320/390 px, Tablet, Desktop sowie echte
Touch-/Tastaturbedienung. Jetzt wurde nur der begrenzte Bestand gelesen.

R12: Einordnung abgeschlossen, keine operative Stilllegung oder Datenmigration.
Als Nächstes R07/R08 gemeinsam: Importvorstufe, private Auslagen und Zahlwegwechsel
im bereits bestätigten Finanzrahmen. F1/F2/F7/F8 und B01 bleiben separat offen.

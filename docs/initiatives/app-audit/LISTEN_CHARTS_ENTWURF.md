# Listen, Tabellen, Filter und Charts – Gestaltungsvorschlag

Stand: 10. Oktober 2026. Block 2 der [Gestaltungsabdeckung](ABDECKUNG_GESTALTUNG.md).
**Grundmuster vom Nutzer bestätigt. Keine Umsetzungsfreigabe.**

Zusätzlicher Nutzerhinweis: Der Verein hat elf Mitglieder. Vor Abschluss der
Gesamtvorlage jeden vorhandenen Charttyp den Regeln zuordnen und notwendige
Ausnahmen benennen. Insbesondere elf gleichzeitige Linien sind nicht mit dem
Einzelverlauf abgenommen. Datenreihenauswahl, Unterscheidbarkeit und reale
Touch-Lesbarkeit mit elf Mitgliedern bei der Umsetzung prüfen. Dieser Punkt
bleibt ausdrücklich offen; ein weiteres Mockup wurde dafür nicht verlangt.

Die Vorschau zeigt Mitgliederliste, Buchungsjournal, Budgetvergleich und GGL mit
Verlauf. Sämtliche Namen und Zahlen sind Beispieldaten. Sie illustrieren die
Darstellung; insbesondere werden keine GGL-Berechnung oder Buchungsregeln geändert.
F8 bleibt offen. Die Vorschau ist keine vollständige Feld-/Rollenabnahme der Seiten.

## Drei unterschiedliche Tabellenmuster

| Zweck | Mobile | Tablet/Desktop |
|---|---|---|
| Einzelne Datensätze finden und öffnen: Mitglieder, Buchungen | Ruhige Liste mit Titel, wesentlichem Status/Betrag und zweiter Informationszeile. Antippen öffnet Details. | Tabelle mit gemeinsam ausgerichteten Spalten; Name/Buchung als beschrifteter Einstieg. |
| Werte nebeneinander vergleichen: Budget/Ist | Tabelle bleibt erhalten; nur ihr Bereich scrollt horizontal. Erste Spalte bleibt sichtbar, Hinweis erklärt die weiteren Spalten. | Vollständige Vergleichstabelle mit rechtsbündigen Beträgen, Währung im Kontext und Totalzeile. |
| Wenige zentrale Spalten: GGL-Rangliste | Rang, Name und Punkte bleiben als schmale Tabelle erhalten. Eigene Zeile durch «Du» und dezente Fläche erkennbar. | Dieselbe Struktur mit mehr Platz. |

Keine pauschale Umwandlung jeder Tabelle in Cards. Zusatzspalten werden nicht
stillschweigend entfernt: Bei der späteren Seitenübertragung muss jedes Feld
einer sichtbaren Spalte, Detailansicht oder bewusst gekürzten Zusammenfassung
zugeordnet werden. Lange Namen umbrechen, Zahlen und Vorzeichen bleiben lesbar.
Die Journalvorzeichen sind eine Darstellung von Zu-/Abflüssen in diesem Beispiel,
keine neue Definition von Soll/Haben.

## Suche, Filter, Sortierung und Navigation

- Häufige Filter stehen direkt über der Liste: Suche, Status und Sortierung.
  Mobile steht die Suche zuerst über die ganze Breite. Weniger häufige Filter
  können später in «Weitere Filter» liegen; aktive Werte müssen sichtbar bleiben.
- Suche und Filter wirken gemeinsam. Trefferzahl aktualisieren, Fokus im bedienten
  Feld behalten, kein Sprung nach oben. Filterwechsel setzt die Ergebnisseite auf 1.
- Sortierung ist auch auf Mobile explizit erreichbar. Im Beispiel Name A–Z/Z–A
  bzw. neueste/älteste Buchung. Gleichartige Werte brauchen später einen stabilen
  zweiten Sortierschlüssel, damit Einträge beim Blättern nicht springen.
- Pagination mit Zurück/Weiter und Seitenstand; hier fünf Einträge pro Seite nur
  zur Demonstration. Die spätere Seitengrösse ist kein Gestaltungsentscheid.
  Bei Seitenwechsel in der App soll der Beginn der Ergebnisliste sichtbar sein;
  weder Suchfelder noch Navigation sollen unerwartet den Fokus übernehmen.
- Beim Öffnen und Zurückkehren bleiben Suche, Filter, Sortierung, Seite und
  Scrollposition erhalten. Die Vorschau demonstriert dies mit einem Lesedialog;
  damit ist kein allgemeiner Dialogzwang für echte Detailseiten beschlossen.
- Kein Löschen neben jeder Zeile. Objektaktionen folgen auf der Detailseite dem
  bestätigten Formular-/Aktionsmuster und den jeweiligen Berechtigungen.

In der Vorschau reagieren Suche und Filter lokal. URL-/Browser-Zurück-Verhalten,
Serverpagination und asynchrone Suchantworten bleiben Umsetzung und Abnahme.

## Diagrammregeln

**Budgetvergleich:** horizontale Balken mit gemeinsamem Nullpunkt und gleicher
Skala. Jahresbudget als beschriftete 100-%-Markierung; Überschreitung ausdrücklich
benennen und nicht bei 100 % abschneiden. Zahlen sind auch in der Tabelle
verfügbar. Positive/negative Abweichungen nicht ausschliesslich durch Farbe zeigen.

**GGL-Verlauf:** Liniendiagramm mit beschrifteten Einheiten, Zeitraum und Auswahl
des Mitglieds. Die Monatsauswahl liefert einen exakten Wert; Tippen/Klicken auf
das Diagramm wählt den nächstgelegenen Beispielmonat. Tastaturbedienung ist über
die Auswahl möglich. Eine aufklappbare Datentabelle gibt alle Werte wieder.

Vergrössern öffnet einen Dialog, der den Fokus hält; Schliessen/Escape kehrt zum
Auslöser zurück. Das Diagramm passt sich seiner tatsächlichen Breite an. Keine
kleiner skalierte Desktopgrafik mit unleserlicher Schrift auf Mobile.

Für spätere Mehrfachreihen gelten eindeutige Namen und zusätzlich unterschiedliche
Linien/Markierungen; Legenden müssen auch per Touch bedienbar sein. Keine erfundenen
Nullwerte für Datenlücken. Rangverläufe und Punktverläufe brauchen unterschiedliche
Achsen: Ein Rangdiagramm zeigt Rang 1 oben. Diese Varianten sind mit dem einfachen
Punktverlauf noch nicht vollständig abgedeckt.

## Zustände und offene Varianten

| Zustand / Variante | Behandlung |
|---|---|
| Noch keine Einträge | Ruhiger Leerzustand; kein technischer Fehler und keine Nullstatistik. In den Listen per Entwurfsoption demonstriert. |
| Keine Filtertreffer | Filter erhalten und Zurücksetzen anbieten; in der Vorschau durch Suche prüfbar. |
| Laden / Ladefehler | Ladehinweis bzw. Meldung mit «Erneut versuchen»; Filter erhalten. Für Listen per Entwurfsoption demonstriert. |
| Diagramm ohne Daten / Fehler | Diagramm durch klare Meldung ersetzen, keine erfundene Kurve. Regel vorgeschlagen, noch kein separater visueller Zustand in dieser Vorschau. |
| Lange Listen / umfangreiche Tabellen | Pagination bzw. begrenztes horizontales Scrollen; reale Datenmengen und zusätzliche Spalten später gezielt prüfen. |
| Inline-Bearbeitung im Kontenplan | Lokales Speichern/Abbrechen direkt am Eintrag; konkreter Entwurf beim Buchhaltungsprozess in Block 3 noch erforderlich. |
| Mehrfachauswahl / Sammelaktionen | Nur für einen fachlich nötigen Ablauf, z.B. Importzuordnung; gehört in dessen Prozessentwurf. |
| Weitere Statistiktypen / Mehrfachreihen | Nach Datenaufgabe passenden Diagrammtyp zuordnen; keine pauschale Freigabe aller vorhandenen Charts durch diese zwei Beispiele. |

## Responsive Regeln und Prüfung

Listen wechseln bei schmalem verfügbaren Platz zur mobilen Darstellung. Die
Vorschau verwendet circa 650 px App-Breite; die endgültige Schwelle muss sich bei
der Umsetzung nach der tatsächlichen Inhaltsbreite richten. Vergleichstabellen
scrollen nur innerhalb ihres eigenen Bereichs, Ranglisten bleiben schmal.
Tablet übernimmt je nach Platz die geeignete Variante, nicht eine verkleinerte
Desktopansicht. Der bestätigte App-Rahmen einschliesslich Theme-Schalter bleibt.

Vier Beispiele bei 320, 390, 768, 820, 1024 und 1440 px in lokalem Chrome geprüft:
kein horizontaler Seitenüberlauf. Suche, Filter, Pagination, Detailrückkehr,
Monats-/Mitgliedsauswahl, Vergrössern/Escape und Datentabelle geprüft. Mobile
Ansichten visuell geprüft; dies ist keine reale Touch-/Safari-/Screenreaderabnahme.

Nach Rückmeldung zu diesen Grundmustern folgt Block 3: Fachprozesse mit ihren
Detailseiten. Die offenen Varianten bleiben sichtbar in dieser Liste und werden
nicht durch Zustimmung zum Grundmuster automatisch abgeschlossen.

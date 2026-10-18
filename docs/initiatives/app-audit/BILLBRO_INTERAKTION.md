# BillBro Schritte und Bedienverhalten

Status: Ablauf grundsätzlich bestätigt mit den nachfolgenden Nutzerkorrekturen,
10. Oktober 2026. App-Rahmen und Grundlayouts von Dashboard, Eventdetail und
Buchhaltung sind bestätigt. Dies ist kein Auftrag zur Umsetzung; die laufende
App bleibt unverändert. Die Korrekturregel nach Finalisierung ist inzwischen
bestätigt; auch Zahlwegwechsel und der Umgang mit geschlossenen Geschäftsjahren
sind inzwischen separat bestätigt (F4/F6 in der Entscheidungsvorlage).

## Bestätigte Anwesenheitsregeln und Korrekturen

- Die Organisation kann zugesagte Mitglieder als abwesend markieren. Abwesende
  blockieren die Runde nicht durch fehlende Angaben und erhalten keinen Essensanteil.
- Mitglieder ohne Zu- oder Absage werden beim Schliessen der Runde als abwesend
  geführt, sofern sie nicht als anwesend erfasst wurden. Die Anzeige unterscheidet
  weiterhin eine ursprüngliche Zusage von tatsächlicher Anwesenheit; keine
  nachträglich erfundene Absage des Mitglieds.
- Von Rechnung führt «Zurück zu Angaben · Runde öffnen» zurück zur offenen Runde.
  Damit kann eine anwesende Person ihre vergessene Zusage und Angaben ergänzen.
  Im Vorschlag bleiben bisherige Angaben und ein Rechnungsentwurf erhalten.
- Unter Prüfen entfällt «Anteil pro Person». Trinkgeld wird als CHF-Betrag und
  als Prozent der Restaurantrechnung ohne Trinkgeld gezeigt. Bei CHF 960.00
  Rechnung und CHF 1’008.00 Gesamtbetrag sind das CHF 48.00 bzw. 5.00 Prozent.
- Der Nutzer hat den übrigen vorgestellten Ablauf grundsätzlich bestätigt.
  Die Wiederöffnung hier betrifft den Ablauf vor der Finalisierung. Die später
  separat bestätigte Korrekturregel steht im nächsten Abschnitt.

## Bestätigte Korrekturregel nach Abschluss

Der Nutzer hat folgende Regel ausdrücklich bestätigt:

- Solange niemand bezahlt hat, kann die Organisation «Korrektur vorbereiten»
  wählen und nach einem Vorher-/Nachher-Vergleich bestätigen.
- Bereits vorhandene Zahlungen bleiben erhalten. Aus geänderten Anteilen wird
  nur der zusätzliche offene Betrag oder Rückzahlungsbedarf abgeleitet.
- Sind Vereinszahlungen betroffen, bestätigt der Schatzmeister die finanzielle
  Korrektur. Die Organisation kann sie vorbereiten.
- Bei privater Auslage bestätigt das auslegende Mitglied die betroffenen
  Zahlungseingänge bzw. Rückzahlungen.
- Der Korrekturablauf verlangt einen Grund und zeigt alte/neue Beträge.
  Eine Rückzahlung wird nicht automatisch ausgeführt.

Beispiel: CHF 84.00 bezahlt, neuer Anteil CHF 90.00 ergibt CHF 6.00 offen.
Neuer Anteil CHF 78.00 ergibt CHF 6.00 zurückzuzahlen. Die ursprüngliche Zahlung
bleibt in beiden Fällen nachvollziehbar.

Damit ist F3 hinsichtlich Betragskorrektur und Bestätigung entschieden. Das
Das Benachrichtigungsverhalten bleibt offen. F6 erlaubt die Wiederöffnung eines
abgeschlossenen Jahres durch Systemadmin oder Schatzmeister jeweils allein,
ohne Zustimmung des Revisors, mit dokumentiertem Grund (Nutzeränderung vom
11. Oktober 2026); anschliessend erneute Revision und neue Berichtsversion.
F4 wurde separat im Abschnitt «Bestätigter Zahlwegwechsel» entschieden.
Die bisherigen grafischen
Entwürfe zeigen den Einstieg; der vollständige Korrekturdialog ist noch auszuarbeiten.

## Ein Event mit vier klaren Phasen

Die bestehenden BillBro-Phasen bleiben fachlich erkennbar: Angaben bzw. Schätzrunde,
Rechnung, Gesamtbetrag und Abschluss. Die sichtbaren Kurzlabels lauten **Angaben →
Rechnung → Prüfen → Abschluss**. Der aktuelle Schritt trägt zusätzlich zur Farbe
eine Beschriftung. Die Schrittanzeige ist keine frei anklickbare Navigation;
ein Rückschritt erfolgt über eine zulässige, benannte Aktion am betreffenden Inhalt.

Mitglieder bearbeiten ihre Angaben und sehen anschliessend den Stand der
Organisation. Sie müssen sich nicht durch deren Eingabeformulare klicken.
Die Organisation bearbeitet nacheinander Rechnung und Zahlweg, Gesamtbetrag und
finanzielle Folgen. Ohne GGL entfallen Schätzung und Schätzungsrangliste; Ess-Typ,
Rechnung und Verteilung bleiben bestehen.

## Mitglied

| Zustand | Inhalt und Aktionen | Nach der Aktion |
|---|---|---|
| Teilnahme noch offen | Teilnahme angeben; keine versteckte automatische Zusage durch BillBro. | Bestätigte Teilnahme anzeigen; BillBro als nächste Aktion anbieten. Kein automatischer Tabwechsel ohne bewusste Aktion. |
| Runde offen, Angaben fehlen | Ess-Typ und bei Monatsessen Schätzung ohne Trinkgeld. Hauptaktion unten: «Angaben speichern». | Formular wird durch eine Zusammenfassung mit den gespeicherten Werten ersetzt. Meldung «Deine Angaben sind gespeichert. Du bist fertig.» |
| Angaben gespeichert | Zusammenfassung zuerst. «Angaben bearbeiten» direkt darunter. | Bearbeiten öffnet dieselben Felder mit gespeicherten Werten. Speichern übernimmt, Abbrechen verwirft nur den Entwurf und zeigt den bisherigen Stand. |
| Schätzung löschen | Unter «Weitere Aktionen» am eigenen Angabenblock. Textbutton mit Gefahrfarbe, keine alleinstehende Papierkorb-Schaltfläche. | Bestätigungsdialog nennt Anlass und Folge. Teilnahme und Ess-Typ bleiben erhalten; Schätzung fehlt danach wieder. Nur solange die Runde offen ist. Dieser Löschumfang ist ein Vorschlag. |
| Runde geschlossen | Eigene Werte lesbar, eindeutiger Hinweis «Die Rechnung wird erfasst» bzw. «Die Abrechnung wird geprüft». | Keine Bearbeiten-/Löschen-Aktionen. Fehler mit Organisation klären. Bei neuer Phase nur Status aktualisieren, ohne Fokus oder Scrollposition zu entziehen. |
| Abgeschlossen | Eigener Anteil, Empfänger, bereits bezahlt und Restbetrag. Hauptaktion «Zahlungsdetails ansehen». | Keine pauschale Selbstbestätigung «bezahlt». Vereinszahlungen kommen aus dem Bankabgleich, private Eingänge bestätigt der Auslegende. |

## Organisation

| Phase | Inhalt und Aktionen | Grenze und Übergang |
|---|---|---|
| 1 Angaben | Anwesenheit, Ess-Typen und fehlende Schätzungen. Zugesagte als abwesend markieren; Personen ohne Antwort werden beim Schliessen als abwesend geführt. Hauptaktion «Runde schliessen und weiter». | Benötigte Angaben nur für tatsächlich Anwesende verlangen. Nach Erfolg sind Mitgliedereingaben gesperrt; Rechnungseingabe wird sichtbar. |
| 2 Rechnung | Rechnungsbetrag ohne Trinkgeld und Zahlweg; bei privater Auslage eine tatsächlich teilnehmende Person auswählen. «Rechnung speichern und weiter». Sekundär: «Zurück zu Angaben · Runde öffnen». | Rückkehr öffnet die Runde für vergessene Zusagen/Angaben. Bisherige Angaben und Rechnungsentwurf erhalten; nach erneuter Schliessung wieder prüfen. Noch keine endgültigen Vereinsforderungen. Ohne GGL keine Schätzrangliste. |
| 3 Prüfen | Rechnung, Gesamtbetrag inkl. Trinkgeld, Trinkgeld in CHF und Prozent sowie Empfänger. Kein Anteil pro Person. Gesamtbetrag bleibt bearbeitbar; Vorschlag folgt der Eventregel. «Rechnung bearbeiten» als sekundäre Rückkehr. | Sichtbarer Vorher/Nachher-Effekt: Vereinsforderungen oder private Zahlungen ausschliesslich für Anwesende. Hauptaktion «Verbindlich abschliessen» erst bei gültigem Gesamtbetrag und vollständigem Zahlweg. Kein zweiter inhaltsgleicher Bestätigungsdialog hinter dieser ausdrücklichen Prüfansicht. |
| 4 Abschluss | Zusammenfassung und erfolgreiche Wirkung. | Statt «Alles löschen» oder unbeschränktem Neustart: «Korrektur vorbereiten» unter Weitere Aktionen. Rollen und Umgang mit bezahlten Beträgen folgen den bestätigten F3-/F4-Regeln. |

Bearbeiten steht bei dem Gegenstand, den es verändert. Eine Eventbearbeitung gehört
in den Organisationsbereich des Events; sie ist keine BillBro-Schrittaktion.
Event löschen und BillBro korrigieren dürfen nicht dieselbe unklare Schaltfläche sein.
Ob und unter welchen Bedingungen ein Event mit Finanzbezug überhaupt gelöscht
werden darf, muss mit F3/F4 festgelegt werden. Der Entwurf behauptet keine Löschfreigabe.

## Scroll Fokus und Rückmeldungen

| Auslöser | Vorschlag für Scrollen | Vorschlag für Fokus und Meldung |
|---|---|---|
| Angaben erfolgreich gespeichert | Keine Rückkehr zum Seitenanfang. Zusammenfassung am bisherigen Formularort; nur scrollen, wenn ihr Anfang verdeckt oder ausserhalb des sichtbaren Bereichs liegt. | Kurze lokale Erfolgsmeldung. Fokus auf «Angaben bearbeiten»; die Zusammenfassung wird über Statusmeldung verständlich. |
| Nächster Organisationsschritt | Zum Beginn des neuen Schrittblocks, nur wenn dieser nicht sinnvoll sichtbar ist. Eventkopf und Hauptnavigation nicht erneut durchscrollen. | Fokus auf erstes Eingabefeld; beim Prüfschritt auf Gesamtbetrag, nach Abschluss auf nächste sinnvolle Aktion. |
| Feldfehler | Erstes ungültiges Feld in den sichtbaren Bereich bringen, einschliesslich Label und Fehlertext. | Fokus auf dieses Feld; Feldfehler mit dem Feld verknüpfen, Eingaben erhalten. Kein Fortschritt der Phase. |
| Speicherfehler | Position und Formular erhalten. Fehlerhinweis beim Formular statt ausschliesslich am Seitenende. | Keine Löschung der Eingaben und kein automatisch ausgelöster neuer POST. Fehler ankündigen. |
| Unklares Speicherergebnis nach Netzunterbruch | Formular und Kontext erhalten; keine optimistische Erfolgsmeldung. | «Speicherstand prüfen» statt blindem Wiederholen einer Finalisierung. Serverzustand abgleichen; keine Doppelbuchung. |
| Bearbeiten / Abbrechen | Am betroffenen Block bleiben. | Bearbeiten: erstes Eingabefeld. Abbrechen: ursprüngliche Bearbeiten-Schaltfläche. |
| Dialog öffnen / schliessen | Hintergrundposition erhalten. | Fokus im Dialog, zunächst auf Abbrechen. Escape verwirft; Rückgabe an Auslöser. Nach bestätigter Löschung an das nun fehlende Schätzfeld. |
| Hintergrundaktualisierung | Nie ungefragt scrollen oder einen Tab wechseln. | Keine Fokusübernahme. Geänderte Phase ankündigen; offene Eingaben bei zwischenzeitlicher Sperre erhalten und verständlich erklären. |
| Eventliste / Browser-Zurück | Filter und Listenposition wiederherstellen. | Zum zuvor geöffneten Eventeintrag zurückkehren, soweit noch vorhanden. |

Die reale Umsetzung berücksichtigt Höhe der Kopfzeile, Bottom-Navigation,
Safe Area und Bildschirmtastatur. Scrollen erfolgt ohne Animation bei reduzierter
Bewegung. Beim ersten Seitenaufruf wird nicht vorsorglich gescrollt oder fokussiert.
Ein Direktlink auf eine konkrete offene Aufgabe darf gezielt deren Block öffnen.

## Mobile Klickzustände und gemeinsame Formregeln

Interaktive Elemente erhalten mindestens 44 px grosse Ziele. Ein gedrückter
Zustand verwendet die vorhandene Gourmen-Farbe bzw. eine leichte Flächenänderung.
Die unerwünschte blaue Browser-Tap-Markierung wird für eigene Buttons und Links
ersetzt. Tastaturfokus bleibt über `:focus-visible` deutlich sichtbar; kein globales
Entfernen von Outlines und keine Unterdrückung normaler Textauswahl.

Während einer laufenden Speicherung ist dieselbe Aktion gesperrt und verständlich
als «Wird gespeichert …» beschriftet. Mehrfachklicks erzeugen keine zweite Operation;
die Oberfläche ersetzt dabei nicht die notwendige serverseitige Absicherung.

Beim Verlassen eines geänderten Formulars über App-Navigation folgt «Änderungen
verwerfen?» mit Bleiben/Verwerfen. Reines Lesen oder ein unverändertes Formular
erzeugt keine Warnung. Externes Schliessen/Neuladen nutzt die verfügbaren
Browsermechanismen; deren mobile Grenzen müssen auf echten Geräten geprüft werden.

## Durchspielbarer Entwurf und offene Entscheidungen

Die Work-Vorschau führt mit gemeinsamen Beispieldaten durch Mitgliedereingabe,
Speichern/Bearbeiten/Abbrechen/Löschen und anschliessend die Organisationsschritte.
Die Rollenwahl und «Neu durchspielen» stehen ausserhalb der App. Theme- und
Grössenwechsel erhalten das gerade offene Formular. Über Entwurfsoptionen lassen
sich fehlende Angaben und Speicherfehler simulieren.

Die Rechnungssimulation verwendet normale Ess-Typen der als anwesend geführten
Beispielpersonen und einen ausdrücklich
als Beispiel gekennzeichneten Gesamtbetrag; sie ist kein Ersatz für den fachlichen
BillBro-Rechner. In der echten App gelten die Eventgewichte und Rundungsregel.
Rollenvergleich ist eine Vorschaufunktion, kein Rollenwechsel im Konto.
Die Vorschau bildet weder reales Netz noch Hintergrundaktualisierung, Browser-History
oder alle Wege beim Verlassen ungespeicherter Eingaben vollständig nach. Diese
Verhaltensregeln sind oben festgelegt und später separat abzunehmen.

Die Anwesenheitskorrektur löst die bisher offene Frage nach fehlenden Angaben:
Abwesende blockieren die Runde nicht; für Anwesende bleiben die benötigten Angaben
erforderlich. Die Vorschau zeigt Luca mit Zusage und fehlender Schätzung sowie Alex
ohne Antwort. Die Organisation kann Anwesenheit korrigieren. Nach Rundenschluss
erscheint Alex ohne Antwort als abwesend. Die Rückkehr von Rechnung öffnet die
Angaben wieder; ein später hinzukommendes Mitglied muss seine Angaben ergänzen.

## Bestätigter Zahlwegwechsel

F4 wurde vom Nutzer ausdrücklich bestätigt:

- Vor Abschluss kann die Organisation den Zahlweg ändern.
- Nach Abschluss ohne vorhandene Zahlungen erfolgt die Änderung mit Vorschau;
  bisherige Forderungen werden nachvollziehbar ersetzt.
- Bei vorhandenen Zahlungen gibt es keinen einfachen Wechsel im Auswahlfeld.
  Organisation und Schatzmeister klären im Korrekturablauf, wer wem noch Geld
  schuldet. Private Zahlungseingänge bestätigt die auslegende Person.
- Bereits erfasste Zahlungen bleiben erhalten. Die bestätigte Korrekturregel
  gilt auch bei diesem Wechsel; Rückzahlungen werden nicht automatisch ausgeführt.

F5 Teil- und Überzahlungen beim Bankimport ist inzwischen bestätigt; siehe
[Entscheidungsstand](OBERFLAECHENENTWUERFE.md). F6 zu geschlossenen Geschäftsjahren
ist ebenfalls bestätigt. Benachrichtigungen und die vollständige Korrekturoberfläche bleiben
gesondert zu behandeln. Die laufende App bleibt unverändert.

## Bestaetigte Rundungsregel vom 18.10.2026

Der Auftraggeber hat ausdruecklich rappengenaue, summengleiche Verteilung
bestaetigt. Gewichtete exakte Anteile zuerst auf ganze Rappen abrunden; die
verbleibenden Rappen nach groesstem Rechenrest zuweisen, bei Gleichstand
stabil nach Mitglied-ID. Beispiel CHF 100 auf drei gleiche Anteile:
CHF 33.34 + CHF 33.33 + CHF 33.33. Kein zusaetzlicher Rundungsueberschuss
und keine Aufrundung auf 5 oder 10 Rappen. Bestehende abgeschlossene
Abrechnungen werden nicht automatisch neu berechnet.

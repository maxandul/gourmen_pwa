# Oberflächenentwürfe und Fachentscheidungen

Stand: 10. Oktober 2026. **Vorschlag zur Rückmeldung; keine Umsetzungsfreigabe.**
Grundlage: [Gesamtbeurteilung](GESAMTBEURTEILUNG.md), [UI](../../UI.md) und
[Vereinsbegriffe](../../DOMAIN.md). Die Auditbaseline bleibt `bf4d84a`.

Dashboard, Eventdetail und Buchhaltung erhalten einen gemeinsamen Aufbau mit
klarer Hauptaktion. Navy, Orange, Hell-/Dunkelmodus, vier Hauptbereiche und
persönliches Menü bleiben erkennbar. Die interaktive Darstellung in der zugehörigen
Work-Unterhaltung enthält die drei Seiten jeweils in Mobile, Tablet und Desktop.
Alle Namen, Termine, Beträge und Zähler darin sind Beispieldaten.

Die nachfolgenden Regeln beschreiben den Entwurf unabhängig von der Vorschau.
Neue Layoutvarianten werden damit noch nicht Teil des verbindlichen Designsystems.
App-Templates, Styles, Geschäftslogik und PWA-Version bleiben unverändert.

## Aktuelle Abstimmung des App-Rahmens

**Geltungsbereich:** Die drei Beispielansichten sind keine vollständige
Gestaltungsvorlage. Die [Gestaltungsabdeckung](ABDECKUNG_GESTALTUNG.md) ordnet alle
weiteren Muster und ihre Bearbeitungsreihenfolge. Formulare, Tabellen, Charts und
weitere Prozesse erhalten vor der abschliessenden Gesamtvorlage eigene
Grundsatzentscheide. Die folgende Beschreibung bewahrt den bisherigen Verlauf.

Die Reihenfolge auf dem Dashboard ist vom Nutzer bestätigt: nächster Anlass und
Teilnahme, danach offene Zahlungen und Aufgaben, danach GGL. Der Nutzer hat auch
Kopfzeile, Navigation und Abstände des überarbeiteten Dashboard-Entwurfs bestätigt,
einschliesslich Logo, Icons, Theme-Schalter und Kontomenü. Diese Gestaltungsabstimmung
ist keine Umsetzungsfreigabe. Darauf folgen Eventdetail und Buchhaltung und
anschliessend die offenen Fachregeln.

Der überarbeitete Dashboard-Entwurf in der Work-Unterhaltung ersetzt für diese
Abstimmung die vereinfachte Rahmenzeichnung der ersten Vorschau. Er zeigt das
bestehende runde Gourmen-Logo, die Lucide-Icons `layout-dashboard`, `calendar`,
`trophy` und `landmark` sowie einen bedienbaren Sonne/Mond-Schalter neben dem
Kontomenü. Das Menü enthält wie bisher Profil, Sicherheit, Einstellungen und
Abmelden; Kalender, Benachrichtigungen und Installation bleiben unter Einstellungen.
Escape schliesst das Menü und gibt den Fokus an den Auslöser zurück.

Mobile verwendet 16 px Seitenabstand, 40 px Logo, 44 px grosse Kopfzeilenaktionen,
22 px Navigationsicons mit 12 px Textlabels sowie eine farbig hinterlegte aktive
Navigation. Unter sehr schmalen Breiten entfällt die zusätzliche Wortmarke neben
dem Logo. Desktop verwendet 184 px Sidebar und 32 px Inhaltsabstand. Tablet behält
die Bottom-Navigation; Inhaltsspalten entstehen nur bei genügend Platz. Der
Navigationsfuss steht in der Vorschau weiterhin im Dokumentfluss; das Verhalten
beim Scrollen und die Safe Area sind erst in der Umsetzung auf Geräten abzunehmen.

Zwölf lokale Breiten-/Theme-Kombinationen (320 bis 1440 px, Hell/Dunkel) wurden
ohne gemessenen Überlauf oder JavaScriptfehler geprüft. Vier gerenderte
Navigationsicons, Theme-Wechsel, Menüaktionen und Escape wurden geprüft;
Mobile Hell/Dunkel und Desktop wurden visuell kontrolliert. Dies betrifft allein
die Vorschau. Der gemeinsame Rahmen und anschliessend das Layout des Eventdetails
sind vom Nutzer bestätigt. Auch die Buchhaltungsgliederung und ihr Grundlayout
sind bestätigt. Aktuell wird die [BillBro-Interaktion](BILLBRO_INTERAKTION.md)
mit Schritten, Aktionen, Scroll-/Fokusregeln und Fehlerfällen abgestimmt.

Die Bestätigungen betreffen Aufbau und Gestaltung. Nach den drei Seitenentwürfen
werden die Interaktionsregeln vor der Umsetzung konkretisiert: Führung durch die
BillBro-Schritte, Rückmeldung und Scroll-/Fokusziel nach Eingaben, Position und
Zulässigkeit von Bearbeiten/Löschen, Bestätigung und Rücknahme sowie Fehler,
Abbruch und Wiederaufnahme. Mobile Klickzustände sollen zur Gestaltung passen
und keine unerwünschte blaue Browser-Markierung zeigen; sichtbarer Tastaturfokus
bleibt erhalten. Diese Details sind durch die Layoutzustimmung noch nicht freigegeben.

## Dashboard

**Ziel:** Ein Mitglied erkennt den nächsten Anlass und seinen nächsten nötigen Schritt.

| Reihenfolge | Inhalt und Verhalten |
|---|---|
| 1 | Nächster sichtbarer Anlass mit Titel, Datum, Uhrzeit, Ort, Organisation und eigener Teilnahme. Hauptaktion «Teilnahme angeben», nach Zusage «Zum Event». |
| 2 | Persönliche offene Aufgaben mit direktem Ziel und verständlichem Grund. Vereinsforderung und private Auslage stehen separat mit Empfänger, Betrag und Anlass. Keine gemeinsame Geldsumme, die beide Zahlwege verschleiert. |
| 3 | Beleg einreichen und Dokumente als sekundäre Vereinseinstiege. |
| 4 | GGL-Saison und persönliche Kennzahlen, ohne mit dringenden Aufgaben zu konkurrieren. |

Mobile zeigt diese Reihenfolge in einer Spalte. Desktop stellt Anlass links und
Aufgaben rechts; Vereinszugänge und Saison folgen darunter. Vorschlag für die
Aufgabenpriorität: konkrete zeitliche Dringlichkeit, danach fällige Zahlungen,
danach ergänzende Aufgaben wie Bewertungen. Eine Aufgabe erscheint nur, wenn
ihre Bedingung erfüllt ist; Fristen dürfen nicht erfunden werden.

**Weitere Zustände:** Ohne Anlass «Aktuell kein kommender Anlass» mit Link zu Events.
Ohne Aufgaben «Alles erledigt» statt leerer Warnkacheln. Scheitert das Laden offener
Posten, steht «Zahlungen konnten nicht geladen werden» mit erneutem Laden statt
CHF 0.00. Für private Auslegende kommt eine eigene Aufgabe «Zahlungseingang bestätigen»
hinzu. Schatzmeister sehen nur berechtigte Verwaltungsaufgaben, Mitglieder nur eigene.

## Eventdetail

**Ziel:** Teilnahme, BillBro und Bewertung bleiben im selben Eventkontext.

Der ausgearbeitete Eventdetail-Entwurf übernimmt den bestätigten App-Rahmen.
Die Vorschau bietet drei Beispielzustände: vor dem Anlass, beim Essen und nach
der Abrechnung. Sie sind ausserhalb der dargestellten App umschaltbar; diese
Auswahl gehört nicht zur späteren Mitgliederoberfläche. Innerhalb des Events
wechseln Teilnahme, BillBro und Bewertungen unter einem bleibenden Kopfbereich.

Zu- und Absage, Ess-Typ/Schätzung samt Betragsvalidierung und eine Bewertung von
Essen, Getränken und Service sind lokal bedienbar. Nach Abschluss stehen eigener
Anteil, Empfänger, bereits bezahlt und Restbetrag gemeinsam vor der Erläuterung
der Gesamtrechnung. Die Entwurfsoptionen ergänzen Organisation und privaten
Zahlweg. Die Organisation prüft Beispielanteile und finanzielle Folgen vor dem
Abschluss; Korrekturen bleiben ausdrücklich abhängig von F3/F4. Der Beginn und
die Berechtigung für Bewertungen bleiben abhängig von F8.

54 lokale Kombinationen aus drei Beispielzuständen, drei Eventansichten und sechs
Breiten von 320 bis 1440 px zeigten keinen gemessenen horizontalen Überlauf oder
JavaScriptfehler. Zu-/Absage, Schätzbetragsvalidierung, Speichern, Theme-Wechsel,
Kontomenü und Bewertungsformular wurden in der Simulation geprüft. Mobile und
Desktop wurden visuell kontrolliert. Keine Produktions- oder Fachabnahme.

Der Rückweg führt zur Eventliste mit vorherigem Filter und Position. Danach folgen
Titel, Termin, Ort und Sichtbarkeit sowie die Ansichten **Teilnahme**, **BillBro** und
**Bewertungen**. Im Seitentitel steht kein zusätzlicher Untertitel; Termin und Ort
sind Sachinformationen im Inhalt. Mobile ordnet eigene Teilnahme vor Teilnehmerliste
und organisatorischen Details. Desktop zeigt die eigene Handlung links und
ergänzende Informationen rechts. Status ist immer auch als Text sichtbar.

| Zustand | Mitglied | Organisation oder berechtigte Korrekturrolle |
|---|---|---|
| Antwort offen | Zu- oder absagen; gespeicherten Zustand klar bestätigen. | Antworten und offene Rückmeldungen sehen. |
| BillBro offen | Ess-Typ wählen; bei Monatsessen Rechnungsbetrag ohne Trinkgeld schätzen. Speichern am Formularende. | Rechnung, Trinkgeld und Zahlweg erfassen; vor Finalisierung Auswirkungen prüfen. |
| BillBro finalisiert | Eigenen Anteil, Empfänger und Zahlungsstatus lesen. Eingaben gesperrt; Grund nennen. | Korrekturablauf statt unbemerkter Änderung von Anteilen. Vorschlag abhängig von F3/F4. |
| Vereinszahlung | Forderung, Teilzahlungen und Rest separat; Bankimport bestätigt Zahlung. | Vereinsforderung und zugehörige Buchungen abstimmen. |
| Private Auslage | An auslegendes Mitglied zahlen; dessen Bestätigung sichtbar. | Auslegendes Mitglied bestätigt Eingang. Kein Vereinsforderungsstatus vortäuschen. |
| Bewertung noch nicht erlaubt | Grund und späteren Einstieg zeigen. | Öffnung und Berechtigung gemäss F8. |

Bei Vorstandssitzungen und Essen (Buchhaltung) entfallen Schätzung und GGL vollständig;
Ess-Typ und Split bleiben. Vertrauliche Events folgen weiterhin ihrer Sichtbarkeit.
Die Entwürfe ändern keine bestehenden Rechte.

**Fehler und Korrektur:** Fehlermeldung direkt am Feld und Zusammenfassung am
Formularanfang; Eingaben bleiben erhalten. Eine Korrektur zeigt alten und neuen
Betrag, betroffene Personen, bereits bezahlte Beträge und Folgeaktionen. Erst die
gemeinsame Bestätigung schliesst den Vorgang ab. Bei unklarem Speicherergebnis darf
die Oberfläche nicht zum blinden erneuten Auslösen auffordern.

## Buchhaltung

**Ziel:** Der Schatzmeister arbeitet den Bankimport nachvollziehbar ab.

Der ausgearbeitete Buchhaltungsentwurf übernimmt den bestätigten App-Rahmen.
Auf Mobile wählt ein beschriftetes Auswahlfeld den Arbeitsbereich; auf Desktop
stehen die drei Bereiche nebeneinander. Unter Buchen bleiben Import, Journal,
offene Posten und Belege direkt sichtbar. Ein laufender Import bietet die
Hauptaktion «Prüfung fortsetzen»; «Datei importieren» bleibt eine getrennte Aktion.
Die Zuordnungsansicht zeigt Zahlung, Forderung und Differenz sowie die geplante
Wirkung. Sie führt in diesem Layoutentwurf keine Buchung aus.

Zahlungslisten wechseln auf Mobile zu kompakten Einzelzeilen, die Budgetübersicht
bleibt zum Betragsvergleich eine Tabelle. Planung zeigt Budget, Ist und Rest;
der Jahresabschluss zeigt offene Aufgaben und Jahresstatus. Ein abgeschlossenes
Beispieljahr bietet lesende Ansichten. Über die Entwurfsoptionen ist zusätzlich
die lesende Revisorenansicht vergleichbar. Vollständige Revisions-, Korrektur-
und Buchungsabläufe folgen in der Interaktionsabstimmung.

36 lokale Kombinationen der drei Hauptbereiche, sechs Breiten von 320 bis 1440 px
und Hell/Dunkel zeigten keinen gemessenen horizontalen Überlauf oder JavaScriptfehler.
Unterbereiche, Importdetail/Rückweg und der Wechsel zum abgeschlossenen Beispieljahr
wurden geprüft; Mobile und Desktop wurden visuell kontrolliert. Dies ist allein
eine Prüfung der Vorschau, keine fachliche oder produktive Abnahme.

«Verein → Buchhaltung» bleibt der Einstieg. Die Seite zeigt Geschäftsjahr und
Jahresstatus dauerhaft im Kontext. Drei benannte Arbeitsbereiche ersetzen einen
unübersichtlichen Wechsel zwischen gleich gewichteten Funktionen:

| Arbeitsbereich | Inhalt | Vorrangige Aktion |
|---|---|---|
| Buchen | Importprüfung, Journal, offene Posten und Belege. Manuelle Buchung bleibt sichtbar als Sonderfall. | Kontoauszug importieren oder laufende Prüfung fortsetzen. |
| Planen und auswerten | Budget, Ist, Abweichungen und Exporte mit gleichem Jahresfilter. | Budget bearbeiten, wenn berechtigt. |
| Abschliessen und prüfen | Abstimmung, Freigabe, Beanstandungen, Revisionsbestätigung und Bericht. | Nächster zulässiger Schritt gemäss Jahresstatus. |

Die Vorschau zeigt diese drei Bereichseinstiege als lokale Navigation. In der
späteren App brauchen sie eigene adressierbare Ziele; sie sind keine versteckten
Aktionen im Filter. Kontenplan bleibt eine getrennte Verwaltungsaufgabe.

**Importfolge:** Datei prüfen → Zeilen zuordnen → Ergebnis. Die Prüfung zeigt offene,
gebuchte und ignorierte Zeilen getrennt. Desktop behält Betragsspalten rechtsbündig
in einer Tabelle. Mobile zeigt pro Zahlung Name, Datum, Zweck, Betrag, Status und
«Prüfen»; zusätzliche Daten bleiben im Detail erreichbar. Fachlich notwendige
Vergleichstabellen wie Budget werden nicht pauschal in Karten umgewandelt.

Die Zuordnungsansicht zeigt Bankbetrag, ausgewählte Forderung, zugeordneten Betrag
und Differenz. Im Beispiel werden CHF 120.00 auf einen Beitrag über CHF 120.00
gebucht; Differenz CHF 0.00. Die Abrechnung im Eventbeispiel ist ebenfalls geschlossen:
CHF 960.00 Rechnung + CHF 48.00 Trinkgeld = CHF 1’008.00; zwölf normale Ess-Typen
ergeben je CHF 84.00. Das ist eine Beispielsituation, keine neue Trinkgeldregel.

**Rollenvarianten:** Mitglieder haben den eigenen Belegeinstieg und eigene offene
Posten. Der Schatzmeister bucht und bereitet den Abschluss vor. Revisoren lesen,
kommentieren und bestätigen; sie erhalten keine Buchungsaktionen. Die heutige
Admin-Sonderstellung ist in F2 ausdrücklich zur Entscheidung gestellt.

**Fehler und Wiederaufnahme:** Ein fehlender Beleg wird am Vorgang sichtbar. Ein
Speicherfehler erhält die Zuordnung; nach Wiederaufnahme zeigt die App den bestätigten
Stand. Ein wiederholter Import darf keine zusätzliche Buchung erzeugen. Im Status
«in Revision» oder «abgeschlossen» sind Buchungen gesperrt. Rückgabe und Wiedereröffnung
benötigen die in F6 festzulegende Regel. Technische Verlässlichkeit bleibt Voraussetzung
aus U2 und wird durch den Entwurf nicht behauptet.

## Regeln für Mobile Tablet und Desktop

Die Breiten beziehen sich auf CSS-Pixel der späteren App. Die Inline-Vorschau ist
auf die Breite der Unterhaltung begrenzt; ihre Desktop-Auswahl zeigt das Layoutmuster,
keine massstäbliche 1440-Pixel-Geräteaufnahme.

| Breite | Navigation | Inhalt und Aktionen |
|---|---|---|
| 320 bis 767 | Vier Bereiche unten, persönliches Menü oben. | Eine Spalte; 16 px Seitenabstand; mindestens 44 px grosse Touch-Ziele. Beträge und Hauptaktionen bleiben vollständig lesbar. |
| 768 bis 1023 | Bottom-Navigation bleibt, keine schmale Desktop-Sidebar. | 24 px Seitenabstand. Dashboard/Event dürfen zwei Spalten erhalten, wenn beide nach Abständen mindestens 320 px breit bleiben; sonst eine Spalte. Importliste nutzt eine Tabelle nur, wenn ihre Kernspalten passen. |
| 1024 bis 1279 | Sidebar gemäss bestehendem 1024-Breakpoint. | Nach Abzug der Sidebar wird erneut die tatsächliche Inhaltsbreite geprüft. Bei Platzmangel eine Inhaltsspalte; niemals die Seite abschneiden. |
| Ab 1280 | Sidebar mit Textlabels. | Maximal etwa 1200 px Inhaltsbreite, 32 px Innenabstand; Hauptinhalt und Nebeninformation ca. 3:2. Tabellen erhalten die verfügbare Breite. |

Tablet quer bei 1024 px ist ausdrücklich ein Übergangsfall: Die Sidebar allein
rechtfertigt keine zweispaltigen Formulare. Lange Namen umbrechen; Beträge bleiben
zusammen. Vergleichstabellen dürfen in einem gekennzeichneten Bereich horizontal
scrollen, niemals das gesamte Dokument. Auf Tablet hochkant erfolgt Detailbearbeitung
als eigene Seite; eine schmale überlagerte Seitenspalte wird vermieden.

Die echte Bottom-Navigation braucht Abstand zur Safe Area und zum letzten Inhalt.
Die Vorschau zeichnet sie zur vollständigen Betrachtung im Dokumentfluss. Eine
Bildschirmtastatur darf Speichern nicht verdecken. Bei 200 Prozent Zoom gelten die
Regeln der tatsächlich verfügbaren CSS-Breite; keine Erkennung nach Gerätetyp.
Hell und Dunkel tragen dieselbe Statusinformation. Fokus, Fehlertexte und Aktionen
sind ohne Hover erreichbar. Ein Dialog braucht Fokusführung, Escape und Rückgabe
an den Auslöser; umfangreiche Geldkorrekturen erhalten eine eigene Seite.

## Fachentscheidungen für Zugang und Geldflüsse

F3 ist bezüglich Betragskorrektur und Bestätigung inzwischen **bestätigt**:
Organisation korrigiert unbezahlte Abrechnungen mit Vorher/Nachher-Vergleich;
Zahlungen bleiben erhalten, Differenzen werden nachgefordert oder als Rückzahlung
ausgewiesen. Bei betroffenen Vereinszahlungen bestätigt der Schatzmeister;
private Eingänge/Rückzahlungen bestätigt der Auslegende. Keine automatische
Rückzahlung. Details und verbleibende Grenzen: [BillBro-Interaktion](BILLBRO_INTERAKTION.md).
F4 ist ebenfalls **bestätigt**: vor Abschluss durch die Organisation änderbar;
danach ohne Zahlungen mit Vorschau und nachvollziehbarem Forderungsersatz,
mit vorhandenen Zahlungen nur über den Korrekturablauf mit Organisation und
Schatzmeister. Private Eingänge bestätigt die auslegende Person. Zahlungen bleiben
erhalten.

F5 ist hinsichtlich Teil- und Überzahlungen ebenfalls **bestätigt**:

- Teilzahlungen reduzieren den offenen Betrag; CHF 50.00 auf CHF 84.00 lässt
  CHF 34.00 offen.
- Überzahlungen werden separat ausgewiesen. Der Schatzmeister bestätigt die
  Behandlung als freiwillige Aufrundung, Zuordnung zu einer anderen offenen
  Forderung oder Rückzahlung. Keine automatische Aufrundungsbuchung.
- Doppelte Zahlungen werden zur Klärung angezeigt und nicht automatisch als
  zusätzliche Einnahme behandelt. Eine echte zweite Zahlung ist vom erneuten
  Import derselben Banktransaktion zu unterscheiden; Wiederimport darf keine
  zweite Buchung erzeugen.

F6 ist ebenfalls **bestätigt**:

- Der Schatzmeister gibt das Geschäftsjahr zur Revision frei; ab dann sind
  Buchungen gesperrt.
- Der Revisor unterscheidet Hinweise von Beanstandungen, die den Abschluss
  blockieren. Offene blockierende Beanstandungen verhindern den Abschluss.
- Für Korrekturen gibt der Revisor das Jahr begründet zurück. Danach ist eine
  erneute Prüfung erforderlich.
- Geändert am 11. Oktober 2026: Systemadmin und Schatzmeister dürfen jeweils
  allein, ohne Zustimmung des Revisors, ein abgeschlossenes Jahr mit
  dokumentiertem Grund wieder öffnen. Der bisherige Bericht bleibt
  erhalten; nach erneuter Revision entsteht eine neue Version.

Diese Produktentscheidungen gelten für die spätere Umsetzung; das in DOMAIN.md
beschriebene bisherige Verhalten wird damit noch nicht geändert. Die übrigen
Entscheidungen sind **offen**. Die nachfolgende Tabelle bewahrt die Ausgangsoptionen;
die bestätigten F3-/F4-/F5-/F6-Stände haben Vorrang.
Keine App-Umsetzung erfolgt.

| ID und konkrete Frage | Empfohlener Ausgangspunkt | Alternative und ihre Folge | Vor welcher Umsetzung |
|---|---|---|---|
| F1 Was beendet alte Zugänge, und wie wird 2FA wiederhergestellt? | Bei Deaktivierung, Passwort-/2FA-Reset und sicherheitsrelevantem Rollenentzug betroffene Sitzungen, Links und Freigaben ausdrücklich widerrufen. Einmalige Wiederherstellung; ein neuer Reset macht ältere Links desselben Zwecks ungültig. Kontoaktivierung ersetzt vorhandene 2FA nicht. Für Verlust beider Faktoren braucht es einen dokumentierten Identitätscheck durch eine festgelegte verantwortliche Person. | Bequeme Fortsetzung bestehender Sitzungen nur bei normaler Passwortänderung wäre möglich, verlangt aber eine klare Ausnahme und sichtbare Sitzungskontrolle. Für kompromittierte Zugänge ist sie ungeeignet. Zu entscheiden: Auslöser, Reichweite, Freigabefenster und zuständige Person. | U1; Hinweise «Bitte neu anmelden», Wiederherstellung und Sitzungsmenü. Grundlage A-075 bis A-090, A-140/A-141. |
| F2 Darf Admin allein Finanzvorgänge und Revision vollständig bedienen? | Finanzaktionen nach Aufgabe vergeben: Schatzmeister bucht, Revisor bestätigt, Mitglieder reichen eigene Belege ein. Admin-Sonderrechte ausdrücklich benennen; Notfallzugriff mit Grund protokollieren. Vertrauliche Events und Kalender erhalten eine bewusst bestätigte Sichtbarkeitsregel. | Den heutigen breiten Admin-Zugriff beibehalten: einfacher Betrieb, geringere Trennung der Verantwortlichkeiten. Auch dann muss feststehen, ob dieselbe Person buchen und die Revision bestätigen darf. | U1/U2; sichtbare Aktionen und direkte Seitenaufrufe. Domain-Rollen, A-074, Auth-Review. |
| F3 Was geschieht bei geänderter Teilnahme, Ess-Typ oder Rechnung nach Finalisierung? | Vor Finalisierung editierbar; danach begründete Korrektur mit alter/neuer Verteilung. Bereits bezahlte Beträge bleiben erhalten; Differenz wird als zusätzlicher offener Betrag oder Rückzahlungsbedarf gezeigt. | Entsperren und neu berechnen nur, solange niemand bezahlt hat und kein betroffener Abschluss existiert. Auch dann Historie behalten. Zu entscheiden: wer korrigiert und wer betroffene Mitglieder informiert. | U2/U3; Event-Korrekturvorschau. A-023 bis A-029, A-031, A-033, A-046, A-138. |
| F4 Darf der Zahlweg zwischen Vereinskonto und privater Auslage wechseln? | Freie Wahl vor Finalisierung; danach explizite Überleitung mit Forderungen, bestätigten Zahlungen und Erstattungen im Vorher/Nachher-Vergleich. Private Auslagen bleiben ausserhalb der Vereinsbuchhaltung. | Wechsel nach Finalisierung ganz sperren und separat mit dem Schatzmeister klären. Weniger Automatik, mehr manuelle Abstimmung. Wer bestätigt private Eingänge und darf Bestätigungen zurücknehmen? | U2; Empfänger und Zahlungsstatus auf Dashboard/Event. A-024 bis A-029. |
| F5 Wie werden Teilzahlung, Überzahlung und Importwiederholung behandelt? | Teilzahlung reduziert nur den Restbetrag. Eine Überzahlung verlangt sichtbare Zuordnung als Aufrundung, Guthaben oder Rückzahlung; für jeden Fall verbindlich festlegen. Importwiederholung und Korrektur müssen dieselbe Zahlung eindeutig wiedererkennen. | Jede Überzahlung pauschal als ausserordentliche Einnahme übernehmen, wie in der Domain beschrieben: einfacher, aber versehentliche Doppelzahlung wird sonst fälschlich Einnahme. Zu entscheiden: welche Fälle automatisch als Aufrundung gelten und wann Rückfrage nötig ist. | U2; Zuordnungsansicht, Restbetrag und Ergebnismeldung. A-057 bis A-073. |
| F6 Welche Beanstandung blockiert den Jahresabschluss, und wer öffnet erneut? | Revisor unterscheidet Hinweis und blockierende Beanstandung; offene Blocker verhindern Bestätigung. Schatzmeister kann nach begründeter Rückgabe korrigieren; anschliessend erneute Revision. Nach Abschluss nur protokollierte Wiedereröffnung durch festgelegte Rolle; bisherigen Bericht erhalten und als ersetzt kennzeichnen. | Geschlossene Jahre bleiben unveränderlich, Korrekturen erfolgen im Folgejahr. Einfachere Sperrregel; Behandlung und Bericht müssen fachlich bestätigt werden. | U2/U3; Abschlusscheckliste, Rollen und Berichtshistorie. A-070 bis A-074. |
| F7 Welcher Preis gilt bei einer Merch-Bestellung und bei Storno nach Zahlung? | Mitgliedspreis zum bestätigten Bestellzeitpunkt binden. Spätere Preisänderung und Storno mit eigener Differenz bzw. Rückzahlung; bezahlte Forderung nicht löschen. | Preis erst zum Bestellschluss verbindlich: braucht vor Abschluss eine klare Information und Zustimmung bei Preisänderung. | U2/U3; spätere Shop-/Verwaltungsentwürfe. A-048 bis A-056. |
| F8 Wer darf wann bewerten und welche GGL-Regeln gelten verbindlich? | Bewertung nach dem Anlass für tatsächliche Teilnehmende; Änderungsfrist bewusst festlegen. Die dokumentierte GGL-Regel mit fractional ranking und Kalenderjahrsaison als Ausgangspunkt bestätigen; exakte Tipps, fehlende Tipps und spätere Deaktivierung ausdrücklich definieren. | Abweichende Vereinsregel ist möglich, muss aber dieselben Ergebnisse in Event, Rangliste und Statistik erzeugen. Historische Saisons nur mit eigenem Beschluss neu berechnen. | U3; Bewertungsstatus, Schätzung und Saisonwerte. A-021/A-022/A-032/A-040/A-041/A-047, Domain. |

Für die nächste Besprechung zuerst F1/F2 (Zugang und Verantwortlichkeit), danach
F3 bis F6 an einem bezahlten Essen und einem Import mit Teilzahlung durchgehen.
F7/F8 können separat beschlossen werden, bevor ihre Fachabläufe umgesetzt werden.
Eine Rückmeldung sollte pro ID die gewählte Regel, berechtigte Rolle und relevante
Ausnahme festhalten. Für den Oberflächenentscheid genügen zunächst drei Punkte:
Priorität auf dem Dashboard, gemeinsamer Eventkontext und die drei Buchhaltungsbereiche.

## Prüfung und verbleibende Grenzen

Die Vorschau ist eine lokale Simulation ohne Serverzugriff. Ausgearbeitete Wege:
Dashboard zum Event, Teilnahme, BillBro-Eingabe und abgeschlossener Anteil,
Import zur Zuordnung und zurück. Ergänzende Ziele geben eine erklärende Rückmeldung;
sie sind keine vollständigen Unterseiten. Hell/Dunkel, leerer Aufgabenbestand,
BillBro-Status und Zahlweg sind über die Entwurfsoptionen vergleichbar.

Die bestehenden Lücken K1 bis K5 im [Abschlussplan](COMPLETION_PLAN.md) bleiben offen.
Insbesondere sind reale Geräte, Safari/iOS, Produktion, Rechteprüfungen, tatsächliche
Geldverarbeitung und eine vollständige Tastatur-/Screenreader-Abnahme damit nicht
verifiziert. Neue Tests müssen weiterhin eine konkrete Entscheidung oder Abnahme
absichern; dieser Schritt eröffnet keine weitere umfassende Befundsuche.

Lokale Vorschauprüfung am 10. Oktober 2026: 36 Kombinationen aus drei Seiten,
320/390/768/820/1024/1440 px und Hell/Dunkel in Headless Chrome, ohne JavaScriptfehler
oder gemessenen horizontalen Überlauf. Die Hauptwege Teilnahme speichern,
BillBro-Eingabe, Importzuordnung und Importfilter funktionierten in der Simulation.
Mobile- und Desktop-Bildaufnahmen wurden visuell kontrolliert. Dies ist eine
Darstellungsprüfung des Entwurfs und keine Abnahme der App oder ihrer Fachregeln.

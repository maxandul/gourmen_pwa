# Direktes Bearbeiten und Warteschlangen – Bedienmuster

Stand: 11. Oktober 2026. Gestaltungsblock 3, Ergänzung der Formular-/Tabellenmuster.
**Darstellung und gezeigte Benutzerführung am 11. Oktober 2026 bestätigt.
Keine fachliche Gesamtabnahme, Umsetzungsfreigabe oder App-Änderung.**

Zwei interaktive Beispiele: Budgetplanung eines offenen Jahres und offene
Rückmeldungen zu vergangenen Anlässen. Daten und Vorgänge sind synthetisch.
Die Beispiele legen weder Budgetzuständigkeiten noch neue Teilnahmerechte fest.
Die tatsächlichen Buchhaltungsabläufe und fachlichen Voraussetzungen der
Bereinigung müssen separat abgestimmt werden.

## Direktes Bearbeiten

Ein Bearbeiten-Button öffnet die Eingabe unmittelbar unter dem betroffenen
Tabelleneintrag. Auch auf Mobile bleibt der Zusammenhang mit Bereich und Wert
sichtbar. Speichern und Abbrechen stehen bei dieser Eingabe. Es ist immer nur
ein Eintrag in Bearbeitung; Wechsel mit ungespeicherter Änderung verlangt eine
Entscheidung. Abbrechen der aktuellen Eingabe verwirft diese ausdrücklich.

Nach erfolgreichem Speichern aktualisieren sich nur Eintrag und Summe. Der Fokus
kehrt zum zugehörigen Bearbeiten-Button zurück. Fehler erhalten den Entwurf.
Die letzte Änderung lässt sich im Beispiel zurücknehmen; bei zwischenzeitlicher
Weiterbearbeitung stoppt die Rücknahme mit einer Erklärung.

Das ist ein vorgeschlagenes Bedienmuster. Welche Budget-/Kontenänderungen
zurückgenommen werden dürfen, wie historische Daten behandelt werden und welche
Jahrssperren gelten, folgt den Fachregeln. Kein pauschales Undo für Finanzvorgänge.

## Offene Einträge nacheinander bearbeiten

| Aktion | Bedeutung |
|---|---|
| Antwort auswählen | Entwurf ändern, noch nicht speichern. |
| Speichern und weiter | Nur nach erfolgreicher Speicherung zum nächsten Eintrag wechseln. |
| Überspringen | Offen lassen und zum nächsten Eintrag wechseln; zählt nicht als erledigt. |
| Vorheriger / Weiter ansehen | Navigation ohne Speicherung; geänderten Entwurf vor Verlassen behandeln. |
| Letzte Änderung zurücknehmen | Genau die letzte gespeicherte Änderung zurücknehmen und den betroffenen Eintrag zeigen, sofern noch zulässig. |
| Zur Klärung vormerken | Beispiel eines gesperrten Falls; keine Teilnahme, Forderung oder Abrechnung ändern. |

Position («Eintrag 2 von 3»), Zahl bearbeiteter Einträge und übersprungene Einträge
sind getrennt. Am Listenende heisst es «Durchgang beendet»; offene Einträge bleiben
sichtbar und können erneut aufgerufen werden. Es wird kein pauschales «Alles erledigt»
angezeigt, wenn lediglich alle Einträge angesehen wurden.

Mobile und Desktop nutzen dieselbe lineare Bedienung mit begrenzter Inhaltsbreite.
Nach Eintragswechsel Fokus und Sichtbereich auf den neuen Eintrag setzen. Fehler
halten den aktuellen Eintrag offen. Rücknahme und Konfliktmeldungen sind auch ohne
Hover erreichbar. In der Vorschau gibt es dafür Speicherfehler-/Konfliktoptionen.

## Fachliche Grenzen ausdrücklich offen

Die Beispielrückmeldung darf nicht als neue Selbstbedienungsregel für nachträgliche
Anwesenheit verstanden werden. Ob eine Antwort noch geändert werden darf, hängt
von tatsächlicher Anwesenheit, Rolle, Rundenschluss und Abrechnung ab. Die bereits
bestätigten BillBro-Regeln zur Organisatorenkorrektur und zum Abwesend-Label bleiben
bestehen. Abgeschlossene Abrechnungen werden im Entwurf zur Klärung geführt und
nicht durch einen gewöhnlichen Bereinigungsschritt geändert.

Eine Rücknahme darf keine zwischenzeitlichen Tipps, Bewertungen oder anderen
Änderungen löschen. Sie benötigt in der App eine Prüfung des aktuellen Datenstands,
der Berechtigung und des fachlichen Zustands. Die Vorschau illustriert den Konflikt,
implementiert aber keine serverseitige Versionsprüfung.

## Einordnung und Prüfstand

Die Entwürfe konkretisieren M04 (lokales Bearbeiten), M06 (Tabellenaktionen) und
M05 (Warteschlange). Mehrfachauswahl/Sammelzuordnung im Import ist ein anderer
Vorgang und bleibt offen. Merch, Dokumente/Uploads, Zugang und die weiteren
Muster der Gesamtübersicht folgen weiterhin; dieser Entwurf schliesst Block 3
nicht vollständig ab.

Lokal in Chrome bei 320, 390, 768, 820, 1024 und 1440 px ohne horizontalen
Seitenüberlauf geprüft. Eingabevalidierung, Speichern/Abbrechen, Wechselwarnung,
Rücknahme, Überspringen, Fortschritt, gesperrter Eintrag und Rücknahmekonflikt
durchgespielt. Mobile-Ansichten visuell geprüft. Keine App-/Geräte-/Fachabnahme.

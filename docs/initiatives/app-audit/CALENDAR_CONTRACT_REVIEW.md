# Kalender-Feed: Cache und Aenderungsvertrag

Stand 2026-09-20. Begrenztes Teilpaket aus D-06; keine Gesamtfreigabe der
Capability. Gelesen: CalendarFeedService, Feed-Route, Token-Routes und
Capability-Sektionen 8.3/8.4/11.1/11.4. Bestehende Lifecycle-Proben bleiben gueltig.

Reproduktion: `check_calendar_cache.py`. Originale App mit synthetischer
In-Memory-Datenbank, gesperrtem externem Netzwerk. Nur das Zeitargument fuer
die originale VEVENT-Erzeugung wird kontrolliert; keine Wartezeit und keine
Tokenwerte im Ergebnis. Testdatum nicht als Produktionsmessung verstehen.
Belege: [CALENDAR_CACHE_CHECKS.json](CALENDAR_CACHE_CHECKS.json).

| Probe | Ergebnis | Zuordnung |
|---|---|---|
| CAL-01 | Gleicher Zeitpunkt, gleiche Daten: ETag liefert 304. | Positivkontrolle: bedingte Antwort prinzipiell vorhanden. |
| CAL-02 | Fuenf Minuten spaeter, keine Datenaenderung: ETag anders und HTTP 200; einzige geaenderte Event-Eigenschaft DTSTAMP. | A-124. |
| CAL-03 | Notiz aendert DESCRIPTION, SEQUENCE bleibt 0. | A-125. |
| CAL-04 | Restaurant geaendert: SEQUENCE steigt auf 1. | Positivkontrolle des vorhandenen Vergleichs. |
| CAL-05 | audience als relevant deklariert, fehlt jedoch im Snapshot; Aenderung belaesst SEQUENCE bei 1. | A-125; kein Nachweis unberechtigter Feed-Sichtbarkeit. |

## Empfehlungen und Grenzen

DTSTAMP und ETag an stabile Inhalts-/Aenderungsdaten binden; Tests muessen
unveraenderte Daten ueber verschiedene Abrufzeitpunkte vergleichen. Aktuell
werden Query und Serialisierung bereits vor dem ETag-Vergleich ausgefuehrt.
Eine 304-Antwort allein wuerde deshalb noch keine eingesparte DB-Abfrage belegen.

Den Snapshot aus den tatsaechlich ausgegebenen Kalenderfeldern ableiten und
zentral pflegen. Notizen sind kein reines internes Feld: sie stehen in DESCRIPTION.
Auch Organisator-Anzeigenamen koennen Feed-Inhalt ohne Event-Edit veraendern;
dieser weitere Pfad ist hier noch nicht getestet. UID stabil erhalten.

Capability 11.4 behauptet einen Datumsfilter im SQL. Der Service laedt dagegen
alle veroeffentlichten, fuer das Mitglied sichtbaren Events und filtert das
Datum danach in Python. Statische Performance-Abweichung, keine neue
Produktions-Laufzeitmessung; als Erweiterung A-012 erfasst.

Offen: vollstaendige Feld-/Route-Matrix fuer SEQUENCE, echte Apple/Google/Outlook-
Synchronisierung inklusive Entfernen/Entpublizieren, Zeitumstellung, Rate-Limit,
Header-Varianten und betriebliche Log-/Tokenbehandlung. Dieses Teilpaket
prueft keine produktiven Tokens, Kalender-Abos oder Einstellungen.

## Zweiter Durchlauf: Inhalt, Sichtbarkeit und Zeitgrenzen

Reproduktion: `check_calendar_content.py`; Belege:
[CALENDAR_CONTENT_CHECKS.json](CALENDAR_CONTENT_CHECKS.json).
Sieben weitere Pruefgruppen, insgesamt zwoelf Kalendergruppen einschliesslich
des ersten Durchlaufs. Keine zusaetzlichen Browser-/Kalender-Client-Tests.

| Probe | Umfang | Ergebnis |
|---|---|---|
| CAL-06 | Kontrolliertes heutiges Datum, Event heute 01:00 vs. gestern 23:00 | Heute enthalten, gestern ausgeschlossen; Filter ist datumsbezogen, nicht uhrzeitbezogen. |
| CAL-07 | Board-Event fuer normales Mitglied als Organisator, Vorstandsmitglied, Admin ohne Vorstand | Nur Vorstandsmitglied erhaelt Termin im Feed; entspricht dem speziellen Kalenderfilter. |
| CAL-08 | Event entpublizieren | Termin faellt aus generiertem Feed. Kein Beleg fuer Entfernung aus realem Client-Cache. |
| CAL-09 | Datum, Typ, Restaurant, Place-Name, Adresse, Organisator-ID, Notizen jeweils separat | UID immer stabil; erste sechs erhoehen SEQUENCE um 1, Notizen um 0 (A-125). Beide Testorganisatoren haben denselben angezeigten Vornamen, deshalb kein CN-Unterschied beim ID-Wechsel behauptet. |
| CAL-10 | Rufname des Organisators aendern | CN und DESCRIPTION anders; Event-SEQUENCE und LAST-MODIFIED unveraendert. Erweiterung A-125. |
| CAL-11 | Serialisieren und erneut parsen: 28./29.03. sowie 24./25.10.2026 | Beginn 18:00, Ende 23:00; UTC-Offsets +1/+2/+2/+1. Positiver Bibliotheks-Roundtrip, kein echter Apple-/Google-/Outlook-Test. |
| CAL-12 | Inaktives Mitglied mit Token und unbekannter Token | Je 404 und leerer Body; keine produktiven Token ausgegeben. |

Die Feldmatrix nutzt die originalen Snapshot-/Bump-/Serialisierungsfunktionen,
nicht alle Event-POST-Routen. Direkte Datenaenderungen erfolgen ausschliesslich
in der synthetischen Datenbank. Vollstaendige End-to-End-Feldabdeckung ist offen.

### Dokumentationskonflikt praezisiert

Capability 6.1 verlangt DTSTAMP zum Zeitpunkt der Feed-Generierung; 11.1
verspricht 304 bei unveraendertem Inhalt und ETag ueber den gesamten Feed.
Beides zusammen verursacht A-124. Die Implementierung folgt hier einer
widerspruechlichen Spezifikation. Deshalb bei der Korrektur beide Stellen
gemeinsam anpassen, nicht nur den Code als vom Soll abweichend bezeichnen.

### Restliste nach diesem Durchlauf

Echte Client-Synchronisierung (Verschieben, Entpublizieren, Loeschen),
weitere abhaengige Profilfelder, alle Mutationsrouten, doppelte/mehrfache
Aenderungen pro Speichervorgang, Rate-Limit, Header-Varianten und operative
Token-/Logbehandlung. Sichtbarkeit/Zeitzone sind nur fuer die genannten
Kombinationen lokal belegt. Weiterhin 125 Befunde; kein neuer Fall fuer dieselbe
Versionierungsursache angelegt.

## Dritter Durchlauf: echte Event-Speicherrouten

`check_calendar_routes.py` sendet POSTs an die Original-Edit-/Delete-Routen
mit jeweils neu angelegten synthetischen Events. Belege:
[CALENDAR_ROUTE_CHECKS.json](CALENDAR_ROUTE_CHECKS.json).

| Probe | Originalroute / Aktion | Ergebnis |
|---|---|---|
| CAL-13 | Edit ohne Inhaltsaenderung | SEQUENCE bleibt 0, UID stabil. |
| CAL-14 | Datum verschieben | Neues Datum gespeichert, SEQUENCE 1, UID stabil. |
| CAL-15 | Nur Notiz aendern | DESCRIPTION geaendert, SEQUENCE 0: A-125 im POST-Pfad bestaetigt. |
| CAL-16 | Datum, Restaurant und Notiz gemeinsam aendern | Werte gespeichert, Version steigt genau einmal auf 1. |
| CAL-17 | Sichtbarkeit all → board bei Monatsessen | Erfolgsredirect, weiterhin all und im normalen Mitgliederfeed. Bestaetigt A-026; kein neuer Befund. |
| CAL-18 | Typ auf Vorstandssitzung aendern | Erzwingt board, Version 1, aus normalem Mitgliederfeed entfernt. |
| CAL-19 | Fremdes Event als normales Mitglied bearbeiten | Redirect, Daten und Version unveraendert. Positiver Rechtefall, keine vollstaendige Rollenmatrix. |
| CAL-20 | Unabhaengiges synthetisches Event als Admin loeschen | Zeile entfernt und anschliessend nicht mehr im Feed. Keine echte Kalender-Client-Pruefung. |

Die Rollenwechsel laufen in getrennten App-Kontexten. Ein erster Testaufbau
teilte den Flask-Login-Cache zwischen Requests und wurde deshalb korrigiert;
dessen scheinbar erfolgreicher Fremdzugriff war ein Fixture-Artefakt und wird
nicht als App-Befund gewertet. Danach alle acht Proben erneut bestanden.

CSRF und Rate-Limit bleiben in Testing deaktiviert. Geprueft sind Edit und
Delete fuer die genannten Felder/Rollen; Erstellung, alle Profilrouten,
Parallelitaet und externe Kalender-Synchronisierung nicht pauschal abgedeckt.
Insgesamt 20 Kalender-Pruefgruppen, weiterhin 125 nummerierte Befunde.

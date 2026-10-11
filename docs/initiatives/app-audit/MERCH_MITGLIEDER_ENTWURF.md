# Merch v2: Mitgliedersicht

Aktuelle Nachführung: Modell `merch-member-v2` berechnet Preise je Ausführung
statt pauschal je Artikel. Definitiv Shirt M/L CHF 32/34, Hoodie M/L CHF 62/60;
derselbe Beispielpreiskatalog wie die gemeinsame Runde. Auswahl zeigt geschätzte
Variantenpreise, Prüfen nennt Verbindlichkeit und Einkaufspreis ohne Marge.
Der Beispielstand-Schalter lädt weiterhin unabhängige Beispieldaten; er ist
kein echter Rundenfortschritt. Für eine durchgängige Rollen-/Zahlungsfolge gilt
die Ergänzung `merch-gemeinsame-runde.html`, dokumentiert im Verwaltungsentwurf.
Preisberechnung und sechs Breiten in Hell/Dunkel lokal geprüft.

Stand: 11. Oktober 2026. Gestaltung und gezeigte Benutzerführung vom Nutzer
bestätigt («top. passt. weiter mit dem nächsten»). Offene Fachpunkte bleiben offen.
Grundlage: `phase/10-merch-wip@c90082e`, siehe [Zielversion](MERCH_ZIELVERSION.md).
Keine Änderung an App, Daten oder Deployment.

## Vorschau und Umfang

Interaktive Work-Vorschau: `merch-mitglieder-entwurf.html` im lokalen
Visualisierungsordner der Unterhaltung. Ausschliesslich Beispieldaten.

- Einstieg mit Bestellrunde, Frist und eigener Bestellung.
- Artikelauswahl mit Farbe/Grösse, Menge und Warenkorb; Entfernen mit Rücknahme.
- Prüfung vor Einreichen; Bearbeiten und Stornieren während der offenen Runde.
- Vorschauzustände: Runde offen, Preise folgen, Zahlung offen, bezahlt mit
  offener Abholung sowie abgeschlossen.
- Vorläufiger Betrag beim Bestellen, definitiver Betrag nach Preisfestlegung.
  Beispiel: Shirt und Hoodie definitiv CHF 92, Zuschuss CHF 20, Eigenanteil CHF 72.
  Die Bezeichnung «Vereinsbeitrag» im Mockup meint diesen Zuschuss, keinen
  jährlichen Mitgliederbeitrag; endgültige Benennung noch abstimmen.

Mobile stapelt Artikel und Warenkorb; vier Fortschrittsfelder stehen in zwei
Zeilen. Desktop stellt Artikelauswahl und Warenkorb nebeneinander. Tablet folgt
dem verfügbaren Platz statt einer festen Geräteorientierung. Gemeinsamer
Rahmen, Logo, Lucide-Navigation und Hell-/Dunkelmodus bleiben erhalten.

## Fachliche Abgrenzung

**F7-Teilentscheidungen bestätigt:** Die Bestellung ist verbindlich trotz
vorläufigem Preis. Der definitive Preis wird später mitgeteilt; keine erneute
Bestätigung durch das Mitglied. Keine Bindung des definitiven Preises an den
vorläufigen Betrag aus dem früheren Altshop-Vorschlag übernehmen.

Bei Wiederöffnung einer geschlossenen Bestellrunde bleiben bestehende
Bestellungen bestätigt. Mitglieder können während der erneuten Öffnung ihre
Bestellung bearbeiten; unveränderte Bestellungen brauchen keine erneute
Einreichung. «Runde wieder offen» setzt bestätigte Bestellungen nicht auf
Entwurf zurück. Lokale, noch nicht gespeicherte Änderungen dürfen den
bestätigten Stand nicht unbemerkt ersetzen; genaue Änderungsbestätigung noch
im Bedienablauf festlegen.

Diese Entscheidung erlaubt kein beliebiges Zurücksetzen nach Lieferantenauftrag,
Preisfestlegung oder Zahlung. Deren Korrektur-/Stornofolgen bleiben gesondert
offen. Eine Preisabweichungsgrenze oder Rücktrittsregel wurde nicht festgelegt.

Zahlung und Abholung werden getrennt dargestellt. «Bezahlt, Abholung offen»
bleibt im Entwurf im Schritt Zahlung & Abholung. Dies ist jetzt bestätigt:
Der untersuchte Mitgliederhelfer der Zielversion ordnet bereits PAID oder
PICKED_UP der letzten Phase zu, während die Capability-Dokumentation beide
Bedingungen für den Abschluss nennt. Im Ziel sind beide Bedingungen erforderlich;
Liefer-/Erstattungsfälle müssen ebenfalls erledigt sein. Teillieferungen,
positionsweises Storno nicht lieferbarer Artikel, Rückzahlungsbedarf bei bereits
bezahlten Ausfällen und ausdrückliche Zustimmung zu Ersatzartikeln sind bestätigt.
Details in MERCH_VERWALTUNG_ENTWURF.md, Abschnitt Lieferausnahmen. Die bisherige
Vorschau deckt diese neuen Ausnahmefälle noch nicht vollständig ab.

Änderungs-/Stornowege inzwischen bestätigt: in offener Runde selbst ändern oder
stornieren; nach Schliessung über Merch-Verantwortliche/Systemadmin, nach
Lieferantenauftrag erst nach Klärung der Möglichkeit. Nach Zahlung mit
Vorher/Nachher, Zuschuss und Nach-/Rückzahlungsbedarf; Zahlungen bleiben erhalten.

F7 ist nicht pauschal vollständig ausgearbeitet. Vor Umsetzung sind insbesondere
spätere Rückschritte, Preis-/Variantenfälle und Zahlungsinformation
gegen die gewünschte Vereinspraxis abzugleichen. Das bekannte v2-Prinzip
vorläufiger/definitiver Preise ersetzt keine Zustimmung zu allen Detailregeln.

Zuschuss inzwischen bestätigt: fester Betrag je Mitglied und Bestellrunde,
gedeckelt auf den definitiven Warenwert; kein Auszahlen ungenutzten Zuschusses.
Nach Storno auf verbleibende Artikel neu berechnen und zu viel geleistete
Eigenzahlungen zurückerstatten. Details und Beispiel im Verwaltungsentwurf.

## Grenzen und nächste Arbeit

Aktueller Preisentscheid: tatsächlicher Einkaufspreis je gewählter Ausführung
abzüglich des Zuschusses je Mitglied/Runde, keine zusätzliche Vereinsmarge.
Grössen/Varianten können unterschiedliche Preise haben. Bei Ersatz werden neuer
Preis und Mitgliederanteil vor Zustimmung gezeigt. Mit «ja» bestätigt; Details
und Rechenbeispiel in MERCH_VERWALTUNG_ENTWURF.md. Ältere Aussagen über vollständig
offene Preis-/Variantenregeln sind dadurch konkretisiert, visuelle Nachführung offen.

Als Nächstes Verwaltung der Runde mit ihren acht Schritten gestalten: Vorbereitung,
Sammeln, Lieferantenbestellung, effektive Preise, Beleg, Wareneingang, Verteilung,
Abschluss. Wiederöffnung gezielt am jüngeren Code prüfen, da ältere Dokumentation
und jüngere Änderung unterschiedliche Angaben zur Behandlung von Bestellungen machen.

Produktbilder sind Platzhalter, Varianten und Beträge Beispiele. Mehrere Runden,
reale Zahlungsinformationen, Berechtigungen, Fristdurchsetzung und Persistenz
sind nicht umgesetzt. Die Vorschau trennt beim Bearbeiten den eingereichten
Stand noch nicht vollständig vom lokalen Entwurf; daraus keine Speicherregel
für die App ableiten. Keine echte Bestellung oder Zahlung wird ausgelöst.

## Prüfung

Lokaler Chromium-Test bei 320, 390, 768, 820, 1024 und 1440 Pixeln über fünf
Vorschauzustände: kein äusserer horizontaler Überlauf, keine JavaScript-Fehler.
Mengenvalidierung, Variante, Warenkorbsumme/Zuschuss, Entfernen/Rücknahme,
Einreichen/Stornieren und getrennte Abholung geprüft. Mobile Ansichten visuell
kontrolliert. Kein Nachweis für echte Geräte, Safari oder die laufende App.

Die alte Zuordnung von 83 Templates bleibt eine Baseline-Zuordnung; sie ist
keine vollständige Inventur der zusätzlichen v2-Oberflächen.

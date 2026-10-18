# U2-05: Historische Konten und Richtungssummen

## Vertrag vor Code

A-067/A-068, bestehende K1-Regel und Revisionsvertrag: Historische Buchungen
werden nicht umgeschrieben. Live-Auswertungen enthalten aktive sowie im Jahr
bebuchte/budgetierte inaktive Konten. Konto-Ist ist richtungsbezogen: bei
Ausgabenkonten OUT minus IN, bei Einnahmenkonten IN minus OUT. Gruppierung
enthaelt Kontoart im Schluessel. Das daraus berechnete Ergebnis entspricht dem
Journal; Bruttoeinnahmen/-ausgaben bleiben separat unveraendert.

Neue/Bearbeitete Buchungen brauchen ein aktives Konto mit passender Richtung.
K1-Rueckfluesse werden getrennt auf 3620/6710 gebucht, nicht als neue gegenlaeufige
Buchung auf dem Ursprungskonto. Historische Gegenlaeufigkeit bleibt lesbar.
Neue Prueffassungen speichern die richtungsbezogene Berechnungsregel. Bereits
gesicherte Fassungen ohne diese Kennzeichnung behalten ihre bisherige
Berechnung und PDF-Bytes; Korrektur erfordert begruendete neue Vorlage.
Keine Migration und keine Altdatenreparatur.

## Lokaler Nachweis

18.10.2026: 88 Tests fuer Kontoauswertung, Buchungseingaben, eingefrorene
Berichte, Revision, Rueckzahlung und atomare Importbuchung bestanden
(933 Warnungen, 41.36 s). Nach Vereinheitlichung des Budgetvorschlags weitere
23 Tests fuer Konten, Jahressperren und eingefrorene Berichte bestanden
(211 Warnungen, 13.75 s). Diff-Pruefung sauber. Keine Migration, keine
Frontend-Aenderung. Synthetische Daten ohne dotenv/Netz.

Alte Fassungen ohne Berechnungskennzeichnung bleiben bewusst unveraendert;
eine historische Rechenabweichung wird erst in einer neuen begruendeten
Prueffassung korrigiert. Negative historische Konto-Ist werden nicht in
positive Budgetvorschlaege umgedeutet; Budgetbestaetigung verlangt weiterhin
einen expliziten nichtnegativen Betrag. PostgreSQL-/Browserabnahmen offen.

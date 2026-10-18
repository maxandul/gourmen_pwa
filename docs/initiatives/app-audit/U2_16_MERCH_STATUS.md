# U2-16a: Atomarer Merch-Status und Forderung

## Vertrag vor Code

A-049: Beide bestehenden Statuswege verwenden denselben Service. Status,
Lieferzeitpunkt und erstmalige Forderung werden in einer Transaktion gespeichert;
jeder Fehler rollt alles zurueck. Bestehende passende Forderungen/Zahlungen
werden nicht neu berechnet oder ersetzt. Keine Migration oder Altdatenreparatur.

Die bisherigen Vorwaertsziele bleiben moeglich. Gleicher Status ist eine echte
Nulloperation, setzt keinen neuen Lieferzeitpunkt und repariert keine Altlast.
Rueckschritte sind im einfachen Statusformular gesperrt: Wiedereroeffnung,
Storno und Finanzkorrektur brauchen den getrennten bestaetigten Fachablauf.
Dies ist keine Aenderung der Zielregel, dass unveraenderte Bestellungen bei
Wiedereroeffnung bestaetigt bleiben. Das Rundenmodell folgt separat.

Vor Vorwaertswechsel gespeicherte Positionssummen/Bestellsummen, Wertebereich,
Forderungsart, Mitglied, Betrag und Vereinsglaeubiger pruefen. Mehrdeutige oder
widerspruechliche Altposten unveraendert zur Klaerung melden. Nullbetrag erzeugt
keine kuenstliche Forderung. Geliefert bedeutet weder bezahlt noch Rundenschluss.
Bestellzeilensperre koordiniert mit U2-15; PostgreSQL-Parallelitaet bleibt externe
Abnahme. GET bleibt lesend, Rechte/CSRF und lokale Rueckkehrziele erhalten.

Regression: beide Originalrouten, Erfolg/Retry, vorhandene Teilzahlung,
Rueckschritt, falscher Status, Altinkonsistenz, Nullbetrag, echter Claim-INSERT-
und Commitfehler. Eingefangene Fehler ohne interne Daten in Meldungen/Logs.


## Umsetzung und lokale Nachweise (18.10.2026)

MerchOrderStatusService sperrt und prueft den Bestellstand; beide Originalrouten
verwenden ihn. AccountingService nimmt optional commit=False an. Pflicht-
Forderung und Status haben genau einen aeusseren Commit. Rohes Formular- und
Exception-Logging aus den beiden Routen entfernt. Bestehende Statusauswahl
zeigt Rueckschritte deaktiviert; Detailhinweis trennt Lieferung und Zahlung.
Keine neue UI-Klasse. PWA 3.16.36 / pwa.a03403de.js. Keine Migration.

Isolierter audit_bootstrap-Runner: tests/services/test_merch_order_status.py,
test_merch_order_edit.py, tests/routes/test_merch_area_permissions.py und
test_merch_docs_return_target.py. Erster Lauf: **117 bestanden, 2 fehlgeschlagen**
wegen falschem Enum-Namen ESSEN im neuen synthetischen Test. Korrigiert auf
ESSENSANTEIL; Rueckkehrziel-Fixture um gueltige Position ergaenzt, damit der
injizierte Folgefehler tatsaechlich erreicht wird. Zweiter Lauf:
**119 bestanden, 2137 Warnungen, 44.57 s**, Prozesscode 0.

30 neue Statusfaelle fuer beide Endpunkte: Vorwaertswechsel, Teilzahlung und
Wiederholung ohne DML/neuen Lieferzeitpunkt; Rueckschritte/ungueltiger Status;
abweichende Zeilen-/Bestellsummen, fehlende Positionen, falscher Betrag,
privater Glaeubiger, falsche Forderungsart, doppelte Forderung; Nullbetrag;
echter INSERT- und Commitfehler ohne Teilzustand oder interne Fehlermeldung.
Vorhandene Rechte-/CSRF-/Rueckkehrzieltests bleiben enthalten. Ein aelterer
Test erwartete den fehlerhaften bereits gespeicherten Status; jetzt wird der
unveraenderte Ausgangsstand verlangt und der Folgefehleraufruf nachgewiesen.
Node Edit/Worker: **24 bestanden**. git diff --check ohne Fehler.

Gleicher Status repariert absichtlich keine fehlende Altforderung. Altstand,
Wiedereroeffnung, Preis-/Zuschuss-/Stornokorrektur und vollständiges Rundenmodell
bleiben getrennte Folgearbeit. PostgreSQL-Sperren/Parallelitaet und reale
Browserdarstellung nicht geprueft; keine Produktionsfreigabe. U1 bleibt offen.

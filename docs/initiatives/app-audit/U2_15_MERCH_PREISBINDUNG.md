# U2-15: Merch-Preisbindung beim Bearbeiten

## Vertrag vor Code

A-055: Bestellbearbeitung ist keine definitive Preisfestlegung. Vorhandene
Positionen behalten ihre gespeicherten Stueckpreise/Bezeichnungen, auch bei
Mengenanpassung derselben Ausfuehrung. Neue Ausfuehrungen verwenden angezeigte
Katalogpreise. Unveraendertes Speichern ist eine echte Nulloperation, auch
wenn Katalogpreise inzwischen anders sind. Keine Neuverpreisung alter Zeilen.

Formularvorschau verwendet dieselben gebundenen Preise wie der Server.
Versionsvergleich verhindert das Ueberschreiben spaeterer Bestellaenderungen
und unbemerkt geaenderter Preise neuer Positionen. Alte/inaktive eigene
Ausfuehrungen lesbar/erhaltbar; keine Mengenerhoehung davon. Unbekannte,
mehrdeutige oder unvollstaendige Auswahl ablehnen statt still auslassen.
Leere Bestellung verlangt eigenen Stornoweg; kein implizites Loeschen.

Bei vorhandenen Forderungen keine einfache finanzielle Bestellaenderung;
Nulloperation bleibt moeglich. Der bestaetigte Korrektur-/Rundenablauf folgt
in A-049/U3. Mengen/Preise vor Mutation validieren, alles atomar speichern.
Keine Migration. Eingaben bei Fehler erhalten, keine ausgehenden Verbindungen.

## Umsetzung und Nachweis (18.10.2026)

MerchOrderEditService erhaelt bestehende Positions-IDs, Stueckpreise und
Bezeichnungen; neue Positionen erhalten einen Snapshot. Wiederholung ohne
Aenderung fuehrt keine INSERT/UPDATE/DELETE aus. Mengen und Gesamtsummen
werden vor Mutation geprueft, auch aggregierte Mengen kostenloser Artikel.
Forderungen und widerspruechliche Altbetraege sperren einfache Aenderungen;
kein stilles Reparieren von historischer Rechnung oder Zahlung.

Der getrennte Anzeige-Kontext enthaelt auch eigene inaktive Varianten und ihre
gebundenen Preise. Fehler behalten Auswahl/Mengen; JSON-Eingaben werden escaped.
Zusaetzlicher beim Review gefundener Fehler: bisheriges merch-order-edit.js
setzte Mengen bereits bei Initialisierung auf 0. Initialwerte bleiben jetzt
erhalten, einschliesslich korrigierbarer Fehlereingaben. Bestehende Klassen;
PWA 3.16.34 / pwa.e1afe4db.js, Edit-JS-URL v2.0.2. Keine Migration.

Isolierter Runner audit_bootstrap: tests/services/test_merch_order_edit.py,
test_merch_variant_integrity.py, tests/routes/test_merch_read_only.py,
test_merch_area_permissions.py, test_merch_prices.py: zunaechst **77 bestanden,
1647 Warnungen, 33.98 s**, erweitert **80 bestanden, 1721 Warnungen, 36.54 s**.
Faelle: Original-GET/POST, Vorschaupreis, wiederholtes Speichern ohne DML,
Mengen-/neue Positionsaenderung, stale Formular, Forderung/Teilzahlung,
Inaktivitaet, ungueltige/zu grosse/aggregierte Mengen, inkonsistente Altbetraege,
unvollstaendige Formulare und echter Commitfehler ohne Teilmutation.

Node-Harness fuehrt das originale Edit-JS mit synthetischen DOM-Elementen aus:
vier Mengen-/Eingabeerhaltfaelle gegen alten HEAD-Code **4 fehlgeschlagen**
(Menge jeweils 0), korrigierter Code **4 bestanden**. Zusammen mit Worker:
**23 bestanden**. Kein echter Browser-/Touch-/Darstellungsnachweis.
git diff --check ohne Fehler. Kein dotenv, Netz oder Produktionszugriff.

Nach der vom Nutzer gewuenschten Pause wurde der begonnene Teil gezielt gegen
bestaetigte Preis-/Korrekturregeln und die letzten Pakete abgeglichen. Keine
neue Fachfreigabe angenommen: definitive Preisfestlegung, Storno, Rundenzustand
und Finanzkorrektur bleiben eigene Folgepakete. Naechster Schritt ist eine
breite lokale Regression vor weiterer Implementierung; U1 bleibt offen.


## Breite Regression und Nachkorrektur

Gesamter Python-Testbestand auf Commit 68246e2 mit audit_bootstrap, pytest
`tests -q --disable-warnings --tb=short -p no:cacheprovider`:
**1320 bestanden, 18268 Warnungen, 739.49 s**. Prozesscode 0; erst beim
Interpreterabbau meldet pyreadline3 einen ignorierten Windows-Handle-Fehler.
Dies ist keine PostgreSQL- oder Browserabnahme.

Gezielte Nachpruefung fand drei Randfaelle: Reihenfolge eigener inaktiver
Varianten beeinflusste den Formularfingerabdruck; Unterstriche in Farbe/Groesse
konnten im JS denselben Schluessel bilden; bei fehlendem Farbfeld gingen die
anderen geposteten Felder in der Fehleransicht verloren. Neue Regressionen
reproduzierten **2 Python-Fehler und 1 JS-Fehler** vor der Korrektur.
Varianten/Artikel werden jetzt stabil nach ID projiziert, der JS-Schluessel
ist ein JSON-Paar, und die Fehlereingaben werden aus allen drei Feldarten
zusammengetragen. Keine neue Fachregel oder Migration. PWA 3.16.35 /
pwa.61d523f4.js, Edit-JS-URL v2.0.3; keine neuen UI-Klassen.

Nachkorrektur: derselbe erweiterte Merch-Testumfang **82 bestanden, 1763
Warnungen, 33.16 s**; Node Edit/Worker **24 bestanden**. git diff --check
ohne Fehler. Volltest oben gilt fuer 68246e2, nicht fuer diese Nachkorrektur.

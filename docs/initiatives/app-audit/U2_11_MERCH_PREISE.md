# U2-11: Exakte Merch-Preise

## Vertrag vor Code

A-053, bestaetigte Merch-Preisregel (Einkaufspreis minus Zuschuss, keine
Marge): Katalogpreise vor jeder Mutation exakt als nichtnegative Rappen
validieren. Null erlaubt kostenlose Lieferung oder vollen Vereinszuschuss;
Mitgliederpreis darf Einkaufspreis nicht uebersteigen. Keine Float-Abschneidung
und keine stille Rundung von Rappenbruchteilen. Integer-Grenze wie BillBro.
Fehler neben Lieferanten-/Mitgliederpreis, Eingaben und Variantenwahl erhalten.
Keine automatische Korrektur historischer Preise oder bestehender Bestellungen.

A-050/A-055 bleiben nachgelagert: referenzierte Varianten nicht loeschen und
Bestellpreise bei unveraenderter Bestellung erhalten. U2-11 allein behauptet
keine neue Varianten-/Bestellhistorie. Keine Migration.

Der isolierte Parser wurde waehrend des Gesamttests auf 623f5ba vorbereitet,
aber noch nicht in App-Routen eingebunden. Dieser Gesamttest bewertet nur den
vorher gesicherten App-Stand; U2-11 erhaelt eigene Regressionen.

## Umsetzung und Nachweis (18.10.2026)

MerchPriceService wird vor Artikel-/Variantenmutation aufgerufen. Beide Preise
haben korrigierbare Feldfehler mit Eingabeerhalt; unveraenderte Bestellungen
werden nicht neu bepreist. Bestehende form-field-Komponenten, keine neue Klasse.
PWA 3.16.30, Fingerprint pwa.6532e296.js. Keine Migration.

Isolierter pytest-Lauf ueber run_existing_tests.py als audit_bootstrap:
`tests/routes/test_merch_prices.py`, `test_merch_area_permissions.py` und
`test_billbro_amount_validation.py`: **92 bestanden, 1180 Warnungen, 35.21 s**.
Zuvor Parser allein: 21 bestanden, 9 deselected, 1.68 s.
Worker: `node --test tests/js/sw_cache_isolation.test.cjs`: **19 bestanden**.
Synthetische Daten, kein dotenv/Netz. Formfehler pruefen erhaltene Preise,
Artikelname, Varianten-IDs und korrigierbare Eingaben auf Originalrouten.

Breiter vorheriger Stand 623f5ba (HEAD waehrend des Laufs nur dokumentarisch
auf f22531e erweitert): **1212 bestanden, 16748 Warnungen, 727.76 s**.
U2-11 war dort noch nicht eingebunden und ist durch den eigenen Lauf belegt.
PostgreSQL, echte Browser/Touch/Hell-Dunkel und Produktionsbestand nicht geprueft.
U1 bleibt insgesamt offen. Naechstes Paket U2-12: bestaetigte BillBro-Verteilung.

Nach bedingter ARIA-Fehlerverknuepfung: 32 Merch-Tests bestanden, 151 Warnungen,
9.63 s. git diff --check ohne Fehler.

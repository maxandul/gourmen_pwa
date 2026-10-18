# U2-13: Merch-Lesewege ohne Fachmutation

## Vertrag vor Code

A-051: Shop, Bestellformular und Bearbeitungsformular duerfen beim GET keine
persistente Variantenrelation veraendern. Aktive Varianten und Farben als
separaten Template-Kontext in zwei gebuendelten Katalogabfragen laden.
Historische/inaktive Varianten und deren Bestellreferenzen bleiben erhalten.
Keine Preis-/Status-/Bestellmutation; A-049/050/052/054/055 bleiben eigene Pakete.
Regression mit bestellter inaktiver Variante und SQL-DML-Ueberwachung;
Skalierungspruefung 3/30 Artikel. Keine Migration oder externe Verbindung.

## Umsetzung und Nachweise (18.10.2026)

catalogue_context liefert getrennte Varianten-/Farbenlisten ohne Zuweisung an
article.variants; auch existing_items bleibt separater Template-Kontext.
Keine neuen UI-Klassen; PWA 3.16.32 / pwa.b579c3a0.js. Keine Migration.

Vorher: alle drei Original-GETs mit bestellter inaktiver Variante fehlgeschlagen
(3 Fehler, NOT NULL bei versuchtem UPDATE merch_order_items.variant_id).
Skalierung vorher: 3 Artikel = 10 SQL/6 Variantenabfragen, 30 = 64 SQL/60.
Nachher: jeweils 5 SQL/1 Variantenabfrage, historische Referenzen unveraendert.

Isolierter Runner audit_bootstrap: tests/routes/test_merch_read_only.py,
test_merch_area_permissions.py und test_merch_prices.py: **45 bestanden,
927 Warnungen, 18.61 s**. SQL-Ueberwachung bestaetigt keine INSERT/UPDATE/DELETE
beim GET. Synthetisch, kein dotenv/Netz. Die Zahlen gelten fuer diese Fixture,
nicht fuer Produktivdaten oder Browserlaufzeiten. Keine pauschale Shopfreigabe:
Bestell-POSTs und Ausfuehrungs-/Preishistorie bleiben Folgepakete.

Abschliessend 5 Leseweg-/Skalierungstests bestanden (214 Warnungen, 6.15 s),
19 Worker-Tests bestanden; git diff --check ohne Fehler.

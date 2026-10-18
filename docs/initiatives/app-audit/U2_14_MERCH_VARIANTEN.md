# U2-14: Stabile Merch-Varianten

## Vertrag vor Code

A-050/A-054: Artikelpflege erhaelt Varianten-IDs, Farbe/Groesse und bisherige
Ausfuehrungspreise. Abgewaehlte Kombinationen deaktivieren, nicht loeschen;
erneut gewaehlte Kombination reaktiviert dieselbe ID. Basispreise gelten fuer
neu angelegte Kombinationen, nicht als pauschale Ueberschreibung historischer
Ausfuehrungspreise. Formular erklaert diese Grenze. Preisbindung von
Bestell-POSTs und Runden-/Zuschussmodell bleiben A-049/A-055/U3.

Farben/Groessen trimmen, innere Leerraeume vereinheitlichen, Unicode NFC und
casefold als Vergleichsschluessel; erste Schreibweise erhalten. Doppelte
Auswahl einmal bilden; leere/zu lange Felder ablehnen. Bestehende normalisiert
mehrdeutige Varianten sperren Artikelpflege, ohne automatische Zusammenlegung
oder neue Referenzzuordnung. Artikel-Zeilensperre serialisiert App-Bearbeitungen;
PostgreSQL-Nachweis separat. Kein ungepruefter Unique-Constraint ueber Altbestand.

Bestellbezeichnungen als Snapshot speichern. Neue Positionen erfassen ihre
Bezeichnung bei Anlage. Vor erster Katalogaenderung vorhandene Positionen
sichern den bis dahin angezeigten Text als gekennzeichneten Altbestand;
keine Behauptung, dies sei die urspruengliche Bestellbezeichnung. Bestehende
Positionspreise und Zahlungen bleiben unveraendert. Nullable Snapshotfelder,
keine pauschale Datenrueckfuellung; Migration separat committen.

## Umsetzung und Nachweis (18.10.2026)

MerchVariantService kapselt Anlage/Pflege, rollt Validierungs-/Speicherfehler
vollstaendig zurueck und erhaelt Eingaben. Reaktivierung verwendet alte ID und
Preise. Aktive Bestellwahl lehnt normalisiert mehrdeutige Varianten ab; beide
Bestell-POSTs rollen dann vollstaendig zurueck. Neue Positionsbezeichnungen
werden vor Speichern erfasst. Historische Produktnamen bleiben bei spaeterem
Umbenennen sichtbar, Altbestandsherkunft gekennzeichnet. Keine neue UI-Klasse.
PWA 3.16.33 / pwa.cdd0f152.js.

Migration **e9d6f95**, u21420261018 nach u202c2b20261018, separat gesichert.
Synthetisch SQLite Upgrade/Downgrade/Upgrade und Downgrade-Sperre bei vorhandener
Historie: **1 Test bestanden, 0.25 s**. Keine Bestandsdaten gelesen/migriert.

Isolierter Runner audit_bootstrap mit tests/services/test_merch_variant_integrity.py,
tests/routes/test_merch_prices.py, test_merch_read_only.py und
 test_merch_area_permissions.py: zuerst **59 bestanden, 1209 Warnungen, 24.63 s**;
nach erweiterter mehrdeutiger Bestellwahl **61 bestanden, 1255 Warnungen,
26.36 s**. Worker **19 bestanden**. git diff --check ohne Fehler.
Faelle: offene/bestellte/gelieferte Historie, Umbenennung, mehrfaches Bearbeiten,
Deaktivierung/Reaktivierung, Ausfuehrungspreise, neue Kombinationen, doppelte
Eingaben, Altduplikate, Feldgrenzen, Commitfehler, neue Bestellsnapshots und
Ruecknahme mehrdeutiger Bestell-POSTs. Keine ausgehenden Verbindungen/dotenv.

Kein PostgreSQL-Parallelitaets-/Produktionsnachweis oder Browserabnahme.
Kein Unique-Constraint ueber ungeklaerte Altduplikate, keine automatische
Zusammenlegung. App-Pflege serialisiert je Artikel; direkte Datenbankschreibwege
sind damit nicht abgesichert. A-055-Preisbindung beim Bestellbearbeiten bleibt
naechstes Paket; heutiges Neuaufbauen der Positionen ist noch kein Korrekturablauf.

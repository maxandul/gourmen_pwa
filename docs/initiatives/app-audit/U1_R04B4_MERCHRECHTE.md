# U1-R04b4 – Merchbereichsrechte

## Vertrag vor Umsetzung

Aktiver Marketingchef/Systemadmin oder aktive Zusatzfreigabe `merch_manage`
erhalten die vorhandene Merchverwaltung: Bestellungen/Lieferanten/Artikel lesen,
Bestellstatus aendern, Artikel und Varianten pflegen. Alle Verwaltungsendpoints
pruefen denselben Scope vor Datenzugriff; gewoehnliche Mitglieder behalten Shop
und eigene Bestellungen, keine fremden Verwaltungsdaten. Keine Finanz-, Reise-,
Vorstands- oder Adminrechte aus diesem Scope. Widerruf nach U1-R04b1.
Bestehende Prozess-/Buchungsprobleme und Merchzielsystem bleiben U2/U3; dieses
Paket erweitert keine Statuszustaende. Oeffentliche Inhalte sind statische
Templates: kein vorhandener CMS-Mutationsweg, kein neues CMS in diesem Paket.
Keine Migration. Synthetische Regression ohne dotenv/Netzwerk.

## Umsetzung und Nachweis 18.10.2026

Alle vorhandenen Merch-Verwaltungsrouten, Legacy-Variantenweiterleitungen und
UI-Controls verwenden denselben Scope. Eigene Bestellungen bleiben erreichbar.
PWA 3.16.14, pwa.js fingerprinted; keine neuen UI-Klassen, keine Migration.

Isolierter Runner, pytest mit test_merch_area_permissions.py,
test_merch_docs_return_target.py und test_member_area_permissions.py:
**80 bestanden, 1148 Warnungen**. Erstlauf 79 bestanden/1 fehlgeschlagen: Test
suchte die nicht dargestellte Bestellnummer; korrigiert auf den sichtbaren eigenen
Bearbeitungslink. Rollenmatrix prueft Lesen, Anlegen, Bearbeiten, beide Statuswege,
Widerruf/inaktiv und keine Adminausweitung. Worker-Test: **19 bestanden**.
`git diff --check` sauber. Keine reale Zustellung oder Browser-/Drive-Abnahme.
U1 bleibt offen. Naechster Bereich R04c Dokumentrechte mit bestaetigter
Admin-only-Regel fuer unklassifizierten Altbestand.

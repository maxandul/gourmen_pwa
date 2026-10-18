# U1-R04b3 – Reisebereichsrechte

## Vertrag vor Umsetzung

Reisekommissar/Systemadmin oder aktive Freigabe `travel_manage` duerfen Ausfluege
anlegen und sichtbare Ausfluege bearbeiten, Teilnahme/BillBro verwalten und Ratings
freischalten. Zugewiesene Organisatoren behalten ihre Eventrechte. Die gemeinsame
Pruefung verlangt immer aktive Mitgliedschaft und Event-Sichtbarkeit. Keine
Vorstandssichtbarkeit, keine Pass-/ID-Freigabe aus `travel_manage`, keine Monatsessen-
Anlage oder Umtypisierung durch die Reisebereichsfreigabe. Eventloeschung und
Jahresplanung bleiben Adminaufgaben. RSVP-Erinnerungen bleiben gemaess U1e allein
Organisator/Admin; keine Erweiterung durch Reisebefugnis. Eigene Bewertungen,
Ess-Typen und Schaetzungen verlangen weiterhin die jeweilige Teilnahme.

Bereichsfreigaben verwenden U1-R04b1 samt aktionsgebundenem Beweis, Widerruf und
Sitzungsrotation. Kein Schemawechsel. Regression synthetisch ohne dotenv/Netzwerk;
reale Zustellung und Geraeteabnahme bleiben extern offen.

## Umsetzung und Nachweis 18.10.2026

Gemeinsame Rechtepruefung in Eventbearbeitung, Ratingfreigabe, BillBro-Verwaltung,
Polling und UI; gesonderte Typauswahl beim Anlegen/Bearbeiten. Selbstzuweisung
umgeht die Typgrenze nicht. PWA 3.16.13, nur pwa.js neu fingerprinted, vorhandene
fremde Hashdateien erhalten. Keine Migration.

Isolierter Runner mit pytest: test_travel_area_permissions.py,
test_reminder_permissions.py und test_event_visibility.py: **47 bestanden,
959 Warnungen**. Erstlauf 45 bestanden/2 fehlgeschlagen wegen falscher erwarteter
403 statt bestehender HTML-Weiterleitung; Erwartungen korrigiert und verbotenen
Versand explizit mit abbrechendem Fake abgesichert. Abschliessender Lauf Exit 0;
pyreadline meldete beim Prozessabbau einen ignorierten Windows-Handlefehler.
`node --test tests/js/sw_cache_isolation.test.cjs`: **19 bestanden**.
`git diff --check`: sauber. Keine reale Browser-/Mail-/Drive-/PostgreSQL-Abnahme.
U1 bleibt offen; naechstes Paket R04b4 Merchbereich.

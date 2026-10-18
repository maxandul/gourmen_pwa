# U1-R02 – Event- und Bewertungssichtbarkeit

Technischer Vertrag, 18.10.2026, Basis U1z 18285ef.

Bestaetigte Leserentscheidung vom 18.10.: Alle Mitglieder mit Eventzugriff duerfen
Einzelbewertungen einschliesslich Namen/Kommentaren lesen. Schreibrechte bleiben
separat; F8-Schreibablauf ist kein Teil dieses Sichtbarkeitspakets.

- Event-Edit uebernimmt all/board aus POST; Vorstandssitzung erzwingt weiter board.
- Oeffentliche Teaser/Restaurantaggregate nur aus publizierten all-Events. Keine
  Mitgliedernamen oder Kommentare oeffentlich. Board-Besuche liefern auch keine
  identifizierenden Restaurant-/Terminangaben ueber Aggregate.
- Interne Statistiken filtern vor Aggregation nach dem bestehenden Eventvertrag.
  Teilnahmequoten beruecksichtigen zusaetzlich die Sichtbarkeit des Mitglieds.
- Dashboard-Forderungen/Betraege bleiben erhalten. Bei inzwischen unsichtbarem
  Event keine Eventdetails/Deep Links; neutrale Kennzeichnung.
- Kalender behaelt seine dokumentierte strengere Board-Regel ohne Adminshortcut.
  Keine Rollen- oder Datenmigration, keine reale Zustellung oder Dienste.

Tests und offene Abnahmen folgen nach Implementierung.

## Tatsaechliche Pruefung und Ergebnis

Isolierter Runner per runpy wie U1z, danach pytest auf
`tests/routes/test_event_visibility.py`, `tests/services/test_calendar_feed.py`,
`tests/routes/test_calendar_feed_http.py`, `tests/routes/test_rating_return_target.py`
mit `-q --disable-warnings -p no:cacheprovider`: **63 bestanden**, 811 bestehende
Warnungen. Zuvor Collectionfehler wegen `from conftest`; auf
`from tests.conftest` korrigiert. Kein Testfall war dabei ausgefuehrt worden.

Elf neue Regressionen: vier Leserrollen auf Detail/API/Liste/Statistik,
Nichtteilnehmer Lesen vs. Schreiben, Public-Teaser/Aggregate ohne interne Daten,
all/board in beide Richtungen und erzwungene Vorstandssitzung mit Kalender,
ungueltige Audience ohne Mutation sowie bestehende Forderung im Dashboard.
Synthetische SQLite-Daten; dotenv und ausgehende Verbindungen gesperrt.
`git diff --check` ohne Fehler. UI-Cacheversion 3.16.9 und PWA-Fingerprint aktualisiert.
Keine neue UI-Klasse, keine Migration. Keine Aenderung historischer Bewertungen.

Echte Browser-/Layoutabnahme der neutralen Dashboardanzeige und reale Kalenderclients
bleiben offen. Bestehende F8-Schreib-/Gewichtungsrestarbeit bleibt bei U3;
dieses Paket schliesst ausschliesslich A-026/A-037/A-042 im dokumentierten Umfang.
U1 bleibt offen. Naechstes Paket: U1-R03 (Beleg-/Dokumentauswahl).

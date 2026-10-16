# U1y – Onboarding vor Versand sichern (A-139)

Stand: 16.10.2026. Basis `95c213a`, Branch `codex/u1y-onboarding-delivery`.
Begrenzte lokale Fortsetzung; U1 bleibt offen.

## Vertrag vor Umsetzung

- Neues Mitglied, U1x-Einmalverbrauch und Aktivierungstoken werden gemeinsam
  gespeichert, bevor irgendeine Mail versendet wird. Token nur als Hash;
  Empfängeradresse und Zugangsversion als unveränderliche Ausgabesnapshots.
- Neue Links gelten sieben Tage und nur für das aktive Konto mit derselben
  Adresse und Zugangsversion. Aktivierung/Passwortwechsel widerrufen sie wie U1v.
  Bestehende ungebundene Altlinks behalten ihren bisherigen Verbrauchsvertrag;
  keine Datenmigration oder nachträglich erfundene Versandsnapshots.
- Versandstatus am jeweiligen Token: `pending` (vorbereitet, Ergebnis offen),
  `accepted` (Maildienst hat angenommen), `unconfirmed` (nicht bestätigt),
  `obsolete` (vor Versand nicht mehr gültig). Keine Zustellgarantie behaupten.
  Prozessabbruch oder Fehler beim Speichern des Versandresultats lässt `pending`.
- Admin kann über einen eigenen GET/POST-Einstieg erneut einladen. GET/HEAD
  schreibt und sendet nichts. POST braucht CSRF und frisches Adminpasswort,
  gebunden an Aktion, Konto, Sitzung, Zielgeneration und angezeigte Zieladresse.
  U1x-Verbrauchszeile verhindert Wiederholung desselben Formularauftrags.
- Wiederholung nur für Konten mit einem U1y-Ausgabesnapshot und unveränderter
  Zugangsversion; keine erneute Einladung nach Aktivierung, Passwort-/MFA-Reset
  oder Berechtigungswiderruf. Altbestände nutzen die bestehenden Recoverywege.
  Adresskorrektur vor erneutem Versand ist erlaubt, alter Link passt nicht mehr.
- Unter Mitgliedssperre ersetzt ein neuer Link ältere ONBOARDING-Links dieses
  Kontos. Neuer Token und Formularverbrauch werden vor Versand committet.
  Passwort und sonstige Rollen/Sitzungen werden durch erneuten Versand nicht verändert.
- Keine automatische Wiederholung eines unsicheren Mailaufrufs. Bewusste neue
  Einladung ersetzt den Link. Späte Versandresultate werden nur am zugehörigen
  Token gespeichert und überschreiben keinen neueren Auftrag. Ein inzwischen
  widerrufener Link kann noch in einer bereits laufenden Mail eintreffen, bleibt
  aber unbrauchbar. Kein Exactly-once-Versprechen für externe Mailanbieter.
- Audit speichert nur Status und Token-ID, keine Links, rohen Providerfehler oder
  Passwörter. Fehler nach Versand können den bereits committed Link nicht löschen.
  Anlage sensibler Felder bleibt separat; Fehler dort werden zurückgerollt und
  neutral gemeldet, damit sie den Einladungsweg nicht in einer defekten Transaktion lassen.

## Grenzen und Nachweise

Additive nullable Spalten an `auth_tokens`: Migration `a13920261016` über
`f120261016`, separat in `9405a7a` gesichert. Kein Backfill, keine bestehenden
Datenbanken oder echten Maildienste verwendet. Schema vor Appwechsel migrieren;
keine ungeprüfte Mischversion oder Schema-Downgrade bei laufendem Betrieb.
Ein Downgrade entfernt die Bindungssnapshots und ist keine sichere Rücknahme
bereits ausgegebener Links. Vor Veröffentlichung koordiniert prüfen.
PostgreSQL-Parallelität, Geräte-/Darstellungsabnahme und reale Zustellung bleiben
offen. Kein Rollenumbau, Admin-Notfallzugang oder allgemeiner Mail-Outbox-Umbau.

## Lokale Tests

Runner `run_existing_tests.py`: synthetische Konten und SQLite im Speicher,
dotenv deaktiviert, ausgehende Verbindungen gesperrt, Mailservice ersetzt.
Versionierte Login-Identitäten aus `auth_id`, echte Passwortprüfung.

- Erster Lauf: **57 Tests bestanden** (118,70 Sekunden): 16 neue Onboarding-
  Fälle, Migration, 21 U1x-Fälle und 19 Admin-Mailkonfliktfälle. Bestehende
  Auditfehler-Proben auf den jetzt transaktionalen Auditpfad umgestellt;
  Fehler führen zu offenem Status statt Exception/Tokenverlust.
- Abschliessend **159 Tests bestanden** (371,27 Sekunden): alle 20 neuen
  Onboarding-Fälle, bestehende Aktionsbestätigung, Sitzungs-/Gerätewiderruf,
  Passwort-/Aktivierungslinks, gemeinsame Zahlenfelder und vier Migrationstests
  einschliesslich eindeutiger Alembic-Kette. Kein Fehler in diesen beiden Läufen.
- `git diff --check` ohne Fehler; die erzeugte PWA-Kopie übernimmt vorhandene
  Leerzeichen ihrer Quelle und wird beim Whitespace-Check ausgenommen.
- Zusätzliche Fälle prüfen späte Versandresultate, Adresswechsel zwischen
  Resolver und Mitgliedssperre, Altbestand ohne Wiederholung sowie Fehler beim
  Speichern sensibler Angaben ohne Geheimnisse im Log.
- PWA 3.16.7: Quelle und Fingerprint bytegleich, Hash/Manifest/Templateverweis
  stimmen überein. Neue Seite nutzt ausschliesslich bestehende UI-Klassen.

Kein vollständiger Gesamttestlauf oder tatsächlicher Versand. SQLite simuliert
zwischenzeitliche Änderungen, beweist keine PostgreSQL-Sperren. Keine pauschale
U1-Abnahme. Allgemeine Audit-Ausfallsicherheit, Altbestandsaufarbeitung sowie
Adressnormalisierung bleiben separat; Mailannahme ist keine Zustellbestätigung.

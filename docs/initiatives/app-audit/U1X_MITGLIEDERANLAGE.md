# U1x – Aktionsbestätigung bei Mitgliederanlage

Stand: 16.10.2026. Lokale Fortsetzung von U1w (`536242d`) auf
`codex/u1x-member-creation-confirmation`. U1 bleibt insgesamt offen.

## Technischer Vertrag

- Jede Mitgliederanlage vergibt initiale Rechte (Rolle, Funktion, Vorstand,
  Aktivität) und benötigt das aktuelle Passwort des handelnden Admins im selben
  POST wie die neuen Werte. Kein wiederverwendbares Step-Up-Fenster.
- Signierter Formularnachweis: eigene Aktion `member_create`, versionierte
  Adminidentität, zufällige Anmeldesitzungskennung, zufällige Auftragskennung;
  600 Sekunden gültig. Noch keine Ziel-ID: der konkrete Anlageauftrag ist das
  Ziel. Werte und Passwort werden gemeinsam übermittelt, keine Vorabfreigabe.
- GET/HEAD erzeugt keine DB-Zeilen. Abbruch lässt keine Freigabe zurück; ein
  noch gültiges Formular benötigt beim späteren Absenden erneut das Passwort.
  Andere Tabs haben eigene Aufträge. Login/Logout/Cookie-Anmeldung verwerfen
  die Sitzungsbindung wie in U1w. Antworten sind `no-store`, CSRF bleibt aktiv.
- Unter denselben Admin-/Mitgliedssperren wie U1w werden aktuelle Identität,
  Aktivität, Adminrecht und Passwort geprüft. Verlust der Identität/Rechte
  während der Anfrage führt zu 403. Rate-Limit wie U1w: fünf Prüfungen/Minute.
- Weil noch keine Zielgeneration existiert, wird der SHA-256-Hash der zufälligen
  Auftragskennung in `action_confirmation_uses` zusammen mit dem neuen Mitglied
  committet. Primärschlüssel verhindert Doppelverbrauch auch bei Parallelität.
  Kein Passwort, Formularinhalt oder signierter Nachweis wird dort gespeichert.
  Die Admin-Zugangsversion bleibt unverändert; seine anderen Sitzungen bleiben.
- Validierungs-/Passwortfehler schreiben nichts. Rollback beim ersten Commit
  nimmt Mitglied und Verbrauch gemeinsam zurück; erneuter Versuch braucht das
  Passwort wieder. Nach erfolgreichem Commit bleibt der Auftrag verbraucht,
  auch bei anderer Zieladresse, altem Cookie oder Fehler in Mail/Audit danach.
- Bestehende Anlagefolgeschritte (sensible Daten, Onboarding-Mail und Audit)
  werden nicht zu einer Gesamttransaktion umgebaut. A-139 (Versand vor dauerhaft
  gesichertem Onboarding-Link) bleibt separat offen. Auch R13/Rollenumbau und
  Admin-Notfallweg gehören nicht zu diesem Paket.

## Migration und Abnahme

Additive Tabelle, keine Bestandsdatenänderung; Migration `f120261016` über
`a07720261013` separat in `2c288ba` gesichert. Keine bestehende lokale oder
produktive Datenbank migriert.
Verbrauchszeilen werden vorerst nicht automatisch gelöscht. Spätere Bereinigung
darf niemals noch gültige Aufträge wieder freigeben. Downgrade entfernt den
Verbrauchsnachweis und ist nur ohne laufende U1x-App/alte gültige Formulare sicher.
PostgreSQL-Parallelität und echte Geräte-/Darstellungsabnahme bleiben separat.

## Lokale Prüfnachweise

Isolierter Runner `run_existing_tests.py`, synthetische Daten und SQLite im
Arbeitsspeicher; dotenv deaktiviert, ausgehende Verbindungen gesperrt. Echte
Passwortprüfung; Mailtransport ersetzt. Versionierte Testidentitäten über `auth_id`.

- Erster Lauf: **82 bestanden, 1 fehlgeschlagen** (221,10 Sekunden). Einziger
  Fehler: neue Testannahme verglich `Funktion` mit String statt Enum-Wert.
  Die Erwartung wurde korrigiert; keine Änderung der Fachlogik erforderlich.
  Bestehende Mailkonflikt-/Zahlenfeldtests bestanden in diesem Lauf.
- Abschliessend **63 Tests bestanden** (255,56 Sekunden): alle 21 U1x-
  Anlagefälle einschliesslich der korrigierten Enum-Prüfung und drei ergänzter
  Randfälle, 39 bestehende U1w-Fälle sowie drei Migrationstests. Eindeutiger
  Alembic-Head geprüft; kein offener Testfehler aus diesen Läufen.
- `git diff --check` ohne Fehler (erzeugte PWA-Kopie mit unveränderten
  bestehenden Leerzeichen aus der Quelle ausgenommen).
- Neue Tests prüfen GET/HEAD/Abbruch, unabhängige Tabs, initiale Rechte,
  fehlenden/manipulierten/abgelaufenen Nachweis, falsches/fehlendes Passwort,
  Aktions-/Konto-/Sitzungsbindung, Cookie-Replay mit anderer Zieladresse,
  Validierungs-/Commitfehler und echten E-Mail-Constraint-Rollback,
  Fehler nach dem ersten Commit, während der Anfrage entzogene Adminrechte
  und aktiviertes Rate-Limit. Migration separat mit Upgrade/Downgrade/Upgrade
  und eindeutiger Verbrauchskennung auf synthetischer SQLite-Tabelle geprüft.
- PWA 3.16.6: Quelle und erzeugte Kopie bytegleich; Hash, Manifest und
  Templateverweis stimmen überein. Keine neuen CSS-Klassen.

Kein vollständiger Gesamttestlauf in U1x. SQLite-Tests simulieren Änderungen
zwischen Authentifizierung und Sperre, beweisen keine PostgreSQL-Parallelität.
Mobile/Desktop, Hell/Dunkel und reale Geräte bleiben ungeprüft. Die Migration
muss vor Nutzung dieses Appstands angewendet werden; keine produktive Migration,
kein Push/Merge/Deploy und keine Schlüsseländerung erfolgt.

Nächster zusammenhängender Kandidat: A-139, dauerhafte Sicherung des Onboarding-
Links vor Versand und nachvollziehbare Wiederholung bei Zustellfehlern. Zuerst
separaten technischen Vertrag festhalten; kein stiller Rollenumbau oder Gesamtaudit.

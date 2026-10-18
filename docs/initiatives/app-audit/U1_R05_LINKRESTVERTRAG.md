# U1-R05 – verbleibender Link-/Adressvertrag

## Abgleich vor Umsetzung

F1 aus KONTO_ZUGANG_ENTWURF.md, U1o/q/r/v/y und bestehende Linkrouten sind
massgeblich. Passwort/MFA-Reset: eine Stunde; Aktivierung und Google-Bestaetigung:
sieben Tage. Keine neue Frist. Neuer Link ersetzt den eigenen Zweck; Verbrauch
und relevante Sicherheitsmutation widerrufen wie U1q/r/v. Kalenderfeed ist ein
bewusst dauerhafter persoenlicher Zugang mit eigenem U1n/v-Widerruf, kein Einmallink.
MAGIC_LINK existiert nur als Enum ohne produktiven Aussteller/Verbrauchsroute.

Gefundene Restluecken: Resetlinks ohne Empfaengerbindung, alte ungebundene
Aktivierungslinks noch zugelassen; Hauptadresswechsel widerruft die alten
Wiederherstellungslinks nicht ausdruecklich. Login/Formulare behandeln Schreibweise
uneinheitlich. Passwort-/MFA-Resetversand erfolgt noch vor sicherem Tokencommit.

## Teilpakete

- R05a: Reset-/Aktivierungsbindung an aktuelle Hauptadresse; ungebundene Altlinks
  verwerfen und neu anfordern. Hauptadresswechsel widerruft Reset/Aktivierung/MFA
  atomar mit der Adressaenderung, auch beim spaeteren Wechsel zurueck. Onboarding
  behaelt zusaetzliche Generationbindung; Resetzwecke behalten U1q/r-Zwecktrennung.
- R05b: Hauptmailadresse trimmen/kleinschreiben, einheitliche Suche/Formularpruefung
  und Datenbankgrenze. Kein Zusammenlegen von Konten. Konfliktbestand vor Migration
  abweisen, nicht automatisch korrigieren. Google-Adresse bleibt eigener Vertrag;
  D-01 zu mehreren Mitgliedern bleibt offen und blockiert diese Arbeit nicht.
- R05c: persistierte Resetlink-Ausgabe vor Versand, gebundener Empfaengersnapshot,
  kontrollierte Zustellfehler und nachvollziehbarer Status ohne Tokenleaks.

R05a nutzt vorhandene recipient_email-Spalte. Keine Schemaaenderung, keine
Aenderung bestaetigter Passwort-/MFA-/Fristregeln. Synthetische Negativtests fuer
Adress-/Zweckwechsel, Altlinks, inaktive Konten, Ablauf, Ersatz und Rollback;
PostgreSQL-Konkurrenz und echte Zustellung bleiben externe Abnahmen.

## R05a Nachweis 18.10.2026

Reset-/Aktivierungslinks sind adressgebunden, Aktivierung zusaetzlich an die
Zugangsversion. Profil-/Adminadresswechsel widerrufen alte Links in derselben
Transaktion; aktueller Tokenstand wird beim Verbrauch unter Sperre erneut gelesen.
Ungebundene alte Aktivierungen: vorhandener Passwort-Recoveryweg bzw. bestaetigte
Adminwiederherstellung, keine automatische Neuerteilung einer Legacy-Einladung.
Linkantworten no-store/no-referrer. Keine Migration/Assets.

Isolierter pytest-Lauf mit test_primary_email_link_binding,
test_password_link_revocation, test_mfa_link_revocation,
test_mfa_reset_confirmation, test_onboarding_delivery und test_profile_email_conflict:
**91 bestanden, 2067 Warnungen**, 56.54 Sekunden. Vorher Bestandsgruppe
82 bestanden/1728 Warnungen; neue Tests hatten zuerst einen zu fruehen Routenimport
vor Limiterinitialisierung und danach zwei synthetische .test-Formularadressen,
die der Mailvalidator korrekt ablehnt. Auf lazy Import bzw. example.com korrigiert;
keine Validatorlockerung. Rollback, Altlink-POST, fehlende Sitzung, Adresswechsel
hin/zurueck und Zweckverwechslung nachgewiesen. `git diff --check` sauber.
Reale Mail-/PostgreSQL-/Geraeteabnahme offen. Naechstes Paket R05b Normalisierung.

## R05b technischer Vertrag

Neue Formulareingaben: ASCII-Rand-Leerraum (Leerzeichen/Tab/CR/LF/VT/FF) entfernen,
kleinschreiben; keine Plus-/Punkt-/Providerumdeutung. Lookup/Formular-Konfliktcheck
und Unique-Index verwenden dieselbe lower(trim())-Form. Bestehende gespeicherte
Adressen werden durch die Migration nicht umgeschrieben. Konflikte einschliesslich
inaktiver Konten blockieren die Migration, ohne Adressen in Fehlermeldungen zu
nennen. Lookup liefert bei Mehrdeutigkeit keinen Account. Primary und Google-Mail
bleiben getrennt; keine Entscheidung zu D-01 vorwegnehmen.

## R05b Nachweis 18.10.2026

Migration **b17be2b** separat. Modellindex, Formularfilter, Konfliktpruefung und
Login-/Resetlookup vereinheitlicht; bestehende Adressen bleiben unveraendert,
neue Profileingaben kanonisch. Reset-Empfaenger wird normalisiert.
Isolierter pytest-Lauf mit test_primary_email_normalization,
test_primary_email_migration, test_profile_email_conflict,
test_primary_email_link_binding und test_onboarding_delivery:
**45 bestanden, 916 Warnungen**, 22.95 Sekunden. Login mit vier Schreibweisen
gegen Legacybestand, kanonischer Empfaenger, Profil/Admin-Duplikate, DB-Konflikt
und Mehrdeutigkeit vor Migration geprueft. Migration Upgrade/Downgrade/Upgrade,
Konfliktabbruch ohne Bestandsaenderung. `git diff --check` sauber.
Keine UI-/Assetaenderung; Worker nicht erneut ausgefuehrt. PostgreSQL-Index/
Konkurrenz und echter Bestandskonflikt-Check bleiben offen; keine Produktionsdaten
gelesen. Naechstes Paket R05c persistierter Resetversand.

# U2-01: Exakte Buchungswerte und Jahreszuordnung

## Vertrag vor Umsetzung

Quellen: A-057/A-058, B01 (BUCHHALTUNG_PRAXISABGLEICH.md),
BUCHHALTUNG_PROZESSE_ENTWURF.md, Accounting-Capability und Anchor-Docs.
Buchungseingaben in CHF werden exakt in positive Integer-Rappen umgewandelt,
keine Fuenf-Rappen-Rundung. Bruchteile eines Rappens, nichtendliche/ungueltige
Werte und Werte ausserhalb der vorhandenen 32-Bit-Integer-Spalte ablehnen.
19.99 bleibt 1999, 0.01 ist gueltig. Keine Aenderung historischer Buchungen.

Buchungsdatum muss im gewaehlten Kalenderjahr und zwischen dessen gespeicherten
Grenzen liegen. Anlage, Bearbeitung und Import nutzen dieselbe Servicepruefung;
Import waehlt weiterhin das Jahr des Bankbuchungsdatums, nicht das Forderungsjahr.
Service-Updates validieren alle Kandidaten vor der ersten Mutation, damit ein
spaeterer Validierungsfehler keine unbemerkte Teilmutation autoflushen kann.

Formulare zeigen Betrags-/Datumsfehler feldbezogen mit erhaltenen Eingaben.
Vorhandene Rollen, CSRF und Jahresstatus bleiben verbindlich. Keine Migration,
keine Umverteilung historischer Werte, kein Import-/Forderungsneubau.
A-060–065 und Revisions-/Beleg-Lebenszyklus bleiben eigene Folgepakete.

## Pruefung

18.10.2026: isolierter Runner, test_booking_values, test_bank_import,
test_finance_area_permissions und test_upload_selection_permissions:
**71 bestanden, 1147 Warnungen, 26.67 s**. Erster Lauf 55 bestanden/1 Fehler:
Berechtigungstest erwartete bei leerem Formular bisher Redirect statt neuem
400 mit Formularfehlern; Erwartung angepasst. Kein Berechtigungsabbau.

Nachgewiesen: 19.99/0.01/0.04, ganze CHF und nachgestellte Null; NaN/Infinity,
Rappenbruchteil, negative/zu grosse Werte; beide Jahresgrenzen, direkte Service-
Umgehungsversuche, Feldfehler und Eingabeerhalt beim Editieren, keine Teilmutation
nach spaeterem Validierungsfehler, unveraenderte Revisions-/Abschlusssperre,
Importjahreswechsel und zentrale Jahresgrenze. Bestehende Bereichs-/Belegrechte
mitgeprueft. SQLite/synthetisch/kein dotenv/kein Netz. Ignorierte pyreadline-
Handlewarnung am Prozessende, Exitcode 0.

Worker-Simulation: **19 bestanden**. `git diff --check` ohne Fehler.
PWA 3.16.19, Fingerprint 0df1449a. Keine neue UI-Klasse, keine Migration.
Echte PostgreSQL-Konkurrenz und Browserabnahme bleiben offen. Importatomaritaet,
Zahlungszuordnung/Korrektur und Revisionszustandsmodell folgen separat; U1 offen.

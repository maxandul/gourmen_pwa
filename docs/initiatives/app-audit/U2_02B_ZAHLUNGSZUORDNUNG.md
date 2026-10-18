# U2-02b: Sichere Zahlungszuordnung

## Zuschnitt und Vertrag vor Code

Quellen: A-061, bestaetigtes F5/B01, Buchhaltungsprozessentwurf, Praxisabgleich,
Accounting-Capability, U2-01/02a. b1 sichert den vorhandenen Einzelpostenweg;
b2 fuehrt danach persistierte Mehrfachzuordnung und offene Reste ein. Kein
pauschaler Abschluss des Sammelzahlungs-/Rueckzahlungsmodells durch b1.

b1: Eine positive Forderungstilgung braucht einen Eingang. Konto muss aktiv und
zur Richtung passen, bei Forderung zusaetzlich deren bestehendem Postenkonto.
Explizit gewaehltes Mitglied/Event muss zur Forderung passen; ohne Auswahl wird
die Forderungszuordnung verwendet. Auszahlungen oder widerspruechliche Felder
lassen alle Bestaende unveraendert. Das zugeordnete Mitglied ist der Schuldner,
nicht automatisch der Bankzahler. Originaler Bankzahler bleibt im Auszug erhalten;
Alias nur nach ausdruecklicher Bestaetigung, nie aus blosser Fremdzahlung lernen.

Ueberzahlung wird nicht mehr automatisch aufgerundet. Im bestehenden Einzelweg
ist ausdrueckliche freiwillige Aufrundung auf das bestehende passende Konto
moeglich (Essen/Merch); sonst bleibt die ganze Bewegung zur Klaerung pending.
Forderung wird nur um ihren zugeordneten Anteil fortgeschrieben, Zusatzbuchung
zeigt den freiwilligen Rest. Kein pauschales Begleichen durch vollen Bankbetrag.

Weitere Forderung oder Rueckzahlungsbedarf erhalten in b2 einen eigenen,
summenerhaltenden Zuordnungsstand; bis dahin nichts erfinden oder als bezahlt
markieren. Neue Wahl ist standardmaessig leer, Aufrundung nie vorausgewaehlt.
Alle Schritte bleiben in der U2-02a-Transaktion, keine Migration fuer b1.

## Nachweise

18.10.2026: b1 lokal geprueft. Isolierter Runner mit test_bank_payment_assignment,
test_bank_booking_atomicity, test_bank_import und test_booking_values:
**75 bestanden, 692 Warnungen, 27.74 s**. Nach Ergaenzung Event-Widerspruch und
Originalformular einschliesslich leerer/nicht vorausgewaehlter Restwahl:
Zuordnung/Atomaritaet/Import/Finanzrechte **43 bestanden, 709 Warnungen, 18.22 s**.
Worker **19 bestanden**, `git diff --check` ohne Fehler.

Synthetische Daten, SQLite, kein dotenv/Netz. Teil-/Exaktzahlung, explizite
Aufrundung und fehlende Wahl, Auszahlung, falsches Mitglied/Konto/Event,
inaktives Konto, aliasfreie Fremdzahlung und bewusste Aliasbestaetigung abgedeckt.
Vorherige Atomaritaetsproben bleiben wirksam; ihre Eingaben waehlen nun bewusst
Aufrundung und gegebenenfalls Alias, Forderungserwartung nur zugeordneter Anteil.
PWA 3.16.20, Fingerprint b9083e99; keine neue UI-Klasse oder Migration.

b2 mit persistierter Mehrfach-/Restzuordnung ist naechstes Paket. Echte
PostgreSQL-Konkurrenz und Browserabnahme offen, keine historischen Zahlungsdaten
korrigiert. U1 und die weitergehenden Geldflussablaeufe bleiben offen.


## b2: technischer Vertrag vor Schema/Code

Additives BankPaymentAllocation-Journal je Bankbewegung: Betrag, Art
(Forderung, freie Buchung, freiwillige Aufrundung, vorgemerkter Rueckzahlungsbedarf),
optionale Forderung, gebuchte Journalzeile, handelnde Person und Zeitpunkt.
BankTransaction erhaelt allocation_version. Kein Altbestand wird nachtraeglich
als zugeordnet interpretiert. Historisch verbuchte Bewegungen bleiben verbucht.

Pro bestaetigtem Teilauftrag genau eine neue Version unter Kopf-/Zeilensperre;
angezeigte Version muss noch gelten. Summe gebuchter Zuordnungen plus vorgemerkte
Rueckzahlung plus nicht zugeordneter Rest entspricht immer dem Originalbetrag.
Forderungsanteil darf ihren offenen Betrag nicht uebersteigen, weitere Forderung
auch eines anderen Mitglieds in weiterem Schritt moeglich. Bankbewegung bleibt
einmal vorhanden. Jede Buchung folgt deren Zahlungsjahr, Forderungsjahr bleibt.

Rueckzahlungsbedarf ist eine Vormerkung, keine Ausgabe, keine Bankueberweisung
und keine zusaetzliche Einnahmenbuchung. Er bleibt im offenen Abgleich sichtbar;
Abwicklung/Korrektur folgt im separaten Korrektur-/Rueckflusspaket. Rest ohne
Zuordnung bleibt ebenfalls offen. Erst volle gebuchte Verteilung ohne Vormerkung
setzt die Bewegung auf verbucht. Journal zeigt nur tatsaechlich zugeordnete
Anteile; offene/vorgemerkte Betraege werden im Abgleich gesondert ausgewiesen.

Bestehender Einzelweg schreibt kuenftig dasselbe Journal; bei vorhandener
Teilverteilung ist nur der versionsgebundene Teilweg zulaessig. Teilverteilte
Bewegungen nicht ignorieren/loeschen, verbundene Buchungen nicht frei bearbeiten.
Historische Teilbuchung ohne passenden Status/Journal wird nicht automatisch
weiterverarbeitet; gezielte Korrektur ist U2-02c. Aendern/Ruecknehmen gespeicherter
Zuordnungen bleibt bis zu diesem Korrekturvertrag gesperrt. Migration separat.


## b2 Abschlussnachweis 18.10.2026

Migration separat **b63c328**, additive Version/Zuordnungstabelle ohne Backfill.
SQLite Upgrade/Downgrade/Upgrade erhaelt synthetischen Bestand; Downgrade mit
benutztem Journal verweigert. Neue Modelle/Service/Formularansicht lokal geprueft.

Erster isolierter Lauf 93 bestanden, 889 Warnungen, 33.84 s. Abschluss nach
Eingabeerhalt, Rollen-/CSRF-Grenzen, Journal-Flushfehler und Ausgabesplit:
**104 bestanden, 1198 Warnungen, 37.65 s**. Dateien: test_payment_allocation_migration,
test_payment_allocations, test_bank_payment_assignment, test_bank_booking_atomicity,
test_bank_import, test_booking_values, test_finance_area_permissions.
Worker **19 bestanden**; `git diff --check` ohne Fehler. PWA 3.16.21,
Fingerprint 2316d7b4. Keine neue UI-Klasse. Ignorierte Windows-pyreadline-Warnung
beim Prozessende, Exitcode 0; kein dotenv, Netz oder echte Daten.

Mehrere Schuldner, Teil-/Schlusszuordnung, Aufrundung, Rueckzahlungsbedarf,
Summenerhalt, anderer Zahlungsjahrgang, veraltete Version/Replay, Original-POST,
fehlendes CSRF/Leserrechte, DB-Commit-/echter Journal-Constraintfehler, historisch
unklarer Teilbestand sowie Editier-/Ignorier-/Loeschsperre abgedeckt.

A-062 ist damit vor weiterer Entkopplung geschuetzt, aber **Korrektur bleibt offen**.
Korrektur/Ruecknahme und Vollzug vorgemerkter Rueckzahlung benoetigen den kommenden
versionierten Revisions-/Korrekturvertrag; keine Zahlungs- oder Historienreparatur
behauptet. PostgreSQL-Konkurrenz, reale Browser/Geraete und U1-Abnahmen offen.

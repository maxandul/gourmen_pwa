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

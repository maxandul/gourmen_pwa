# U2-12: Summengleiche BillBro-Verteilung

## Vertrag vor Code

A-031, Nutzerentscheid vom 18.10.2026: exakte gewichtete Rappenanteile,
ganze Rappen zuerst abrunden, Rest nach groesstem Rechenrest, Gleichstand
aufsteigend nach Mitglied-ID. Eingabereihenfolge darf nichts veraendern.
Anteile summieren sich zum bestaetigten Gesamtbetrag, auch bei Nullanteilen.
Nur anwesende Teilnahmen mit vollstaendigem Ess-Typ; keine stille Auslassung.
Ungueltige/fehlende Gewichte, leere Runde oder unvollstaendige Angaben werden
vor Mutation abgelehnt. Keine Float-Rundung.

Individuelle gespeicherte Anteile sind massgeblich fuer Anzeige, Teilen und
Forderungen. Kategorie-Felder koennen nur uniforme Werte abbilden; bei
unterschiedlichen Anteilen bleiben sie leer, Anzeige zeigt die Spanne.
Neue Abschluesse markieren largest_remainder_rappen im vorhandenen Regelfeld.
Historische Abschluesse bleiben unveraendert, keine Migration/Neuberechnung.

Abschluss und erste Forderungsanlage werden atomar gespeichert. Direkte erneute
Finalisierung veraendert keinen vorhandenen Abschluss; vorhandene Forderungen
nach einem alten Reset sperren neue Verteilung. F3/F4-Korrekturablauf bleibt
eigenes Folgepaket. Rechen-/Speicherfehler bewahren den Ausgangsstand.
Echte PostgreSQL-Konkurrenz und Browserdarstellung bleiben externe Abnahmen.

## Umsetzung und Nachweis (18.10.2026)

BillBroShareService verwendet Fraction aus validierten Dezimalgewichten.
Originalrouten set_total und accept_suggested_total speichern Erstabschluss
und Forderungen gemeinsam. Gespeicherte Kategoriebetraege bleiben nur bei
einheitlichem Anteil gesetzt. Persoenliche Anzeige und WhatsApp-Linktext
verwenden Einzelbetraege; API liefert den eigenen Anteil und die Regelfassung.
Keine Nachricht gesendet. PWA 3.16.31 / pwa.f55ddc3c.js, vorhandene UI-Klassen.
Keine Migration. Bestehender Trinkgeld-/Gesamtvorschlag unveraendert; die
bestaetigte neue Regel betrifft die Verteilung des festgelegten Gesamtbetrags.

Isolierter Runner (audit_bootstrap) mit tests/services/test_billbro_shares.py,
tests/routes/test_billbro_amount_validation.py, test_event_visibility.py und
tests/services/test_bank_import.py: **114 bestanden, 1457 Warnungen, 48.85 s**.
Worker: **19 bestanden**. Synthetisch, kein dotenv/Netz.
Echte SQLAlchemy-Insert-/Commitfehler pruefen Rollback, weitere Faelle:
Gewichte, Gleichstand, Eingabereihenfolge, Nullanteile, Maximalbetrag,
unvollstaendige/abwesende Teilnahme, private Auslage, Forderungssumme,
Altabschluss, wiederholter Abschluss und alte Resetreste mit Zahlung.

Korrigierte Testvorbereitung: zuerst falscher Enumname (11 Setupfehler),
danach fehlender Passwortwechselzeitpunkt beim synthetischen Nullanteil-Leser
(1 Redirect statt 200). Beide Fixtures korrigiert; obiger Abschlusslauf gruen.
Pyreadline-Windows-Destruktor meldet nach pytest gelegentlich ein ungueltiges
Handle; pytest beendet den Abschlusslauf mit Exitcode 0.

F3/F4 sowie bisherige Undo-/Reset-/Teilnahme-/Zahlweg-Korrekturwege sind damit
nicht insgesamt geloest. Keine pauschale BillBro-Freigabe. PostgreSQL-Konkurrenz,
Browserdarstellung und reale Zahlungen bleiben ungeprueft. U1 bleibt offen.

Nach ergaenzter Original-API-Pruefung: 36 Tests bestanden, 362 Warnungen,
11.85 s. git diff --check ohne Fehler.

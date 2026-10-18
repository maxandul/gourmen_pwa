# U2-02c: Korrektur von Importzuordnungen

## c1: Vertrag vor Code

A-062, F5/B01 und bestehendes U2-02b-Journal. Bankbewegung, Betrag, Richtung,
Datum und Referenz bleiben unveraendert. Kein freies Editieren der Importbuchung.
Ein ausdruecklicher Ruecknahmeweg zeigt alle aktiven Zuordnungen und ihre
Forderungswirkung vor Bestaetigung, verlangt Grund und aktuelle Version.

Ruecknahme bezieht sich auf den gesamten aktuellen Zuordnungsstand einer
Bankbewegung, damit abhaengige Aufrundungen nicht verwaisen. Alle urspruenglichen
Zuordnungen/Buchungen bleiben mit Verweis auf Ruecknahmejournal erhalten;
aktive Auswertungen zaehlen sie danach nicht mehr. Keine Gegenbuchung, die
scheinbaren Geldfluss oder Einnahmen/Ausgaben erzeugen wuerde. Forderungen
verlieren genau die bisher dieser Bewegung zugerechneten Anteile, andere
Zahlungen bleiben erhalten. Keine Herabsetzung der Forderungssumme und keine
Rueckueberweisung. Vorgemerkter Rueckzahlungsbedarf kann mit zurueckgenommen
werden; er war nie als Zahlung bestaetigt.

Unter Importkopf-/Transaktionssperre alle betroffenen Buchungsjahre und
Forderungen sortiert sperren, nur offene Zahlungsjahre erlauben. Widersprueche
zwischen Journal, Bankbetrag und Forderungsstand explizit abweisen, nicht
automatisch reparieren. Vorherige Revisionen/PDF bleiben unveraendert. Historisch
verbuchte Bankbewegungen ohne Zuordnungsjournal bleiben fuer gezielten Abgleich
gesperrt; kein Backfill. Atomarer Commit samt Grund, Person und Zeitpunkt.

Nach Ruecknahme steht der unveraenderte Bankbetrag wieder zur Zuordnung bereit.
Neuzuordnung nutzt den vorhandenen Teilzuordnungsweg (auch fuer einen ganzen
Betrag), neue Version, neue Buchung; alte Zuordnung bleibt im Verlauf.
Ignorieren/Loeschen einer Bewegung mit Historie bleibt gesperrt. Belege bleiben
an der erhaltenen alten Buchung und koennen mit dem vorhandenen geprueften
Belegweg im offenen Jahr neu zugeordnet werden.

Regression: Mehrfach-/Fremdzahlung und Aufrundung, Teilzahlung/Rest/Reservierung,
Wiederholung, veraltete Version, Jahres-/Rollen-/CSRF-Grenzen, echter Commitfehler,
Summen/Export/Statistik nach Ruecknahme, Wiederzuordnung ohne Doppelzaehlung,
alte Prueffassung erhalten. Migration getrennt; synthetische Daten ohne Netz.

c2 folgt fuer den tatsaechlichen Bankabgleich einer vorgemerkten Rueckzahlung
(eigene Ausgangsbewegung, Teilbetraege, Jahreswechsel). Dieser c1-Schritt
behauptet keine ausgefuehrte Erstattung und keinen BillBro-/Merch-Korrekturablauf.

## c1: Lokaler Nachweis

18.10.2026: Ruecknahmejournal, versionierter Vorschau-/Bestaetigungsweg und
aktive Auswertungen implementiert. Belege und alte Buchungen bleiben erhalten.
Eine versehentlich auf MemberClaim duplizierte, unbenutzte Revisionsproperty
wurde entfernt. Regressionen pruefen auch die Jahresisolation von Kommentaren.

- 62 Tests fuer Ruecknahme, Teilzuordnung, atomare Bankbuchung und Revision bestanden.
- Nach Erweiterung: 44 Tests fuer Ruecknahme, Belegauswahl, Jahressperren und
  eingefrorene Berichte bestanden (762 Warnungen, 23.28 s).
- Abschliessend 18 Tests fuer Ruecknahme und Finanzbereichsrechte bestanden
  (424 Warnungen, 13.46 s).
- 19 Service-Worker-Tests bestanden; PWA 3.16.26; Diff-Pruefung sauber.
- Migration mit synthetischer SQLite auf/ab/auf und Schutz vor Historienverlust
  geprueft. PostgreSQL-Sperren und Browserabnahme bleiben offen.

## c2: Bestaetigte Kontierung und verbleibende Arbeit

Am 18.10.2026 vom Auftraggeber bestaetigt: Bei CHF 90 Eingang und CHF 84
Forderung werden die zur Rueckzahlung bestimmten CHF 6 bei ausdruecklicher
Bestaetigung auf 3620 Sonstige Einnahmen erfasst. Der spaetere tatsaechliche
Ausgang folgt K1 auf 6710. Keine automatische Ueberweisung.

Noch umzusetzen: bestaetigten Ueberschuss, offenen Rueckzahlungsbedarf und
tatsaechliche Ausgangsbewegung getrennt verknuepfen; Teilbetraege, Wiederholung,
Ruecknahme und Jahreswechsel pruefen. Die bestehende Vormerkung allein ist
weiterhin keine Buchung und kein Nachweis einer Zahlung.

### c2a: Vertrag vor Code – Eingang bestaetigen

Eine bestehende aktive Vormerkung mit eindeutigem Mitglied kann ein
Buchhaltungsberechtigter ausdruecklich auf 3620 bestaetigen. Person, Zeitpunkt,
Vormerkung und neue Einnahmenbuchung werden atomar verknuepft. Kein automatischer
Altbestandsabgleich. Zahlungsjahr muss offen und Konto 3620 aktiv/Einnahme sein.
Die urspruengliche Vormerkung bleibt unveraendert; der bestaetigte Anteil zaehlt
jetzt als gebuchter Eingang, aber weiterhin als offener Rueckzahlungsbedarf.
Forderungszahlung wird dadurch nicht erhoeht. Version/CSRF verhindern Wiederholung.
Ruecknahme nimmt auch diese Einnahmenbuchung aus aktiven Zahlen, erhaelt aber
den Nachweis. c2b verknuepft erst danach den tatsaechlichen Ausgang auf 6710.

### c2a: Lokaler Nachweis

18.10.2026: 46 Tests fuer Bestaetigung, Ruecknahme und Teilzuordnung bestanden
(552 Warnungen, 25.85 s), einschliesslich CHF 90/84/6, Commitfehler,
Rollen/Jahressperre, Wiederholung, CSRF, Teilrest, Summen und Migration
auf/ab/auf samt Historienverlustschutz. Zwei anfangs fehlerhafte Testannahmen
zu einem nicht vorhandenen Statusattribut korrigiert; Wiederholung gruen.
19 Worker-Tests bestanden, PWA 3.16.27. Keine reale Ueberweisung, kein Netz.
PostgreSQL-Parallelitaet und Browserabnahme offen; c2b bleibt naechstes Paket.

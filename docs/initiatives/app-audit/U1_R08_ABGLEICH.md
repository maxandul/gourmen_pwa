# U1-R08: Lokaler Abschlussabgleich, U1 weiterhin offen

Stand 18.10.2026, Codebasis c97f066, bestehende Branchkette seit 5b6d28d.
Kein neuer Gesamtaudit. Abgleich der im Umsetzungsplan gefuehrten U1-Restfolge
mit Paketnachweisen, F1/F2/R13 und dem historischen Befundregister.

## Abdeckung und verbleibende Arbeit

| Vertrag | Lokaler Nachweis | Noch offen |
|---|---|---|
| Cache/Nutzerwechsel A-010 | U1z, 19 Worker-Simulationen; dynamische Antworten ausgeschlossen | Installierte PWA, Browsercache, mehrere Tabs und echte Geraete |
| Event-/Bewertungsleser A-026/037/042 | R02; Eventausschluss auch in API, Kalender und oeffentlichen Aggregaten | Browser-/Kalenderclientabnahme |
| Belegauswahl A-071 und R13-Dokumente | R03, R04c1–c3; Altbestand admin-only, Datei/Parent/Event/Belegpruefung, Loeschjournal | Reale Drive-Freigaben, Bestand zuordnen, ausstehende externe Loeschvorgaenge separat abgleichen |
| Sensible Felder und Delegation F2/R13 | R04a, R04b1–b4; sechs Reisedokumentfelder, gezielte Finanz-/Reise-/Merchrechte, Entzug versioniert | PostgreSQL-Sperren, Browserabnahme; keine Zahlungsfelder erfunden |
| Revision F2/F6/R13 | Aktuelle Finanzrollen begrenzt; Zielvertrag in R04-Matrix | **R04d bleibt echte lokale Restarbeit**: stabiler Pruefstand, Ruecknahme mit Grund, Historie, markierte Admin-Stellvertretung mit U2/U3 |
| Aktion/Link/Kontolebenszyklus F1 | U1c/f/k/o/p/q/r/t/u/v/w/x/y und R05a–c; Adressbindung, separate Linkzwecke, persistierter Versand | Echte Zustellung, PostgreSQL-Parallelitaet, Geraetewiderrufe; D-01 Google-Mehrfachadresse nicht entschieden |
| Backup-Ausgabe A-121 | R06; funktionsloser QR entfernt, Drucken/Kopieren und Einmalanzeige erhalten | Echte Druck-/Zwischenablageabnahme |
| Eigener Admin-Notfall | R07; CLI-Vorschau und atomare Wiederherstellung mit synthetischem Login und MFA-Neueinrichtung | Hostingzugriff/Identitaetsnachweis, autorisierte Live-Ausfuehrung |
| Auditfehler A-137 | Neue R04c/R05c/R07-Transaktionen sichern ihren eigenen Audit mit | Allgemeiner historischer Audithelfer und andere Aufrufer bleiben U2/U5 |

Alle 26 primaer U1 zugeordneten Befunde bleiben in der Rueckverfolgung des
Umsetzungsplans genau einmal erfasst. Historisches CSV bleibt unveraendert.
Lokale Nachweise sind keine externe Abnahme. Keine pauschale Fertigmeldung fuer
F1/F2/R13 oder U1; insbesondere Revision und externe Freigaben sind offen.

## Naechster begrenzter Auftrag

Nach lokalem Abschluss dieses Abgleichs U2-01: rappengetreue manuelle Buchung
und passende Jahreszuordnung (A-057/A-058). Grundlage B01/Praxisabgleich und
Buchhaltungsprozessentwurf: ein Vereinskonto, Zahlungsjahr aus Bankdatum,
Integer-Rappen, keine fuenf-Rappen-Rundung fuer Buchungseingaben. Servicegrenze
fuer Anlage/Bearbeitung/Import, Jahresgrenzen und ungueltige Betragseingaben
pruefen. Keine historischen Buchungen verschieben oder korrigieren.

Spaetere begrenzte U2-Pakete: Importatomaritaet/Zahlungszuordnung A-060–065,
Beleg-/Revisionszustand einschliesslich R04d/A-059/066/069/070/073/074,
BillBro-/Merch-Integritaet sowie A-137. Reihenfolge nach konkreten Abhaengigkeiten
verfeinern; Rechtebasis ist lokal vorhanden. Ausstehende externe U1-Abnahmen
blockieren diese isolierten lokalen Arbeiten nicht. Neue Migrationen separat.

## Tatsaechliche Pruefungen

Gesamte isolierte Python-Suite auf geladenem Stand c97f066:
**903 bestanden, 1 Fehler, 12929 Warnungen, 418.51 s**. Einziger Fehler ist die
unten dokumentierte Alt-Erwartung; Korrektur und betroffene 34 Tests danach
bestanden. Kein vollstaendiger gruener Gesamtlauf des korrigierten Stands
behauptet; Produktcode seit Suite-Start unveraendert. Der bereits vorhandene
ignorierte Windows-pyreadline-Handlefehler trat beim Prozessende erneut auf.
`git diff --check` ohne Fehler.
Keine Netzverbindung, dotenv oder echte Daten. Kein PostgreSQL-/Hosting-/
Mail-/Drive-/Geraetenachweis. U1 bleibt insgesamt offen.

Zwischenbefund: historischer Admin-Mailtest erwartete unveraenderte Grossschreibung.
R05b verlangt inzwischen kanonische Hauptmailadressen. Separat reproduziert
(1 bestanden/1 Fehler), explizite Erwartung auf freemixed@example.com korrigiert.
Admin-/Profil-Konflikte und Hauptmailnormalisierung danach gemeinsam:
**34 bestanden, 408 Warnungen, 17.13 s**. Keine Aenderung des Produktcodes.
Dokumentpruefung: 141 Registereintraege, alle 26 U1-IDs genau einmal im Plan,
lokale Links in Plan/Handoff/README/R08 vorhanden.

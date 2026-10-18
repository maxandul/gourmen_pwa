# U2-17b: Unbezahlte BillBro-Korrektur

## Vertrag vor Code: b1 Gesamtbetrag und Zahlweg

Bestaetigte Quellen: BILLBRO_INTERAKTION.md F3/F4 und REVISION_KORREKTUR_ENTWURF.md.
Organisation (bestehendes can_manage_event inklusive Admin) bereitet Grund,
Gesamtbetrag und Zahlweg vor; Rechnung, Teilnahme, Ess-Typ und Schaetzung bleiben
in b1 unveraendert. B2 folgt fuer diese Eingaben inklusive GGL-Folgewerte.
Keine pauschale Erledigung von F3/F4. Kein Versand und keine automatische Zahlung.

Vorschau zeigt alte/neue Gesamtbetraege, alle Einzelanteile und Glaeubiger.
Signierter, zeitlich begrenzter Nachweis bindet Akteur/Zugangsversion, Event,
vollstaendigen Ausgangsstand und konkrete Eingabe. Bestaetigung liest/sperrt
Event, Jahresstand und Forderungen erneut. Geaenderter Stand oder Zahlung seit
Vorschau sperrt; Wiederholung derselben bestaetigten Vorschau erzeugt nichts.

Nur finalisierte, noch unbezahlte Abrechnung mit unveraenderten offenen Posten:
paid != 0, abgeschlossene/erlassene Posten, Zahlungszuordnungen (auch rueckgenommen),
Eventbuchungen und betroffene Jahre in Revision/abgeschlossen sperren b1.
Private Zahlungseingaenge bleiben ebenfalls gesperrt. Fehlende oder mehrdeutige
Altforderungen bei vorhandenem Zahlweg werden nicht still repariert.

Bei Bestaetigung werden alte Forderungen mit saemtlichen Feldern in unveraenderlicher
Korrekturhistorie gesichert, neue Posten erzeugt und alte unbezahlte Posten ersetzt.
Keine referenzierten Zahlungszeilen loeschen. Gesamtbetrag, Anteile, Zahlweg,
Forderungen und Historie in einem Commit; Fehler rollen alles zurueck. Historie
mit Grund, Akteur, Zeitpunkt, Vorher/Nachher und Einmalnachweis. Separate additive
Migration, kein Backfill erfundener Historie; Downgrade mit Historie verweigern.


## b1 umgesetzt und lokal geprueft (18.10.2026)

Migration **3f16cb4**, Revision u217b120261018 nach u21420261018: neue
BillBroCorrection-Historie, Fremdschluessel mit RESTRICT, eindeutiger
Request-Hash. Upgrade/Downgrade/Upgrade und Historien-Downgrade-Sperre auf
synthetischem SQLite: **1 bestanden, 0.20 s**. PostgreSQL-Abnahme bleibt offen.

Originalroute /billbro/<id>/correction mit reiner Vorschau und getrenntem
Bestaetigungs-POST. Bestehende Abschlussaktionen verlinken Korrektur/Verlauf.
Vorschau zeigt Anteil und offenen Posten getrennt, auch beim Wechsel zur
privaten Auslage. Forderungs-Jahreszuordnungen bleiben fuer bestehende
Schuldner erhalten. Rechnung und GGL-Werte werden in b1 nicht veraendert.
Neue Posten werden vor Loeschen der alten erzeugt, damit auch SQLite keine
alte Posten-ID wiederverwendet. Alte Posten bleiben vollstaendig im JSON-Verlauf.
Eventloeschung respektiert diese Historie. Private Zahlungsbestaetigung und
manueller Abschluss sperren den Posten vor Mutation. Keine zweite Transaktion
innerhalb der Korrektur. Bestehende UI-Klassen; PWA 3.16.37 / pwa.c4809d76.js.

Regression ohne dotenv/Netz ueber audit_bootstrap:
- Neuer Korrekturlauf zuerst 19 bestanden/1 Testfehler: auth_generation wurde
  faelschlich als Zahl behandelt; Fixture verwendet nun rotate_auth_generation.
- Erweiterter Lauf zuerst 138 bestanden/1 falsche Test-Erwartung fuer CSRF
  (403 statt tatsaechlichem 400). Danach **139 bestanden, 2472 Warnungen,
  62.61 s**: correction, correction_migration, shares, finalization_boundary,
  payment_allocations und accounting_year_guards.
- Nach Jahreszuordnungs-/Vorschauergaenzung: correction und
  event_deletion_atomicity **41 bestanden, 1161 Warnungen, 26.79 s**.
  Ein erster Aufruf mit falschem Testdateinamen fuehrte keine Tests aus;
  danach korrekter Pfad verwendet.
- Bestehende private/manuelle Zahlungsbestaetigung aus test_bank_import:
  **2 bestanden, 13 abgewaehlt, 39 Warnungen, 6.24 s**.
- Node Edit/Worker: **24 bestanden**. git diff --check ohne Fehler.

Geprueft: keine Vorschau-DML, Gesamt-/Einzel-/Forderungssummen, Zahlwegwechsel
in beide Richtungen ohne Selbstforderung, Historie/IDs, unveraenderte GGL-Werte,
Retry ohne zweite Korrektur, manipulierte/abgelaufene/fremde Vorschau,
Zugangswiderruf, CSRF, spaetere Zahlung/Teilnahme/Notiz/Jahresstatus, private
Abrechnung bei unbeteiligtem geschlossenem Vereinsjahr, ungueltige Eingaben,
bezahlte/erlassene/inkonsistente/doppelte Posten, Buchung/Zuordnungsnachweise,
echter Posten-/Historien-INSERT- und Commitfehler mit erfolgreichem Retry.

Kein echter Browser-, PostgreSQL- oder Parallelitaetsnachweis. Keine Live-
Migration, kein Versand/Push/Deploy. U1 und U2-17b insgesamt bleiben offen.
Naechstes b2: Rechnungsbetrag mit korrekter GGL-Vorschau/Neuberechnung und
Speicherung gebrochener Raenge; Teilnahme/Ess-Typ danach separat (b3).
Bezahlte Korrekturen brauchen anschliessend die bestaetigten Finanzrollen.

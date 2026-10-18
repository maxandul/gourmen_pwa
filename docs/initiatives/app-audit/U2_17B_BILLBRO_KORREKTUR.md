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


## Vertrag vor Code: b2 Restaurantrechnung und GGL

Rechnungsbetrag als zusaetzliche explizite Korrektureingabe. Vorschau bindet alte/
neue Rechnung und zeigt betroffene GGL-Differenzen, Raenge und Punkte. Keine
Aenderung von Schaetzungen/Teilnahme/Ess-Typ. Neuer Gesamtbetrag mindestens
Rechnung; Trinkgeld ist Differenz. Genauigkeit/Summe nach U2-12. Berechnung
von GGL nach DOMAIN: absolute Differenz, Null ist bester Treffer, mittlerer
Rang bei Gleichstand, Punkte N-Rang+1. Alles zusammen mit Forderungen/Historie
atomar speichern; vorhandene Zahlungssperren bleiben bestehen.

Schemafund: Participation.rank und points sind Integer im Model; Initial-
migration hat rank, aber keine points-Spalte, auch keine spaetere Migration.
Separate Migration hebt rank auf Float und points auf Float (falls vorhanden)
oder fuegt die fehlende nullable Spalte hinzu. Keine Neuberechnung alter Werte.
Downgrade verweigert gebrochene Werte, konvertiert sonst beide auf Integer;
points bleibt als Kompatibilitaetsspalte erhalten, weil der vorige App-Code sie
bereits verwendet. Dieser bewusste Unterschied zur unvollstaendigen alten
Migrationskette verhindert Verlust vorhandener Legacy-Punkte.

Rechnungswechsel berechnet GGL neu; reine Gesamtbetrag-/Zahlwegkorrektur b1
laesst bestehende GGL-Werte unveraendert. Keine neue GGL-Fachregel. Vorschau
bei Nicht-GGL-Event ohne erfundene GGL-Neuberechnung. Alter signierter b1-
Nachweis darf nach b2 nicht mit fehlender Rechnung bestaetigt werden; neu vorbereiten.


## b2 umgesetzt und lokal geprueft (18.10.2026)

Separate Migration **37e081c** (u217b220261018): beide Legacy-Formen, Integer-
Datenerhalt, Upgrade/Downgrade/Upgrade und Sperre gegen Verlust halber Werte:
**2 bestanden, 0.29 s**. Downgrade behaelt die alte App-Kompatibilitaetsspalte
points wie im Vertrag beschrieben. Keine bestehende GGL-Historie neu berechnet.

GGLService.project_points ist eine reine Projektion. Rechnungskorrektur verwendet
sie fuer Vorschau und denselben atomaren Fachcommit; erstmalige Rechnung verwendet
dieselbe Berechnung. Das alte `difference or infinity` behandelte einen exakten
Treffer falsch; Null wird nun richtig vor positiven Abweichungen sortiert.
Gespeicherte halbe Raenge werden auch im Eventdetail statt Listenposition angezeigt.
Verlauf zeigt alte/neue Rechnung und GGL-Werte; vorhandene Tipps bleiben erhalten.
Nicht-GGL-Events erhalten keine erfundenen Punkte. Tokenzweck jetzt v2, alte
b1-Vorschauen werden kontrolliert abgewiesen. PWA 3.16.38 / pwa.34b2a6b8.js.

Isolierter Runner: test_billbro_invoice_correction, test_billbro_correction,
test_ggl_fractional_migration und test_billbro_amount_validation:
**91 bestanden, 1824 Warnungen, 44.83 s**. Nach Erweiterung um fehlende Tipps,
Abwesenheit und alte Vorschautokens: invoice_correction + fractional_migration
**14 bestanden, 376 Warnungen, 10.27 s**. Node Worker **19 bestanden**.
git diff --check ohne Fehler. Kein dotenv/Netz/Produktionszugriff; pyreadline3
meldete teilweise erst beim Interpreterabbau einen ignorierten Handlefehler
bei Prozesscode 0. Echte PostgreSQL-/Browserabnahme weiterhin offen.

B3 wird weiter begrenzt: b3a Ess-Typ der vorhandenen Anwesenden mit Auswirkung
auf Einzelanteile/Forderungen; b3b Anwesenheit getrennt von urspruenglicher
RSVP-Antwort modellieren. Die bestaetigte Regel verbietet erfundene nachtraegliche
Absagen; daher keine einfache Erweiterung um ein teilnahme-Umschreibefeld.

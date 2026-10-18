# U2-17a: Direkte BillBro-Mutationen nach Abschluss begrenzen

## Vertrag vor Code

Quellen: A-023/A-024, BILLBRO_INTERAKTION.md (bestaetigte F3/F4), U2-12.
Finaler Gesamtbetrag, gespeicherte Anteile oder vorhandene Essensforderungen
verlangen einen expliziten Korrekturablauf. Bis dessen eigener Umsetzung keine
stille Aenderung ueber RSVP, An-/Abwesenheit, Ess-Typ/Schaetzung, Rechnung,
Zahlweg, Oeffnen oder alte Reset-/Undo-Buttons. Zahlungen bleiben erhalten.
Dies ist eine Schutzgrenze des einfachen Wegs, kein Ersatz fuer die bestaetigte
Vorschau, Begruendung und zustaendige Bestaetigung im Folgepaket U2-17b.

Gemeinsame Event-Zeilensperre vor Lesen/Mutation koordiniert mit Erstabschluss.
Vor Abschluss bleibt Bearbeitung moeglich; geschlossene Schaetzrunde ist allein
noch kein finanzieller Abschluss. Bereits strengere Bereinigungspruefung U2-09
bleibt bestehen. Zahlweg vor Abschluss erzeugt keine Forderungen; nur atomarer
Erstabschluss U2-12 tut dies. Kein automatischer Versand, keine Migration.

Pruefung: alle betroffenen Originalrouten bei Abschluss, bezahlter Alt-Forderung
nach altem Reset, gespeicherten Anteilen ohne Gesamtbetrag, HTML/AJAX, Wiederholung,
keine DML/keine Zahlungsaenderung; gueltige Vorabschlusswege und U2-12-Regressionslauf.
PostgreSQL-Parallelitaet und kompletter Korrekturablauf bleiben separat offen.


## Umsetzung und Abgrenzung

BillBroStateService prueft den gespeicherten Fachstand; gemeinsamer Route-Guard
sperrt Eventzeile vor normalem RSVP und zehn direkten BillBro-Mutationswegen.
Erstabschluss prueft ebenfalls verbliebene historische Anteile. Kein reiner
billbro_closed-Test: vor Finalisierung bleiben Zahlungsauswahl und Anwesenheit
bearbeitbar. Die strengere CleanupParticipationService-Pruefung aus U2-09 war
bereits vorhanden und bleibt unveraendert; Originalroute wird mitgetestet.

Der alte nachgelagerte _sync_billbro_claims-Aufruf/Helper ist entfernt: im
nun ausschliesslich vorfinalen Zahlwegformular darf keine Forderung entstehen.
U2-12 bleibt der atomare Erstabschluss. Alte Reset-/Undo-Wege sind nach
Abschluss gesperrt und koennen gespeicherte Zahlungen nicht mehr ausblenden.
Kein neuer UI-Baustein/Asset, keine Migration, kein Versand oder externer Zugriff.

Dies liefert noch keinen F3/F4-Korrekturdialog und keine automatische
Umbuchung. U2-17b muss Grund, versionierte Vorher-/Nachher-Vorschau und Historie
fuer den unbezahlten Fall liefern; bezahlte Faelle anschliessend mit den
bestaetigten Finanzzustaendigkeiten. U1 bleibt offen.


## Tatsaechliche Regression (18.10.2026)

Isolierter audit_bootstrap-Runner, synthetische DB, kein dotenv/Netz:
Erster Lauf Boundary + Shares: **73 bestanden, 1 fehlgeschlagen**, weil der
neue Vorabschluss-Test MITGLIED statt des tatsaechlichen Enum-Werts mitglied
sendete. Fixture korrigiert; Schutz gegen erneute Finalisierung bei alten
Einzelanteilen ergaenzt. Erweiterter Lauf mit test_billbro_finalization_boundary,
test_billbro_shares, test_billbro_amount_validation, test_cleanup_undo,
test_event_visibility und test_travel_area_permissions:
**160 bestanden, 2619 Warnungen, 53.75 s**, Prozesscode 0.

36 Kombinationen aus 12 direkten Originalaktionen und drei historischen
Zustaenden jeweils zweimal ohne INSERT/UPDATE/DELETE; gesamter Event-/
Teilnahme-/Forderungsstand unveraendert. Dazu AJAX-Konflikt, Vorabschluss bei
bereits geschlossener Eingaberunde und zwei Finalisierungswege bei Altanteilen.
Bestehende Sichtbarkeits-, Rechte-, Betrags- und Erstabschlussregression enthalten.
git diff --check ohne Fehler. Echte PostgreSQL-Parallelitaet nicht nachgewiesen;
SQLite beweist nur die lokalen Transaktions-/Zustandsgrenzen.

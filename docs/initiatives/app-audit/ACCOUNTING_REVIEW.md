# Buchhaltung – erster vertiefter Durchlauf

Stand 2026-09-20, Baseline `bf4d84a`. **Teilpruefung, kein abgeschlossenes
Modulreview.** Zunaechst sieben isolierte Szenarien, Befunde A-057 bis A-059;
anschliessend zwoelf Import-/Zuordnungsszenarien, Befunde A-060 bis A-065.
Dritter Durchlauf: sieben Revisions-/Berichtsszenarien (einschliesslich einer
Matrix mit 16 Rollen-/Aktionskombinationen), Befunde A-066 bis A-070.
Vierter Durchlauf: fuenf Beleg-/Korrekturszenarien, Befunde A-071 bis A-074.
Damit 31 Buchhaltungsszenarien insgesamt; Matrix-Unterfaelle nicht doppelt gezaehlt.
App-Code und produktive Daten unveraendert.

## Nachweise und Grenzen

[ACCOUNTING_CHECKS.json](ACCOUNTING_CHECKS.json), reproduzierbar mit
`check_accounting_workflows.py`; Laufprotokoll ACCOUNTING_RUN.txt.
Original-Routes, Formulare, Services und Models mit synthetischen Mitgliedern,
Konten, Buchungen, Forderungen und Belegen. Pro Szenario neue SQLite-Datenbank
im Arbeitsspeicher. ENV-Laden unterbunden, ausgehende Sockets gesperrt.
Kein Bankimport, echter Beleg, Drive-Zugriff oder produktiver Finanzvorgang.

Globaler CSRF-Schutz und Rate-Limit in Testing aus. Die Beleg-Route besitzt
zusaetzlich eine manuelle CSRF-Pruefung; hier wurde ein gueltiger signierter
Token verwendet. Kein Nachweis fuer den gesamten produktiven CSRF-Schutz.
PostgreSQL, parallele Requests und Browserbedienung bleiben separat zu pruefen.
Die Szenarien dokumentieren beobachtetes Verhalten, darunter Fehler; sie sind
nicht sieben bestandene Regressionstests.

| Szenario | Beobachtung |
|---|---|
| manual_booking_precision | Formularwert CHF 19.99 als 2000 Rappen gespeichert, A-057 |
| manual_booking_outside_year | Datum 2025-06-01 unter Geschaeftsjahr 2026 akzeptiert, A-058 |
| locked_in_review | Service lehnt neue Buchung und Betragsaenderung ab; Bestand unveraendert |
| locked_closed | Dieselben Schreibversuche im abgeschlossenen Jahr abgelehnt |
| move_receipt_out_of_closed_year | Beleg aus abgeschlossenem Jahr 2026 an Buchung im offenen Jahr 2027 verschoben, A-059 |
| read_create_role_matrix | Admin/Schatzmeister: Uebersicht, Detail und Anlageformular erreichbar; Revisor: Lesen erlaubt, Anlageformular 403; normales Mitglied: alle drei 403 |
| private_payment_ownership_repeat | Schuldner kann privaten Zahlungseingang nicht bestaetigen; Glaeubiger einmal erfolgreich, Wiederholung abgelehnt; bezahlt bleibt 2000 Rappen |

Die Rollenmatrix prueft GET-Zugriffe auf drei konkrete Seiten, nicht alle
Schreibaktionen. Die private Zahlungsbestaetigung wurde direkt im Service
geprueft. Jahrssperren gelten in den getesteten Service-Aufrufen; die
Beleg-Reproduktion zeigt, warum daraus keine globale Unveraenderlichkeit
des Jahres abgeleitet werden darf.

## Empfehlungen aus diesem Durchlauf

- Rappen exakt erhalten. Anzeige- oder bewusst gewaehlte Zahlungsrundung von
  gespeicherten Buchungsbetraegen trennen; verbindliche Rundungsregel im
  Fachmodell festhalten. Der aktuelle Formularpfad widerspricht der eigenen
  Dokumentation in `docs/capabilities/accounting.md:150`.
- Geschaeftsjahr und Buchungsdatum gemeinsam validieren, auch bei Bearbeitung
  und Import. Eine bewusst zugelassene abweichende Zuordnung braucht eine
  explizite fachliche Regel und nachvollziehbare Darstellung.
- Sperren fuer Revision/Abschluss auf alle Aenderungswege ausdehnen. Bei
  Verschiebungen sowohl Quelle als auch Ziel pruefen, einschliesslich Belegen.

## Zweiter Durchlauf: Bankimport und Zahlungszuordnung

[BANK_CHECKS.json](BANK_CHECKS.json), `check_bank_workflows.py`, BANK_RUN.txt.
Synthetische CSV-Dateien, Original-Parser und Services, fuer die kritischen
Schreibaktionen Original-Routes. SQLite-Fremdschluessel explizit aktiviert und
verifiziert. Die Imports mit Fehlern sind absichtlich konstruierte Eingaben;
keine Aussage ueber vorhandene produktive Bankdaten oder Konfiguration.
Manuelle CSRF-Pruefungen der Buchungsroute werden mit gueltigem Token passiert.
Der Edit-/Upload-Pfad nutzt die globale Testing-Konfiguration ohne CSRF.

| Szenario | Ergebnis |
|---|---|
| repeat_import_same_reference | Positiv: erneut importierte Referenz als Duplikat erkannt, nur eine Transaktion |
| different_purpose_without_reference | Verschiedene Zahlungszwecke ohne Referenz zusammengelegt, A-063 |
| collective_missing_detail | Ein CHF-40-Detail auf CHF 100 hochgerechnet, obwohl zwei Details angekuendigt, A-064 |
| collective_complete | Positiv: CHF 40 + 60 bleiben erhalten; Sammelzeile nicht separat zu buchen |
| missing_rounding_account_retry | Fehlendes Aufrundungskonto: erster Versuch hinterlaesst CHF 20, zweiter nochmals CHF 20; Import weiter offen, A-060 |
| overpayment_split_and_delete_guard | Positiv: vorhandenes Konto erlaubt CHF 20 + 5; Forderung beglichen; Loeschen des verbuchten Imports abgelehnt |
| outgoing_payment_settles_claim | Ausgaben-POST kann Einnahmeforderung begleichen; UI bietet diese Auswahl nicht an, A-061 |
| booking_member_differs_from_claim | Buchungsmitglied und Schuldner koennen abweichen, A-061; Zahlung fuer Dritte als Fachregel klaeren |
| partial_full_and_repeat | Positiv: CHF 8 und 12 begleichen CHF 20; wiederholte erfolgreiche Buchung abgelehnt |
| edit_imported_booking_amount | Edit-POST setzt Journalbetrag auf CHF 5, Bank/Forderung bleiben CHF 20, A-062 |
| closed_year_import_booking_blocked | Positiv: geschlossenes Jahr blockiert Importverbuchung, keine Buchung/Forderungsaenderung |
| invalid_amount_in_csv | Upload mit ungueltigem Betrag wirft unbehandelten ValueError; keine Teilanlage, A-065 |

Zentrale Empfehlung: Importbewegung, daraus entstehende Buchungen und
Forderungszahlungen als zusammenhaengenden Vorgang behandeln. Derzeit gibt es
einen Link von der Bankbewegung zur Hauptbuchung und einen kumulierten
Zahlungsbetrag in der Forderung; das reicht fuer kontrollierte Ruecknahmen
und Fehlerwiederaufnahme nicht aus. Das spaetere Zielmodell braucht eine
fachliche Entscheidung, noch keine Schemaaenderung in diesem Audit.

## Dritter Durchlauf: Revision, Budget und Berichtsdaten

[REVISION_CHECKS.json](REVISION_CHECKS.json), `check_revision_workflows.py`,
REVISION_RUN.txt. Synthetische SQLite-Daten, Original-Services und Routes.
Push und externe Berichtserstellung in der Rollenmatrix ersetzt; im Fehlerfall
wird gezielt die PDF-Erzeugung zum Scheitern gebracht. Keine echten Nachrichten,
PDFs oder Drive-Dateien erzeugt. Berichtsdaten und Aufrufpfade geprueft,
kein visueller PDF-Test und keine Aussage ueber produktive Archivdateien.

| Szenario | Ergebnis |
|---|---|
| budget_during_review | Budget waehrend Revision per POST veraenderbar, A-066 |
| budget_closed_blocked | Positiv: Budget nach Abschluss unveraendert |
| deactivated_account_closed_report | Konto verschwindet aus historischen Details, Gesamtsumme bleibt, A-067 |
| opposite_directions_same_account | CHF 20 Ausgabe + 5 Eingang ergibt Konto-Ist 25 statt Saldo 15, A-068 |
| closed_year_opening_changes | Vorjahresaenderung veraendert Anfangssaldo eines geschlossenen Jahres, A-069 |
| report_failure_then_retry | Abschluss ohne Bericht; erneutes Bestaetigen startet keine Berichtserstellung, A-070 |
| revision_action_role_matrix | Positiv: 16 Kombinationen pruefen Berechtigung und resultierenden Jahresstatus |

Rollenmatrix: Admin darf alle vier Aktionen. Schatzmeister darf freigeben und
Freigabe zurueckziehen, Revisor darf bestaetigen und Abschluss zuruecknehmen.
Normales Mitglied darf keine dieser Aktionen. Unerlaubte Requests ergeben 403
und lassen den Status unveraendert. Ausgangsstatus je Aktion bewusst gueltig;
alle ungueltigen Statusuebergaenge und konkurrierenden Requests noch offen.

## Vierter Durchlauf: Belege, Kommentare und erneute Freigabe

[RECEIPT_CHECKS.json](RECEIPT_CHECKS.json), `check_receipt_workflows.py`,
RECEIPT_RUN.txt. Original-Routes/-Services mit synthetischen Mitgliedern,
Board-Event, Buchung und Belegen. Drive-Upload/-Download und Ordnerbeschaffung
durch feste Testantworten ersetzt; kein Dateiversand. Der Upload prueft die
App-seitige Verknuepfung und Rueckleitung, nicht die externe Dateivalidierung.
Testing-CSRF global aus; Kommentar-Erledigung mit gueltigem manuellem Token.

| Szenario | Ergebnis |
|---|---|
| member_upload_choices_disclosure | Buchungsbeschreibung und gesperrter Board-Event im Mitglieder-Formular sichtbar, A-071 |
| member_direct_receipt_upload_redirect | Verknuepfter Beleg gespeichert, Weiterleitung fuehrt zu 403, A-072 |
| receipt_download_ownership | Positiv: Admin/Schatzmeister/Revisor/Uploader 200; anderes Mitglied 403, kein Downloadaufruf fuer den abgewiesenen Zugriff |
| revoke_correct_reapprove_history | Korrekturfolge funktioniert; vorherige Bestaetigung und Berichtverweis werden entfernt, A-073 |
| unresolved_comment_approval_and_resolution | Abschluss trotz offenem Kommentar, Erledigung danach durch Schatzmeister; normales Mitglied 403, Regelentscheid A-074 |

Die Korrekturfolge wurde ueber Services geprueft; die Rollenrechte ihrer
Einzelaktionen stehen im dritten Durchlauf. Keine Behauptung, dass alte
Drive-Berichte geloescht werden: nachgewiesen ist der Verlust der App-Verknuepfung.

## Noch offen fuer weitere Durchlaeufe

- Bankimport: restliche Formate/Encodings, Pflichtspalten, Vorzeichen und
  Nachkommastellen, Fremdwaehrung/gemischte Waehrungen, geaenderte Exporte bei
  gleicher Referenz, Jahreswechsel, grosse Dateien, parallele Imports,
  Ignore/Reopen/Delete und Wiederimport. Kein echtes Bankformat vollstaendig validiert.
- Zuordnung von Bankbewegungen und Forderungen: Teil-/Ueberzahlungen,
  Korrekturen/Ruecknahme, Verzicht, andere Forderungstypen, Alias-Mehrdeutigkeit,
  Konten-/Event-Konsistenz und konkurrierende Requests. Erste Teil-/Ueberzahlungs-
  und Wiederholungsfaelle oben geprueft, keine pauschale Vollstaendigkeit.
- Revision/Jahresabschluss: ungueltige Statusuebergaenge, Korrekturfolge im
  Browser/mit echten Berichtsversionen, Kommentarzuordnung zu anderen oder
  ungueltigen Buchungen/Jahren, Parallelitaet und weitere Vollstaendigkeitskriterien.
- Abschlussberichte: PDF-Rendering, lange Inhalte, reale Drive-Fehler,
  Upload erfolgreich/DB-Verknuepfung fehlgeschlagen, Wiederaufnahme und Archivversionen.
- Belege: Upload, ungebundene Belege, Rechte, externe Fehler, Move/Delete,
  Metadaten und Verhalten waehrend laufender Revision.
  Erste Upload-/Downloadrollen oben geprueft; Jahresordner bei Zuordnung zu
  anderem Jahr, Datei-/Groessenvalidierung und Drive/DB-Fehlerkompensation offen.
- Konten/Budget: historische Namens-/Art-/Gruppenaenderungen, gemischte Gruppen,
  Budgetvorschlag/Jahreseroeffnung, ungueltige Betraege und Kontenauswahl.
- Journal/Exporte/Diagramme: Abgleich derselben Daten, Filter, leere und lange
  Listen, Datumsgrenzen, Navigation, Formfehler und responsive Bedienung.

Die frueheren Viewport-Pruefungen der Buchhaltung stehen in BROWSER_REVIEW.md;
sie ersetzen diese fachlichen und rollenbezogenen Restpruefungen nicht.

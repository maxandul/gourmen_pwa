# Events / BillBro / GGL / Bereinigung – vertiefter Teilbericht

Stand 2026-09-07, unveraenderte App-Baseline `bf4d84a`. Durchlauf 02 ist begonnen,
**nicht abgeschlossen**. Dieser Teilbericht prueft zentrale Mutationen und ihre
Folgewirkungen. Er ersetzt weder das vollstaendige Route-Review noch die Browsermatrix.

## Methode und Belege

`check_event_workflows.py` nutzt Original-Models, Services und Flask-Routes.
18 getrennte Szenarien mit jeweils frisch erzeugter SQLite-In-Memory-Datenbank,
drei synthetischen Mitgliedern, lokalen Events und synthetischen Forderungen.
Keine Produktionsdaten, kein Versand, keine externen API-Aufrufe; dotenv deaktiviert
und ausgehende Python-Sockets gesperrt wie im bisherigen Audit-Testaufbau.
Ergebnisse: [EVENT_WORKFLOW_CHECKS.json](EVENT_WORKFLOW_CHECKS.json).

Die Faelle sind Audit-Reproduktionen, keine 18 bestandenen Regressionstests:
mehrere demonstrieren absichtlich fehlerhaftes Verhalten. CSRF und Rate-Limit
sind in Testing ausgeschaltet; SQLite beweist keine PostgreSQL-Typ-/Constraint-
oder Migrationskompatibilitaet. Exceptions werden fuer das Protokoll aufgefangen;
ein 302 allein beweist keinen fachlichen Erfolg. Gespeicherte Folgezustaende
wurden deshalb nach den Requests erneut aus der Datenbank gelesen.

## Gepruefte Szenarien

| Fall im JSON | Erwartung / Beobachtung | Befund |
|---|---|---|
| exact_guess_zero_diff | Exakter Tipp gewinnt nicht, sondern wird Letzter | A-021 |
| reset_retains_points | Rechnung/Rang weg, Punkte bleiben | A-022 |
| closed_attendance_changes_claim_stays | Organisator meldet ab, Forderung bleibt | A-023 |
| member_rsvp_after_final | Mitglied kann abgeschlossene Teilnahme umschalten | A-023 |
| cleanup_rsvp_after_final | Bereinigung kann abgeschlossene Teilnahme aendern | A-023 |
| closed_guess_regular_rejected | Regulaere Tippaenderung bleibt gesperrt | positiver Gegenbeleg |
| closed_guess_organizer_accepted | Organisator aendert Tipp, Rang/Punkte bleiben alt | A-022, Redirect auch A-001 |
| payment_change_with_partial_claim | Zahlweg Mitglied, teilbezahlter Posten weiter an Verein | A-024 |
| bill_input_abc | Unbehandelte Decimal-Exception | A-025 |
| bill_input_NaN | Unbehandelte ValueError | A-025 |
| bill_input_-10 | Negativer Rechnungsbetrag gespeichert/ausgewertet | A-025 |
| bill_input_0 | Null gespeichert, Folgeschritte behandeln sie als fehlend | A-025 |
| edit_audience_and_clear_fields | Neuer Sichtbarkeitswert und Leeren bleiben wirkungslos | A-026/A-027 |
| cleanup_nonfirst_yes_loses_focus | Zusage Event 1 leitet zu Event 2 | A-028 |
| rounding_three_equal_shares | Feste 5-Rappen-Rundung statt gespeicherter Regel | A-031 |
| board_visibility_denies_nonboard | Detail und BillBro-POST liefern 403 | positiver Gegenbeleg |
| cleanup_undo_deletes_later_guess | Undo loescht zwischenzeitlich gespeicherten Tipp mit | A-029 |
| cleanup_query_scaling | 7 vs. 87 SELECTs bei 1 vs. 21 Kandidaten | A-030 |

## Vergleich der fachlichen Zustandsregeln

| Vorgang | Gegenwaertige Regel | Luecke / zu vereinheitlichen |
|---|---|---|
| Mitglied speichert Tipp/Ess-Typ | Teilnahme erforderlich, `billbro_closed` sperrt | Zahlenvalidierung; Ergebnis bei spaeter Wiedereroeffnung |
| Organisator erfasst Tipp | Organisator + Teilnahme erforderlich | Keine gleiche Abschlusssperre, kein Neuberechnen |
| Rechnung erfassen | Organisator, Betrag vorhanden | Keine positive/finite Validierung; vorhandene Finals gesondert pruefen |
| Total bestaetigen | Organisator + Rechnung | Final und Forderungen in getrennten Commits; Fehler-Injektion offen |
| Zahlweg speichern | Organisator, privater Zahler muss teilnehmen | Konflikt bei bestehenden Zahlungen bleibt unsichtbar |
| Teilnahme umschalten | Sichtbarkeit + Login | Kein gemeinsamer Vertrag mit bereits finaler Abrechnung |
| Anwesenheit setzen | Organisator | Unterschiedliches Loeschen von Folgefeldern, keine Claim-Synchronisierung |
| Bereinigung Zusage/Absage | Sichtbarkeit + vergangenes Datum | Abschlusszustand unbeachtet; Index/Fokus geht verloren |
| Bereinigung Undo | Session-Snapshot fuer aktuelles Mitglied | Kein Versionsvergleich mit neuerem Datenstand |
| BillBro Reset | Organisator | Punkte bleiben; bezahlte Claims bleiben laut Service bewusst bestehen |

Ein gemeinsamer fachlicher Service fuer diese Uebergaenge ist die Empfehlung.
Die Oberflaeche sollte dessen erlaubte Aktionen darstellen. Nur Buttons zu
verstecken wuerde die reproduzierten Original-POST-Probleme nicht beheben.
Details, Risiken und Abnahmekriterien stehen in A-021 bis A-047.

## Fortsetzung: Bewertungen, Erstellung, Planung und GGL-Abgleich

Weitere **17 isolierte Szenarien** in `check_event_followup.py`, Ergebnisse in
[EVENT_FOLLOWUP_CHECKS.json](EVENT_FOLLOWUP_CHECKS.json). Gleiche Isolation und
Grenzen wie oben. Zusammen 35 Workflow-Szenarien, weiterhin kein vollstaendiger
Modulabschluss. 10 weitere Befunde A-032 bis A-041; darunter zwei ausdruecklich
offene fachliche Entscheidungen (Bewertungs-Leserecht und Bewertungszeitraum).

| Fall | Ergebnis |
|---|---|
| rating_next_external_redirect | Ungeprueftes externes next-Ziel im Location-Header, A-035; nicht aufgerufen |
| rating_invalid_loses_input | Ungueltiger Score korrekt abgelehnt, eingegebener Text verloren, A-036 |
| rating_future_event | Bewertung in 30 Tagen bereits speicherbar; Regelentscheidung A-041 |
| rating_nonparticipant_access_difference | API verweigert Lesen, Event-HTML zeigt Freitext; Schreiben gesperrt, A-037 |
| organizer_change_deletes_data_and_leaves_absence | Alte Teilnahme mit Tipp/Anteil geloescht, neue Absage bleibt, A-033 |
| create_board_audience_enforced | Positiv: Vorstandssitzung erzwingt board trotz eingereichtem all; Organisator angemeldet |
| create_invalid_places_number | Ungueltige Koordinate wirft ValueError, A-039 |
| year_planning_duplicate_and_repeat | SQLite: 1 → 13 → 25 Events, A-034; PostgreSQL-Gegenpruefung offen |
| ggl_fractional_and_tie_view_disagreement | Tabelle Rang 1/1, Performance 1/2; interner Kontext schneidet halbe Punkte ab, A-032 |
| event_type_change_retains_ggl_scores | Ausflug behaelt GGL-Punkte und Renn-Eintrag, A-040 |
| ggl_inactive_member_views | Inaktiv in Tabelle entfernt, im Rennen enthalten, A-040 |
| admin_ui_actions_denied_by_routes | Gegenbeleg: nur Admin, nicht Organisator; kein Zahlweg-Formular im HTML, Rechnungseingabe verweigert |
| rating_repeated_post_no_duplicate | Positiv: zweiter sequentieller POST erzeugt keine zweite Bewertung und ueberschreibt die erste nicht |
| rating_clears_matching_cleanup_undo | Positiv: gespeicherte Bewertung entfernt passenden Undo-Snapshot; A-029 bleibt fuer spaetere BillBro-Eingabe bestehen |
| edit_today_switches_past_classification | Gleiches Datum gespeichert, Zeit auf Mitternacht gesetzt, is_past wechselt auf True, A-038 |
| planning_rejects_nonadmin_and_invalid_year | Positiv: kein neues Event fuer normales Mitglied oder Jahr 9999 |
| event_date_updates_ggl_season | Positiv: Datumswechsel auf 2025 aendert season; Punkte verschwinden aus 2026 und erscheinen in 2025 |

Praezisierung des GGL-Befunds: `current_stats.total_points` speist die sichtbare
Punkte-Kachel korrekt. Nur `performance_context.user_points` wird abgeschnitten;
sichtbar belegt ist der abweichende Rang, nicht eine falsche Punkte-Kachel.
Der BillBro-Tab ueberschreibt sein `is_organizer` lokal mit der tatsaechlichen
Organisator-ID. Aus der weiter gefassten Variable in `events.detail` allein laesst
sich deshalb kein Fehler bei angezeigten Admin-Aktionen ableiten.

## Fortsetzung: Datenfluss, Loeschen, Ratings-Ownership und Reminder

Weitere **9 Szenarien**, zusammen nun **44 Workflow-Szenarien**:
`check_event_boundaries.py`, [EVENT_BOUNDARY_CHECKS.json](EVENT_BOUNDARY_CHECKS.json).
Tests nutzen dieselbe Isolation, bei Reminder-Pruefungen zusaetzlich explizite
Mocks des gesamten Versandservices oder von `_send_with_cleanup`. Es wurde
keine Nachricht versendet. Ein Transportaufruf belegt hier Empfaengerselektion
und Payload, niemals echte Zustellung.

| Fall | Ergebnis |
|---|---|
| board_event_public_and_stats_visibility | Detail 403/Archiv ohne Name, aber Public-Hitlist und Statistik mit Restaurantname; A-042 |
| disabled_ratings_statistic_policy | Public ausgeschlossen, interne Bewertungsstatistik weiter vorhanden; A-047 |
| nonorganizer_legacy_reminder_permission | Legacy-POST erreicht Mock, neue API verweigert denselben Benutzer mit 403; A-043 |
| rsvp_reminder_unanswered_row_excluded | Unbeantwortete vorhandene Zeile ausgelassen, fehlende Zeile erinnert; A-044 |
| rating_reminder_disabled_inactive_and_target | Deaktiviertes Rating dennoch beworben, Ziel 404; inaktives Mitglied korrekt ausgelassen; A-045 |
| delete_without_dependencies | Admin loescht zukuenftiges Event samt Teilnahme erfolgreich |
| delete_with_rating_partial_commit | Event-Loeschen scheitert, Teilnahme bereits weg; A-046 |
| delete_role_and_past_guards | Nichtadmin und vergangenes Event gesperrt, Daten unveraendert |
| rating_ownership_edit_delete | Fremde Bewertung bleibt geschuetzt; eigene bearbeitet/geloescht, auch ohne Participation |

Die letzte Beobachtung ist eine fachliche Rechtefrage: nachtraegliches Verwalten
der eigenen Bewertung ist moeglich, obwohl das Erstellen Teilnahme verlangt.
Dies ist kein nachgewiesener Zugriff auf fremde Daten und wird nicht als neuer
Sicherheitsfehler gezaehlt. Die Quelle des Fehlers beim Loeschen ist dagegen
durch den verbleibenden DB-Zustand belegt, nicht nur durch einen Fehlerstatus.

Testhygiene: Bei Wechsel zwischen mehreren synthetischen Clients in einem
aeusseren App-Kontext wird Flask-Logins gecachte Identitaet geloescht. Dadurch
bleibt die Ownership-Gegenpruefung unabhaengig vom vorherigen Testclient.
Zwei vorangehende Skriptabbrueche betrafen einen falschen Ergebnis-Key im
Audit-Skript (`charts`/`charts_payload` statt `charts_json`); sie sind keine
App-Befunde. Das gespeicherte JSON stammt aus dem vollstaendigen erfolgreichen Lauf.

## Weitere Codebeobachtungen – noch keine abgeschlossenen Befunde

- `Participation.rank` und `points` sind im Model Integer, fractional ranking
  produziert halbe Werte. SQLite kann andere Speichereigenschaften als PostgreSQL
  haben. Typen der produktiven Migrationen und Roundtrip mit PostgreSQL pruefen;
  hier keine Behauptung ueber bereits entstandene produktive Datenverluste.
- GGL-Saisonqueries filtern nicht einheitlich nach Monatsessen, publiziertem
  Event und ausgewerteter Rechnung. Typwechsel nun reproduziert (A-040),
  Saisonwechsel positiv geprueft; Publikation und Restmatrix bleiben offen.
- `ggl.index` baut Saisonstatistik-Rang per Listenposition statt geliefertem
  Gleichstands-Rang. Ob dies in der aktuellen Oberflaeche genutzt wird, bleibt offen.
- Organisatorwechsel in `events.edit` loescht die Participation des alten
  Organisators komplett. Inzwischen als A-033 reproduziert; bereits bezahlte
  Forderungen und Buchungen bei einem Wechsel noch gesondert pruefen.
- `billbro.export_pdf` leitet auf den nicht vorhandenen Endpoint `billbro.results`.
  Registrierte Altpfade vollstaendig gegenpruefen (Erweiterung von A-001).
- `MoneyService.validate_franken_amount` referenziert `DecimalException`, ohne
  sie zu importieren. Nutzung und weitere Geldkonvertierungen noch erfassen.
- `SecurityService.log_audit_event` committet die gemeinsame Session. Bei
  `enter_bill` fuer Nicht-GGL-Events ist dadurch das Audit-Logging Teil des
  Persistenzpfads. Transaktionsgrenzen und fehlgeschlagene Logs/Claim-Sync pruefen.
- UTC-Kalendertage in Bereinigung/Event-Helfern gegen die fachliche Schweizer
  Tagesgrenze und iCal-Zeiten vergleichen. Noch kein reproduzierter Zeitzonenbefund.

## Verbleibender Umfang dieses Moduldurchlaufs

- Events: Archiv-Such-/Pagination-Grenzen, Statistikgewichtung bei vielen/laengeren
  Daten, weitere Loeschabhaengigkeiten (Claims/Buchungen/Drive), Places-Fehler-
  kombinationen und Konkurrenz bei Planung/Erstellung. Grundpfade von Loeschen,
  Reminder-Berechtigung und Statistik-Audience inzwischen geprueft.
- BillBro: alle Phasenkombinationen, keine/eine/viele Teilnahmen, unvollstaendige
  Ess-Typen, Wiedereroeffnung, Wiederholung und Konkurrenz, weitere Altpfade,
  Claims bei Fehlern und bereits bezahlten Betraegen.
- GGL: fractional ranking auf PostgreSQL, weitere Gleichstaende/Leersaisons,
  Publikationsgrenzen, Insight-Texte und Diagramm-Frontend. Tabellen-/Performance-
  Vergleich, Inaktivierung und einfacher Saisonwechsel inzwischen geprueft.
- Bereinigung: Rating-Fehlerkontext in der Queue, Skip/Back am Listenende,
  Beitritts-/Veroeffentlichungsgrenzen, veraltetes Undo nach Rechteaenderungen.
- Rollen vollstaendig: Admin, Organisator, Vorstand, Teilnehmer, Nichtteilnehmer,
  deaktiviert/ausgeloggt. Bisher nur gezielte positive/negative Faelle.
- Browser: alle obigen Form- und Fehlerzustaende, Tastatur, kleine/grosse Viewports.
- Reminder/Betrieb: wiederholte Cron-Ausfuehrung, Wochen-/21-Tage-Fenster,
  Audience nach Aenderungen, Push-Subscription-Bereinigung und reale Zustellung.

Naechster Modulschwerpunkt: Merch. Die oben verbleibenden Event-/Betriebsfaelle
bleiben im Register offen fuer spaetere Gegenpruefung; das Modul wird nicht
vorzeitig als abgeschlossen markiert.

Weiterhin keine App-Reparatur, Migration oder Neuberechnung vorgenommen.

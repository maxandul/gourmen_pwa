# Dokumentverwaltung – erster vertiefter Durchlauf

Stand 2026-09-20. Teilpruefung, Modul nicht abgeschlossen.
Erster Durchlauf: sieben Szenarien, A-091 und Erweiterungen A-035/A-071.
Zweiter Durchlauf: sieben weitere Szenarien, A-092/A-093 und Erweiterung A-091.
Insgesamt 14 Szenarien; Matrix-Unterfaelle nicht zusaetzlich gezaehlt.
App und externe Dateien unveraendert.

## Nachweise und Grenzen

[DOCS_CHECKS.json](DOCS_CHECKS.json), `check_docs_workflows.py`, DOCS_RUN.txt.
Original-Routes und fuer Rename/Move/Auto-Sync Original-Service-Logik;
Drive-Transport/Metadaten ersetzt. Synthetische Mitglieder, Dokumentzeile und
Board-Event, SQLite im Arbeitsspeicher. Netzwerk blockiert, kein echter Upload,
Move, Rename, Download oder Loeschvorgang. Einige reine Route-Grenzen ersetzen
die gesamte Service-Methode; der jeweilige Testaufbau ist im Skript ersichtlich.

Globaler Testing-CSRF-Schutz aus. Die manuelle Docs-CSRF-Pruefung ist aktiv:
gueltige signierte Tokens fuer Aktionen, fehlender Token im Negativfall.
Rate-Limit, reale Google-Berechtigungen und PostgreSQL nicht nachgewiesen.

| Szenario | Ergebnis |
|---|---|
| csrf_and_feature_guards | Positiv: fehlender Token 403, Feature aus 404; keine Rename-Service-Aufrufe |
| delete_role_archive_confirmation_guards | Positiv: Member 403; Admin ausserhalb Archiv oder mit falschem Dateinamen abgewiesen; keine Loeschaufrufe |
| rename_error_external_redirect | Ungeprueftes next leitet nach Fehler extern weiter, Erweiterung A-035 |
| remote_rename_http_error | API-HttpError propagiert statt behandeltem DriveError, A-091 |
| detail_metadata_error_after_sync | Metadatenfehler nach Sync-Versuch propagiert, A-091 |
| move_failure_preserves_db_parent | Positiv: behandelter DriveError, DB-Ordner unveraendert |
| docs_upload_event_choices_visibility | Board-Eventlabel fuer unberechtigtes Mitglied sichtbar, Erweiterung A-071 |

Das Drive-Konzept erlaubt Mitgliedern ausdruecklich gemeinsame Dokumentpflege
(«alle sehen alles»). Daraus wird hier kein pauschaler Rechtebefund abgeleitet.
Die Eventauswahl muss trotzdem die getrennte Event-Sichtbarkeitsregel beachten.
Drive- vs. Buchhaltungs-Belegrechte sind als fachliche Abgrenzung noch zu pruefen.

## Empfehlungen aus diesem Durchlauf

Einheitlichen Fehlervertrag fuer externe Dienste umsetzen: Die Route muss
erkennen koennen, ob eine Aktion fehlgeschlagen ist, bereits teilweise wirksam
wurde oder nur die nachfolgende Anzeige scheitert. Auswahlfelder und Rueckleitungen
an dieselben Regeln wie die uebrige App binden. Schutzbedingungen beim Loeschen
sind in den geprueften Faellen sinnvoll und sollten erhalten bleiben.

## Zweiter Durchlauf: Upload, Zielordner und Sync-Grenzen

[DRIVE_BOUNDARY_CHECKS.json](DRIVE_BOUNDARY_CHECKS.json),
`check_drive_boundaries.py`, DRIVE_BOUNDARY_RUN.txt. Original-Services mit
synthetischen API-Antworten; SQLite-Fremdschluessel aktiviert und verifiziert.
Keine echten Dateien, Netzwerkverbindungen oder Produktivkonfigurationen.
Groessenvalidierung anhand Zahlenwerten, keine 100-MB-Datei angelegt.

| Szenario | Ergebnis |
|---|---|
| folder_target_matrix | Root/direkter/verschachtelter Ordner akzeptiert; ausserhalb, Zyklus, Papierkorb und Nicht-Ordner abgelehnt |
| upload_validation_matrix | Gueltiger PDF-Metadatensatz akzeptiert; leer, zu gross, verbotener MIME-Typ und leerer Titel abgelehnt |
| invalid_event_upload_compensation | Erst Uploadversuch, dann FK-Fehler und Kompensationsaufruf; keine neue DB-Zeile, A-092 |
| sync_permission_error_preserves_cache | 403 erhaelt Dokumentzeile, Fehlernotiz im Service-Ergebnis |
| trash_restore_loses_uploader | Papierkorb/Restore/Resync verliert Uploaderzuordnung, A-093 |
| resync_second_page_failure | Seite 1 gespeichert, Seite 2 scheitert; alte und neue Zeile erhalten, Erweiterung A-091 |
| sync_parent_drift_preserves_uploader | Ordnerabweichung wird korrigiert, Uploader bleibt erhalten |

Die Zielordner-Matrix prueft `assert_is_folder_in_drive`, keine pauschale
Zugriffssicherheit aller Listen-/Downloadwege. MIME-Pruefung belegt die
Allowlist, keine Inhalts-/Signaturerkennung. Partielle Sync-Commits sind nicht
automatisch fehlerhaft, brauchen aber einen definierten Wiederaufnahmevertrag.

## Offene Fortsetzung

- Root-/Ordnergrenzen aller Lesewege, verschwundene Dateien, Suche und
  Pagination; Zielordner-Service und einfache Parent-Korrektur oben geprueft.
- Upload: erlaubte Formate, Groessen, SVG-Bereinigung, Dateinamenkollisionen,
  verborgene Eventreferenzen, wiederholter Upload und scheiternde Kompensation.
  Unbekannte Eventreferenz und Validierungs-Matrix oben geprueft.
- Rename/Move/Archiv/Restore/Trash: erfolgreiche Service-Ablaeufe, externe
  Fehler, API erfolgreich/DB fehlgeschlagen, Retry und parallele Aktionen.
- Auto-Sync/Resync: 404 vs. Rechteverlust, entfernte/verschobene Dateien,
  Cache-/Audit-Historie, Abbruch und Wiederaufnahme grosser Bestandsabgleiche.
- Detailansicht/Download: Fehler bei Folgeabfragen, fehlende Konfiguration,
  Dateitypen, Dateinamen, Links und erreichbare Rueckleitungen.
- Vollstaendige Rollen-/Statusmatrix, CSRF aller Aktionen, reale Feature-
  Konfiguration und notwendige Abgrenzung gegen Buchhaltungsbelege.
- Browser: leere/grosse/lange Bestandslisten, Suche/Filter, Picker, Upload-
  Fortschritt, Abbruch/Fehlererhalt, mobile und Tastaturbedienung.

## Browser-Nachtrag: Upload und verschachtelter Picker

B-41 bis B-44 pruefen synthetischen zweistufigen Ordnerbaum, Enter-Auswahl,
Escape-Rueckkehr, Entwurfserhalt und sichtbaren Ladefehler. A-126 zu fehlenden
semantischen Zustaenden. Positive Fokus-Rueckkehr im nativen Dialogstapel.
Kein echter Upload oder eingereichter Ordner-ID-Nachweis; Root-Fehler und
weitere Dialog-/Rollen-/Datenzustaende bleiben offen. BROWSER_REVIEW.md.

## Upload-Fehlernachtrag

B-45/B-46 bestaetigen verlorenen Titel bei fehlender Datei (A-127) und fehlende
Rueckmeldung beim initialen Root-Ladefehler (A-128). Der Unterordnerfehler B-44
ist dagegen sichtbar behandelt. Originalroute/Controller in lokaler Fixture;
keine reale Datei und kein echter Drive-Ausfall. Weitere Transport-/Dateityp-/
Groessenfehler und erneuter Versuch nach Erholung bleiben offen.

## Nachtrag: Wiederaufnahme und Ordnerhierarchie

B-47 schliesst den gezielten Wiederholungsfall nach einmaligem Root-503 ab:
erneuter Klick erfolgreich, Titel erhalten. B-48 bestaetigt falsch platzierte
Unterordner (A-129), B-49 eine weiter aktive, nach Zuklappen unsichtbare Auswahl.
Empfehlung: Kinder direkt unter ihrem Elternordner und aktuelles Ziel stets
sichtbar anzeigen. Die Uebernahme selbst zeigt im Test den richtigen Zielnamen.
Keine Datei hochgeladen; tiefere/grosse Baeume und weitere Fehlerwege offen.

## Nachtrag: Unabhaengige Zweige und leere Unterordner

B-50 bis B-52 pruefen gleichzeitig einen erfolgreichen und einen fehlerhaften
Zweig: getrenntes Zuklappen funktioniert; Zu-/Aufklappen loest einen erneuten
Ladeversuch aus. Leere Unterordner erhalten keine ausdrueckliche Rueckmeldung
(Ergaenzung A-126). Weiterhin 129 Befunde. Wiederholung bei fortbestehendem
Fehler ist kein Nachweis einer erfolgreichen Erholung. Zwei erfolgreiche
befuellte Nachbarzweige und verzoegerte Antworten bleiben offen.

## Asynchrone Picker-Ablaufpruefung

PICK-01 bis PICK-04 fuehren den unveraenderten Controller mit minimalem
synthetischem DOM und manuell aufgeloesten Fetch-Promises aus. Beleg:
[PICKER_ASYNC_CHECKS.json](PICKER_ASYNC_CHECKS.json), Skript check_picker_async.cjs.

| ID | Ablauf | Ergebnis |
|---|---|---|
| PICK-01 | Zwei befuellte Nachbarzweige, Antworten B vor A, dann A zuklappen | Beide Inhalte vorhanden, B bleibt beim Zuklappen von A erhalten. Hierarchiereihenfolge A-129 weiterhin falsch. |
| PICK-02 | Zweig laden, zuklappen, neu laden; neue Antwort vor alter | Nur neuer Inhalt im angehaengten Baum; alte Antwort schreibt in entfernten Container. |
| PICK-03 | Zweimal Oeffnen vor Root-Antwort, Antworten rueckwaerts | Zwei Root-Zeilen; A-130. |
| PICK-04 | Zweimal Oeffnen, erste Antwort, Schliessen, zweite Antwort | Controller ruft erneut showModal auf; A-130. |

Vier Ablaufproben erfolgreich ausgefuehrt, insgesamt 130 Befunde. Dies schliesst
die gezielten Controllerfaelle, nicht deren Browser-Abnahme: native Dialoge,
Fokus, reale Latenzen, tiefe/grosse Baeume und Rollenmatrix bleiben offen.
Kein App-Code geaendert, kein Upload und keine externe Verbindung. Der minimale
DOM-Ersatz ist kein allgemeines Testframework und prueft keine CSS-Darstellung.

## Browser-Bestaetigung des Root-Rennens

B-53/B-54 bestaetigen A-130 mit nativen Dialogen im lokalen Browser: zwei
Root-Zeilen und ungewolltes Wiederoeffnen nach Schliessen, einschliesslich
Fokuswechsel zurueck in den Picker. BROWSER_REVIEW.md und
browser/docs-root-race.json enthalten Ablauf, synthetische Verzoegerungen und
Grenzen. Damit ist die Browser-Bestaetigung fuer PICK-03/04 ergaenzt; die
weiteren PICK-01/02-Ablaufvarianten bleiben nur isoliert geprueft.

## Suchdurchlauf vom 2026-09-21

Acht isolierte Gruppen in [DOCS_SEARCH_CHECKS.json](DOCS_SEARCH_CHECKS.json),
reproduzierbar mit check_docs_search.py. Originalroutes/templates fuer sechs
Renderproben; Originalsuchservice mit synthetischen API-Seiten fuer zwei
Paginierungsproben. SQLite im Speicher und blockiertes Netzwerk.

| Gruppen | Ergebnis |
|---|---|
| root_empty / folder_empty | Echte leere Suche zeigt Keine Treffer ohne Fehlerwarnung, Suchbegriff bleibt im Feld. |
| root_error / folder_error | Warnung und Keine Treffer gleichzeitig; A-132. Suchbegriff bleibt erhalten. |
| root_short_query | Direkter GET mit einem Zeichen fuehrt keine Suche/Ordnerabfrage aus, behauptet dennoch leeren Root-Bestand; A-132. |
| root_hit_folder_link | Treffer verlinkt auf dessen Ordner ohne Suchparameter. Suchkontext wird nicht im Link mitgegeben. |
| scope_target_after_50_global_hits | Passender Treffer auf Folgeseite wird nicht abgefragt; A-131. |
| scope_target_after_49_global_hits | Positivkontrolle: Folgeseite gelesen und passender Treffer gefunden. |

Ruecknavigation: Der Template-Link Zurueck zu Dokumente fuehrt ebenfalls auf
den Einstieg ohne Suchparameter. Empfehlung: Rueckkehr zum Suchergebnis mit
Begriff anbieten, wenn der Ordner aus einer Suche geoeffnet wurde. Dies ist
eine Struktur-/UX-Beobachtung, kein Nachweis defekter Browser-Zuruecknavigation.

Insgesamt 132 Befunde. Acht Gruppen ergaenzen die bisherigen 14 fachlichen
Dokumentszenarien, Dialog-/Pickerproben weiterhin separat. Keine Dateien oder
Produktivdaten veraendert. Browserdarstellung, reale Google-Suchsemantik,
Suchbudget/Latenz und tief verschachtelte Baumgrenzen bleiben offen. Das Feld
query_preserved in den Renderproben prueft speziell value="Audit"; false bei
root_short_query trifft keine Aussage ueber den Erhalt von A.

## Zweiter Suchdurchlauf vom 2026-09-21

Sechs weitere Gruppen mit Originalsuch- und Originalpfadmethode;
nur Google-Transport synthetisch. [DOCS_SEARCH_BOUNDARY_CHECKS.json](DOCS_SEARCH_BOUNDARY_CHECKS.json)
und check_docs_search_boundaries.py. Insgesamt jetzt 28 fachliche
Dokumentszenarien, Dialog-/Pickerproben weiterhin separat.

| Gruppe | Ergebnis |
|---|---|
| direct_nested_sibling_parentless_scope | Direkter und verschachtelter Treffer enthalten; Nachbarzweig und Datei ohne Elternordner ausgeschlossen. Pfadreihenfolge korrekt. |
| apostrophe_backslash_unicode | Rand-Leerzeichen entfernt, Apostroph/Backslash escaped, Umlaut erhalten; Kontrolle der erzeugten Anfrage, keine echte Google-Parserpruefung. |
| empty_page_with_continuation | Leere API-Seite mit nextPageToken wird weitergelesen, Treffer auf Folgeseite gefunden. |
| second_page_http_error | HTTP-403 auf Folgeseite propagiert als HttpError; Erweiterung A-091. |
| breadcrumb_http_error | HTTP-403 beim Trefferpfad propagiert als HttpError; Erweiterung A-091. |
| fifty_hits_same_two_level_parent | 50 Treffer: 1 Suchabfrage plus 100 Pfad-Metadatenabfragen, A-133. |

Empfehlung: Pfade pro Suche wiederverwenden und denselben Fehlervertrag fuer
Suchseiten und nachgeladene Metadaten einsetzen. Die Positivkontrollen beheben
A-131 nicht: Ordnerfilterung ist innerhalb der beruecksichtigten Roh-Treffer
korrekt, kann aber weiterhin spaetere passende Ergebnisse verpassen.

Keine echten Drive-Zugriffe oder gemessenen Ladezeiten. Keine neue Route-/
Browserabnahme, kein Beleg fuer vollstaendige Such-/Rechteabdeckung. Reale
Google-Suchsemantik, grosse/tiefe Baeume, Cache-Invalidierung und gemischte
Fehler bleiben offen. Insgesamt 133 Befunde.

## Aktionsvergleich vom 2026-09-21

Quellen: templates/docs/folder.html, detail.html, _drive_quick_modals.html,
static/js/v2/docs-quick-actions.js und backend/routes/docs.py. Liste und Detail
verwenden bereits dieselben vier Dialoge und denselben Controller. Keine zweite
Implementierung fuer eine spaetere Vereinheitlichung erfinden.

| Aktion | Vorbelegung / Abbruch im Code | Nach behandeltem Fehler | Erfolgsrueckleitung der Route |
|---|---|---|---|
| Umbenennen | Namensstamm aus aktuellem Dateinamen; erneutes Oeffnen setzt Eingabe zurueck | Redirect ohne neuen Namen | next, in beiden Templates Quellordner |
| Verschieben | Leeres Ziel bei jedem Oeffnen | Redirect ohne gewaehlt gebliebenes Ziel | next, im Template Quellordner |
| Archivieren | Allgemeiner Hinweis ohne Dateiname | Redirect mit Fehlermeldung | konfigurierter Archivordner |
| Wiederherstellen | Leeres Ziel bei jedem Oeffnen | Redirect ohne gewaehlt gebliebenes Ziel | gewaehlter Zielordner |

Die Schliessen-/Abbrechen-Buttons sind type=button und schliessen im Controller
den naechsten Dialog; dieser Pfad sendet im Code kein Formular. Escape und
Fokus-Rueckkehr hier nicht im Browser geprueft. Unterschiedliche Ziele nach
Erfolg sind zunaechst UX-Entscheidung, kein nachgewiesener Fachfehler: definieren,
ob die App am Ursprungsort bleibt oder die verschobene Datei am Ziel zeigt.

Zehn isolierte Routenproben in [DOCS_ACTION_CHECKS.json](DOCS_ACTION_CHECKS.json),
check_docs_actions.py: je Erfolg/DriveError fuer vier Aktionen sowie fehlendes
Ziel fuer Move/Restore. Originalroutes mit signiertem manuellem CSRF-Token,
saemtliche Mutationsservices ersetzt. Alle erwarteten Redirects/Flash-Kategorien
bestaetigt; fehlendes Ziel ruft keinen Service auf. Keine echte Datei veraendert.
Der erste Skriptstart scheiterte vor App-Erzeugung am Importpfad; nach Laden des
bestehenden Audit-Bootstraps bestanden alle zehn Gruppen.

Neuer A-134 zum fehlenden Dateikontext; A-127 um fehlenden Entwurfserhalt nach
Aktionsfehlern erweitert. Insgesamt 134 Befunde und 38 fachliche Dokumentgruppen.
Die Erfolgsmocks beweisen keine Storage-/DB-Konsistenz oder korrekte Berechtigung
aller Aktionen. Echte Service-Erfolgsablaeufe, Teilfehler, Wiederholung und die
Browserabnahme der Aktionsdialoge bleiben offen.

## Browser-Nachtrag zu den Dateiaktionen

B-55 bis B-58 pruefen vier Gruppen mit zwei synthetischen Dateizeilen als
regulaeres Mitglied. Original-Listen-/Dialogtemplates und Controller:
Abbruch bei Rename/Archive/Restore und Escape bei Move funktionieren;
Rename-Neuoeffnung setzt den bewusst verworfenen Entwurf zurueck. Beta bekommt
den eigenen Namensstamm und die richtige ID in Rename-/Restore-Formularzielen.
A-134 fuer drei Dialoge im Browser bestaetigt. Weiterhin 134 Befunde.
Keine echten Dateien, kein Submit; Detailansicht, verschachtelter Picker in
diesen Aktionen, mobile Breiten und Fehlerwiederaufnahme weiter offen.
Beleg: browser/docs-actions-followup.json und BROWSER_REVIEW.md.

## Service-Lifecycle vom 2026-09-21

Acht Gruppen in [DOCS_LIFECYCLE_CHECKS.json](DOCS_LIFECYCLE_CHECKS.json),
check_docs_lifecycle.py. Originale Aktionen, Zielvalidierung, Archivpruefung,
Kollisionsabfrage und Audit-Writer; nur Drive-Transport durch zustandsbehaftete
Simulation ersetzt. App-Zustand nach expire_all erneut aus SQLite gelesen.

| Gruppe | Ergebnis |
|---|---|
| rename_success | Dateiendung erhalten, simulierter Name geaendert, genau ein DOCUMENT_RENAMED mit altem/neuem Namen. |
| move_success | Simulierter Drive-Elternordner und DB-Ziel stimmen ueberein; ein DOCUMENT_MOVED. |
| archive_success | Ziel Archiv in beiden Systemen; ein DOCUMENT_ARCHIVED, kein zusaetzliches Move-Log. |
| restore_success | Ziel ausserhalb Archiv in beiden Systemen; ein DOCUMENT_RESTORED, kein zusaetzliches Move-Log. |
| same_parent_noop | Bereits konsistentes Ziel: kein externer Move und kein Aktionslog. |
| same_remote_target_stale_db | Drive bereits am Ziel, DB noch Quelle: DB bleibt veraltet, A-136. |
| restore_into_archive | Kein Move, trotzdem Restore-Log; Datei bleibt archiviert, A-135. |
| restore_into_archive-child | Move in Archiv-Unterordner plus Restore-Log; Datei bleibt archiviert, A-135. |

Jetzt 46 fachliche Dokumentgruppen und insgesamt 136 Befunde. Normale
Service-Erfolgswege in diesen Datenkonstellationen bestaetigt; keine pauschale
Abnahme der Aktionen. Teilfehler nach externem Erfolg, Audit-/DB-Fehler,
Parallelitaet, Kollisionsvarianten und reale Google-/Postgres-Semantik offen.
Keine echten Dateien oder Produktionsdaten veraendert.

## Teilfehler und Wiederaufnahme vom 2026-09-21

Fuenf Gruppen in [DOCS_PARTIAL_FAILURE_CHECKS.json](DOCS_PARTIAL_FAILURE_CHECKS.json),
check_docs_partial_failures.py. Originale Services und Audit-Writer, synthetischer
Drive mit Zustand. Commit-Fehler vor Commit-Aufruf injiziert; Audit-Fehler als
OperationalError im echten ORM-Insert-Flush. Explizites Rollback vor Wiederaufnahme.

| Gruppe | Ergebnis |
|---|---|
| Rename, DB-Commitfehler | Externer Name bereits geaendert, kein Audit. Wiederholung schreibt erneut; Fake-Kollisionssuche liefert immer leer, daher keine Idempotenzfreigabe. |
| Move, DB-Commitfehler | Externer Zielordner geaendert, DB alt. Wiederholung korrigiert DB nicht, kein Log; A-136 erweitert. |
| Archive, DB-Commitfehler | Wiederholung erzeugt Archive-Log, DB bleibt dennoch alter Quellordner; A-136. |
| Restore, DB-Commitfehler | Wiederholung erzeugt Restore-Log, DB bleibt dennoch Archiv; A-136. |
| Move, Audit-Insertfehler | Move committed, Audit fehlt. Helfer unterdrueckt Fehler; Folgeabfrage vor Rollback scheitert mit PendingRollbackError, A-137. |

Die erste Kontrollannahme, Archive/Restore wuerden bei Wiederholung den Cache
korrigieren, wurde durch den Test widerlegt. Erwartung danach an den beobachteten
No-op-Pfad angepasst, alle fuenf Gruppen erneut ausgefuehrt. Das Audit dokumentiert
Fehlerverhalten und schreibt keine gewuenschte App-Implementierung vor.

Jetzt 51 fachliche Dokumentgruppen und insgesamt 137 Befunde. Kein echter
Drive-Zugriff oder Produktionsschreibzugriff. Request-Teardown, globale
Audit-Aufrufer, echte DB-Ausfaelle/PostgreSQL, Kollisionen und Parallelitaet
bleiben offen. Ein Fehler nach bereits extern wirksamer Aktion braucht eine
verstaendliche Teilfehler-Rueckmeldung und kontrollierte Synchronisierung;
pauschales Wiederholen ist keine verifizierte Wiederherstellung.

# U1-R03 – Beleg-/Dokumentauswahl (A-071)

Vertrag vor Umsetzung, 18.10.2026, Basis a038b6e.

Eventoptionen werden vor Limitierung mit dem vorhandenen Eventvertrag gefiltert.
Normale Mitglieder reichen Belege ohne direkte Buchungsverknuepfung ein;
Schatzmeister/Admin duerfen offene Buchungen verknuepfen, mit zusaetzlicher
Eventberechtigung. Revisor bleibt lesend und erhaelt keine Verknuepfungsoptionen.
Query-Kontext booking und manipulierte POST-IDs duerfen diese Grenzen nicht
umgehen. Services pruefen vor Datei-/Drive-Nebenwirkungen erneut. Dokumentupload
prueft Eventbezug auch bei direktem Serviceaufruf. Keine neuen Rollen/Dependencies.
Die umfassende R13-Dokument-/Ordner-/Drive-Rechtematrix folgt in U1-R04;
dieses Paket behauptet keine vollstaendige Drive-Zugriffstrennung.


Ergaenzend vorhandene Belegauswahl/receipt-Kontext/Download und manipulierte
Verknuepfung abgesichert; Eventberechtigung fuer Vorschlag und vorhandene Buchung
kumulativ. Eventauswahl im Buchungsformular folgt derselben Filterung.

## Pruefung

Isolierter Runner per runpy wie U1z; pytest auf
`tests/routes/test_upload_selection_permissions.py`, `tests/routes/test_docs_smoke.py`,
`tests/services/test_drive_storage.py`, mit `-q --disable-warnings --tb=short
-p no:cacheprovider`. Erster Lauf: 22 bestanden, 11 Setupfehler durch fehlende
start_date/end_date im neuen synthetischen Geschaeftsjahr. Fixture korrigiert;
danach 33 bestanden. Abschlusslauf mit zusaetzlicher Beleg-Zuordnungsregression: **34 bestanden**,
425 bestehende Warnungen; Exit 0. Ignorierte pyreadline-Destruktorwarnung beim
Interpreterende wie bei U1z. `git diff --check` ohne Fehler.
Alle Drive-Nebenwirkungen sind Fakes; kein dotenv/Netz, keine echte Dateiablage.
Keine Migration/ENV/Dependencies oder neue UI-Klasse; kein Cache-Bump erforderlich
(reine serverseitige Rechte-/Auswahlaenderung ohne Template-/Assetaenderung).

Umfassende Finanzlisten und Dokument-/Ordnerrechte, direkte Drive-Freigaben,
Parallelitaet unter PostgreSQL und Browserabnahme bleiben getrennte Arbeit;
kein pauschaler R13-Abschluss. U1 bleibt offen; naechstes Paket U1-R04 Matrix.

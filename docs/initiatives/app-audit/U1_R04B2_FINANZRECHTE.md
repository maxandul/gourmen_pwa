# U1-R04b2 – Finanzbereichsfreigaben

Vertrag 18.10.2026 vor Code: accounting_read erlaubt Journal, Belege, Statistik,
Berichte und vorhandene Detailansichten; accounting_write zusaetzlich Buchungen,
Belegzuordnung, Import/Zuordnung, Beitraege, Budget, Kontenplan und Jahresanlage.
Schatzmeister erhaelt write, Revisor read; write impliziert read. Kein Scope
verleiht Admin- oder sensible Vollrechte. Importbearbeitung bleibt write.
Revisionskommentare bleiben Revisor/Schatzmeister/Admin bzw. write, read allein
schreibt nicht. Revisionsstatuswechsel und -bestaetigung werden **nicht** durch
Zusatzfreigaben erweitert; R04d liefert zuerst den versionsgebundenen Vertrag.
App-Navigation und serverseitige Guards verwenden dieselbe Scopepruefung.
Belegrechte behalten zusaetzliche Eventpruefung aus R03.
Keine Migration (Scopes sind registrierte Strings); keine automatischen Vergaben.


Lokaler Erstlauf: 27 Tests bestanden. Nach Abgleich der UI-Formulare und
Kontenplan-/Jahresanlagebereitstellung erneut geprueft (Abschluss unten).
Runner per runpy wie U1z, Dateien tests/routes/test_finance_area_permissions.py,
test_upload_selection_permissions.py, test_member_area_permissions.py;
-q --disable-warnings --tb=short -p no:cacheprovider. Echte DB/Drive/Versand
nicht verwendet. Keine Migration/neue UI-Klasse. Cacheversion 3.16.12.
Browser-/Layoutabnahme und PostgreSQL bleiben offen; U1 bleibt offen.

Abschluss: **27 Python-Tests bestanden**, 865 bestehende Warnungen; **19 Worker-Tests
bestanden**; `git diff --check` ohne Fehler.

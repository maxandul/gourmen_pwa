# U1-R04c – Dokumentrechte: lokaler Vertrag

Stand 18.10.2026. F2/R13 und bestaetigte Altbestandsregel haben Vorrang vor dem
historischen Drive-Konzept «alle sehen alles». Direkte Drive-Freigaben werden
nicht veraendert. Ohne deren separate Abnahme ist keine Gesamtabnahme moeglich.

## Teilpakete

1. R04c1: lokale Datei-/Ordnerklassifikation, atomare Aenderungshistorie,
   gemeinsame Rechtepruefung und synthetische Modell-/Service-Regression.
2. R04c2: Adminzuordnung mit UI, Liste/Suche/Detail/Download/Ordnerpicker und
   Upload/Pflege/Archiv/Wiederherstellung durchgaengig anbinden. Unklassifiziert
   und extern neu entdeckt bis zur expliziten Zuordnung nur Systemadmin.
3. R04c3: endgueltiges Loeschen mit Referenz-/Aufbewahrungspruefung und
   Abschlussregression. Keine allgemeine Dokumentaktion entfernt Belege.

## Klassifikationsvertrag

Explizite Policy pro Drive-ID und Objekttyp (Datei oder Ordner), keine Ableitung
aus Namen, keine automatische Vererbung oder nachtraegliche Klassifikation des
Altbestands. Zugriffsebenen: Verein (aktive Mitglieder), Vorstand (Board/Admin),
Finanzen (accounting_read/Admin). Pflegebereich separat: Vereinsdokumente
(documents_manage), Vorstandsdokumente (board_documents_manage), Finanzen
(accounting_write), Reisen (travel_manage), Merch (merch_manage). Die beiden neuen
Dokumentscopes sind explizite Zusatzfreigaben; Vorstand allein ist kein Pflegerecht.
Systemadmin verwaltet die Zuordnung. Reise-/Merch-Funktion oeffnet keine Board-
oder Finanzleserechte. Lesen ist stets Voraussetzung fuer Pflege.

Datei und direkter Elternordner werden unabhaengig geprueft, zusaetzlich bestehende
Eventgrenzen und bei identischer Drive-ID die Belegrechte. Ein unbekannter oder
nicht sichtbarer Elternordner erweitert keine Dateirechte. Root ist lediglich ein
lesbarer Einstieg; kein impliziter Uploadbereich. Unterordner erhalten eigene
explizite Regeln; Breadcrumbs duerfen unlesbare Segmente nicht offenlegen.
Ein klassifizierter Unterordner erbt keine Rechte eines Vorfahren. Neue Uploads
uebernehmen die explizite Zielordnerpolicy; Verschieben aendert nie stillschweigend
die Dateiklassifikation. Archiv ist kein Sonderweg zur Offenlegung.

Policy-Aenderungen und Historie committen atomar, mit Actor, Zeit, Begruendung,
alter/neuer Ebene und Pflegebereich. Keine externen Freigaben, Secrets oder
Dokumentinhalte in der Historie. Fehlende/ungueltige Policy: nur aktiver Admin.
R04c1 allein behauptet noch keine Durchsetzung in bestehenden Routen.

## R04c1 Nachweis 18.10.2026

Migration **7d471a4** separat. Synthetisches SQLite Upgrade/Downgrade wiederholt,
vorhandene Dokument-ID unveraendert, keine impliziten Policy-Zeilen.
Isolierter Runner mit test_document_permissions.py, test_document_policy_migration.py
und test_member_area_permissions.py: **26 bestanden, 575 Warnungen**. Matrix
prueft Verein/Vorstand/Finanzen, Funktionen/gezielte Freigaben, aktive Konten,
Typverwechslung, unbekannte IDs, Elternordner, versteckte Events und Beleg-Alias.
History/Policy gemeinsam zurueckgerollt, veralteter Vorzustand abgewiesen.
Erster Lauf vor zusaetzlichem Beleg-Aliastest 25 bestanden/549 Warnungen.
`git diff --check` sauber. Keine UI-/Worker-Aenderung, kein erneuter Worker-Lauf.
PostgreSQL-Parallelitaet und externe Drive-Grenzen offen. Bestehende Dokumentrouten
verwenden die neue Grundlage erst nach R04c2; U1 bleibt insgesamt offen.

## R04c2 Nachweis 18.10.2026

DocumentBrowserService filtert Root/Ordner/Suche/Picker und Breadcrumbs vor
Darstellung. Nichtadmins erhalten keine ungefilterten Child-Counts. Direkte
Datei-/Download-/Pflegewege pruefen dieselben Rechte, nach Auto-Sync erneut.
Transport prueft Upload/Download/Move/Rename/Archiv/Restore vor I/O; Live-Eltern-
wechsel wird vor Download/Move/Rename erneut geprueft. Admin ordnet Dateien und
Ordner mit CSRF, Begruendung und Vorzustandspruefung zu. Externe Dateien werden
bei Zuordnung lokal registriert; keine Freigabeaenderung in Drive.

Gemeinsames Archiv: Dokumentpflege plus Leserecht am konfigurierten Archivziel
reicht fuer Archivierung; Datei-Leseebene/Pflegebereich bleiben erhalten. Normales
Verschieben/Wiederherstellen verlangt Zielpflege. Upload kopiert eine vorhandene
explizite Zielpolicy atomar samt Historie; Root/Altbestand wird nicht pauschal offen.
Ordnerpicker navigiert durch lesbare Ordner, nur can_select-Ziele sind waehlbar.

Isolierte Regression (test_document_access, test_docs_smoke,
test_merch_docs_return_target, test_upload_selection_permissions,
test_document_permissions): **98 bestanden, 1573 Warnungen**. Vorlaeufige Laeufe:
88 bestanden/1 Fehler (alter Upload-Smoke ohne nun erforderliche Pflegefreigabe),
92 bestanden/3 Fehler (abort innerhalb PermissionError-Handler wurde weitergeworfen;
auf regulaere 403-Antwort korrigiert), danach 97 bestanden und ergaenzter Archivtest.
Fakes pruefen keinen realen Drive-Zugriff. CSRF-Verweigerung, veraltete Formulare,
verbotene Transporte, Klassifikationserhalt und aktuelle Download-Eltern geprueft.
Worker: **19 bestanden**. `node --check` Folder-Picker und `git diff --check` sauber.
PWA 3.16.15, Picker-Queryversion 3.16.15, keine neue UI-Klasse/Migration.
Breite isolierte Bestandsregression gestartet; deren Ergebnis wird separat
nachgetragen und ist noch keine Abschlussbehauptung. Naechstes Paket R04c3.

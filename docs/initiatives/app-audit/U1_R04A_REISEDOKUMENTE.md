# U1-R04a – Begrenzte Reisedokumentansicht

18.10.2026, Basis 3fcf346. Technischer Vorvertrag: U1_R04_RECHTEMATRIX.md.

Neue lesende Route /admin/members/<id>/travel-documents, erreichbar ueber die
Mitgliederliste fuer Reisekommissar/Systemadmin. Sechs Pass-/ID-Felder nach
sitzungsgebundenem Step-Up, Service prueft aktuelle Identitaet nochmals vor
Entschluesselung. Kein Allergie-/Fuehrerschein-/unbekannter Payload-Inhalt im
Template; kein Schreibweg. Fehler erhalten Daten, Antworten private/no-store.
Bestehendes Leseaudit mit field_scope ohne Feldwerte. Keine neue UI-Klasse,
vorhandene page/card/button-Klassen; Version 3.16.10 mit PWA-Fingerprint.

Isolierter Runner wie U1z: pytest auf tests/routes/test_travel_sensitive_fields.py
und tests/routes/test_sensitive_data_preservation.py, -q --disable-warnings
--tb=short -p no:cacheprovider. Erster Lauf 57 bestanden/1 absichtlich uebersprungene
Doppelvariante; Parametrisierung bereinigt. Abschliessender Lauf siehe unten.
Synthetischer Fernet-Schluessel nur in Testkonfiguration, kein bestehender
Schluessel/kein dotenv/Netz. Keine Migration. Browser-/Layout-/Geraeteabnahme offen.
R04b (delegierte Bereiche) folgt; U1 und umfassende R13-Durchsetzung bleiben offen.

Abschluss: **57 Python-Tests bestanden**, 1058 bestehende Warnungen, kein Skip;
**19 Worker-Tests bestanden** nach Versionswechsel. `git diff --check` ohne Fehler.

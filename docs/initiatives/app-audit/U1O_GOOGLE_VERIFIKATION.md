# U1o – Google-Bestätigungslinks an die Adresse binden

Stand: 12. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1o-google-verification-binding`, Basis U1n-Commit `4a0d569`.
Umfang: A-088. Bestätigte Linkregel aus `KONTO_ZUGANG_ENTWURF.md` gilt;
keine erneute Fachentscheidung. A-087 hatte bereits die minimale Renderkorrektur
in U1a erhalten; sein umfassender Formularvertrag bleibt separat.

## Änderung

`GoogleEmailVerificationService` bindet jeden neuen Link an die konkrete
Google-Adresse. Ein alter Link bestätigt weder eine neue Adresse noch die
ursprüngliche Adresse nach Wechsel hin und zurück. Erneuter Versand ersetzt
ältere Links desselben Mitglieds und Zwecks. Andere Tokenzwecke bleiben erhalten.
Ungebundene alte Google-Links werden bewusst abgelehnt: erneut senden.

Zufallstoken und bestehende Sieben-Tage-Frist bleiben. Die vorhandene 128-Zeichen-
Spalte speichert Lookup-Hash plus Adressbindungshash; keine Schemaänderung und
keine neue ENV/Abhängigkeit. Die Adresse steht nicht im Link. Details zur
Hashbildung in `CONVENTIONS.md`; keine Schlüsselrotation.

Speichern/Ersetzen sperrt die Mitgliedszeile und schreibt Adresse, Verifikations-
status und Token gemeinsam. Verbrauch prüft nach derselben Sperre den frischen
DB-Stand und aktualisiert den Verbrauch zusätzlich nur bei `used_at IS NULL`.
Abgelaufene, verwendete, manipulierte, ungebundene oder zweckfremde Links und
inaktive Mitglieder erhalten keine Bestätigung/Einladung.

Mail und Drive-Invite erhalten einen unveränderlichen Snapshot. Eine Änderung
zwischen DB-Commit und externem Aufruf darf kein anderes Postfach zum Empfänger
machen. Die Route, Mailtexte und GET-Link-Bedienung bleiben ansonsten bestehen.

## Prüfungen

18 gezielte Tests mit synthetischen Mitgliedern: Adresswechsel, erneutes Senden,
Wechsel zurück, direkte zwischenzeitliche DB-Adressänderung, aktueller Link,
Wiederholung, Ablauf, Inaktivität, falscher Zweck, verbrauchter/manipulierter/
ungebundener Link, CSRF für Save/Resend, getrennte Tokenzwecke, deaktiviertes
Drive-Feature, Commit-Fehler mit Rollback und fester Empfänger bei einer gezielt
eingeschobenen Änderung vor Mail oder Invite.

Vorherige 13 Tests: **5 fehlgeschlagen, 8 bestanden**. Nach Fix und fünf weiteren
Tests: **18 bestanden** in 6,44 Sekunden bei 256 Warnungen.
SQLite im Speicher; Mail und Invite ersetzt; bestehender isolierter Teststarter
blockiert dotenv/Netzwerk. Keine reale Mail, Einladung oder Rechteänderung.
CSRF in einem eigenen Ablehnungstest aktiviert, sonst Testing-Konfiguration.

Gesamtlauf: **491 Tests bestanden**, darunter **18 neue Regressionstests**,
in 331,61 Sekunden bei 3784 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups gegenüber U1n unverändert.

## Grenzen und spätere Abnahme

Kein echter PostgreSQL-Paralleltest: Sperren sind implementiert, ihr Verhalten
unter parallelen Prozessen muss vor Veröffentlichung auf PostgreSQL geprüft
werden. Die Tests belegen Wiederholung und gezielte Zwischenänderungen, keine
vollständige Nebenläufigkeitsabnahme.

A-089 bleibt offen: alte Drive-Freigaben bei Adresswechsel/Deaktivierung entziehen
und externe Fehler nachvollziehbar wiederaufnehmen. Ein Invite-Snapshot kann
weiter die zuvor verifizierte alte Adresse einladen, wenn unmittelbar danach
ein Adresswechsel stattfindet; er bestätigt oder lädt aber nicht die ungeprüfte
neue Adresse ein. Eine DB-/Drive-Transaktion oder zuverlässige Zustellung wird
hier nicht behauptet. Fehler nach dem Verifikations-Commit können weiterhin
eine verifizierte Adresse ohne Einladung hinterlassen.

Keine Templates/Assets, neue Mockups oder Browserabnahme. Offene visuelle Abnahme
aus U1k bleibt. Kein Push, Deploy, Merge auf master oder Produktionsdatenzugriff.
Fremde Dateien und gesicherte Planung bleiben erhalten.

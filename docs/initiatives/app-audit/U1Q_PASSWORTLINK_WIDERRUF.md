# U1q – Alte Passwortlinks bei Zugangsaenderungen entwerten

Stand: 12. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1q-password-link-revocation`, Basis U1p-Commit `ef384b1`.
Umfang: Passwortanteil A-141; bestätigter Linkvertrag aus F1. Kein neues
Rollenmodell, kein MFA-Umbau und keine Änderung der bestehenden Linkfristen.

## Änderung

Nach normalem Passwortwechsel, Passwort-Reset per Link, Aktivierung und Admin-
Passwortreset sind alle vorher offenen Passwort-Reset- und Aktivierungslinks
desselben Mitglieds entwertet. Sie können weder erneut das Passwort setzen noch
über Aktivierung eine Sitzung eröffnen. Andere Konten und Tokenzwecke bleiben
unverändert, insbesondere Google-Verifikation und MFA-Reset.

Ausgabe eines neuen Passwort-/Aktivierungslinks ersetzt die älteren desselben
Zwecks. Eine neue Anforderung nach erfolgreichem Passwortwechsel funktioniert
weiter. Kein neues Tokenformat oder Datenbankschema; vorhandenes `used_at` dient
wie beim Google-Link auch zur Entwertung.

Alle betroffenen Wege sperren dieselbe Mitgliedszeile. Passwort und Widerruf
werden zusammen committet; ein Rollback bewahrt beides. Linkverbrauch prüft nach
der Sperre Zweck, Ablauf, Nutzung und Aktivstatus erneut. Normaler Wechsel
prüft das bisherige Passwort nach Aktualisierung des Mitgliedsstands. Die
Helfer im SecurityService committen nicht selbst. Admin-Rechte, Step-Up,
Passwortstärke und bestehende Anmelde-/Weiterleitungsabläufe bleiben erhalten.

## Prüfungen

Vor dem Fix scheiterten **10 von 12 gezielten Tests**, zwei Kontrollfälle
bestanden. Nach dem Fix bestanden diese zwölf. Weitere Tests decken gezielte
Zwischenänderungen und Fehler ab. Gezielter Endlauf: **24 Tests bestanden**
in 61,80 Sekunden bei 518 Warnungen.

Abgedeckt: alle vier Passwortwege und beide alten Linktypen, keine Anmeldung
über den entwerteten Aktivierungslink, Zweckerhalt, fremdes Konto, neuer Link
nach Passwortwechsel, Ersatz bei neuer Ausgabe, zweimalige echte Route für
Passwort-vergessen (Mail ersetzt), ungültiges bisheriges Passwort, GET und
ungültige Formulare ohne Entwertung, inzwischen verwendete/abgelaufene Links
und deaktivierte Konten, Rollback bei Commitfehler für Wechsel und Reset sowie
Rollback der Linkausgabe. Aktuelle Sitzung beim normalen Wechsel bleibt erhalten.

Synthetische Konten, SQLite im Speicher, Mail/Audit ersetzt, bestehender
isolierter Teststarter ohne dotenv/Netzwerk. Test-Konfiguration mit deaktiviertem
CSRF; vorhandene CSRF-/Berechtigungsprüfungen nicht verändert.

Gesamtlauf: **532 Tests bestanden**, darunter **24 neue Regressionstests**,
in 253,44 Sekunden bei 4480 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups gegenüber U1p unverändert.

## Grenzen

Kein echter PostgreSQL-Paralleltest. Die Sperrstrategie setzt READ COMMITTED
voraus; gezielte Zwischenänderungen im Test ersetzen die Abnahme mit parallelen
Prozessen nicht. Der Widerruf ist ein App-Vertrag für die genannten Routen;
direkte Passwortänderung über Model-/DB-Skripte muss ihn ausdrücklich verwenden.

A-141 bleibt hinsichtlich MFA-Reset und erneuter MFA-Einrichtung offen. Andere
Sitzungen/Geräte, Pflichtwechsel-Durchsetzung A-076 und der dauerhafte Drive-
Widerruf A-089 bleiben eigene Pakete. Bestätigte Fachregeln werden damit nicht
neu abgestimmt. Fehler nach dem Commit (z.B. Audit/Mail) erhalten weiterhin den
bestehenden Ablauf; keine zuverlässige Zustellung oder vollständige Recovery-
Kette behauptet.

Keine Templates/Assets, Migration, neue Abhängigkeit oder Schlüsseländerung.
Kein Push, Deploy, Merge auf master oder Produktionsdatenzugriff. Fremde Dateien
und gesicherte Planung erhalten; offene visuelle Abnahme aus U1k bleibt bestehen.

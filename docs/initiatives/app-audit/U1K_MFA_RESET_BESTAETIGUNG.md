# U1k – MFA-Reset erst nach bewusster Bestätigung

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1k-mfa-reset-confirmation`, Basis U1j-Commit `170e4de`.
Umfang: A-083, keine neue Audit-/Mockup-Runde.

## Änderung

GET und HEAD auf einen gültigen MFA-Reset-Link ändern nichts mehr am MFA-Zustand,
an Wiederherstellungscodes oder am Token-Verbrauch. Die neue Bestätigungsseite
erklärt die Folgen, verlangt eine Checkbox und bietet Abbrechen zur Anmeldung.
Nur ein expliziter POST mit gültigem CSRF-Token und Bestätigung führt den bisherigen
Reset aus. Zweck, Gültigkeit, Verbrauch und aktives Konto werden erneut geprüft.
Bestätigungsantworten sind mit no-store/no-referrer versehen.

Vorhandene UI-Komponenten werden wiederverwendet. Vorgeschriebener Cache-Buster
auf 3.16.3 in SW, PWA und Basis-Template; neuer PWA-Fingerprint mit Manifest und
Script-Partial. Fingerprint-Skript gezielt nur auf das geänderte PWA-JS angewendet,
damit fremde/gehashte Dateien erhalten bleiben. Kein Deploy.

## Prüfungen

14 neue Regressionstests mit synthetischen Konten/Token und aktiviertem CSRF:
GET/HEAD unveränderlich, erfolgreicher POST, erneute Verwendung abgelehnt,
fehlender/ungültiger CSRF-Token, fehlende Bestätigung, Ablauf, schon verbrauchter
Link, falscher Tokenzweck und inaktives Konto. Zustand aus neuer DB-Session gelesen.
Vorher: 12 Fehler, 2 bestanden (noch kein Bestätigungsformular). Danach 14 bestanden.
Teststarter isoliert dotenv/Netzwerk; SQLite im Speicher, keine echten Zugangsdaten.
Gesamtlauf: **401 Tests bestanden**, darunter **14 neue Regressionstests**,
in 249,20 Sekunden bei 2944 Warnungen. PWA-Version/Fingerprint/Quellkopie und
Template-Verweis gesondert konsistent geprüft; Mockups unverändert.
JavaScript-Syntaxprüfung bestanden. Diff-Whitespace-Prüfung der Quelländerungen
bestanden; die neue unveränderte Fingerprint-Kopie übernimmt die bereits im
PWA-Quelltext vorhandenen Leerzeichen am Zeilenende (Gesamtprüfung meldet diese).

Template wird durch echte GET-/POST-Tests gerendert; keine neuen Styles/Klassen.
Eine zusätzliche Chromium-Prüfung für 390/1440 Pixel, Hell/Dunkel wurde versucht,
konnte aber mangels installiertem Playwright-Browser nicht starten. Daher keine
visuelle Geräteabnahme behauptet; diese bleibt vor Veröffentlichung erforderlich.

## Grenzen

Dies sichert ausschliesslich den bestehenden Link gegen Mutation beim Öffnen ab.
Die bestätigte künftige Recovery-Regel (Identitätsprüfung durch Systemadmin),
Widerruf anderer Sitzungen/Geräte und Ersatz alter Links werden hier nicht
implementiert. Der bestehende E-Mail-Anforderungsweg bleibt technisch erhalten;
daraus folgt keine fachliche Freigabe dieses vollständigen Recovery-Ablaufs.
Einmaligkeit ist sequenziell geprüft; keine PostgreSQL-Nebenläufigkeitsabnahme.
Kein echter Mailversand/Mailscanner-Test, keine Schlüsselrotation, Migration oder
Produktionsdatenänderung. Kein Push, Deploy oder Merge auf master. Planung,
Mockups und fremde lokale Dateien erhalten.

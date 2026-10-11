# U1m – Mailkonflikte bei Anlage und Admin-Bearbeitung

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1m-admin-email-conflict`, Basis U1l-Commit `d18d565`.
Umfang: A-084 anteilig, Mitgliederanlage und Admin-Bearbeitung.

## Änderung

Das gemeinsame Mitgliederformular prüft belegte Adressen anderer Konten,
einschliesslich deaktivierter. Beim Bearbeiten wird ausschliesslich das durch
die Route geladene Mitglied ausgenommen. Anlage hat keine Ausnahme. Wie beim
Profil bleibt die bestehende Schreibweise unverändert; keine Normalisierung.

Der erste Mitglieds-Commit wird zusätzlich gegen `IntegrityError` abgesichert.
Bei Konflikt vollständiger Rollback, Feldfehler und Wiederanzeige des Formulars.
Andere Integritätsfehler werden neutral gemeldet, ohne DB-/SQL-Details. Die
WTForms-Eingaben bleiben erhalten; keine Erfolgsmeldung bei fehlgeschlagenem Commit.
Abgelehnte Anlage erreicht weder sensible Zusatzdaten noch Onboarding-Token,
Mail oder Audit. Abgelehnte Bearbeitung erreicht keinen Erfolgs-Audit.

## Prüfungen

19 neue Tests: Anlage/Bearbeitung, aktive/inaktive Adressinhaber, mit Vorprüfung
und echtem DB-Konflikt nach ausgelassener Vorprüfung; unveränderte eigene/freie
Adresse; generischer Integritätsfehler; Adminrecht und CSRF; Wiederholung der
Anlage nach Erfolg, strukturiertem Mailfehler und erstem Auditfehler.
DB-Zustand und Anzahl von Mail-/Audit-Aufrufen werden unabhängig geprüft.

Vorherige 15 Fälle: **11 fehlgeschlagen, 4 bestanden**; nach Fix **15 bestanden**.
Vier zusätzliche Fehler-/CSRF-Tests ergänzt. Mail/Audit simuliert, kein echter
Versand. Synthetische Konten, SQLite im Speicher, isolierter Audit-Teststarter
ohne dotenv/Netzwerk; CSRF für gezielte Ablehnung aktiviert, sonst Testing-Konfiguration.
Kein echter PostgreSQL-Paralleltest.

Gesamtlauf: **428 Tests bestanden**, darunter **19 neue Regressionstests**,
in 250,41 Sekunden bei 3227 Warnungen. `git diff --check` ohne Fehler.
Templates/Assets gegenüber U1l und gesicherte Mockups unverändert.

## Grenzen

Mit U1l sind die dokumentierten Unique-Konflikte in Profil, Anlage und Admin-
Bearbeitung behandelt. Systemweite Normalisierung und Bestandsprüfung bleiben
offen, daher A-084 nicht pauschal vollständig abgeschlossen.

Ein Fehler nach bereits erfolgreicher Kontoanlage kann weiterhin ein angelegtes
Konto mit unvollständigem Onboarding hinterlassen. Der erneute Erstellen-POST
wird nun verständlich abgelehnt und löst keine zweite Mail aus; ein eigener
Wiederaufnahme-/Erneutversandweg ist nicht Bestandteil dieses Schritts.
Keine Änderung an Rollen, sensiblen Feldern, Zahlenvalidierung oder Mailinhalten.
Keine Templates/Assets, Migration, Produktionsdaten oder Schlüssel verändert.
Kein Push, Deploy oder Merge auf master. Fremde Dateien und Planung erhalten;
offene visuelle Abnahme aus U1k bleibt bestehen.

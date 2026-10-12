# U1n – Gemeinsame Zahlenvalidierung für Mitgliedsdaten

Stand: 12. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1n-member-numeric-validation`, Basis U1m-Commit `7e6c066`.
Umfang: technischer Teil von A-085, Profil, Mitgliederanlage und Admin-Bearbeitung.

## Änderung

Die drei Wege verwenden gemeinsame WTForms-Feldfabriken in
`backend/forms/member_fields.py`. Grösse und Gewicht werden vor jeder Mutation
als ganze Zahlen geprüft, Schuhgrösse als endliche Gleitkommazahl. Negative
oder ungültige Eingaben sind Formularfehler; keine nachträgliche manuelle
Konvertierung im Admin-Speicherpfad und dadurch kein dortiger ValueError mehr.

Leere Felder und reine Leerzeichen ergeben `None`. Null bleibt zulässig und
wird auch beim Laden des Admin-Formulars nicht mehr durch ein Leerfeld ersetzt.
Dezimalwerte sind nur bei Schuhgrössen erlaubt. Für die beiden Integer-Spalten
gilt zusätzlich die technische PostgreSQL-Obergrenze 2147483647. Das ist keine
medizinische oder vereinsbezogene Plausibilitätsgrenze.

Fehlerhafte Formulare werden mit ihren Eingaben wieder angezeigt. Es wird
weder ein Mitglied angelegt noch eine Teiländerung bestehender Mitgliedsdaten
gespeichert; die abgelehnte Anlage erreicht keinen Mailversand.
Admin behält die bisherigen Text-Eingabefelder, das Profil seine Zahlenfelder.
Keine neue Abhängigkeit, Datenbankmigration oder Änderung an Templates/Assets.

## Prüfungen

45 neue Regressionstests: alle drei Wege mit negativen Werten je Feld,
Text je Feld, Dezimalwerten in Integer-Feldern, NaN/Unendlich, Integer-Überlauf,
Leerfeldern, Leerzeichen, Null und regulären Werten einschliesslich Schuhgrösse
43.5. Fehlerfälle prüfen den unveränderten Datenbankstand, erhaltene weitere
Formulareingaben und ausbleibenden Mailversand; gültige Fälle die gespeicherten
Werte und erfolgreiche Weiterleitung.

Vor dem Fix: **28 fehlgeschlagen, 17 bestanden**. Nach dem Fix:
**45 gezielte Tests bestanden** in 19,25 Sekunden bei 301 Warnungen.
Synthetische Konten, SQLite im Speicher, simulierter Mailversand und bestehender
isolierter Audit-Teststarter ohne dotenv/Netzwerk. Kein PostgreSQL-Lauf und
keine visuelle Browserabnahme; CSRF in diesen Validierungstests gemäss
Testing-Konfiguration deaktiviert.

Gesamtlauf: **473 Tests bestanden**, darunter **45 neue Regressionstests**,
in 383,02 Sekunden bei 3528 Warnungen. `git diff --check` ohne Fehler.

## Grenzen

Die dokumentierten technischen Eingabefehler von A-085 sind behandelt.
Fachliche Unter-/Obergrenzen bleiben ohne neuen Entscheid offen. Bestehende
negative oder nicht endliche Daten werden nicht automatisch bereinigt; beim
nächsten Speichern der betroffenen Formulare greift die neue Validierung.
Keine Änderung an Rollen, sensiblen Feldern oder Zahlenformat-Lokalisierung.

Kein Push, Deploy oder Merge auf master, keine Produktionsdaten oder Schlüssel
verändert. Fremde Dateien und gesicherte Planungsunterlagen bleiben erhalten.
Die offene visuelle Abnahme aus U1k bleibt bestehen.

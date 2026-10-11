# U1l – Profil bei Mailkonflikten bewahren

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1l-profile-email-conflict`, Basis U1k-Commit `aeb074c`.
Umfang: A-084 anteilig, nur eigenes Profil. Keine neue Audit-Runde.

## Änderung

Die Profilvalidierung erkennt eine belegte E-Mail-Adresse vor dem Ändern des
Mitglieds und zeigt einen Feldfehler. Das eigene Konto ist ausgenommen;
deaktivierte andere Konten behalten ihre belegte Adresse.

Ein Unique-Konflikt beim Commit wird zusätzlich mit vollständigem Rollback
behandelt. Nachweisbar belegte Adresse: Feldfehler. Andere Integritätsfehler:
neutrale Speichermeldung statt SQL-/DB-Details. Kein Erfolgshinweis bei Fehlern.
Vorname, Telefon und andere Profilwerte werden nicht teilweise gespeichert;
die eingereichten Werte bleiben im vorhandenen Formular zur Korrektur erhalten.

Keine neue Normalisierung: Eingabeschreibweise und bestehender DB-/Login-Vergleich
bleiben erhalten. Eine systemweite kanonische Adresse würde auch Altbestände,
Anmeldung, Anlage und Administration betreffen und ist hier nicht eingeführt.

## Tests

8 neue Regressionstests: belegte Adresse aktiver/inaktiver Konten, unveränderte
eigene Adresse, freie neue Adresse, Erhalt gemischter Schreibweise, echter
Unique-Constraint-Konflikt nach ausgelassener Vorprüfung, anderer Integritätsfehler
mit Rollback und CSRF-Ablehnung. Persistierte Werte werden in neuer DB-Session
geprüft. Formular enthält nach Konflikt weiterhin eingereichte Adresse/Vorname.
Nach Rollback ist ein korrigierter Folgespeicherversuch erfolgreich.

Vorher **4 fehlgeschlagen, 4 bestanden**, nach Fix **8 bestanden**.
SQLite im Speicher, synthetische Konten, isolierter Audit-Teststarter ohne
dotenv/Netzwerk. CSRF für die gezielte Ablehnung aktiviert, sonst Testing-Konfiguration.
Der Vorprüfungs-/DB-Zwischenfall wird deterministisch simuliert; kein echter
PostgreSQL-Paralleltest.

Gesamtlauf: **409 Tests bestanden**, darunter **8 neue Regressionstests**,
in 244,80 Sekunden bei 3002 Warnungen. `git diff --check` ohne Fehler.
Templates und Assets gegenüber U1k unverändert.

## Grenzen

A-084 ist nicht vollständig abgeschlossen: Konflikte bei Mitgliederanlage und
Admin-Bearbeitung sowie systemweite Normalisierung bleiben offen. Keine Migration
oder Bestandskorrektur. Auch andere Profilvalidierungen (A-085) bleiben separat.
Keine Template-/Assetänderung, deshalb kein neuer PWA-Versionswechsel. Die offene
visuelle Abnahme aus U1k bleibt bestehen. Kein Push, Deploy, Merge auf master,
Produktionsdatenzugriff oder Schlüsselwechsel. Fremde Dateien und Planung erhalten.

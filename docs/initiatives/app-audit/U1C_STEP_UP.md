# U1c – sensible Freigaben an die Anmeldung binden

Stand: 11. Oktober 2026. Fortsetzung nach U1b auf Nutzerauftrag «ok weiter».
Basis `d7317a0`, Branch `codex/u1c-step-up-session`. U1a/U1b und gesicherte
Planungsunterlagen enthalten, keine neue Fremdbranch-Integration.
Umfang: vorhandener A-075 einschliesslich dort belegter MFA-Einrichtungsreste.

## Verhalten

- Sensible Freigaben speichern zusätzlich zur bisherigen Ablaufzeit die ID des
  angemeldeten Mitglieds. Prüfung verlangt Anmeldung, passende Mitglieds-ID
  und gültige Ablaufzeit. Alte reine Zeitfreigaben erfordern einmalig eine neue
  Passwortbestätigung; keine Datenmigration.
- Login, Logout und Wiederanmeldung über ein gespeichertes Login-Cookie
  entfernen zentral die sensible Freigabe, begonnenes MFA-Einrichtungssecret,
  ausstehende MFA-Konto-ID und altes Step-up-Rückkehrziel. Flask-Login-Signale
  decken die gemeinsamen Grenzen aller Anmeldewege ab, statt einzelne Routes
  unterschiedlich zu behandeln. Registrierung je App in `init_extensions()`.
- Erneute Anmeldung als dasselbe Mitglied benötigt ebenfalls eine neue Freigabe.
  Kontowechsel wird zusätzlich durch die Mitgliedsprüfung abgefangen.
- Normale Requests derselben Anmeldung behalten ihre gültige Freigabe bis zur
  bestehenden konfigurierten TTL. Andere Session-Einstellungen bleiben erhalten.
  Keine Änderung der fachlichen Rechte, Login- oder MFA-Prüfregeln.

## Nachweise

`tests/routes/test_step_up_session.py` prüft mit synthetischen Mitgliedern echte
Login-, Logout-, Step-up- und sensible Profilrouten sowie die zentralen Signale.
Vor dem Fix: 12 fehlgeschlagene, 1 bestandener Test. Im ersten Nachlauf wurde
ein falsch aufgebauter Zeittest korrigiert: simulierte Zeit vor Login setzen,
damit nicht unbeabsichtigt das Session-Cookie durch den Zeitsprung abläuft.

Abdeckung: Logout ohne/wieder mit demselben bzw. anderem Konto; alte, fremde,
abgelaufene und fehlerhafte Freigaben; Neuanmeldung ohne vorherigen Logout;
Kontowechsel ohne normale Hooks; falsches Passwort; konfigurierte TTL;
Login-/Logout-/Cookie-Signale; echte Wiederanmeldung per Remember-Cookie;
zweiter Browser; keine Freigabe für anonyme Kontexte.

Die U1a-Testfixture enthält jetzt auch die Mitgliedsbindung. Der U1b-Logtest
erteilt die Freigabe über den echten Service in einem angemeldeten Kontext.
Die bisherigen Schutz- und Logging-Regressionen bleiben Teil des Gesamtlaufs.

Ausführung über den vorhandenen isolierten Audit-Teststarter mit gebündeltem
Python, ohne dotenv und ohne ausgehendes Netzwerk. SQLite im Speicher, keine
Produktionsdaten. Testing-CSRF/Rate-Limits deaktiviert.

Abschluss: **155 Tests bestanden**, einschliesslich **16 neuer U1c-Tests**,
in 94,41 Sekunden; keine Fehler oder übersprungenen Tests. 1273 Warnungen aus
bestehenden Legacy-/Deprecation-Pfaden, keine Warnungsbereinigung in diesem Paket.
`git diff --check` bestanden. Templates/Assets entsprechen unverändert `d7317a0`,
Mockups unverändert `551e1ef`. Code, Tests und Dokumentation werden gemeinsam
als lokaler Commit auf dem U1c-Branch gesichert.

## Grenzen

Kein globaler serverseitiger Sitzungs-/Gerätewiderruf, keine Ungültigmachung
kopierter alter signierter Cookies und keine Reparatur der anderen MFA-Befunde.
Widerruf bei Passwort-/MFA-Reset und Deaktivierung gehört zum späteren
zusammenhängenden Zugangs-Lifecycle-Paket. Keine neuen Fristen, Rollen,
Datenbankschemata, ENV-Werte, Schlüssel oder externen Freigaben.
Keine Templates/Assets geändert. Kein Push, Deploy oder Merge auf master.
Fremde Dateien und historische Auditbelege bleiben erhalten.

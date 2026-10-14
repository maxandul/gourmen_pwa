# U1w: Aktionsgebundene Identitätsbestätigung

Stand: 14.10.2026. Beauftragte lokale Fortsetzung auf `74077f0` einschliesslich
Migration `24e68fc`, Branch `codex/u1w-action-confirmation`. F1 ist bestätigt;
dies ist die technische Ausgestaltung, keine neue Fachabstimmung.

## Vertrag vor Implementierung

Die Identität wird im selben POST wie die konkrete Änderung erneut mit dem
aktuellen Passwort des Handelnden bestätigt. Keine vorgängig gespeicherte
Authentifizierungsfreigabe; das allgemeine Step-Up-Fenster genügt nicht.
MFA-Einrichtung verlangt zusätzlich den Code des neu eingerichteten Faktors.
Eine zusätzliche Pflicht-MFA für alle Verwaltungsaktionen wird nicht eingeführt.

| Aktion | Nachweis / Bindung |
|---|---|
| Eigener Passwortwechsel, einschliesslich Pflichtwechsel | Aktuelles Passwort, eigener Kontostand, Aktion password_change |
| MFA einrichten (inkl. Ersatzcodes aus U1u) | Aktuelles Passwort plus neuer TOTP, Aktion mfa_enroll |
| MFA selbst deaktivieren | Aktuelles Passwort, Aktion mfa_disable |
| Admin setzt fremdes/eigenes Passwort oder MFA zurück | Passwort des Admins, explizites RESET, genaues Zielkonto, getrennte Aktionen admin_password/admin_mfa |
| Rolle, Funktion, Vorstandsstatus, Aktivität bestehender Konten ändern | Passwort des Admins, Zielkonto und Aktion permissions; gewöhnliche Profildaten ohne diese Abfrage |
| Passwort-/MFA-Mailreset, Aktivierung | Bestehender zweckgebundener Einmallink als separater Recovery-Vertrag; kein unerfüllbarer Nachweis des verlorenen Passworts |

Ein signierter Formularnachweis gilt 10 Minuten ab Ausgabe. Er bindet Aktion,
versionierte Identität des Handelnden, zufällige Kennung dieser Anmeldesitzung,
Ziel-ID und Ziel-Zugangsversion. Er enthält keine Passwörter oder Faktorwerte
und ist allein keine Freigabe. Das Passwort wird nur im aktuellen Request geprüft.
Login/Logout/Remember-me-Wiederanmeldung entfernen die Sitzungskennung.

Vor Mutation: handelndes und betroffenes Konto unter DB-Zeilensperren frisch
lesen, aktuelle Login-Identität sowie Adminrechte erneut prüfen. Adminaktionen
verwenden dieselbe Sperrreihenfolge wie der Schutz des letzten Admins (Admins
nach ID, dann Ziel). Fachvalidierung bleibt erforderlich. Jede geschützte
Mutation rotiert die Ziel-Zugangsversion in derselben Transaktion: damit ist
der Nachweis nach Commit verbraucht, auch bei Replay eines alten Sessioncookies.
Keine neue Tabelle/Migration nötig. Diese Technik gilt nur für Aktionen, die
garantiert die Version rotieren; nicht für beliebige Fachmutationen übernehmen.

Die konkreten neuen Werte werden zusammen mit dem frischen Passwort im POST
übermittelt, nicht nach einer allgemeinen Freigabe in einem späteren Request.
Ziel/Aktion sind signiert; es gibt keine Umleitung zur automatischen POST-Wiederholung.

## Abbruch, Fehler und Konkurrenz

- Abbruch/GET ändern keine Credentials und erteilen keine Freigabe. Ein noch
  offenes Formular benötigt weiterhin das Passwort und verfällt nach 10 Minuten.
- Falsches Passwort, falscher Faktor oder Formularfehler: keine Mutation;
  Passwort/Faktor müssen erneut eingegeben werden. Normale Felder bleiben im Formular.
- Abgelaufener/fremder/manipulierter Nachweis oder parallele Sicherheitsänderung:
  ablehnen, keine stillschweigende Übernahme des neuen Kontostands. Formular wird
  mit Fehlermeldung neu angeboten; erneutes Absenden benötigt neuen Passwortbeweis.
- Ist die Identität/Sitzung des Handelnden inzwischen widerrufen oder dessen
  Adminrecht entzogen, direkt 403 statt erneuter Formularausgabe.
- DB-Fehler: Rollback, kein Verbrauch ohne Mutation; Wiederholung benötigt wieder
  das Passwort. Nach Commit verhindert die Zielversion eine zweite Ausführung,
  auch wenn Antwort oder Audit scheitern. Keine Bestätigungspasswörter in Logs/Session.
- Zwei Tabs auf demselben Zielstand: erste erfolgreiche Sicherheitsänderung
  entwertet beide alten Formulare. Andere Zielkonten bleiben getrennt.
- CSRF bleibt aktiv; geschützte POST-Routen werden begrenzt. Antworten no-store.

## Paketgrenzen und noch offene Abnahmen

Mitgliederanlage/Onboarding mit initialen Rechten bleibt ein eigener Vertrag
(noch kein Zielkonto mit Zugangsversion); kein vollständiger F1-Abschluss.
Rollen-/Feldmatrix R13, neue Rechtepfade, Admin-Notfallzugang und Cache-Nutzertrennung
bleiben separat. Keine neuen Rollen, externen Dienste, ENV oder Schlüsselwechsel.
PostgreSQL-Sperren/Parallelität und echte Browser-/Geräteabnahme sind separat nötig.
SQLite-Tests beweisen diese nicht. U1 insgesamt bleibt offen.

Vor einer späteren Veröffentlichung müssen alle Appinstanzen die neue Prüfung
verwenden; Mischbetrieb mit U1v würde weiterhin alte Schreibwege zulassen.
Bereits offene alte Sicherheitsformulare ohne Nachweis werden abgelehnt und
müssen neu bestätigt werden. Die U1v-Migrations-/Cookie-Rolloutgrenze bleibt
bestehen. Keine Veröffentlichung oder Produktionsabnahme in diesem Auftrag.

## Tatsächliche Prüfungen

Erster Lauf: 32 neue Vertragsfälle bestanden (215,56 Sekunden), zunächst mit
Rate-Limit-Decorator. Bestandssuite fand beim frühen Blueprint-Import dessen
uninitialisierte Extension. Auf Request-Zugriff umgestellt; erster Nachlauf
zeigte die fehlende Flask-Limiter-Registrierung im deaktivierten Testmodus.
Die App hält jetzt ihren Limiter explizit unter `gourmen_limiter`. Diese
Zwischenläufe waren fehlgeschlagen/abgebrochen, kein bestandener Gesamtlauf.

Danach fünf ergänzende Fälle bestanden (36,94 Sekunden): erneute Prüfung nach
zwischenzeitlicher Actor-/Zielrotation, keine Mutation des falschen Ziels,
Eingabeerhalt ohne Passwortausgabe und echte 429-Begrenzung mit aktiviertem
Limiter. Weitere vier MFA-Fehlerfälle bestanden (83,82 Sekunden): falscher
Code, CSRF, Commitfehler und gezielter Fehler beim Rendern der Backup-Codes nach
Beginn der Mutation. Der Formular-GET bleibt in diesem Fehlerfall funktionsfähig,
damit der Test nicht schon vor dem eigentlichen POST abbricht.
Vollständiger Lauf: **703 bestanden, 1 fehlgeschlagen**, 1368,86 Sekunden.
Der einzige Fehler war der unten beschriebene Letzter-Admin-Test: sein synthetischer
Eingriff deaktivierte den Handelnden bereits beim Formular-GET. Die Korrektur
beschränkt ihn auf den validierten POST; alle drei Varianten wurden nachgeprüft.
Kein zweiter vollständiger Gesamtlauf behauptet.

Zusätzlich drei gezielte Letzter-Admin-Konkurrenzfälle bestanden (10,78 Sekunden).
Der Test simuliert die fremde Änderung erst nach gültiger POST-Validierung,
nicht schon beim neu hinzugekommenen Formular-GET. Die gesamte bestehende
Sitzungs-Testgruppe mit zusätzlichem `action_session`-Zwischenzustand bestand:
16 Tests, 40,50 Sekunden, einschliesslich Login/Logout/Cookie-Wiederanmeldung.

Ausschliesslich synthetische Daten mit
`run_existing_tests.py`, ohne dotenv und ausgehende Verbindungen.

Abschliessende Fehlerhärtung: ein nach dem Request-Login, aber vor der Sperre
widerrufener/deaktivierter/herabgestufter Handelnder erhält direkt 403. Auch die
Nachweisausgabe an einen inzwischen nicht authentifizierten Handelnden liefert
403 statt eines technischen Fehlers. Abschliessender gezielter Lauf auf diesem
Stand: **56 bestanden**, 150,98 Sekunden (32 Aktionsfälle, sieben ergänzende
Grenzfälle und alle 17 Letzter-Admin-Fälle). Darin sind die beiden zusätzlichen
Fälle für Deaktivierung/Herabstufung während der Anfrage enthalten. Keine
unverändert offene Testfehlermeldung; kein zweiter vollständiger Gesamtlauf.

Whitespace-Prüfung des staged Diff ohne generierte PWA-Kopie fehlerfrei.
Die neue Fingerprint-Kopie übernimmt vorhandene nachgestellte Leerzeichen aus
`pwa.js` unverändert; der vollständige Check meldet diese. Bytegleichheit mit
dem Quellasset und SHA-256-Fingerprint `84fd1755` geprüft. Keine sachfremde
Formatbereinigung des bestehenden PWA-Skripts. PWA 3.16.5; keine neue
Migration. Ausschliesslich lokale Sicherung, keine Veröffentlichung.

# U1v / A-077, A-082: Sitzungen und Gerätevertrauen widerrufen

Stand: 13.10.2026. Lokale Fortsetzung auf «ok, weiter», Basis `f756240`,
Branch `codex/u1v-auth-revocation`. Fachgrundlage ist das bestätigte F1-Regelpaket
in `KONTO_ZUGANG_ENTWURF.md`. Keine erneute Abstimmung bestätigter Fachregeln.

## Technischer Vertrag

Eine zufällige `Member.auth_generation` ist die serverseitige Zugangsversion.
Session und Remember-me enthalten die signierte Identität `id:generation`.
Der Loader verlangt aktive Mitgliedschaft und aktuelle Generation. Alte oder
fehlerhafte Identitäten werden abgewiesen; kontogebundene Zwischenzustände und
veraltetes Gerätevertrauen werden entfernt. Normale Mitglieds-IDs bleiben DB-IDs.

| Ereignis | Wirkung |
|---|---|
| Normale eigene Passwortänderung / erster Pflichtwechsel | Neue Generation atomar mit Passwort/Linkwiderruf. Nur aktuelle Sitzung und ihr bisher gültiges Gerätevertrauen werden nach Commit übernommen; ursprüngliche Vertrauensfrist unverändert. Andere Sitzungen und Remember-me-Cookies verlieren Zugriff. |
| Passwortreset per Mail oder Admin | Alle bisherigen Anmeldungen und Gerätefreigaben ungültig; bestehende MFA bleibt bestehen. |
| Aktivierung per Link | Alte Version ungültig. Bei bestehender MFA weiter zur Anmeldung; ohne MFA neue Sitzung nur für genau die eben committed Generation. |
| MFA-Selbsteinrichtung oder Selbstdeaktivierung | Neue Generation; aktuelle Sitzung bleibt, alle bisherigen Gerätefreigaben und anderen Sitzungen ungültig. Bestehender Neueinrichtungsweg U1u bleibt nutzbar. |
| MFA-Mail-/Adminreset | Alle bisherigen Anmeldungen, Gerätefreigaben und MFA-Zwischenzustände ungültig, auch wenn MFA bereits deaktiviert war. |
| Adminänderung an Rolle, Funktion, Vorstandsstatus oder Aktivität | Neue Generation in derselben Transaktion; keine Übernahme der betroffenen Sitzung. Gewöhnliche Profilfelder lösen keinen Widerruf aus. |
| Deaktivierung | Loader verweigert Zugriff; Rotation verhindert Wiederaufleben alter Cookies bei späterer Reaktivierung. Passwort-/Aktivierungs-/MFA-Resetlinks ebenfalls entwertet. Drive-Verifikation/-Widerruf nach U1s. |

Der Passwortschritt speichert die Generation für die nachfolgende MFA-Prüfung.
Diese prüft aktives Konto und aktuelle Generation unter der Mitgliedssperre.
Eine inzwischen entfernte MFA ist kein Weg zur automatischen Anmeldung.
Auch nach einem Commit muss die erwartete Generation noch gelten; eine durch
parallelen Reset neu geladene Generation darf nicht übernommen werden.
Step-Up bindet sich über `get_id()` ebenfalls an die vollständige Login-Identität.

Gerätevertrauen wird nur nach erfolgreichem TOTP im Login und gesetzter Checkbox
erteilt. Technische Frist: **30 Tage** ab Ausstellung, ohne gleitende Verlängerung.
Der signierte Zustand enthält Mitglied, Generation und beide Zeitpunkte. Alte
100-Jahre-Freigaben ohne Version und fehlerhafte/überlange/abgelaufene Freigaben
werden verworfen. Der alte POST zum Merken ohne erneuten Faktorbeweis liefert
403. Nach Logout kann gültiges Vertrauen den zweiten Faktor eines neuen
Passwortlogins ersetzen; es ist selbst keine laufende Anmeldung. Die bestehenden
separaten Session-/Remember-me-Fristen wurden nicht geändert. Keine neue ENV.

## Migration und Rolloutgrenze

Migration `a07720261013` über `a08920261012`, separat in `24e68fc` gesichert:
additive, nicht nullable Spalte mit Default `0` für bestehende Mitglieder.
Keine vorhandenen Credentials, Schlüssel oder verschlüsselten Daten ändern.
Neue Konten und Rotationen verwenden zufällige Versionen. `0` akzeptiert keine
alten Cookies ohne Versionsanteil.

Upgrade/Downgrade/erneutes Upgrade lokal auf synthetischer SQLite-Tabelle geprüft,
Mitglied bleibt erhalten. Kein produktiver Lauf. Vor Veröffentlichung PostgreSQL
und koordinierten Appwechsel prüfen: alte Cookies erfordern erneute Anmeldung;
ältere Appversionen verstehen die neuen IDs nicht. Kein ungeplanter Mischbetrieb
oder blinder Code-Rollback nach Ausgabe versionierter Cookies. Ein Schema-Downgrade
allein ist kein getesteter App-Rollback. Keine Rotation von CRYPTO_KEY/Signaturschlüssel.

## Tests und Grenzen

Isolierter Runner `run_existing_tests.py`, synthetische Daten, SQLite im Speicher,
dotenv deaktiviert, ausgehende Verbindungen gesperrt. Nachweise:

- Erste 23 neue Widerrufstests bestanden; 111 bestehende Login-/Link-/
  Pflichtwechseltests ebenfalls bestanden (326,01 Sekunden).
- Gesamtlauf: **669 bestanden, 1 fehlgeschlagen**, 924,26 Sekunden. Einziger
  Fehler war die veraltete Annahme des U1s-Migrationstests, dass dessen Revision
  weiterhin der Alembic-Head sei. Der Test prüft jetzt weiterhin einen eindeutigen
  Head und die Existenz seiner Migration, statt spätere Migrationen abzulehnen.
- Nach Korrektur **28 Tests bestanden** (91,80 Sekunden): beide Migrationstests
  und die inzwischen 26 Widerrufsfälle, einschliesslich zwischenzeitlicher
  Resets nach Commit. Kein unverändert offener Testfehler.
- Abschliessende Härtung gegen übergrosse Zeitwerte: **8 Gerätefreigabe-Fälle
  bestanden** (23,18 Sekunden, 19 abgewählt). Die neue Auth-Testdatei enthält
  damit 27 Fälle. Die zusätzliche Migration und dieser zusätzliche Grenzfall
  wurden gezielt geprüft; kein zweiter vollständiger Gesamtlauf behauptet.
- `git diff --check` ohne Fehler. Keine Installation zusätzlicher Dependencies.

Reguläre Testfixtures verwenden nun versionierte Identitäten statt alter IDs;
keine Ausnahme von den Produktionsregeln im Testmodus.

Kein Beweis echter PostgreSQL-Parallelität oder Geräteabnahme. Widerruf greift
bei der nächsten Authentifizierungsprüfung; bereits laufende Requests werden
nicht abgebrochen. Gerätefreigaben sind kontoweit widerrufbar, kein neuer
Einzelgeräte-Verwaltungsbildschirm. Aktionsgebundene erneute Bestätigung,
vollständige Rollen-/Feldmatrix und technischer Admin-Notfallweg bleiben offen.
Dieses Paket ist kein vollständiger U1-Abschluss. Keine Template-/Assetänderung,
kein PWA-Bump, kein Push, Merge, Deploy oder Zugriff auf produktive Daten.

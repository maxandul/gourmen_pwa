# U1-R07: Lokaler Admin-Notfallweg

## Vertrag vor Umsetzung

F1 bestaetigt Wiederherstellungscodes getrennt vom Handy und als letzte Stufe
technische Wiederherstellung ueber den eigenen Hostingzugang. Hier wird nur der
lokale technische Weg implementiert und mit synthetischen Daten nachgewiesen.

Ein Flask-CLI-Befehl richtet sich ausschliesslich an einen vorhandenen aktiven
Systemadmin per Mitglied-ID. Standard ist eine schreibfreie Vorschau. Erst
--apply, verdeckte doppelte Passworteingabe, Operator-/Vorgangsbezug und explizite
Zielbestaetigung erlauben die Mutation. --reset-mfa ist zusaetzlich notwendig,
wenn der zweite Faktor verloren ist; andernfalls bleibt MFA erhalten.

Vor Eingabe gelesene Zugangsversion wird nach Eingabe unter Mitgliedssperre
verglichen. Zwischenzeitliche Kontoaenderung bricht ab. Passwort, Zugangsversion,
Widerruf aller offenen AuthToken-Zwecke und Erfolgs-Audit committen gemeinsam.
Bei MFA-Reset werden TOTP und alle alten Backup-Codes unbrauchbar. Kein neuer
Admin, keine Aktivierung gesperrter Konten, kein Mailversand, kein Drive-Aufruf,
keine Schluesselrotation und keine Aenderung verschluesselter Mitgliedsdaten.
Keine Passwoerter als Argument, Ausgabe, Session- oder Auditinhalt.

## Betriebsablauf (noch keine Hosting-Abnahme)

1. Bei erhaltenem Passwort zuerst einen getrennt aufbewahrten Backup-Code im
   normalen Login verwenden; dieser ist einmalig. Danach MFA neu einrichten
   und die neuen Codes wieder getrennt sichern.
2. Bei vollstaendigem Verlust: eigener Hostingzugang und Identitaet des
   berechtigten Kontoinhabers muessen ausserhalb der App verifiziert sein.
   Projekt, Umgebung und Service explizit pruefen. Wiederherstellbares Backup
   und Freigabe fuer genau diesen produktiven Eingriff sind erforderlich.
   Diese Arbeit erteilt keine Produktionsfreigabe und fuehrt diesen Schritt nicht aus.
3. Im autorisierten Service mit dessen bestehender Konfiguration und
   unveraendertem CRYPTO_KEY zunaechst `flask --app backend.app admin-recover
   --member-id ID` ausfuehren. Keine ENV-/Schluesselwerte ausgeben oder kopieren.
4. Nach Pruefung dieselbe Eingabe um `--apply` ergaenzen; bei verlorenem MFA
   zusaetzlich `--reset-mfa`. Passwort nur im verdeckten interaktiven Prompt
   eingeben. Operatorreferenz und begruendete Vorgangsreferenz ohne Geheimnisse
   angeben; danach die angezeigte Ziel-ID ausdruecklich bestaetigen.
5. Nur die Erfolgsmeldung nach Commit gilt. Bei Abbruch/DB-Fehler nichts als
   erfolgreich protokollieren; Audit/aktuellen Zustand pruefen, keinen blinden
   Wiederholungsautomatismus verwenden. Ein erneuter bewusster Durchlauf verlangt
   neue Eingaben und widerruft erneut alle bisherigen Zugangsstaende.
6. Neu anmelden, bei Faktorverlust MFA sofort neu einrichten, neue Backup-Codes
   sicher ablegen. Alte Sitzungen/Geraete/Links pruefen; sensible Mitgliedsdaten
   muessen lesbar bleiben. Zeitpunkt, Operator, Ziel und Ergebnis im Notfallprotokoll
   erfassen; keine Passwoerter, Codes oder Tokens. PostgreSQL-Sperren und der echte
   Hosting-/Identitaetsnachweis bleiben separat zu belegen.

## Lokale Pruefung

18.10.2026, isolierter Runner ohne dotenv/Netz, synthetisches SQLite:
`tests/services/test_admin_recovery.py`, `tests/routes/test_auth_revocation.py`
und `tests/routes/test_backup_code_login.py`: **53 bestanden, 876 Warnungen,
39.43 s**. Nach Ergaenzung des Ende-zu-Ende-Nachweises (Recovery, Login,
MFA-Neueinrichtung und zehn neue Codes) nochmals gesamte Recoverydatei:
**15 bestanden, 313 Warnungen, 11.20 s**. Erster Versuch 14 bestanden/1 Fehler:
synthetische .test-Adresse wurde vom Loginformular abgewiesen; auf example.com
korrigiert. Keine Produktionsadresse verwendet. Ignorierter pyreadline-
Handlefehler beim Prozessende, Exitcode des erfolgreichen Tests 0.

Geprueft: Vorschau, Abbruch, ungueltige/fehlende/nichtaktive Adminziele,
Passwortregeln, geaenderte Generation, mit/ohne MFA-Reset, erhaltene Rolle und
verschluesselte Nutzdaten, alte Links und Sitzung, Commitfehler ohne partiellen
Reset oder Erfolgsaudit, kein Passwort in Ausgabe/Audit, erneute Einrichtung.
`git diff --check` ohne Fehler. Keine Migration oder neue ENV.

Echte Hostingidentitaet, interaktives Terminal, PostgreSQL-Konkurrenz,
Browser/Geraete und produktive Ausfuehrung nicht geprueft. CLI-Eingaben sind
keine eigenstaendige Verifikation der Operatoridentitaet. U1 bleibt offen.

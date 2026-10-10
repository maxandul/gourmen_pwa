# Anmeldung, Profil und Mitgliederdaten – erster Durchlauf

Stand 2026-09-20. Teilpruefung, kein abgeschlossenes Sicherheitsreview.
Erster Durchlauf: sieben Szenarien, A-075 bis A-078 und Erweiterung A-035.
Zweiter Durchlauf: sieben MFA-Szenarien, A-079 bis A-083 und Erweiterung A-075.
Dritter Durchlauf: acht Profil-/Admin-Szenarien, A-084 bis A-087.
Vierter Durchlauf: sieben Zugangs-/Verwaltungsszenarien, A-088 bis A-090.
Insgesamt 29 isolierte Szenarien.
App-Code und produktive Daten unveraendert.

## Nachweise und Testgrenzen

[AUTH_CHECKS.json](AUTH_CHECKS.json), `check_auth_workflows.py`, AUTH_RUN.txt.
Original-Login, Passwortpruefung, Step-up, Logout, Profil und Passwort-Reset
mit synthetischen Konten. Passwort-Hashing und Tokenverarbeitung nicht ersetzt.
SQLite nur im Arbeitsspeicher; ENV-Laden und Netzwerk blockiert. Keine Mail,
keine produktiven Zugangsdaten. Reset-Tokens direkt ueber den Originalhelfer
ausgestellt, nicht ueber Mail angefordert; keine Tokenwerte im Ergebnis-JSON.

Globaler CSRF-Schutz und Rate-Limit sind in Testing deaktiviert; deren
Wirksamkeit ist durch diesen Durchlauf nicht bewiesen. Das Flask-Login-Caching
im aeusseren Test-App-Kontext wird vor jeder Anfrage entfernt, damit die
Sitzungswechsel tatsaechlich neu ausgewertet werden.

| Szenario | Ergebnis |
|---|---|
| deactivated_account_sessions | Positiv: vorhandene Sitzung wird beim Profilzugriff zum Login umgeleitet; neue Anmeldung des deaktivierten Kontos abgelehnt |
| step_up_cross_account_after_logout | Freigabe von A gilt nach Logout/Login auch fuer sensible Profilseite von B, A-075 |
| first_password_change_bypass | Pflichtwechsel-Hinweis durch Profil-GET oder next umgehbar, A-076 |
| login_protocol_relative_redirect | Externes protokollrelatives next wird akzeptiert, Erweiterung A-035 |
| mfa_login_loses_return_target | Internes next geht beim Uebergang zur MFA-Seite verloren, A-078 |
| reset_password_existing_session | Passwort tatsaechlich geaendert, alte Sitzung bleibt nutzbar; Token hingegen einmalig, A-077 |
| token_expiry_and_purpose_guards | Positiv: abgelaufene, unbekannte und fuer anderen Zweck verwendete Tokens abgelehnt |

Der MFA-Fall prueft bisher nur den Uebergang nach korrektem Passwort;
TOTP-Verifikation, Backup-Codes und Geraetevertrauen sind noch offen.
Die Deaktivierungspruefung umfasst Profilzugriff und normalen Passwort-Login,
nicht alle Rollen, Endpunkte oder einen bereits begonnenen MFA-Vorgang.

## Empfehlungen aus diesem Durchlauf

Sitzungszustand zentral definieren: angemeldet, Passwortwechsel erforderlich,
MFA noch offen, sensible Freigabe und gemerktes Geraet muessen eine klare
Bindung an Mitglied und Sitzung besitzen. Logout/Reset/Kontowechsel brauchen
explizite Aufraeum- und Widerrufsregeln. Rueckkehrziele sollten ueber alle
Loginvarianten einheitlich erhalten und auf interne Ziele begrenzt werden.

## Zweiter Durchlauf: MFA, Backup-Codes und Geraetevertrauen

[MFA_CHECKS.json](MFA_CHECKS.json), `check_mfa_workflows.py`, MFA_RUN.txt.
Echte TOTP-Berechnung, Verifikation und Verschluesselung mit frisch erzeugtem
Schluessel ausschliesslich in der isolierten Test-App. Kein ENV-/Produktionskey
gelesen, geaendert oder rotiert. Synthetische Secrets/Codes nur im Arbeitsspeicher.
Logger-Aufrufe abgefangen, Nachweise als Booleans gespeichert. Kein Mailversand.
Globales CSRF und Rate-Limit weiterhin aus; keine Aussage ueber deren Wirksamkeit.

| Szenario | Ergebnis |
|---|---|
| valid_backup_code_rejected | Gueltiger Hash verifiziert, Login-Code trotzdem abgelehnt, A-079 |
| totp_repeat_and_logging | Derselbe gueltige TOTP meldet zwei Clients an; Code im Logger-Aufruf, A-081 |
| trust_created_before_mfa_enrollment | Vertrauen vor MFA moeglich; spaeterer Login ohne neuen TOTP; Secret im Log, A-081/A-082 |
| reenrollment_cannot_get_fresh_backup_codes | Neueinrichtung aktiv, keine nutzbaren Backup-Codes, A-080 |
| enrollment_secret_survives_account_switch | Einrichtung A/B verwendet denselben zwischengespeicherten Secret, Erweiterung A-075 |
| reset_get_and_old_device_after_reenroll | GET deaktiviert MFA; altes Geraet bleibt nach Neueinrichtung vertraut, A-082/A-083 |
| invalid_totp_and_anonymous_device_guards | Positiv: ungueltiger TOTP abgewiesen; unangemeldetes Geraetevertrauen zum Login umgeleitet |

Wiederholte Verwendung desselben gueltigen TOTP innerhalb des Zeitfensters
reproduziert. Wiederverwendungsschutz, akzeptiertes Zeitfenster und Ratenbegrenzung
im verbleibenden Sicherheitsdurchlauf gemeinsam bewerten; hier noch kein eigener
Befund dazu. Kein Produktionsangriff oder echter Reset.

## Dritter Durchlauf: Profil speichern und sensible Mitgliederdaten

[PROFILE_CHECKS.json](PROFILE_CHECKS.json), `check_profile_workflows.py`,
PROFILE_RUN.txt. Original-Formulare/-Routes, synthetische Mitglieder und
verschluesselte Daten mit frischem Key ausschliesslich in der Test-App.
Keine echten Personendaten und kein ENV-/Produktionskey verwendet.
Zwei Faelle injizieren eine Entschluesselungs-Exception, um das Fehlerverhalten
zu pruefen. Freigabe fuer sensible Daten wird im Test per Session gesetzt;
die echte Passwortbestaetigung wurde im ersten Auth-Durchlauf geprueft.
CSRF/Rate-Limit weiterhin in Testing deaktiviert.

| Szenario | Ergebnis |
|---|---|
| profile_duplicate_email | IntegrityError statt Feldfehler, Originaladresse nach Rollback erhalten, A-084 |
| negative_physical_values | Negative Groesse/Gewicht/Schuhgroesse gespeichert, A-085 |
| clear_optional_and_ignore_privileged_fields | Positiv: Telefon leerbar; eingeschleuste Rolle/Aktivstatus im eigenen Profil ignoriert |
| admin_invalid_numeric_field | «abc» als Groesse wirft ValueError, A-085 |
| self_sensitive_get_deletes_on_error | Entschluesselungsfehler loescht Datensatz beim GET, A-086 |
| admin_sensitive_get_deletes_on_error | Dieselbe Loeschung, danach zusaetzlicher Templatefehler, A-086/A-087 |
| admin_sensitive_valid_data_render | Gueltige Daten bleiben erhalten, aber Template erwartet fehlendes form, A-087 |
| member_admin_and_sensitive_guards | Positiv: fremde Admin-Bearbeitung und sensible Admin-Daten 403; eigene sensible Seite ohne Freigabe leitet zum Step-up |

Keine vollstaendige Feld-/Rollenmatrix: beispielsweise Admin-Rollenaenderungen,
Legacy-Auswahlwerte und sensible POST-Daten sind noch nicht abschliessend geprueft.

## Vierter Durchlauf: Google, Kalender und Administration

[ACCESS_CHECKS.json](ACCESS_CHECKS.json), `check_access_lifecycle.py`, ACCESS_RUN.txt.
Original-Routes, Testdaten und lokale Feed-Generierung. Mailtransport und
Drive-Einladung/-Entfernung ersetzt. Verifikationslink aus dem abgefangenen
synthetischen Mailtext verwendet; keine Links/Tokens in Ergebnisdatei gespeichert.
DRIVE_FEATURE_ENABLED nur in der isolierten App aktiviert. Kein externes Konto
oder Mitglied veraendert; CSRF/Rate-Limit weiterhin in Testing deaktiviert.

| Szenario | Ergebnis |
|---|---|
| old_email_token_verifies_new_address | Alter Mail-Link verifiziert neue Adresse und stoesst deren Invite an, A-088 |
| google_address_change_no_revoke | Verifikationsstatus zurueckgesetzt, kein Drive-Widerruf, A-089 |
| inactive_google_verification_guard | Positiv: deaktiviertes Mitglied wird nicht verifiziert/eingeladen |
| calendar_enable_regenerate_disable | Positiv: wiederholtes Aktivieren behaelt Token; Erneuern sperrt alten Link; Deaktivieren sperrt neuen Link |
| inactive_calendar_guard | Positiv: deaktiviertes Mitglied erhaelt keinen Feed (404) |
| last_admin_self_demotion | Null aktive Admins nach eigener Rollenherabstufung, A-090 |
| member_deactivation_no_drive_revoke | Mitglied deaktiviert, kein Drive-Widerruf, A-089 |

Kalenderpruefung umfasst hier leeren Feed und Token-Lebenszyklus. Kein Nachweis
fuer aktualisierte Inhalte in echten Kalender-Clients, Cache-Widerruf bereits
heruntergeladener Daten oder vollstaendige Event-/Audience-Abdeckung.

## Offene Fortsetzung

- TOTP/Backup-Codes: restliche Fehler-/Abbruchwege, Wiederverwendungsschutz,
  Zeitfenster, Deaktivierung des Kontos waehrend MFA, Konkurrenz und Ratenbegrenzung.
- Gemerkte Geraete: Berechtigung zum Anlegen, Gueltigkeit, Logout, Passwort- und
  MFA-Reset, Widerruf anderer Sitzungen/Geraete. Erste Reset-/Neueinrichtungsfolge
  oben geprueft; Admin-Wege und Passwort-Reset offen.
- Passwort-/MFA-Reset und Aktivierung: mehrere gueltige Tokens, Mailfehler,
  Ablaufgrenzen, parallele Nutzung, Admin-Wege und verpflichtender Passwortwechsel.
- Profil speichern: restliche Felder/Leerwerte/Legacy-Werte, Mail-Normalisierung,
  sensible POST-Formulare, Fehlererhalt, Step-up-Ablauf waehrend Bearbeitung.
  Erste Duplikat-/Leerwert-/Zahlenfaelle und Rechtekontrollen oben dokumentiert.
- Mitgliederverwaltung: Rollen-/Funktionsaenderungen, Admin-Schutz, Deaktivierung,
  Sicherheitsuebersicht, Initialpasswort und sichtbare Mitgliederdaten.
- Google-Adresse: doppelte Adressen, Invite-/Mailfehler, erneute Einladung und
  Wiederherstellung externer Berechtigungen. Kalender: Inhalte/Audience, ETag,
  Aenderungen/Loeschungen und echte Kalender-Clients; Token-Widerruf oben geprueft.
- Session-Cookies, produktive Konfiguration, CSRF, reale Rate-Limits,
  Audit-Logging und Browser-/PWA-Verhalten bei Kontowechsel.

## Querschnitts-Nachtrag: Auditfehler

AUDIT_FAILURE_REVIEW.md prueft unter anderem zwei Login-Pfade und die Kalender-
Aktivierung bei einem synthetischen Audit-Insertfehler. Login ohne next scheitert
im Folgezugriff, Login mit lokalem next funktioniert ohne Protokolleintrag;
Kalenderaktivierung bleibt erfolgreich gespeichert (201), ebenfalls ohne Audit.
A-137 erweitert. Keine MFA-/Admin-/Produktivfreigabe daraus ableiten.

## Mitgliederanlage und Versand vom 2026-09-28

Fuenf Gruppen in [ONBOARDING_FAILURE_CHECKS.json](ONBOARDING_FAILURE_CHECKS.json),
check_onboarding_failures.py. Originalformular, Route, Passwort-Hashing und
Audit-Writer; MailService.send vollstaendig ersetzt. Synthetischer Admin und
Neumitglied, SQLite im Speicher, keine realen Nachrichten oder Zugangsdaten.

| Fall | Antwort | Dauerhaft gespeichert |
|---|---|---|
| Erfolg | 302 und success | Konto, Token, beide Audit-Eintraege. |
| Mail liefert success=false | 302 und warning | Konto, Token, beide Audit-Eintraege. |
| Erster Audit-Insert scheitert | PendingRollbackError | Konto, kein Token und kein Audit; Versand-Mock zuvor erfolgreich. |
| Zweiter Audit-Insert scheitert | PendingRollbackError | Konto, Token, erster Audit-Eintrag. |
| Versand wirft unerwartete Exception | RuntimeError | Konto, kein Token und kein Audit. |

A-139 zur Versand-/Speicherreihenfolge; A-137 erweitert. Die Probe
pending_token_in_session=false bedeutet nur, dass der Token beim Versand
nicht mehr in session.new liegt (Autoflush moeglich); sie belegt keinen Commit.
Massgebend ist die DB-Pruefung nach Request-Ende/Rollback. Kein Link/Tokenwert
wurde in Bericht oder Ausgabe uebernommen.

Ein erster Skriptstart scheiterte vor App-Erzeugung am falschen Mail-Importpfad;
danach bestanden alle fuenf Gruppen. Globale Testing-CSRF-/Rate-Limits aus.
Echte Zustellung, Wiederholung der Mitgliederanlage, erneute Einladung und
parallele Aktivierungen bleiben offen; Mail-Exception ist eine injizierte
Vertragsgrenze, keine nachgewiesene normale Rueckgabe des Mail-Service.

## Wiederaufnahme der Mitgliederanlage vom 2026-09-28

Drei Gruppen mit jeweils zwei Original-POSTs in
[ONBOARDING_RETRY_CHECKS.json](ONBOARDING_RETRY_CHECKS.json),
check_onboarding_retry.py. Gemeinsame Fixture aus check_onboarding_failures.py
als importierbarer Helfer weiterverwendet; bestehende Einzelproben bleiben
ueber dessen direkten Aufruf verfuegbar.

| Erster Verlauf | Zweiter identischer Erstellen-POST |
|---|---|
| Erfolgreiche Anlage | IntegrityError, genau ein Mitglied/ein Token, kein neuer Mailaufruf. |
| Anlage mit gemeldetem Mailfehler | IntegrityError, genau ein Mitglied/ein Token, kein neuer Mailaufruf. |
| Anlage mit erstem Auditfehler | IntegrityError, genau ein Mitglied/kein Token, kein neuer Mailaufruf. |

A-084 um Duplikatbehandlung in der Anlage erweitert; A-139 um fehlende
Wiederaufnahme. Kein zweites Mitglied wurde angelegt. Gleiche Mailadresse,
keine Aussage zu Gross-/Kleinschreibung, Leerzeichen oder Parallelitaet.

Quellensuche nach ONBOARDING/Onboarding und SEND_ONBOARDING_MAIL in backend
zeigt Token-/Mail-Erstellung in admin.create_member und Nutzung in auth.activate;
kein separater Wiederholungs-/Einladungsversandpfad gefunden. Admin-Sicherheits-
templates bieten Passwort-/MFA-Reset, keine eigene Onboarding-Neusendung.
Passwort-Reset ist ein anderer Ablauf und wurde hier nicht als Ersatz getestet.
Empfehlung: bestehendes Mitglied mit Aktivierungs-/Versandstatus anzeigen und
kontrollierte Neusendung anbieten, statt das Anlageformular erneut abzusenden.

Weiterhin 139 Befunde. Mail vollstaendig abgefangen; SQLite im Speicher,
Originalformular/-route, Testing-CSRF/Rate-Limits deaktiviert. Kein echter
Versand, keine Browser-/Produktivpruefung.

## Aktivierungsgrenzen vom 2026-09-28

Sechs Gruppen in [ACTIVATION_BOUNDARY_CHECKS.json](ACTIVATION_BOUNDARY_CHECKS.json),
check_activation_boundaries.py. Originalformular/-route, lokale Passwortpruefung,
synthetische Tokens und Mitglieder; SQLite im Speicher. Keine echten Mails.

| Fall | Ergebnis |
|---|---|
| Normaler Abschluss und erneuter Aufruf | Passwort gesetzt, Token verbraucht, Session angemeldet, ein Audit. Erneuter POST mit frischem unangemeldetem Client zur Loginseite, keine weitere Aenderung. |
| Abgelaufener Link | Zur Anmeldung, Passwort/Token unveraendert. |
| Deaktiviertes Mitglied | Zur Anmeldung, Passwort/Token unveraendert, keine Session. |
| Token fuer anderen Zweck | Zur Anmeldung, keine Aenderung. |
| Zu kurzes Passwort | Formular erneut mit 200, keine Aenderung und Token weiter unbenutzt. |
| Audit-Insertfehler nach Commit | PendingRollbackError, Passwort gesetzt und Token verbraucht, keine Login-Session/kein Audit. Wiederholung fuehrt zur Anmeldung, ohne weiteren Zustandswechsel. |

A-137 erweitert, weiterhin 139 Befunde. Empfehlung: nach gespeichertem Passwort
den erfolgreichen Teil des Vorgangs auch bei Protokollfehler nachvollziehbar
abschliessen; keinen Eindruck vermitteln, das Passwort sei nicht gesetzt worden.
Keine dauerhafte Kontosperre nachgewiesen, normaler Login nach diesem Teilfehler
hier noch nicht getestet.

Erster Skriptstart scheiterte am Import der Auth-Routen vor App-Initialisierung;
Reihenfolge im Audit-Skript korrigiert, danach alle sechs Gruppen erfolgreich.
Tokens und Passwortwerte nicht ausgegeben. Testing-CSRF/Rate-Limits aus.
Exakter Ablaufzeitpunkt, parallele Linknutzung, bereits angemeldete andere Konten,
MFA-aktivierte Konten und Browserdarstellung bleiben offen.

## Aktivierung und Sessionzustand vom 2026-09-28

Drei Gruppen in [ACTIVATION_SESSION_CHECKS.json](ACTIVATION_SESSION_CHECKS.json),
check_activation_sessions.py. Originalrouten, synthetische Konten/Token,
direkt gesetzter MFA-Status ohne echtes Geheimnis oder generierten TOTP-Code.

| Fall | Ergebnis |
|---|---|
| Gueltiger Onboarding-Token plus aktiviertes MFA | Normaler Login verlangt MFA. Aktivierung erzeugt ohne MFA-Pruefung volle Session, Dashboard 200; A-140. |
| Anderes Konto schon angemeldet | Weiterleitung zum Dashboard des bestehenden Kontos; Zielpasswort und Token bleiben unveraendert. |
| Normaler Login nach Aktivierungs-Auditfehler | Anmeldung mit neuem Passwort funktioniert. Keine dauerhafte Kontosperre im Fall ohne MFA. |

A-137-Recovery damit praezisiert; neuer bedingter Sicherheitsbefund A-140,
insgesamt 140 Befunde. Der MFA-Fall belegt den abweichenden Zugangspfad, noch
nicht die Entstehung dieser Token-/MFA-Kombination ueber normale UI-Schritte.
Regulaere Reihenfolge, Tokenwiderruf beim MFA-Setup und alte Aktivierungslinks
als naechste Gegenpruefung offen. Kein reales Konto/2FA-Setup veraendert.
SQLite im Speicher, CSRF/Rate-Limits im Testing deaktiviert; keine Browser-
oder Produktionsabnahme und keine echten Tokens/Passwoerter ausgegeben.

## Erreichbarkeit des MFA-/Aktivierungszustands, abgeschlossen 2026-10-10

Eine zusammenhaengende Originalrouten-Probe in
[ONBOARDING_MFA_SEQUENCE_CHECKS.json](ONBOARDING_MFA_SEQUENCE_CHECKS.json),
check_onboarding_mfa_sequence.py. Admin-Anlage erzeugt das Konto und den Link;
nur Mailversand abgefangen. Danach normale Anmeldung mit Anfangspasswort,
MFA-Einrichtung ueber GET/POST mit lokal erzeugtem gueltigem TOTP. Keine
MFA-Zeile oder Aktivierungsverknuepfung manuell gesetzt.

Ergebnisse: Kontoerstellung 302; Anfangspasswort ermoeglicht angemeldete Session;
MFA-Einrichtung 200/302, MFA anschliessend aktiv. Onboarding-Token bleibt unbenutzt.
Kontrolllogin fordert zweiten Faktor. Frischer Client mit Aktivierungslink und
neuem Passwort bekommt dagegen volle Session ohne MFA-Pruefschritt, Dashboard 200.

A-140 damit ueber vorhandene Anwendungsablaeufe erreichbar, weiterhin 140
Befunde. Empfehlung priorisieren: vorhandenes MFA auch auf Aktivierungsweg
durchsetzen und Lebensdauer unbenutzter Einladungslinks bei Kontouebergaengen
verbindlich regeln. Besitz eines noch gueltigen Links bleibt Voraussetzung.
Keine Aussage ueber reale betroffene Mitglieder oder einen erfolgten Angriff.

SQLite im Speicher, echte lokale TOTP-/Verschluesselungslogik mit neuem reinem
Testschluessel im Prozess; keinerlei ENV-/Produktionsschluessel geaendert.
Bekanntes Secret-Debuglogging waehrend dieser Probe unterdrueckt; weder
Passwoerter noch Token/Schluessel ausgegeben. Keine Mail versendet. Testing-
CSRF/Rate-Limits aus, keine Browser-/Postgres-Abnahme. Pruefung am 2026-09-28
begonnen und nach Umgebungsfortsetzung am 2026-10-10 abgeschlossen; Berichtsdatum
an Abschluss angepasst, keine Datumsgrenzenpruefung aus diesem Lauf abgeleitet.

## Alte Zugangslinks nach Passwortaenderung, 2026-10-10

Vier isolierte Ablaufgruppen in
[CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json](CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json),
check_credential_token_lifecycle.py. Originaler Ausgabehelfer, Formulare und
Login-/Passwortwechsel-/Reset-/Aktivierungsrouten, keine Versandroute.

| Aelterer, noch unbenutzter Link | Zwischenzeitliche Aktion | Ergebnis bei anschliessender Linknutzung |
|---|---|---|
| Aktivierung | Passwortwechsel nach normalem Login | Passwort erneut ueberschrieben, volle Session |
| Aktivierung | Passwort-Reset mit anderem Link | Passwort erneut ueberschrieben, volle Session |
| Passwort-Reset | Passwortwechsel nach normalem Login | Passwort erneut ueberschrieben, Weiterleitung zur Anmeldung |
| Passwort-Reset | Passwort-Reset mit neuerem Link | Passwort erneut ueberschrieben, Weiterleitung zur Anmeldung |

In allen Gruppen wird das zwischenzeitlich gesetzte Passwort nach alter
Linknutzung abgelehnt. Der verwendete Link wird anschliessend korrekt verbraucht:
erneute Nutzung mit frischem Client aendert das Passwort nicht mehr.

Neuer A-141 zum fehlenden Widerruf anderer ausstehender Links, insgesamt 141
Befunde. A-140 behandelt MFA auf dem Aktivierungsweg, A-077 bestehende Sessions.
Empfehlung: Passwortaenderung und Widerruf ueberholter Zugangslinks in derselben
Transaktion; andere Tokenzwecke separat regeln. Grundlage fuer Recovery:
[OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html),
Account Recovery After Suspected Compromise; Ausweitung auf normalen
Passwortwechsel ist eine projektspezifische Empfehlung.

SQLite im Speicher, synthetische Token/Konten, ausgehendes Netzwerk blockiert,
keine Mail, keine echten Zugangsdaten ausgegeben. Testing-CSRF/Rate-Limits aus.
Keine Browser-/Postgres-/MFA-/Parallelitaetsabnahme. Noch offen: Ausgabe ueber
normale Reset-Anfrage mit mehreren Links, Admin-Passwortwechsel und Verhalten
anderer Tokenzwecke; kein realer Kontobestand untersucht. Alle vier Gruppen
einschliesslich Wiederverwendungskontrollen ohne Assertionfehler abgeschlossen.

## Reset-Anfragen und administrativer Passwortreset, 2026-10-10

Zwei Folgegruppen in [RESET_REQUEST_SEQUENCE_CHECKS.json](RESET_REQUEST_SEQUENCE_CHECKS.json),
check_reset_request_sequence.py. Die Links entstehen diesmal ausschliesslich
ueber originale Passwort-vergessen-POSTs. MailService.send_async wird vor
Thread/Versand abgefangen; synthetische Linkwerte bleiben im Prozess.

| Folge | Bestaetigtes Ergebnis |
|---|---|
| Zwei Reset-Anfragen, neueren Link verwenden, dann aelteren | Beide Anfragen erzeugen unterschiedliche gespeicherte Tokens. Aelterer Link bleibt nach erstem Reset unbenutzt und kann das Passwort nochmals ueberschreiben. |
| Reset-Anfrage, Admin-Login und Step-Up, Admin-Passwortreset, alten Link verwenden | Originaler Admin-Reset erzeugt ein neues Passwort. Alter Link bleibt verwendbar und ersetzt es; das Admin-Passwort wird danach abgelehnt. |

A-141 damit um regulaere Ausstellung und administrativen Reset erweitert;
weiterhin 141 Befunde. Kein weiterer Befund fuer dieselbe Ursache. Empfehlung:
alle Passwortaenderungswege in denselben Vertrag zur Entwertung offener
Zugangslinks aufnehmen. Besitz eines noch gueltigen geheimen Links erforderlich.

Erster Lauf scheiterte an einer falschen erwarteten URL im Audit-Skript
(/admin/show-temp-password statt /admin/temp-password). Erwartung gegen
Routendeklaration korrigiert; kompletter Wiederholungslauf mit beiden Gruppen
erfolgreich. Keine App-Korrektur. SQLite im Speicher, kuenstliche Mitglieder,
keine echten Mails oder ausgegebenen Passwoerter/Tokens/Cookies. CSRF und
Rate-Limits in Testing aus. Browser, MFA, konkurrierende Anfragen, weitere
Tokenzwecke und produktiver Bestand weiterhin offen.

## Alte MFA-Reset-Links nach Neueinrichtung, 2026-10-10

Zwei Gruppen in [MFA_RESET_LINK_LIFECYCLE_CHECKS.json](MFA_RESET_LINK_LIFECYCLE_CHECKS.json),
check_mfa_reset_link_lifecycle.py. Originale Anmeldung, MFA-Einrichtung mit
gueltigem lokalem TOTP, Backup-Code-Seite, Reset-Anfrage und Reset. Beim
Admin-Fall zusaetzlich originales Admin-Login und Step-Up. Nur Mailversand
abgefangen; Schluessel ausschliesslich neu im Prozess erzeugt.

| Folge nach erster MFA-Einrichtung | Bestaetigtes Ergebnis |
|---|---|
| Zwei MFA-Reset-Links anfordern, neueren nutzen, 2FA neu einrichten, aelteren nutzen | Alter Link deaktiviert die neue 2FA und loescht die neuen Ersatzcodes. |
| MFA-Reset-Link anfordern, Admin setzt MFA zurueck, 2FA neu einrichten, alten Link nutzen | Gleiche Wirkung nach administrativer Wiederherstellung. |

Beide Neueinrichtungen nutzen ein anderes Geheimnis als zuvor. Kontrolllogin
verlangt danach MFA. Nach Verwendung des alten Links gelingt Passwort-Login
ohne Faktor. Nach dritter Einrichtung ist die Wiederverwendung desselben
verbrauchten Links korrekt gesperrt und MFA bleibt aktiv. Zur Ausloesung wurde
POST verwendet; GET-Mutation ist der bereits separate Befund A-083.

A-141 um MFA-Reset-Links erweitert, weiterhin 141 Befunde. Gemeinsame Ursache:
fehlender Widerruf ausstehender Links bei Wechsel des Zugangszustands. A-082
behandelt dagegen gespeichertes Geraetevertrauen. Empfehlung: ausstehende
MFA-Reset-Links bei Reset/Neueinrichtung entwerten und diese Regel auch beim
administrativen Reset anwenden. Gueltiger unbenutzter Altlink erforderlich;
fuer die anschliessende Anmeldung ausserdem das Passwort.

Erster Lauf erwartete Backup-Codes bereits nach dem Einrichtungs-POST; sie
entstehen erst auf der anschliessenden Backup-Code-Seite. Pruefskript um diesen
originalen GET ergaenzt, danach beide Gruppen vollstaendig erfolgreich.
Keine App-Aenderung. SQLite im Speicher; Logging von Geheimnissen unterdrueckt,
keine echten Konten, Mails, Produktionsschluessel oder ausgegebenen Secrets.
Testing-CSRF/Rate-Limits aus. Postgres, Browser, parallele Verwendung, genaue
Ablaufgrenze und produktiv vorhandene Altlinks weiterhin nicht geprueft.

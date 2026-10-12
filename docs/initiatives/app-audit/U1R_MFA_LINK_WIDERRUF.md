# U1r – Alte MFA-Resetlinks bei Faktoränderungen entwerten

Stand: 12. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1r-mfa-link-revocation`, Basis U1q-Commit `0c9543a`.
Umfang: MFA-Anteil A-141. Nutzer wünscht Mitteilung bei sinnvollem Agentwechsel.
Nach U1r ist der Übergang zum grösseren A-089-Paket ein geeigneter Schnitt;
Fortsetzung in `FORTSETZUNG_NACH_U1R.md` vorbereitet.

## Änderung

Erfolgreiche 2FA-Einrichtung, Selbstdeaktivierung, bestätigter Mail-Reset und
Admin-Reset entwerten offene MFA-Resetlinks desselben Kontos. Admin-Reset tut
dies auch bei bereits deaktivierter 2FA. Ein alter Link kann deshalb eine
später eingerichtete 2FA nicht erneut deaktivieren oder neue Backup-Codes löschen.
Neuer Versand ersetzt ältere Links desselben Zwecks; andere Tokenzwecke und
andere Mitglieder bleiben erhalten. Format und bestehende Gültigkeit unverändert.

Widerruf und Faktoränderung liegen in derselben Transaktion. Die betroffenen
Wege sperren die Mitgliedszeile wie die Passwortwege aus U1q. Nach der Sperre
werden MFA-Stand und ggf. Link neu geprüft. Eine zwischenzeitlich erfolgte
Aktivierung wird nicht durch ein älteres Einrichtungsformular überschrieben.
Der Mail-Reset bleibt ein bestätigter POST mit CSRF; GET/HEAD bleiben gemäss U1k
ohne Resetwirkung. Keine neue Pflicht-MFA, Rollenregel oder Recovery-Fachregel.

## Prüfungen

Vor dem Fix: **5 von 7 gezielten Tests fehlgeschlagen**, zwei Kontrollfälle
bestanden. Nach Fix sieben bestanden. Mit Ergänzungen: **16 Tests bestanden**
in 11,51 Sekunden bei 385 Warnungen.

Abgedeckt: alle vier Faktoränderungen mit alten Links; Neueinrichtung mit neuem
synthetischem Geheimnis und anschliessender Versuch, alte Links erneut zu
verwenden; Erhalt von aktivierter 2FA und neuen Backup-Codes; zwei echte
Reset-Anfragen mit ersetztem Mailversand; ungültiger Code/Passwort; Admin-Reset
bei bereits deaktivierter MFA; Rollback von Reset, Einrichtung und Ausgabe;
zwischen Bestätigung und Mutation abgelaufener/verwendeter Link oder deaktiviertes
Konto; zwischenzeitliche Aktivierung; Erhalt anderer Konten/Tokenzwecke.

Synthetische Konten und Schlüssel, echte TOTP-/Verschlüsselungsfunktionen,
SQLite im Speicher, Mail/Audit ersetzt. Bestehender isolierter Teststarter
verhindert dotenv/Netzwerk. CSRF in neuen Ablaufprüfungen gemäss Testing-Konfiguration
aus; bestehende U1k-Tests prüfen CSRF und bestätigten POST weiterhin.

Gesamtlauf: **548 Tests bestanden**, 4892 Warnungen, 302,67 Sekunden.
`git diff --check` ohne Befund. Die Warnungen sind kein Nachweis einer
warnungsfreien Abnahme; die Tests endeten ohne Fehler.

## Grenzen

Mit U1q sind die in A-141 dokumentierten Passwort- und MFA-Linkfolgen lokal
bearbeitet. Kein echter PostgreSQL-Paralleltest: Sperrstrategie setzt READ
COMMITTED voraus und muss vor Veröffentlichung mit parallelen Prozessen geprüft
werden. Gezielte Zwischenänderungen sind kein Ersatz für diese Abnahme.

Gerätevertrauen, andere Sitzungen, vollständige Identitätsprüfung/Recovery,
Pflichtwechsel A-076 und Drive-Widerruf A-089 bleiben separat. Der bestehende
Einrichtungs-GET kann weiterhin eine leere MFA-Zeile anlegen; dieser allgemeine
Formularablauf ist hier nicht überarbeitet. Keine Migration, Templates/Assets,
neue Abhängigkeit oder produktive Schlüssel geändert.

Kein Push, Deploy, Merge auf master, echter Versand oder Produktionsdatenzugriff.
Fremde lokale Dateien und gesicherte Planung erhalten. Offene visuelle Abnahme
aus U1k bleibt bestehen. Agentwechsel empfohlen, nicht automatisch durchgeführt.

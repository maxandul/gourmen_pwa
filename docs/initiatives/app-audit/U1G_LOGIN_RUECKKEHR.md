# U1g – Sichere Rückkehr nach der Anmeldung

Stand: 11. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1g-login-return-target`, Basis U1f-Commit `66595fb`.
Umfang: A-078 und der unmittelbar betroffene Login-Anteil von A-035.

## Verhalten

Ein internes Ziel wie `/member/profile?tab=details#contact` bleibt nach dem
Passwortschritt für die MFA-Prüfung erhalten. TOTP und Wiederherstellungscode
führen nach erfolgreicher Prüfung dorthin zurück. Fehlerhafte MFA-Eingaben
und erneutes Anzeigen des MFA-Formulars erhalten das Ziel. Neue `next`-Angaben
am MFA-Endpunkt ersetzen es nicht.

Das Ziel steht zusammen mit der ausstehenden Mitglieds-ID in der signierten
Session. Ein neuer GET/POST auf die Anmeldung beendet den bisherigen Vorgang,
auch bei falschem Passwort. Login, Logout und Cookie-Wiederanmeldung entfernen
das gespeicherte Ziel über die bestehenden Auth-Signale. Ohne ausstehendes Konto
wird ein zurückgebliebenes Ziel verworfen.

Passwort-Login, Anmeldung mit gemerktem Gerät und MFA verwenden denselben
Prüfer: nur interne root-relative Adressen; externe/protokollrelative Ziele,
Backslashes und Steuerzeichen im Pfad werden verworfen. Query und Fragment
zulässiger Ziele bleiben erhalten. Ungültige Ziele führen zum bisherigen
Standardziel. Die Zielroute prüft weiterhin ihre eigenen Zugriffsrechte.

## Nachweise

Tests mit echten Routen, synthetischen Konten, festem ausschliesslich lokalem
Testschlüssel, echtem TOTP und gesalzenem Backup-Code-Hash. Nach Korrektur der
Testkonfiguration reproduzierte der Vorher-Lauf **10 Fehler, 12 bestandene Tests**.
Nach Umsetzung bestanden diese **22 Tests**. Zusätzlich: Abbruch durch falsches
Passwort, verwaistes Ziel, 20 Prüferfälle und erweiterte Auth-Lifecycle-Regression.

Gesamtlauf über `run_existing_tests.py`, gebündeltes Python, SQLite im Speicher,
ohne dotenv und mit gesperrtem ausgehendem Netzwerk. Keine echten Konten oder
Zugangsdaten. Testing-CSRF und Rate-Limits deaktiviert.

Abschluss: **265 Tests bestanden**, davon **44 neue Tests**, in 137,38 Sekunden
bei 1846 Warnungen. `git diff --check` ohne Fehler. Templates, Assets und
gesicherte Mockups unverändert.

## Grenzen und weitere Pakete

- A-035 ist nur für Passwort-/MFA-Login bearbeitet. Step-Up, Event-, Merch- und
  Dokument-Weiterleitungen bleiben eigene Arbeit; kein appweiter Abschluss behauptet.
- Passwortwechselpriorität, insbesondere A-076, bleibt unverändert. Ziele werden
  nicht über einen anschliessenden Pflichtwechsel hinweg zwischengespeichert.
- Keine neue Frist für den bestehenden ausstehenden MFA-Vorgang eingeführt.
  Rückkehr zur Anmeldeseite beendet ihn; blosses Schliessen eines Tabs ist kein
  serverseitig erkennbarer Abbruch. Mehrere Tabs teilen dieselbe Session und
  starten beim erneuten Login bewusst einen neuen Vorgang.
- Keine Änderung an Gerätevertrauen, MFA-Reset oder globalem Sitzungswiderruf.
- Keine Templates/Assets, Migrationen, Produktionsdaten oder Schlüssel verändert.
  Kein Push, Deploy oder Merge auf master. Fremde Dateien und Planung erhalten.

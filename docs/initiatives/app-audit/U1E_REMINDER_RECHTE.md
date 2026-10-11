# U1e – RSVP-Versandberechtigung vereinheitlichen

Stand: 11. Oktober 2026. Nächster lokaler Umsetzungsschritt auf «ok weiter».
Branch `codex/u1e-reminder-permissions`, Basis U1d-Commit `f8a40f9`.
Vorhandener Befund A-043; bestätigte Eventorganisator-/Admin-Regel übernommen.
Keine neue Rollenentscheidung oder Gesamtaudit-Runde.

## Änderung

Der ältere Formularpfad prüfte das Methodenobjekt `current_user.is_admin`
statt dessen Ergebnis. Dadurch erreichten normale Mitglieder den Versandservice.
Beide vorhandenen RSVP-Einstiege verwenden jetzt denselben Helper
`_can_send_participation_reminders(event)`, der `is_admin()` tatsächlich aufruft
und alternativ die Organisator-ID dieses Events prüft.

Event-Sichtbarkeit wird weiterhin zuerst geprüft. Vorstandsstatus oder eine
andere Vereinsfunktion allein erlauben keinen RSVP-Versand. Bei Ablehnung
antwortet die JSON-API wie bisher mit 403; die Formularroute behält ihre
Weiterleitung zum Event mit präzisierter Fehlermeldung. Beide bleiben erhalten,
damit vorhandene Aufrufer funktionieren. Keine Änderung der Empfängerauswahl,
Versandlogik, Audit-Ereignisse oder Erfolgsantworten.

## Regression

`tests/routes/test_reminder_permissions.py` prüft beide Originalrouten mit
synthetischen Mitgliedern/Events. Der komplette Versandservice ist gemockt.

30 Fälle: beide Einstiege, allgemeine und vorstandsbezogene Events, anonyme
Person, normales Mitglied, Vorstand, Schatzmeister, zugewiesener Organisator
und Admin. Zusätzlich fehlendes Event, unerlaubtes GET und fehlendes CSRF-Token
bei ausdrücklich eingeschaltetem CSRF-Schutz. Bei gesperrtem Zugriff wird kein
Service-Aufruf zugelassen, bei erlaubtem genau einer mit der richtigen Event-ID.

Vor Fix: **4 fehlgeschlagen, 26 bestanden**. Die vier Fehler zeigen den
unberechtigten Service-Aufruf über die Formularroute. Nach Fix: **30 bestanden**.
Ausführung mit gebündeltem Python und vorhandenem isoliertem Audit-Teststarter,
ohne dotenv oder ausgehendes Netzwerk; SQLite im Speicher, keine Produktion.
Abschlusslauf: **210 Tests bestanden**, darunter **30 neue U1e-Tests**,
in 74,46 Sekunden; keine Fehler oder übersprungenen Tests. 1519 bestehende
Legacy-/Deprecation-Warnungen; keine Warnungsbereinigung in diesem Paket.
`git diff --check` bestanden. Templates/Assets unverändert gegenüber `f8a40f9`,
Mockups unverändert gegenüber `551e1ef`. Code, Tests und Dokumentation werden
gemeinsam als lokaler Commit gesichert.

## Grenzen

Keine vollständige Rollenmatrix der gesamten App. Zusätzliche Bereichsrechte
werden in diesem Paket nicht eingeführt. Keine Änderung an separaten Befunden
zu Reminder-Empfängern, Wiederholungen oder Lieferfehlern (u.a. A-044/A-111/A-112).
Keine Templates/Assets, Datenbankschemata oder neuen Dependencies.
Kein echter Versand, Push, Deploy, Merge auf master oder Schlüsselwechsel.
Planungsunterlagen und fremde lokale Dateien bleiben erhalten.

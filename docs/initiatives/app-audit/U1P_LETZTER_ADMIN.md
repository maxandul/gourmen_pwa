# U1p – Letzten aktiven Admin bewahren

Stand: 12. Oktober 2026. Lokale Fortsetzung auf «ok weiter».
Branch `codex/u1p-last-active-admin`, Basis U1o-Commit `9d88a0d`.
Umfang: A-090 im vorhandenen Admin-Mitgliederformular. Technischer Schutz des
bestätigten Betriebs mit einem einzigen Systemadmin, kein neues Rollenmodell
und keine Pflicht zu einem zusätzlichen Admin im Normalbetrieb.

## Änderung

Das Mitgliederformular lehnt Herabstufung oder Deaktivierung des letzten aktiven
Admins ab. Inaktive Admins und gewöhnliche aktive Mitglieder gelten nicht als
Ersatz. Die Felder Rolle/Aktivstatus zeigen den Fehler und erläutern die mögliche
Übergabe an ein anderes aktives Mitglied. Alle weiteren Eingaben bleiben im
Formular erhalten; keine Teiländerung und kein Erfolgs-Audit bei Ablehnung.

Ein zweiter aktiver Admin ermöglicht weiterhin die Änderung. Gewöhnliche
Änderungen am letzten Admin und Deaktivierung gewöhnlicher Mitglieder bleiben
möglich. Die Administration wird nicht automatisch neu besetzt oder ausgeweitet.

Vor Mutation werden Adminzeilen geordnet gesperrt und Mitglied/Handelnder sowie
Adminanzahl neu gelesen. Eine inzwischen entzogene Berechtigung oder deaktivierte
handelnde Person wird mit 403 abgewiesen. Damit wird nicht allein auf den Stand
beim Öffnen des Formulars oder auf eine ungesperrte Zählung vertraut.

## Prüfungen

17 neue Regressionstests: alleiniger Admin mit aktivem normalen Mitglied oder
inaktivem Admin; Herabstufung, Deaktivierung und beides zusammen; wiederholte
Ablehnung, vollständiger Datenerhalt und erhaltene Formulareingaben; erlaubte
Änderung mit zweitem aktivem Admin, gewöhnliche Datenänderung, normales Mitglied
deaktivieren, Übergabe nach vorheriger Beförderung; gezielt eingeschobene
Herabstufung eines anderen Admins bzw. Rechteverlust/Deaktivierung des Handelnden;
CSRF und unberechtigte Bearbeitung. Erfolgs-Audit wird unabhängig geprüft.

Vorherige zwölf Tests: **6 fehlgeschlagen, 6 bestanden**. Nach Fix: **12 bestanden**.
Mit fünf ergänzenden Tests: **17 bestanden** in 13,58 Sekunden bei 177 Warnungen.
Synthetische Mitglieder, SQLite im Speicher, simulierter Audit; isolierter
bestehender Teststarter ohne dotenv/Netzwerk. CSRF für den eigenen Ablehnungstest
aktiviert, sonst Testing-Konfiguration. Keine realen Rollen geändert.

Gesamtlauf: **508 Tests bestanden**, darunter **17 neue Regressionstests**,
in 399,65 Sekunden bei 3961 Warnungen. `git diff --check` ohne Fehler.
Templates, Assets und gesicherte Mockups gegenüber U1o unverändert.

## Grenzen und weitere Arbeit

Die PostgreSQL-Sperrstrategie setzt READ COMMITTED voraus; die lokale
Konfiguration enthält keinen abweichenden Isolation-Level. Ein echter
PostgreSQL-Test mit parallelen Transaktionen bleibt vor Veröffentlichung nötig.
Gezielte Zwischenänderungen im Test ersetzen diesen Nachweis nicht. Direkte
DB-/Skriptänderungen und Reparatur eines bereits adminlosen Bestands sind nicht
Teil dieses Formularschutzes. Aktionseigene erneute Identitätsbestätigung aus
F1 sowie allgemeiner Sitzungswiderruf bleiben separate Zugangsverträge.

A-089 bleibt offen: bestätigte Regeln verlangen bei Fehlern eine dauerhafte,
sichtbare Adminaufgabe. Vor Umsetzung sind Widerrufsauftrag mit altem Adress-/
Permission-Bezug, getrennte Migration, Wiederholungsweg und Zusammenspiel mit
laufenden Einladungen als ein Paket auszuarbeiten. Ein einfacher synchroner
Drive-Aufruf würde diese Anforderungen nicht erfüllen. Dafür wurden hier keine
produktiven oder lokalen Berechtigungen geändert.

Keine Templates/Assets, Migration oder neue Abhängigkeit. Kein Push, Deploy,
Merge auf master, Produktionsdatenzugriff oder Schlüsselwechsel. Fremde Dateien
und gesicherte Planung erhalten; offene visuelle Abnahme aus U1k bleibt bestehen.

# Noch fehlende Betriebsnachweise

Stand 2026-09-20. Dies ist eine offene Nachweisliste, keine Fehlerliste.
Keine Produktion abgefragt oder veraendert. Lokale Code-/Mock-Belege reichen
fuer die folgenden Aussagen nicht aus.

| Bereich | Lokaler Beleg | Noch benoetigt | Sichere Pruefform |
|---|---|---|---|
| Deployment | railway.json, start.sh, runtime.txt | aktiver Commit, Runtime, Service-/Environment-Zuordnung | explizit zugeordnetes read-only Deployment-Metadatum |
| Cron | Runner und Auswahlproben | Zeitplan, Zeitzone, letzte echte Erfolge/Fehler, Ueberlappungen | Scheduler-Metadaten und redigierte Laufnachweise |
| Push | ersetzte Transporte, Fehler-/Subscription-Proben | reale Plattformzustellung und installierte Bibliothek | spaeter vereinbarter Testempfaenger; kein unaufgeforderter Versand |
| Mail | lokaler Ergebnisvertrag | Providerannahme, Zustellung, Neustart bei Hintergrundversand | redigierte Statusbelege; Shutdown-Szenario auf isolierter Testumgebung |
| Datenbank | SQLite-Reproduktionen | PostgreSQL-Plaene, Indizes, realistische Laufzeiten, Schema-Head | separate Testbasis; aktuelle Migrationsrevision read-only |
| Backup/Restore | noch kein gepruefter Betriebsbeleg | Umfang, Aufbewahrung, letzte erfolgreiche Wiederherstellung | vorhandene Metadaten; Restore nur in separater Testumgebung |
| Monitoring | /health und /health/db getrennt | externe Alarme, Empfaenger, Ausfallnachweis | Konfiguration und redigiertes Alarmprotokoll |
| Drive/Zugriff | lokale Rechte-/Fehlerproben | reale Freigaben, Quoten, Retry-/Timeout-Budget | gezielte Metadaten ohne Dateien oder private Inhalte auszulesen |
| PWA/Geraete | lokale UI-/Algorithmus-Proben | echter Update-/Offline-/Kontowechsel auf relevanten Plattformen | isolierte Testkonten und vereinbarte Geraetematrix |

Kein Punkt ist allein wegen fehlender Evidenz als bestanden oder fehlerhaft
gewertet. Vor einem spaeteren Zugriff Projekt, Umgebung, Dienst und konkreten
Nachweis festlegen; keine pauschale Ausgabe von Variablen oder Secrets.

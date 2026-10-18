# U2-06: Fehlergrenze des optionalen Audit-Helfers

## Vertrag vor Code

A-137, AUDIT_FAILURE_REVIEW und Anchor-Docs: SecurityService.log_audit_event
isoliert seinen eigenen INSERT mit einem Savepoint. Fremde offene
Fachaenderungen werden vor diesem Savepoint geflusht, nicht still verworfen.
Scheitert dieser Fach-Flush, wird der Fehler weitergegeben. Scheitert nur
der Audit-INSERT, wird nur sein Savepoint zurueckgenommen; der Helfer gibt
False zurueck und schreibt eine inhaltsfreie Fehlermeldung ins Betriebslog.
Bereits gespeicherte Aktionen bleiben gespeichert und folgende ORM-Abfragen
funktionieren. Kein automatischer erneuter Fachaufruf.

Der bisherige Commit bei erfolgreichem optionalem Audit bleibt kompatibel
erhalten. Ein Fehler dieses aeusseren Commits wird nach Rollback weitergegeben,
nicht als bloss fehlender Audit-Eintrag verschluckt. Diese bestehende
Commit-Grenze ist kein allgemeiner Transaktionshelfer fuer neue Abläufe.
Neue atomare Sicherheitsablaeufe (Recovery, Onboarding, Dokumentloeschjournal)
verwenden weiterhin ihre verbindlichen Audit-INSERTs im eigenen Fachcommit;
ihre Fehler duerfen nicht durch den optionalen Helfer abgeschwaecht werden.
Keine garantierte Audit-Nachlieferung oder dauerhafte Warteschlange behaupten.

## Lokaler Nachweis

18.10.2026: 88 Tests fuer Auditgrenze, Sitzungswiderruf, Secret-Logging,
Einladungszustellung, Admin-Recovery und Reset-Zustellung bestanden
(1831 Warnungen, 79.77 s). Zusaetzlich erweiterte Auditdatei mit Aktivierung:
10 Tests bestanden (111 Warnungen, 9.21 s). Echter ORM-before_insert-Fehler
prueft Login, RSVP, Kalender, Eventloeschung und Aktivierung: gespeichertes
Passwort/verbrauchten Link erhalten, Anmeldung funktioniert. Fremde offene
Aenderungen bleiben rueckrollbar, Fachfehler werden weitergegeben.
Keine sensitiven Fehlerparameter im Log. Diff-Pruefung sauber.

Keine Migration/Frontend-Aenderung, kein dotenv/Netz. PostgreSQL-Savepoints
bleiben extern zu pruefen. A-046 bleibt separat: erfolgreicher Legacy-Audit
committet weiterhin bereits markierte Teilnahmeloeschungen vor Eventloeschung;
dieser konkrete Aufrufer wird im naechsten atomaren Paket umgestellt.
A-138 (RSVP-Zielzustand statt Toggle) bleibt ebenfalls separat offen.

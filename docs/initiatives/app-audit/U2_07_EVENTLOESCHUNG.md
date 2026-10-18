# U2-07: Atomare Eventloeschung

## Vertrag vor Code

A-046: Bestehende Grenze bleibt aktiv/Admin und nicht vergangenes Event,
Eventzugriff vorausgesetzt. Event, erlaubte einfache Teilnahmen und
Loeschprotokoll gehoeren in einen Commit. Kein optionaler Audit-Helfer mit
Zwischencommit. Jeder Fehler rollt alles zurueck und meldet keine Loeschung.

Verknuepfte Bewertungen, Dokumente, Belege, Forderungen oder Buchungen werden
nicht automatisch geloescht/entkoppelt. Solche Events bleiben mit Hinweis
erhalten. Ebenso bleibt gespeicherter BillBro-/GGL-Fachstand erhalten; kein
Kaskadenloeschen als Ersatz fuer einen fachlichen Korrekturablauf. Zulaessig
bleibt die bisherige Loeschung eines zukuenftigen einfachen Events samt
Teilnahmen ohne solche Fachhistorie. Kein Drive-Zugriff und kein Backfill.

Event und Teilnahmen werden vor Pruefung gesperrt; Datenbank-Fremdschluessel
sind zusaetzliche Grenze. PostgreSQL-Parallelitaet bleibt separat abzunehmen.

## Lokaler Nachweis

18.10.2026: 23 Tests fuer atomare Eventloeschung und Auditgrenze bestanden
(245 Warnungen, 12.59 s). Nach Ergaenzung der BillBro-Feldgrenzen 65 Tests
fuer Loeschung, Event-Sichtbarkeit und Bewertungsrueckkehr bestanden
(961 Warnungen, 22.43 s). Diff-Pruefung sauber. Keine Migration oder
Frontend-Aenderung. Echte ORM-Fehler bei Audit-INSERT/Event-DELETE und
Commitfehler bewahren Teilnahmen/Event; Abhaengigkeiten einzeln geprueft.
Der A-137-Test fuer optionale Eventloeschprotokolle wurde entfernt: Dieser
Aufrufer hat jetzt bewusst einen verpflichtenden atomaren Audit-Eintrag.

PostgreSQL-Parallelitaet und reale Browser offen. Kein externer Zugriff.
Keine Loesch-/Archivregel fuer Events mit Fachhistorie eingefuehrt; der
einfache Loeschweg bewahrt diese Daten und verweist auf Korrekturablaeufe.

# Bewertungen und GGL – F8

Stand: 11. Oktober 2026. Fachliche Abstimmung, keine App-Änderung.

**Eventdetail-Vorschau nachgeführt:** Getränke und Service sind optional,
Essen bleibt Pflichtfeld. Nur ausgefüllte Kategorien zählen gleichgewichtet
zum eigenen Gesamtwert; Speichern nur mit Essen sowie Essen/Service geprüft.
Bewertungen bleiben nach dem Anlass ohne Frist bearbeitbar. Sichtbare fremde
Durchschnittswerte sind weiterhin feste Beispieldaten, kein vollständiger
Aggregator. Öffentliche Restaurantansicht zeigt nun Gesamtwert, Kategorien und
jeweilige Anzahl; fehlende Kategorien und keine Bewertungen separat dargestellt.

## Bestätigte Bewertungsregeln

- Bewertungen bleiben nach dem Anlass ohne zeitliche Frist abgebbar und
  änderbar. Der vorher vorgeschlagene 14-Tage-Schluss ist verworfen; auch kein
  Wechsel zu ausschliesslicher Admin-Korrektur nach dieser Frist.
- Getränke und Service sind optional. Leere Angaben bedeuten «nicht bewertet»,
  nicht null Sterne; sie dürfen den jeweiligen Durchschnitt nicht absenken.
- Das bestehende Pflichtfeld Essen wird durch diese Änderung nicht aufgehoben.
  Gezielter Formularbeleg: `backend/forms/rating.py` hat bisher Essen, Getränke
  und Bedienung als Pflichtbewertungen von 1 bis 5; nur die beiden letztgenannten
  sollen optional werden. Kein Formular oder Datenmodell wurde geändert.

Mit «passt» bestätigt: Bewerten dürfen tatsächlich Anwesende. Nachträglich
korrigierte Anwesenheit berücksichtigen. «Immer offen» betrifft hier die Frist
nach dem Anlass, nicht Bewertung
vor dem Anlass oder durch nicht berechtigte Personen.

## Folgen für die Darstellung

**Gewichtung ausdrücklich bestätigt:** Alle ausgefüllten Kategorien zählen
gleich viel. Der Gesamtwert einer einzelnen Bewertung ist das arithmetische
Mittel der vorhandenen Angaben. Beispiel: Essen 4, Service 2, Getränke leer
ergibt 3; nur Essen 4 ergibt 4. Keine Ersatzwerte für ausgelassene Kategorien.
**Restaurantgesamtwert ebenfalls bestätigt:** Jede abgegebene Bewertung zählt
gleich viel, unabhängig von der Anzahl ausgefüllter Kategorien und auch über
mehrere Besuche hinweg. Zuerst je Bewertung das Mittel vorhandener Kategorien
berechnen, dann diese Einzelgesamtwerte gleichgewichtet mitteln. Nicht alle
einzelnen Kategorienwerte gemeinsam mitteln und nicht erst Besuchsmittelwerte
gleich gewichten: Das würde andere Gewichte ergeben. Eine Änderung aktualisiert
die bestehende Bewertung und zählt nicht als zusätzliche Bewertung.

Abnahmekriterium: Nur Essen 5 bei einer Bewertung und Essen/Getränke/Service
jeweils 3 bei einer zweiten ergeben Gesamtwert 4, nicht 3.5. Ein Besuch mit
drei Bewertungen zählt mit drei Bewertungen, ein Besuch mit einer mit einer.

Getränke und Service sichtbar als optional markieren, unbewerteten Zustand und
Zurücksetzen einer optionalen Angabe ermöglichen. Essen bleibt Pflichtfeld.
Kategorie-Durchschnitte beziehen sich jeweils auf tatsächlich abgegebene Werte;
Anzahl je Kategorie kenntlich machen, da diese unterschiedlich sein kann.
Dies sind abgeleitete Gestaltungs-/Abnahmekriterien, kein bereits umgesetzter
oder geprüfter Aggregationsweg. Ohne Werte «Noch nicht bewertet» statt 0 zeigen.

## Noch offen

Öffentliche Bewertungsdetails jetzt mit «passt alles» bestätigt: Gesamtbewertung,
Kategorie-Durchschnitte und Anzahl Bewertungen öffentlich; Einzelbewertungen,
Mitgliedernamen und persönliche Kommentare intern. Die GGL-Regeln wurden
separat bestätigt, siehe unten. Keine automatische historische Neuberechnung.
Vorhandene Bewertungsansichten und Statistiken vor Gesamtvorlage nachführen.

## GGL-Grundregeln – mit «ja» bestätigt

Ausgangspunkt ist `docs/DOMAIN.md`, keine neue Regel aus einem Mockup:
Kalenderjahr als Saison, kleinste absolute Abweichung vom Rechnungsbetrag gewinnt,
N gültige Tipps ergeben N Punkte für Platz 1 bis 1 Punkt für den letzten Platz.
Bei gleicher Abweichung werden die Punkte der belegten Plätze geteilt
(fractional ranking). Beispiel: fünf gültige Tipps, zwei auf den ersten beiden
Plätzen gleich gut, beide 4.5 Punkte. Ein exakter Tipp hat Abweichung 0 und
muss als gültig ausgewertet werden. Fehlende Tipps, historische Korrekturen
und später deaktivierte Mitglieder separat abgleichen.

## Ergänzende GGL-Regeln – mit «ja, passt» bestätigt

- Fehlender/ungültiger Tipp: keine Punkte und nicht in N der gültigen Tipps
  aufnehmen. In der Anzeige «Kein Tipp» statt eines erfundenen Schätzbetrags
  oder einer Nullabweichung. Dies erlaubt keinen neuen Weg an den bereits
  vereinbarten BillBro-Pflichtangaben vorbei; historische/unvollständige Fälle
  sind davon zu unterscheiden.
- Exakter Tipp: reguläre Punkte gemäss Rang, kein zusätzlicher Bonus.
- Später deaktiviertes/ausgetretenes Mitglied: historische Tipps und Ergebnisse
  erhalten; Deaktivierung allein berechnet keine Rangliste neu.
- Historische Ergebnisse nicht automatisch wegen neuer Regeln umrechnen.
  Nachgewiesene Erfassungsfehler darf der Systemadmin gezielt korrigieren;
  Änderung und Auswirkungen auf Event-/Saisonwerte nachvollziehbar zeigen.
  Keine automatische Änderung bezahlter BillBro-Anteile aus einer Tippkorrektur.

# U2-08: BillBro-Betragseingaben

## Vertrag vor Code

A-025 und BILLBRO_INTERAKTION: Rechnung, Schaetzung und manueller Gesamtbetrag
werden vor jeder Fachmutation als positive ganze Rappen validiert. Technische
Obergrenze ist die bestehende Integer-Spalte (2147483647 Rappen), kein neuer
fachlicher Preisdeckel. Schweizer Dezimalpunkt/-komma sowie korrekt gruppierte
Tausender mit Apostroph/Leerzeichen werden akzeptiert; keine stillen
Rundungen von Bruchteilen eines Rappens. Nicht endliche, leere, negative, null,
nicht numerische, exponentielle und uebergrosse Eingaben ergeben Feldfehler.

Automatischer Gesamtbetrag muss ebenfalls in den Bereich passen und mindestens
die Rechnung decken. Trinkgeld darf null sein. Bestehende Vorschlags-/
Verteilungsregeln werden nicht neu entschieden (A-031 separat). Ungueltige
Eingabe aendert weder Ess-Typ, Schaetzung, Rang/Punkte, Rechnung noch Forderung.
HTML zeigt korrigierbares Feld mit Eingabe; AJAX liefert Feldfehler und 400.
Kein Gesamtausbau der bestaetigten F3/F4-Korrekturablaeufe in diesem Paket.

## Lokaler Nachweis

18.10.2026: Zunaechst 48 Tests bestanden, danach mit Leerwert-/Nulltrinkgeld-
und Sichtbarkeitsregressionen 63 Tests bestanden (858 Warnungen, 24.17 s).
19 Worker-Tests bestanden, PWA 3.16.29, Diff-Pruefung sauber. Alle vier
Betrags-POSTs mit negativen/nicht endlichen/zu grossen/ungeraden Rappenwerten
geprueft; keine Aenderung von Ess-Typ, Rechnung, Punkten oder Forderung.
CHF 1’234,56 und exakte Rechnungsrappen sowie Nulltrinkgeld positiv geprueft.
Keine Migration, keine neue CSS-Klasse. Browserabnahme offen.

A-031 bleibt separat: verbindliche Verteilungs-/Rundungsregel am 18.10.2026
beim Auftraggeber angefragt; keine Regel still vorausgesetzt. A-029 kann
unabhaengig weiter umgesetzt werden. Andere Legacy-MoneyService-Aufrufer
sind durch dieses begrenzte BillBro-Paket nicht als bereinigt ausgewiesen.

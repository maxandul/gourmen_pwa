# Dokumentation: begrenzte Pruefpakete

Stand 2026-09-20. 44 Dokumente im Umfang; Game ausgeschlossen.
Ein abgeschlossenes Teilpaket bedeutet keine Dokumentfreigabe oder Fehlerbehebung.

| Paket | Abschlusskriterium | Stand |
|---|---|---|
| D-01 AuditAction | Alle Beispielnamen aus DOMAIN und direkte Backend-Verweise gegen Enum abgleichen | abgeschlossen als Namensabgleich; DOMAIN_SYMBOL_CHECKS.json |
| D-02 Statusnamen | Acht Rollen-/Event-/Status-Enums erfassen und DOMAIN-Tabellen/Beispiele abgleichen | abgeschlossen als Namensabgleich; Durchlauf 8 |
| D-03 DOMAIN-Felder/Konten/Seed | Speicherfelder/Auswahlwerte, Kontencodes und alle Seed-Funktionen statisch abgleichen; Laufzeit/Fachentscheidungen getrennt ausweisen | abgeschlossen als statischer Vertragsabgleich, Durchlauf 9; keine Seed-Laufzeitfreigabe; Fachgrenzen weiter in Modulberichten |
| D-04 Anchors/Setup/Regeln | Restliche Anweisungen gegen Code/Build/Tests pruefen; externe Nachweise getrennt | offen, Teilabdeckung vorhanden |
| D-05 UI Registry | Jede Zeile mit Definition, statischer/dynamischer Verwendung und Ausnahme verknuepfen | in_progress: 18 Registry-Durchlaeufe, 150 Zeilen mit Pruefverweisen; 117 Rueckwaertsfamilien eingeordnet. Fuenf gezielte Restpunkte aus Durchlauf 12 geklaert; sechs Struktur-Familien statisch vertieft, Browserproben bis B-40. Weitere Varianten und Gesamtmatrix offen; UI_REGISTRY_REVIEW.md |
| D-06 Capabilities | Jede Anforderung erfuellt/abweichend/Produktentscheidung/begruendet ungeprueft zuordnen | in_progress: Kalender-Cache/SEQUENCE/Inhalt mit 20 Pruefgruppen einschliesslich Event-Edit/Delete abgeglichen; CALENDAR_CONTRACT_REVIEW.md. Restanforderungen und andere Capabilities offen |
| D-07 Aktive Phasen | Restkriterien und operative Befehle auf heutiges Soll/historischen Kontext pruefen | offen |
| D-08 Archive/Hamburg | Restinhalt auf referenzierte Entscheidungen/Beispiele pruefen, Nachfolger festhalten | offen; Archive bisher nur Einstieg |
| D-09 SEO/Betrieb | Pro Aussage Codebeleg, datierte Messung, Hypothese oder externen Nachweisbedarf festhalten | offen; Betriebsregister vorhanden |

Namensabgleich beweist weder Rechte noch erfolgtes Logging. Kein Dokument
pauschal als abgeschlossen markieren, weil sein Einstieg geprueft wurde.

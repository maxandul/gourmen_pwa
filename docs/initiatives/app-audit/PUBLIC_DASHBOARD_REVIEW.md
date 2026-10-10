# Public-Bereich und Dashboard – erster vertiefter Durchlauf

Stand 2026-09-20. Sieben isolierte Szenarien, neue Befunde A-094 bis A-096,
Erweiterung A-042. Teilpruefung, kein vollstaendiger Modulabschluss.

## Nachweise und Grenzen

[PUBLIC_DASHBOARD_CHECKS.json](PUBLIC_DASHBOARD_CHECKS.json),
`check_public_dashboard.py`, PUBLIC_DASHBOARD_RUN.txt. Original-Routes/-Services,
echtes Template-Rendering mit erfasstem Kontext, synthetische Events/Mitglieder/
Teilnahmen in SQLite-Memory. Kein Netzwerk, keine Produktion. Fuer einen Fall
Statistikabfrage durch Fehler ersetzt. CSRF/Rate-Limit in Testing deaktiviert.

| Szenario | Ergebnis |
|---|---|
| public_next_event_audience | Board-Monatsessen im Public-Teaser; Next-Event im Dashboard korrekt gefiltert, A-042 |
| dashboard_bill_link_after_audience_change | BillBro-Link auf nun unsichtbaren Event, Ziel 403, A-042 |
| today_event_public_date_boundary | Heutiges datum-only-Essen mittags nicht mehr kommend, schon besucht, A-094 |
| public_query_failure_becomes_empty_result | Datenfehler ergibt 200/Nulltreffer und verliert Suche/Sortierung, A-095 |
| search_pagination_and_invalid_parameters | Positiv: 12 Restaurants, Seite 999 auf 2 begrenzt; Suche 1 Treffer bei Baseline 12; ungueltige Parameter auf Defaults |
| same_name_different_restaurants_merged | Zwei Place-IDs/Orte mit gleichem Namen ergeben eine Zeile, A-096 |
| public_private_entry_guards | Positiv: Dashboard ohne Login umgeleitet; eingeloggter Root zum Dashboard; show=1 zeigt Public-Seite |

Die Board-Faelle verwenden publizierte Monatsessen mit Board-Audience, keine
als Monatsessen umgedeutete Vorstandssitzung. Rechnungsfall bildet verbleibende
Teilnahme nach Sichtbarkeitswechsel ab. Eine offene Forderung kann fachlich weiter
bestehen; dafuer braucht es einen erreichbaren, bewusst begrenzten Einstieg.

Keine neue visuelle/Browser- oder Ladezeitmessung. Vorherige Viewport-Belege in
BROWSER_REVIEW.md gelten weiterhin; JavaScript-Suche und Browserhistorie sind
durch serverseitiges Rendering nicht getestet.

## Offene Fortsetzung

- Public: asynchrone Suche/Sortierung, schnelles Wechseln, Abbruch/Fehler,
  Browserhistorie, Pagination-Links und barrierefreie Aktualisierung.
- Restaurantidentitaet, Bewertungsgewichtung, fehlende/alte Ortsdaten,
  gleiche Namen, Namensaenderungen und grosse Bestandsmengen.
- Dashboard: GGL-Ranggleichheit (vgl. A-032), Forderungs-/Merch-Summen,
  Priorisierung konkurrierender Hinweise, Leer-/Langdaten und Fehlerisolation.
- Zeitgrenzen: Tageswechsel, UTC/Europe-Zurich, Saisonwechsel und Event-Uhrzeit.
- Public-Inhalte/Links, strukturierte Daten, Canonical/Sitemap/robots und
  Datenschutzhinweise anhand tatsaechlicher Einbindung.
- Responsive/Tastatur-/Touch-Verhalten und Performance mit realistischen Daten.

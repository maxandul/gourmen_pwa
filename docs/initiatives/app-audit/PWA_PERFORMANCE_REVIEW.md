# PWA, Offline und Performance – erster vertiefter Durchlauf

Stand 2026-09-20; Baseline siehe README. Keine App-Aenderung, keine Produktion.
Dieser Durchlauf prueft Cache-/Update-Algorithmen. Er enthaelt **keine gemessenen
Ladezeiten, Web Vitals, Netzwerktransfers oder Produktions-Datenbanklaufzeiten**.

Ergaenzender [Skalierungsbericht](QUERY_SCALING_REVIEW.md): 48 isolierte
Render-Aufrufe zaehlen SQL und ORM-Ladeereignisse bei mehr Events, Mitgliedern
und Artikeln. Auch dies sind keine Ladezeitmessungen.
Weitere 48 Aufrufe mit Orders, Claims und Buchung-/Belegpaaren ergaenzen dies
auf insgesamt 96 Render-Messungen; A-105/A-106 dokumentieren die neuen Ursachen.
24 weitere Aufrufe mit historischen Saisons/Geschaeftsjahren bringen den Stand
auf **120 Render-Messungen**. Sie vertiefen A-030/A-104 und zeigen als positives
Gegenbeispiel den gemeinsam aggregierten Jahresvergleich der Buchhaltung.

## Methode

`check_sw_strategies.cjs` fuehrt das originale `static/sw.js` und fuer die
Update-Erkennung das aktuell eingebundene `pwa.df1b3f63.js` in Node-VMs aus.
Fetch und Cache Storage sind synthetisch; kein Netz und keine echten Browser-
Caches. Request/Response stammen aus Node. Der Cache ist nach URL modelliert,
ohne vollstaendige Browsersemantik fuer Vary, Cookies, Quoten oder Worker-Lifetime.
Reload wird gezaehlt, nicht ausgefuehrt. Zehn Szenarien:
[SW_STRATEGY_CHECKS.json](SW_STRATEGY_CHECKS.json).

Die bisherigen lokalen UI-Pruefungen sind kein PWA-Nachweis: `pwa.js` deaktiviert
den Service Worker auf localhost standardmaessig. Fuer spaetere echte PWA-Tests
ist eine ausdruecklich aktivierte, isolierte Browser-Testumgebung erforderlich.

## Cache-Vertrag im Bestand

| Anfragen | Strategie | Bewertung |
|---|---|---|
| Navigation / Accept text/html | Netz bzw. Navigation Preload; offline statische Ersatzseite | SW-01/SW-02 bestaetigen keine dynamische HTML-Speicherung. Private HTML-Seiten werden hier nicht offline verfuegbar gemacht. |
| Hash-Assets / feste Precache-Liste | Cache zuerst | SW-05: gecachtes CSS liefert Antwort ohne Fetch. Keine Aussage ueber den kompletten Seitenaufbau. |
| Andere /static/-Assets | Alter Cache sofort, Aktualisierung im Hintergrund | SW-06: Hintergrundarbeit ohne waitUntil, A-102. Versionsparameter in URLs sind Teil des Cache-Schluessels. |
| API und alle sonstigen GETs | Netz zuerst, erfolgreiche Antwort speichern, bei Netzfehler Cache | Keine enge Allowlist und keine sichtbare Groessen-/Altersgrenze. Private Daten/Kontowechsel weiter A-010. |
| Nicht-GET | Kein Eingriff im Fetch-Handler | Keine Offline-Schreibwarteschlange durch diesen Handler. Background-Sync-Listener ist ein No-op. |

`API_CACHE` ist trotz des Namens keine Allowlist: Auch der abschliessende else-
Zweig verwendet denselben dynamischen Cache. Same-Origin-Pruefung gibt es fuer
statische Assets, nicht als globale Fetch-Abgrenzung. Drittanfragen und private
Downloads deshalb in einer kuenftigen Consumer-Matrix einzeln bewerten.

## Ergebnisse und Grenzen

- **A-101:** Nicht gecachte API liefert offline stattdessen die HTML-Ersatzseite
  mit Status 200. JSON-Parsing scheitert in SW-03. Der Push-Status-Client faengt
  diesen Fehler ab und liefert null; kein belegter Absturz der gesamten App.
- **A-010 vertieft:** SW-04 speichert auch eine synthetische Antwort mit
  `Cache-Control: private, no-store`; dieselbe URL liefert sie bei Netzverlust.
  Das belegt den Algorithmus, keine kontoübergreifende Browser-Offenlegung.
  Echte Login-/Logout-Sequenz samt Request-/Vary-Semantik bleibt erforderlich.
- **A-102:** Bei vorhandenem Cache endet die Antwort, waehrend die Revalidierung
  noch laeuft. Der Fetch-Handler verlaengert ihre Lebensdauer nicht ueber
  `waitUntil`. Tatsaechlicher Abbruch durch einen Browser wurde nicht simuliert.
- **A-103:** Der ausgelieferte Update-Handler ruft bei bereits vorhandenem
  Controller sofort reload auf; Formularzustand wird nicht abgefragt. SW-09/10
  bestaetigen zugleich Schutz vor Mehrfach-Reload und Ausnahme fuer Erstaktivierung.

Weitere beobachtete Grenzen, noch kein eigener bestaetigter Nutzerfehler:

- SW-07: Aktivierung entfernt im Modell auch einen fremd benannten Cache und
  den aktuellen dynamischen Cache. Auf dieser Origin tatsaechlich benoetigte
  fremde Caches sind nicht nachgewiesen. Loeschregeln auf eigene Namenspraefixe
  begrenzen und Update-/Rollback-Vertrag festlegen.
- SW-08: Alle 20 Precache-Fetches scheitern, trotzdem wird das Install-Promise
  erfuellt. Abwaegung zwischen robuster Online-Aktivierung und zugesichertem
  Offline-Minimum dokumentieren; bei Aktivierung werden bisherige Caches geloescht.
- Dynamischer Cache hat weder TTL noch Anzahl-/Groessenlimit. Das ist ein
  Wachstumskandidat, keine Messung von Speicherverbrauch oder Quotenfehlern.
- Offline-Seite orientiert Rueckkehr an navigator.onLine und leitet auf `/`.
  Durch fuenf isolierte Originalscript-Proben vertieft: A-107,
  [Wiederverbindungsbericht](INTEGRATION_OPERATIONS_REVIEW.md). Wiederholte
  Navigation im Modell belegt; echte Browser-Schleife weiterhin nicht geprueft.

## Empfehlung fuer ein spaeteres Umsetzungspaket

Einen expliziten Vertrag fuer HTML, oeffentliche Daten, private Daten, Downloads
und unveraenderliche Assets festlegen. Offline-Fehler dem erwarteten Antworttyp
anpassen, Cache-Lifetime begrenzen und Account-Lifecycle beruecksichtigen.
Updates mit Bearbeitungszustaenden koordinieren; Hintergrundaktualisierung an
die Worker-Lebensdauer binden. Referenzen:
[MDN waitUntil](https://developer.mozilla.org/en-US/docs/Web/API/ExtendableEvent/waitUntil),
[Service-Worker-Lifecycle](https://web.dev/articles/service-worker-lifecycle).

## Noch anstehende Pruefungen

- Echtes PWA-Install/Update/Offline-Verhalten, kalter und warmer Cache, mehrere
  offene Tabs, Formularbearbeitung, Accountwechsel und Wiederverbindung.
- Private APIs/Downloads samt Headern und Cookie-/Vary-Verhalten in einer
  aktivierten Browserumgebung; echte iOS-/Android-Installationen separat.
- Netzwerk-/CPU-Messungen mit realistischen grossen Inhalten und Diagrammen.
- Datenbankabfragen je Seite/Aktion bei steigenden Datenmengen; vorhandenes
  N+1-Indiz in Bereinigung (A-030) in weitere Module verfolgen.
- Cron, Integrationstimeouts, Betriebs-/Backup-/Restore-Nachweise.

Zehn Algorithmus-Szenarien sind weder zehn bestandene Produkt-Regressionstests
noch eine Erweiterung der bisherigen 143 fachlichen Workflow-Szenarien.

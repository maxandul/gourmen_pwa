# U1z – Cache-Nutzertrennung (A-010)

Stand: 18.10.2026. Technischer Vertrag vor Implementierung.

- Ausschliesslich gleichurspruengliche statische Ressourcen aus STATIC_ASSETS
  oder /static/ mit zugelassener Dateiendung; Query nur optionales v.
  Authorization-/Range-Anfragen sind ausgeschlossen.
- Speichern nur erfolgreicher, nicht umgeleiteter Antworten mit explizitem public,
  ohne private/no-store, ohne Download-Disposition. Cache-Lesen nur aus dem
  aktuellen statischen Cache und mit derselben Antwortpruefung.
- Alle anderen GETs einschliesslich APIs, Downloads und Tokenlinks sind network-only
  mit no-store. Kein dynamischer Cache und kein Lesen alter/fremder Caches.
- HTML-Netzfehler erhalten die statische Offline-Seite; API-Netzfehler JSON/503,
  sonst Text/503. Keine privaten Offline-Fachfunktionen.
- Aktivierung entfernt nur bekannte versionierte Gourmen-Cache-Namen. Navigation
  Preload wird deaktiviert, damit kein abweichender HTTP-Cache-Pfad entsteht.
  skipWaiting/claim und vorhandener einmaliger Reload bleiben erhalten.
- Logout benoetigt keine asynchrone Cache-Loeschung als Sicherheitsbarriere:
  private Daten werden weder geschrieben noch als Fallback gelesen.

Pruefung und Ergebnisse werden nach der Umsetzung ergaenzt. Browser-HTTP-Cache,
installierte PWA, mehrere Tabs und reale Geraete bleiben separat abzunehmen.

## Umsetzung und tatsaechliche Nachweise

18.10.2026, Basis 5b6d28d, bestehender Branch codex/app-audit-implementation-plan.
Worker auf 3.16.8, PWA-Quelle und Template-Versionen synchron; nur geaenderte
pwa.js mit fingerprint_assets (FILES=['js/pwa.js']) neu gehasht, Manifest und
_head_deferred_scripts nachgefuehrt. Fremde Hashdateien bleiben unangetastet.
Auch die bestehenden Client-Cleanup-Wege entfernen nur eigene Cache-Familien.
Keine neue UI-Klasse, keine Migration, keine Backend-Aenderung.

- `node --test tests/js/sw_cache_isolation.test.cjs`: abschliessend **19 bestanden**.
  Erster Lauf vor Versionsbump: 18 bestanden, 1 fehlgeschlagen, weil der als alt
  gesetzte Cache noch der aktuellen Version entsprach. Nach Bump bestanden.
- Python-Regression ueber `runpy.run_path('docs/initiatives/app-audit/run_existing_tests.py',
  run_name='audit_bootstrap')`, danach `pytest.main(['tests/routes/test_auth_revocation.py',
  '-q', '-p', 'no:cacheprovider'])`: **27 bestanden**, 483 bestehende Deprecation- /
  LegacyAPI-Warnungen; Exit 0. Beim Interpreterende zusaetzlich eine ignorierte
  pyreadline-Destruktorwarnung (Windows Handle), kein Testfehler.
- `git diff --check`: ohne Fehler.

Die JS-VM ersetzt fetch vollstaendig; keine ausgehende Verbindung. Konto A,
Abmeldung und Konto B sind synthetische Transportzustaende, keine Browsercookies
oder echten Anmeldungen. Originale Python-Auth-Routen separat mit synthetischen
Konten geprueft. Alte dynamische/fremde Cacheantworten, private/no-store,
API/Download/Tokenkalender, Update-Cleanup, statisches Offline, fehlgeschlagene
Installation, HTTP-Fehler, Redirects, Hintergrund-Lebenszeit sowie Ausschluss
von Authorization/Range/fremdem Origin/Tokenquery sind abgedeckt.

## Grenzen und naechstes Paket

Echter Browser-HTTP-Cache/Back-Forward-Cache, installierte PWA, mehrere Tabs und
Update auf realen Geraeten sind **offen**. Keine Aussagen ueber PostgreSQL,
Mail, Drive oder Produktion. Bis zur Aktivierung des neuen Workers besteht
naturgemaess der alte Clientstand. Kein Push/Merge/Deploy/Produktionszugriff.
U1 bleibt insgesamt offen. Naechstes Paket ist U1-R02; die dort fehlende konkrete
interne Lesergruppe wurde zur Entscheidung vorgelegt, sonstige Sichtbarkeit
kann lokal unabhaengig umgesetzt werden.

# Auffindbarkeit & Auslieferung der öffentlichen Seiten

Betrifft die drei öffentlichen Seiten `/`, `/ueber-uns`, `/restaurants`. Der
Vereinsbereich hinter dem Login ist bewusst auf `noindex` gesetzt.

## Ausgangslage (September 2026)

Zwei Symptome, zwei verschiedene Ursachen:

1. **Die Landingpage kam aus Firmennetzen unformatiert an** — als würde das CSS
   nicht greifen.
2. **`www.gourmen.ch` war über Google nicht auffindbar.** Eine `site:`-Suche
   lieferte null Treffer, die Domain war offenbar nie gecrawlt worden.

## Was am Laden schiefging

Der Server war nie das Problem — alle Assets lieferten 200 mit korrektem
MIME-Typ. Es war die Ladekette:

| Ursache | Wirkung |
|---|---|
| `main-v2.css` bestand nur aus vier `@import`-Zeilen | Render-blockierender Wasserfall: erst 3.6 KB Hülle laden und parsen, dann erst das eigentliche Design-System anfordern. Reisst eine der vier Anfragen, ist die Seite komplett unformatiert. |
| Icon-Sprite über zwei URLs referenziert (gehasht + ungehasht) | Dieselben 418 KB wurden zweimal geladen — 836 KB pro Seitenaufruf. |
| Flask lieferte `/static/` mit `Cache-Control: no-cache` | ~50 Revalidierungen pro Seitenaufruf. |
| `isStaticAsset()` im Service Worker matchte nur 20 hartcodierte Pfade | Genau die vier CSS-Dateien und das Sprite fielen durch und liefen über `networkFirst` — mit erzwungenem `no-cache` und einem Cache, der bei jedem SW-Update geleert wird. |
| `gunicorn --workers=1 --worker-class=sync` | Genau ein Request gleichzeitig. |
| `brand/logo-master-round.svg` als Hero-Bild, User-Bar-Logo **und** SVG-Favicon | 2.85 MB auf jeder Seite. Die Datei ist kein Vektor-Logo, sondern eine 1300×1300-Bitmap plus C2PA-Metadaten in einer SVG-Hülle — dargestellt wird sie nie grösser als 200 CSS-Pixel. |
| `<link rel="icon" sizes="512x512">` | 444 KB Favicon, das kein Browser in dieser Grösse braucht. |
| `splash-828x1792.a5161c83.png` trug den Hash von `splash-1242x2208` | 404 auf jeder Seite. |

In Summe rund 4.5 MB pro Seitenaufruf (ohne die iOS-Splash-Screens), davon
gut 1 MB render-blockierend, ohne jedes Caching, serialisiert durch einen
Prozess. Von zuhause geht das knapp durch; hinter einem scannenden Proxy nicht
zuverlässig.

Nach den Änderungen sind es 1.03 MB — und beim zweiten Aufruf praktisch nichts
mehr, weil alles gehashte immutable gecacht und vom Service Worker vorgehalten
wird.

### Was dagegen gemacht wurde

- `scripts/build_css.py` konkateniert `css/v2/{tokens,base,layout,components}.css`
  zu einem gehashten `main-v2.<hash>.css`. **Ein** Request statt fünf.
- Alle Sprite-Referenzen zeigen auf die gehashte Datei — eine URL, ein Download.
- `add_static_cache_headers` in `backend/app.py`: gehashte Dateien ein Jahr
  `immutable`, alles andere unter `/static/` eine Stunde. `sw.js` bleibt
  bewusst `no-cache`, sonst kommen SW-Updates nie an.
- Service Worker (`static/sw.js`): alles unter `/static/` wird als Static-Asset
  erkannt. Gehashte Dateien cache-first, ungehashte stale-while-revalidate.
- `gunicorn --worker-class=gthread --threads=8`.
- `scripts/build_web_logo.py` erzeugt aus dem Master-Asset runde WebP-Logos
  (256 px / 512 px, 16 bzw. 48 KB) für Hero, User-Bar und Dashboard. Das
  SVG-Favicon und der 512er-Favicon-Link sind entfallen; die PNG-Icons decken
  alle Grössen ab, für die PWA-Installation zählt ohnehin `manifest.json`.
- Der kaputte Splash-Fingerprint ist korrigiert.

### Logo ändern

`static/brand/logo-master-round.svg` bleibt die Quelle. Nach einer Änderung:

```bash
python scripts/build_web_logo.py
```

Das Script bildet nach, was das SVG tut — Bitmap extrahieren, per
`matrix(...)` platzieren, auf einen Kreis beschneiden. Wer nur die Bitmap
extrahiert und skaliert, bekommt ein dunkles Quadrat: die runde Form steckt im
`clipPath`, nicht im Bild. Die neuen Dateinamen müssen in `templates/` und
`static/sw.js` nachgezogen werden.

### CSS ändern

Die Quellen liegen weiterhin unter `static/css/v2/`. `static/css/main-v2.css`
ist ein **Build-Artefakt** — nicht von Hand bearbeiten. Nach Änderungen:

```bash
python scripts/build_css.py
```

Das Script gibt den neuen Dateinamen aus. Dieser muss nachgezogen werden in:

- `templates/partials/_head_stylesheets.html`
- `templates/offline.html` und `static/offline.html`
- `static/sw.js` (Liste `STATIC_ASSETS`)

Danach `python scripts/update_pwa_version.py <version>`, damit der Service
Worker die neuen Dateien auch wirklich ausrollt.

## Was der Auffindbarkeit fehlte

`/robots.txt` und `/sitemap.xml` lieferten 404, es gab keine Canonical-URLs,
und die Meta-Description beschrieb die Software statt den Verein
("Gourmen-Verein Webapp - Verwaltung und Organisation"). Ergänzt wurden:

- `robots.txt` mit Sitemap-Verweis, interne Bereiche gesperrt
- `sitemap.xml` mit den drei öffentlichen Seiten
- `<link rel="canonical">` auf jeder Seite, paginierte Hitlist kanonisiert auf
  sich selbst
- `<meta name="robots">`: `index, follow` öffentlich, `noindex, nofollow` intern
- Meta-Descriptions pro Seite, formuliert nach dem, wonach Leute suchen
- JSON-LD `Organization`-Markup auf der Landingpage

Festgehalten in `tests/routes/test_seo.py`.

## Offen — muss manuell erledigt werden

Diese zwei Punkte lassen sich nicht im Code lösen und sind vermutlich der
eigentliche Grund, warum die Site nicht im Index ist.

### 1. Google Search Console einrichten

Ohne eingehende Links findet Google eine Domain praktisch nicht von selbst.

1. [search.google.com/search-console](https://search.google.com/search-console)
   öffnen, Property für `gourmen.ch` (Domain-Property) anlegen.
2. Verifizierung per DNS-TXT-Record beim Domain-Provider.
3. Unter *Sitemaps* `https://www.gourmen.ch/sitemap.xml` einreichen.
4. Unter *URL-Prüfung* die Startseite eingeben und Indexierung beantragen.

Bis die Site im Index auftaucht, vergehen erfahrungsgemäss Tage bis Wochen.

### 2. Apex-Redirect muss den Pfad behalten

`gourmen.ch/restaurants` leitet aktuell auf `https://www.gourmen.ch/` um — die
Startseite, nicht die angefragte Seite. Geprüft am 5. September 2026:

```
https://gourmen.ch/            301 -> https://www.gourmen.ch/
https://gourmen.ch/ueber-uns   301 -> https://www.gourmen.ch/
https://gourmen.ch/restaurants 301 -> https://www.gourmen.ch/
```

Jeder Deeplink auf den Apex landet damit auf der Startseite, und die Linkkraft
der Unterseiten verpufft. Die Umleitung passiert **vor** der App (Redirect beim
Domain-Provider bzw. auf der Railway-Edge) — auch `/calendar/*.ics` erreicht die
App über den Apex nicht, der entsprechende Handler in `backend/app.py` läuft in
Produktion also gar nicht an.

Zu tun: beim Domain-Provider den pauschalen Weiterleitungs-Eintrag für
`gourmen.ch` entfernen und den Apex stattdessen per ALIAS/ANAME auf denselben
Railway-Service zeigen lassen wie `www`. Dann übernimmt
`redirect_apex_to_www()` in `backend/app.py` die Weiterleitung korrekt inklusive
Pfad und Query — abgedeckt durch
`test_apex_leitet_mit_pfad_und_query_auf_www`.

## Naheliegende nächste Schritte

- **Sprite verkleinern.** `static/icons/lucide-sprite.svg` enthält 1666 Symbole
  (418 KB), verwendet werden rund 120. Ein Subset brächte die Datei auf etwa
  35 KB. Achtung bei der Umsetzung: neben den literalen `lucide_icon('name')`
  -Aufrufen gibt es dynamische Namen aus `mime_to_lucide_icon()` in
  `backend/services/drive_storage.py` und aus den `dashboard_intent_tile`
  -Aufrufen — die müssen mit ins Subset.
- **Mehr Inhalt auf den öffentlichen Seiten.** Die Landingpage hat rund 670
  Zeichen sichtbaren Text. Für Suchbegriffe wie „Restaurant Tipps Zürich"
  reicht das nicht; die Hitlist mit echten Beschreibungen wäre der natürliche
  Hebel.
- **Eingehende Links.** Instagram-Bio, Vereinsverzeichnisse, die Websites der
  besuchten Restaurants — ohne externe Links bleibt jede Optimierung zahnlos.

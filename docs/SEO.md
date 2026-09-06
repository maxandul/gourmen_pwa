# Auffindbarkeit & Auslieferung der öffentlichen Seiten

Betrifft die drei öffentlichen Seiten `/`, `/ueber-uns`, `/restaurants`. Der
Vereinsbereich hinter dem Login ist bewusst auf `noindex` gesetzt.

## Ausgangslage (September 2026)

Zwei Symptome, zwei verschiedene Ursachen:

1. **Die Landingpage kam aus Firmennetzen unformatiert an** — als würde das CSS
   nicht greifen.
2. **`www.gourmen.ch` wurde über Google nicht gefunden.** Nicht, weil die Seite
   fehlte — sondern weil sie auf Seite 5 steht. Siehe unten.

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

Nach den Änderungen sind es rund 650 KB — und beim zweiten Aufruf praktisch
nichts mehr, weil alles gehashte immutable gecacht und vom Service Worker
vorgehalten wird.

### Was dagegen gemacht wurde

- `scripts/build_css.py` konkateniert `css/v2/{tokens,base,layout,components}.css`
  zu einem gehashten `main-v2.<hash>.css`. **Ein** Request statt fünf.
- Alle Sprite-Referenzen zeigen auf die gehashte Datei — eine URL, ein Download.
- `scripts/build_icon_sprite.py` schneidet aus dem vollen lucide-static-Sprite
  (1666 Symbole, 418 KB) ein Subset der tatsächlich referenzierten Icons:
  129 Symbole, 29 KB.
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

### Icons ändern

Ausgeliefert wird `static/icons/lucide-sprite.svg` — ein **Build-Artefakt**.
Quelle ist `static/icons/lucide-sprite-full.svg`, das komplette
lucide-static-Sprite; es wird nie ausgeliefert und bei einem Lucide-Update
einfach ersetzt. Nach jedem neuen oder entfernten Icon:

```bash
python scripts/build_icon_sprite.py
```

Das Script sammelt die Icon-Namen aus allen Quellen — literale
`lucide_icon('name')`-Aufrufe, `<use href="...#name">`-Attribute, das zweite
Argument von `dashboard_intent_tile()`, im Template gesetzte Variablen wie
`flash_icon`, `lucideInlineIcon()` in `static/js/app.js` sowie
`mime_to_lucide_icon()` und die `icon_name`-Defaults in
`backend/services/drive_storage.py` (die erreichen die Docs-Templates als
`hit.icon_name` / `row.icon_name`).

Es bricht ab, wenn ein referenzierter Name im vollen Sprite nicht existiert.
Das ist Absicht: ein `<use href="...#tippfehler">` wirft weder 404 noch
Konsolenmeldung, es rendert einfach nichts. Genau so waren `alert-circle`,
`more-vertical`, `sliders`, `note` und `upload-cloud` unbemerkt kaputt — Lucide
hatte sie umbenannt. Ebenso bricht der Build ab, wenn ein Icon-Argument ein
Ausdruck ist, den das Script nicht auflösen kann; wer eine neue dynamische
Quelle einbaut, trägt sie in `ALLOWED_DYNAMIC_ARGS` ein.

Der neue Dateiname muss nachgezogen werden in `templates/`,
`static/offline.html`, `static/js/app.js` und `static/sw.js` (Liste
`STATIC_ASSETS`). Abgedeckt durch `tests/routes/test_icon_sprite.py`, das gegen
das tatsächlich ausgelieferte Sprite prüft.

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

## Auffindbarkeit: die tatsächliche Lage

**Wichtig, weil eine frühere Fassung dieses Dokuments das Gegenteil behauptete:
Die Seite ist indexiert und war es die ganze Zeit.** Die Behauptung, sie sei nie
gecrawlt worden, stützte sich auf eine `site:`-Suche über einen Suchdienst, der
nicht Google ist — kein belastbarer Beleg. Die Search Console war ausserdem
längst eingerichtet und per DNS-TXT verifiziert.

Zahlen aus der Search Console (Domain-Property `gourmen.ch`, Stand 5. September
2026, Zeitraum 12 Monate):

| Kennzahl | Wert |
|---|---|
| Indexierte Seiten | 3 |
| Nicht indexiert | 6 (Duplikat ohne Canonical 2, Weiterleitung 2, gecrawlt aber nicht indexiert 2) |
| Impressionen | 157 |
| Klicks | **0** |
| Durchschnittliche Position | **50,2** |
| Position für die Suchanfrage „gourmen" | **44,2** |
| **Externe Links** | **0** |

Das ist kein Indexierungs-, sondern ein Autoritätsproblem. Die Seite rangiert
selbst für den eigenen Vereinsnamen auf Seite 5 — dorthin scrollt niemand.

Zwei Muster in den Suchanfragen sind aufschlussreich:

- Die meisten Impressionen kommen über **Restaurantnamen** („salmen schlieren",
  „restaurant gümmenen", „schlemmerei emmen"). Das ist die Hitlist-Tabelle, die
  arbeitet — der einzige Teil der Site mit substanziellem Inhalt.
- „gourmand restaurant" taucht in der Liste auf. Google hält „Gourmen"
  offenbar teilweise für eine Verschreibung von „gourmet"/„gourmand" und
  erkennt den Namen nicht als eigenständige Entität.

### Der Hebel: externe Links

**Null externe Links** ist die Erklärung für alles darüber. Google hat kein
einziges Signal von aussen, dass es diese Seite gibt oder dass sie für
irgendetwas relevant wäre. Keine technische Massnahme an der Site kann das
ersetzen.

Was hilft, in dieser Reihenfolge:

1. **Instagram-Bio** (`@gourmen_zh`) — der schnellste Link, den es gibt.
2. **Websites der besuchten Restaurants** — viele führen Presse-/Gäste-Seiten.
3. **Zürcher Vereinsverzeichnisse**, Vereinsregister der Stadt, lokale
   Gastro-Verzeichnisse.

Sobald der Name in fremden Kontexten auftaucht, lernt Google „Gourmen" als
Eigennamen statt als Tippfehler. Das JSON-LD-`Organization`-Markup auf der
Landingpage (`name` + `alternateName`) unterstützt das, kann es aber allein
nicht leisten.

## Was technisch gefehlt hat

Das behebt nicht das Ranking, räumt aber echte Mängel aus: `/robots.txt` und
`/sitemap.xml` lieferten 404, es gab keine Canonical-URLs, und die
Meta-Description beschrieb die Software statt den Verein
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

### 1. Sitemap in der Search Console einreichen

Die Search Console ist eingerichtet, aber `/sitemap.xml` lieferte bis zum
5. September 2026 einen 404. Ein damals eingetragener Sitemap-Verweis steht
seither mit Abruffehler drin und hat nie eine URL geliefert. Jetzt unter
*Sitemaps* `https://www.gourmen.ch/sitemap.xml` (neu) einreichen und einen
etwaigen alten, fehlerhaften Eintrag entfernen.

### 2. Externe Links aufbauen

Siehe „Der Hebel: externe Links" oben. Das ist der einzige Punkt, der die
Position tatsächlich bewegt.

### 3. Domain bei Zscaler kategorisieren lassen

Im Firmennetz des Betreibers blockiert Zscaler die Stylesheets mit 403 und
zeigt stattdessen eine Coaching-Seite („Seite nicht kategorisiert — wirklich
aufrufen?"). Beim HTML-Dokument kann man bestätigen, bei einem
`<link rel="stylesheet">` nicht — der Browser bekommt HTML statt CSS, verwirft
es, und die Seite bleibt unformatiert.

Ursache ist nicht die Site, sondern dass `gourmen.ch` in Zscalers globaler
URL-Datenbank als „Miscellaneous or Unknown" geführt wird. Einreichung über
[sitereview.zscaler.com](https://sitereview.zscaler.com/) — das Tool funktioniert
**nur aus einer Zscaler-Cloud-Verbindung heraus**, also vom Firmenlaptop.
Zielkategorie „Society and Lifestyle". Die Datenbank ist bei allen
Zscaler-Kunden weltweit dieselbe: eine Einreichung genügt.

### 4. Apex-Redirect muss den Pfad behalten

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

- **Mehr Inhalt auf den öffentlichen Seiten.** Die Landingpage hat rund 670
  Zeichen sichtbaren Text. Für Suchbegriffe wie „Restaurant Tipps Zürich"
  reicht das nicht; die Hitlist mit echten Beschreibungen wäre der natürliche
  Hebel.
- **Eingehende Links.** Der wichtigste Punkt überhaupt, siehe oben. Ohne
  externe Links bleibt jede technische Optimierung zahnlos.

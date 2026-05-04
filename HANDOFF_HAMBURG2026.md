# Handoff – Hamburg-2026-Reise-Tool

> Stand: 04.05.2026 (Patch 3.4.1). Grundintegration abgeschlossen + erster Inhalts-/UX-Patch
> ausgerollt. Andreas will eventuell weitere UI-/Inhalts-Aenderungen am Reise-Tool und/oder
> am Dashboard-Hero.

---

## TL;DR fuer den naechsten Agenten

- Reise-Tool als Single-File-Standalone unter `templates/events/hamburg2026.html`, Route
  `/events/hamburg2026` (`@login_required`).
- Dashboard hat oben eine `.dashboard-trip-hero`-Section (eigener BEM-Block) mit live-Countdown.
- Beides verschwindet automatisch nach `HAMBURG2026_VISIBLE_UNTIL = 01.06.2026 06:00`
  (in `backend/routes/events.py`).
- Cache-Buster ist auf `3.4.1`. Bei jeder UI-Aenderung weiter bumpen.

---

## Pflicht-Lektuere fuer den naechsten Agenten

1. `AGENTS.md` (Root) – das ist die Eingangstuer ins Repo. **Immer zuerst.**
2. `docs/UI.md` – BEM, Tokens, Cache-Buster-Workflow. Sektion 5.9 hat den
   `dashboard-trip-hero`-Eintrag in der Component Registry.
3. `docs/CONVENTIONS.md` – Service-Layer, Routes, Forms. Bei Backend-Aenderungen.
4. `KONZEPT.md` (Root) – das urspruengliche Konzept fuer beide Spuren (HTML + Canva-Teaser).
5. `COWORK_BRIEFING.md` (Root) – Tech-Briefing das Cowork beim Bauen hatte. Erklaert,
   wie Tokens, Schweizer Typo, BEM, externe Dependencies gehandhabt sind.
6. **Dieses Dokument** – aktueller Stand und To-Dos.

---

## Was schon passiert ist

### Code-Aenderungen

| Datei | Aenderung |
|---|---|
| `backend/routes/events.py` | Konstante `HAMBURG2026_VISIBLE_UNTIL` + Helper `hamburg2026_is_visible()` + Route `/hamburg2026` (`@login_required`, 404 nach Cutoff). Top-Import `abort` ergaenzt. |
| `backend/routes/dashboard.py` | Importiert `hamburg2026_is_visible`, gibt `hamburg2026_visible` an das Template. |
| `templates/dashboard/index.html` | Neue `<section class="dashboard-trip-hero">` ganz oben (`{% if hamburg2026_visible %}`), Mini-Countdown-JS am Script-Block-Ende. |
| `templates/events/hamburg2026.html` | Verschoben aus dem Root. Logo-Platzhalter durch echtes SVG ersetzt (`url_for('static', filename='brand/logo-master-round.svg')`). `.hamburg-back`-Pille oben links zum Dashboard. Leaflet-JS-SRI-Hash gefixt. Sonst Cowork-Original. |
| `static/css/v2/components.css` | Neuer Block `dashboard-trip-hero` (BEM, Brand-Gradient Orange↔Teal, Mobile-Responsive). |
| `docs/UI.md` | `dashboard-trip-hero` in Component Registry (Sektion 5.9 Dashboard). |
| `static/sw.js`, `templates/base.html`, `static/js/pwa.js` | Cache-Buster `3.3.7` → `3.4.0`. |
| `KONZEPT.md`, `COWORK_BRIEFING.md` | Status-Block oben hinzugefuegt. |

### Tests gemacht

- ✓ Tab-Navigation Fr/Sa/So
- ✓ Leaflet-Karte mit allen 11 Pins (nach Hash-Fix)
- ✓ Checkliste persistiert via `localStorage` (`hamburg2026:`-Praefix)
- ✓ Theme-Toggle Light/Dark
- ✓ Mobile 375px sauber
- ✓ Countdown live
- ✓ Lints alle gruen
- ✗ **Live-Test mit Flask** noch offen – Andreas testet selbst

### Patch 3.4.1 (04.05.2026 – Inhalts- und UX-Updates)

| Bereich | Aenderung |
|---|---|
| Hero | Logo entfernt, Titel `Hamburg 2026`, Untertitel `5 Jahre. 11 Gourmen. 1 Stadt.`, `<title>` + `<meta description>` angeglichen, ungenutztes `.hamburg-hero__logo`-CSS raus |
| PROGRAMM-Daten | Optionales `url`-Feld pro Item; gesetzt fuer Limobus, Abflug LX&nbsp;1052, Kieztour, ZWICK, HYGGE, Rueckflug LX&nbsp;1059 (Swiss-Flightstatus mit Query-Params). Limobus-`address` raus. Sa Hafenrundfahrt `time: '10:00'`. Streetfood-Mittag mit Inline-Links `<a class="hamburg-timeline-item__inline-link">` zu Kleine Haie und Grilly Idol |
| Programm-Kachel | Neuer sekundaerer `Website ↗`-Pill rechts unten (`.hamburg-timeline-item__actions` + `.hamburg-timeline-item__website`), wenn `url` gesetzt. Adress-Pill mit Maps-Link bleibt parallel erhalten |
| Pin-Liste | `PINS`-Item kann optional `website` haben → zusaetzlicher `Website ↗`-Pill (`.hamburg-pin-list__website`). Aktuell nur Cityhotel Monopol |
| Hausregeln | Cashless-Zonen-Eintrag entfernt |
| Checkliste | «Schickeres Outfit fuer ZWICK und HYGGE» → «Gourmen-Kleidung fuer ZWICK und HYGGE»; «Toilettenartikel» neu in Sonstiges |
| Sections klappbar | `Locations`, `Persoenliche Checkliste`, `Kontakte`, `Gut zu wissen` als `<details class="hamburg-section hamburg-section--collapsible">` mit `<summary><h2 class="hamburg-section__title">…</h2></summary>` und Chevron, default zu. Programm + Hero bleiben offen |
| Leaflet | `initMap` setzt jetzt `hamburgMap`/`hamburgMapBounds` modulweit; `<details>`-`toggle`-Listener ruft `invalidateSize()` + `fitBounds()` beim ersten Aufklappen, sonst rendert die Karte 0×0 |
| Cache-Buster | 3.4.0 → 3.4.1 |

---

## Architektur-Entscheidungen die nicht aufgeweicht werden duerfen

1. **Single-File bleibt Single-File**. Die HTML wird ohne `base.html`-Wrapper gerendert. Kein
   `{% extends %}`. Eigenes Theme-System, eigenes Layout, eigene Tabs. Begruendung: Cowork-
   Iteration soll moeglich bleiben ohne BEM-Refactoring der ganzen Datei.
2. **Tokens 1:1 aus PWA**. Im `:root`-Block der HTML stehen die selben Werte wie in
   `static/css/v2/tokens.css`. Wenn dort was geaendert wird (selten), muss die HTML
   nachgezogen werden. Beim Aendern der HTML-Tokens nicht raten – immer aus tokens.css
   uebernehmen.
3. **Cutoff zentral**. Alles Hamburg-Sichtbare laeuft ueber `hamburg2026_is_visible()`.
   Nicht an mehreren Stellen `datetime`-Vergleiche bauen.
4. **`hamburg-*`-Praefix in der Standalone-HTML, `dashboard-trip-hero` im PWA-Dashboard**.
   Nicht vermischen. Das Reise-Tool ist isoliert, der Dashboard-Hero ist Teil der PWA.
5. **Login-Wall** auf der Reise-Route. Nicht aufweichen, auch nicht «nur fuers Sharen».
   Wenn Sharing gewollt ist, Konzept mit Andreas absprechen (nicht oeffentliche Route).

---

## Worauf der naechste Agent achten muss

### Bei Aenderung am Reise-Tool (`templates/events/hamburg2026.html`)

- Datei ist >1200 Zeilen, hat eigenen `<style>`- und `<script>`-Block. Nicht in `base.html`-
  Pattern umbauen, das war eine bewusste Entscheidung.
- Schweizer Typo durchziehen: «...» (Guillemets), – (Halbgeviertstrich), `5'000 €` (Apostroph),
  `&nbsp;` zwischen Zahl und Einheit, kein Eszett ausser bei Eigennamen («Aussenalster» wurde
  bewusst als «Außenalster» belassen, weil deutscher Eigenname). Falls weitere Tonalitaet-
  Patches: konsequent.
- Daten-Objekte (`PROGRAMM`, `PINS`, `KONTAKTE`, `CHECKLISTE`) stehen oben im Script-Block.
  Inhaltliche Aenderungen (neue Telefonnummer, geaendertes Programm) gehen dort rein.
- Bei Logo-Aenderung: das echte Logo ist `static/brand/logo-master-round.svg`. Nicht durch
  Inline-SVG-Platzhalter ersetzen – Cowork hatte den nur, weil sie das echte SVG nicht hatte.
- Bei Cowork-Patches an dieser Datei: Cowork sieht die Datei nicht. Entweder Diff manuell
  uebertragen oder einen frischen Standalone-Export erzeugen (im Original-Cowork-Workspace,
  Logo-Block + Back-Link entfernen, dann liefert Cowork eine neue Variante – die wieder
  integriert werden muss).

### Bei Aenderung am Dashboard-Hero (`dashboard-trip-hero`)

- BEM-Klasse ist `.dashboard-trip-hero` mit Elementen `__link`, `__logo`, `__body`, `__eyebrow`,
  `__title`, `__meta`, `__countdown`, `__dot`, `__cta`, `__cta-label`, `__chev`. Bei neuem
  Element/Modifier: Component Registry in `docs/UI.md` Sektion 5.9 erweitern.
- CSS lebt in `static/css/v2/components.css` ganz unten. Markup im Dashboard-Template
  zwischen `{% if hamburg2026_visible %}` und `{% endif %}`.
- Countdown-Logik im `<script>`-Block am Ende von `templates/dashboard/index.html`. Target-
  Zeitpunkt steht als `data-trip-target` am `[data-trip-countdown]`-Element (ISO mit
  Zuerich-Offset).
- Brand-Gradient ist bewusst dezent (Orange 10% / Teal 8%). Nicht stark ueberzeichnen –
  konkurriert sonst mit dem orangenen Hero-Border der `.dashboard-intent-tile`.

### Cache-Buster (Pflicht nach UI-/JS-/CSS-/Template-Aenderungen)

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/update_pwa_version.py 3.4.1
```

⚠️ **Achtung**: Das Skript matcht nicht alle Stellen. Manuell nachziehen:
- `static/sw.js` Zeile 6: `const VERSION = '3.4.x';` (Template-Literal-Pattern)
- `static/js/pwa.js` Zeile 6: `const PWA_VERSION = '3.4.x';`

`templates/base.html` wird vom Skript korrekt aktualisiert. Nach Bump grep'en, dass keine
alten Versions-Strings (`3.3.7`, `3.4.0` etc.) uebrig sind.

### Service Worker im Browser

PWAs cachen aggressiv. Beim lokalen Testen nach Aenderungen entweder
- Hard-Reload (Ctrl+Shift+R), oder
- DevTools → Application → Service Workers → Unregister + Hard-Reload, oder
- DevTools → Application → Storage → Clear site data.

Auf Production loest der Versions-Bump das automatisch aus.

---

## Was Andreas eventuell aendern moechte (Auswahl)

Andreas hat noch nicht spezifiziert was, aber moegliche Richtungen:

- **Tonalitaet/Wording im Reise-Tool**: Texte, Untertitel, Hinweise
- **Inhaltliche Patches**: neue Telefonnummern, geaenderte Adressen, neue Programmpunkte
  (Marlon/Jutta/Stambula-Antworten kommen ggf. noch)
- **Dashboard-Hero**: Wording (Eyebrow, Title, CTA-Label), Countdown-Format, Logo-Groesse
- **Visuelle Tweaks**: Border-Radius, Spacing, Brand-Gradient-Intensitaet
- **Inspirations-Pool**: Optionen ergaenzen/streichen
- **Karte**: weitere Pins, Pin-Icons, Cluster-Verhalten

Wenn was unklar ist – fragen, nicht raten.

---

## Spur 2 (Canva-Teaser) ist noch offen

`KONZEPT.md` Spur 2 beschreibt einen 28-Sekunden-Cinematic-Teaser fuer WhatsApp/Status. Der
ist noch nicht angegangen. Falls Andreas dazu uebergeht: das ist Canva-Arbeit, kein Code.
Du als Code-Agent kannst ihm hoechstens beim Briefing-Sharpening helfen.

---

## Start-Prompt fuer den naechsten Agenten

```
Lies AGENTS.md und HANDOFF_HAMBURG2026.md im Repo-Root, dann die referenzierten Anchor-Docs
(docs/UI.md, docs/CONVENTIONS.md) und KONZEPT.md / COWORK_BRIEFING.md.

Aktueller Stand: das Hamburg-2026-Reise-Tool ist als Standalone-HTML unter
templates/events/hamburg2026.html integriert, Route /events/hamburg2026 (login_required),
Dashboard-Hero-Section .dashboard-trip-hero auf /dashboard, Cutoff 01.06.2026 06:00 ueber
hamburg2026_is_visible(). Cache-Buster auf 3.4.1. Tests sind durch, Lints gruen.

Ich moechte folgendes aendern: INfo folgt.

Wichtige Constraints, die der vorige Agent festgelegt hat (siehe HANDOFF):
- Single-File-Charakter der Reise-HTML bleibt erhalten (kein base.html-Wrap).
- Tokens 1:1 aus static/css/v2/tokens.css.
- Cutoff zentral via HAMBURG2026_VISIBLE_UNTIL.
- Schweizer Typo (Guillemets, Halbgeviertstrich, kein Eszett ausser Eigennamen).
- BEM-Praefix hamburg-* in der Standalone-HTML, dashboard-trip-hero im Dashboard.
- Login-Wall auf der Reise-Route bleibt.
- Cache-Buster nach jeder UI-Aenderung bumpen (sw.js + pwa.js manuell, Skript matcht
  Template-Literal-Pattern nicht).

Bevor du loslegst: kurz zusammenfassen, was du aendern wirst, und auf was du achtest.
Bei Unklarheit fragen, nicht raten.
```

# Briefing-Konzept – Gourmen Jubiläumsreise Hamburg 2026

> Konzept-Dokument für zwei parallele Spuren:
> 1. **Schlanke HTML** – funktionales Tool für die Reise, geliefert als Single-File, von Andreas in `gourmen_pwa` integriert und über die App distribuiert
> 2. **Canva-Teaser-Video** – emotionaler Marketing-Vorbote, MP4 für WhatsApp/Status
> Stand: 02.05.2026, überarbeitet 02.05.2026 nach Andreas' Feedback.

> **Status (03.05.2026):** Spur 1 ist umgesetzt. HTML lebt unter `templates/events/hamburg2026.html`,
> Route `/events/hamburg2026` (login_required), Dashboard-Hero-Section sichtbar bis 01.06.2026 06:00
> (siehe `HAMBURG2026_VISIBLE_UNTIL` in `backend/routes/events.py`). Begleit-Briefing fuer Cowork
> in `COWORK_BRIEFING.md`. Spur 2 (Canva-Teaser) noch offen.
> Nach der Reise (>01.06.2026) sollten beide Source-Briefings nach `docs/initiatives/_archive/`
> verschoben werden.

---

## Globale Rahmenbedingungen

### Visuelle Identität

– **Vereinslogos verfügbar**: `logo-master-round.svg` (rund) und `logo-master-square.svg` (eckig), beide hochauflösend im Projektordner
– **CI-Quelle**: PWA-Repo `gourmen_pwa` (BEM + Tokens V2). Da Andreas den HTML-Single-File später selbst in die App integriert, baue ich mit **CSS Custom Properties** im `:root`-Block – beim Einbinden kann er einfach die paar Variablen-Werte gegen die PWA-Tokens austauschen
– **Sprache**: ausschliesslich Deutsch
– **Schweizer Konventionen**: Guillemets «...», Halbgeviertstrich – als Aufzählungszeichen, kein Eszett

### Distribution
– **HTML**: einziger Verteilungskanal ist die Gourmen-App. Andreas integriert die Single-File ins PWA-Modul, die Mitglieder finden's via App-Navigation
– **Teaser-MP4**: WhatsApp/Status, ggf. Vereinsmail, Social-Media (falls geplant)

---

## Spur 1: Schlanke HTML – «Tool für die Reise»

### Zweck und Persona
Ein Mitglied steht Sa 18:25 verwirrt in der Speicherstadt und muss in 5 Min wissen: *Wo genau ist der Sprinter-Pickup? Wann ist Hygge?* Die HTML beantwortet jede solche Mikro-Frage in unter 10 Sekunden, mobile-first, ohne Scrollen-bis-zum-Mond. Kein Marketing, keine Emotionen – Funktion.

### Architektur

**Format**: Single-File HTML (ein einziges `.html`, alles inline – CSS, JS, Daten). Andreas baut die Datei später in die PWA ein (z.B. als Jinja-Template-Block oder als statische Subseite).

**Layout-Prinzip**: Mobile-first, vertikales Scrollen mit Sticky-Tab-Navigation oben. Sechs Sektionen, alle direkt erreichbar. Auf Desktop maximal 720 px breit zentriert.

**Stil**: CSS Custom Properties im `:root` für Farben, Typo, Spacing – einfach überschreibbar mit PWA-Tokens. Beispiel-Struktur:

```css
:root {
  --color-primary: ...;       /* Vereinsfarbe der PWA */
  --color-text: ...;
  --color-bg: ...;
  --color-accent: ...;
  --font-display: ...;
  --font-body: ...;
  --radius-card: ...;
  --space-stack-md: ...;
}
```

Andreas tauscht beim Integrieren in PWA die Werte gegen seine Tokens V2 aus, Rest läuft.

### Sektionen im Detail

#### 1. Hero (mini)
Eine Bildschirmhöhe oder weniger. Enthält:
– **Vereinslogo (rund)** als Marker oben
– Vereinsname + Anlass: «Gourmen 5 – Hamburg 2026»
– Live-Countdown bis Fr 29.05.2026 08:30 (Abflug Zürich)
– Drei Eckdaten als Pillen: 📅 29.–31.05. ✈️ ZRH↔HAM 🏨 Cityhotel Monopol
– Mini-Hinweis: «Nur Handgepäck» und «Treffpunkt 06:30 Flughafen Zürich Swiss-Schalter»

#### 2. Programm Tag-für-Tag
Tab-Navigation: «Fr» / «Sa» / «So». Jeder Tab ist eine vertikale Zeitleiste mit Eintrags-Karten. Pro Eintrag:
– Uhrzeit (gross, fett)
– Titel der Aktivität
– Adresse mit One-Tap-Link auf Karte-Sektion (oder native Maps-App)
– Icon links als visueller Anker (✈️ 🚐 🐟 🎭 🎸 🍺 ⛵ 🌿 🏖️)
– Bei kritischen Punkten (Limobus, Sammelpunkt Speicherstadt, Sprinter-Abfahrt) farbliche Hervorhebung

##### Eingebauter klappbarer Block: Inspirations-Pool Sa-Nachmittag
Im «Sa»-Tab eine `<details>`/`<summary>`-Sektion: «Inspirations-Pool für den freien Nachmittag» – standardmässig zugeklappt, beim Aufklappen sieben Optionen mit kurzer Beschreibung und Adresse (Speicherstadt+Plaza, Schanze, Außenalster, Michel-Turm, Miniatur Wunderland, Karoviertel, Beatles-Spuren).

#### 3. Locations + Karte
Eingebettete **Leaflet-Karte** (OpenStreetMap-Tiles, datenschutzfreundlich, open-source, kein Google-Tracking). Zentriert auf Hotel. Pins für alle Programm-Locations. Klick auf Pin → Popup mit Name + Adresse + «In Maps öffnen»-Link.
Darunter: Pin-Liste als alphabetisch sortierte Tabelle mit One-Tap-Tel-Links für Restaurants/Bars.

#### 4. Persönliche Checkliste
Liste mit Checkboxen, gegliedert in: Dokumente / Zahlungsmittel / Kleidung / Sonstiges. Stand wird im Browser via `localStorage` pro Person gespeichert (jeder sieht eigenen Stand, kein Sync). Optional: «Reset»-Button.

#### 5. Kontakte + Notfallnummern (schlanker)
Drei Blöcke (Reise-Crew und WhatsApp-Gruppe sind raus, da via Vereinsapp eh redundant):
– **Vor Ort**: Cityhotel Monopol, Hotelplan 24h, Limobus, Kieztour, Stambula – jeweils mit `tel:` und `mailto:` Links
– **Notfälle DE**: 112 / 110 / 116 117

#### 6. Mini-Hausregeln-Box
Vier Bullet-Points, knapp, funktional:
– Glasflaschen-Verbot Reeperbahn Fr 22:00 bis Mo 06:00 (Bussgeld bis 5'000 €)
– Cashless-Zonen: Grilly Idol + StrandPauli Fullservice
– «Zur Ritze» Boxerkeller: Getränkebestellung beim Wirt
– Trinkgeld: 5–10% in DE üblich

### Tech-Stack

– **HTML5** semantisch (header, nav, section, article, details/summary)
– **CSS** inline, Custom Properties für Tokens, mobile-first mit min-width-Media-Queries
– **JavaScript** vanilla, kein Framework, kein Build-Schritt
  – Countdown-Timer (rerendered jede Minute)
  – Tab-Navigation
  – `localStorage`-Handling für Checkliste
  – Leaflet-Initialisierung
– **Externe Abhängigkeit (CDN)**: Leaflet (`leaflet@1.9` von cdnjs) – 41 KB gzipped
– **Keine** Tracking, Analytics, externe Schriftarten (Andreas tauscht beim Integrieren ggf. zur PWA-Schrift)
– **Logo**: rund als Hero-Anker, eckig optional als Footer-Marker

### Pfad zur PWA-Integration
Andreas erhält die Single-File HTML. Beim Integrieren in `gourmen_pwa`:
1. Die `:root`-Custom-Properties gegen Tokens V2 austauschen
2. BEM-Klassen ggf. nachziehen (oder die HTML direkt als isoliertes Modul lassen)
3. Als Jinja-Template einbinden (z.B. `templates/events/hamburg2026.html`) und Blueprint-Route registrieren
4. Service Worker erweitert die Offline-Lesbarkeit der App auch auf diese Seite

### Akzeptanzkriterien
– Lädt in unter 1 Sekunde auf 4G
– Funktioniert offline nach erstem Aufruf (Service-Worker-fähig)
– Lesbar ohne JavaScript für Notfall-Inhalt (Kontakte, Adressen)
– Mobile-tested auf iOS Safari + Android Chrome
– Adressen-Tap öffnet native Maps-App

---

## Spur 2: Canva-Teaser-Video – «Cineastischer Vorbote»

### Zweck und Persona
Ein Gourme öffnet WhatsApp, sieht von Andreas einen 25–30-Sekunden-Clip im Status. Filmtrailer-Vibe für unser Wochenende: erst Spannungsaufbau, dann Eskalation, am Ende eindeutiger Call-to-Action zur App. Soll richtig Lust auf ein geiles Weekend wecken.

### Format und Spezifikation

**Canva-Designtype**: «Your Story» – vertikales Format 1080×1920 px, ideal für Mobile/WhatsApp/Stories.
**Export**: MP4, Qualität horizontal_1080p (~5–10 MB Dateigrösse).
**Dauer**: ~28 Sekunden, 8 Slides mit Cineastik-Übergängen.
**Audio**: Canva-Library, Genre **«Cinematic»** oder **«Epic Cinematic»** – Streicher, Drum-Build-Up, Filmtrailer-Energie. Kein Voice-Over.

### Storyboard (8 Slides)

#### Slide 1 – Cinematic Opener (3.5 Sek)
**Ton**: Tiefer Cinematic-Drone-Sound, langsam ansteigend.
**Visual**: Schwarzer Hintergrund. Vereinslogo (rund) erscheint zentriert in Fade-In, dezent leuchtend. Darunter eingeblendet in Serifen-Display-Schrift: «GOURMEN 5».
**Text-Animation**: Ruhig, kein Wackeln.
**Übergang**: Langsamer Fade auf Slide 2.

#### Slide 2 – Eckdaten (3 Sek)
**Ton**: Subtle Hi-Hat, Beat-Aufbau beginnt.
**Visual**: Hamburg-Skyline-Stockphoto (Hafen mit Elbphilharmonie, Dämmerung) als Vollbild-Hintergrund mit dunklem Overlay. Drei Pillen einblendend: «📅 29.–31. Mai 2026» / «✈️ Zürich → Hamburg» / «🏨 Cityhotel Monopol».
**Übergang**: Crossfade.

#### Slide 3 – Highlight Party-Limo (3.5 Sek)
**Ton**: Erster Drum-Hit.
**Visual**: Stockphoto Stretch-Limo bei Nacht oder Reeperbahn-Lichter. Headline: «Ankunft mit Stil». Subtext animiert einfliegend: «Limobus Hamburg-Edition direkt vom Flughafen».
**Augenzwinkern**: Kleine Bauchbinde unten: «leider ohne Stripshow ;)».
**Übergang**: Cut auf Beat.

#### Slide 4 – Highlight Titten Tina's Kieztour (3.5 Sek)
**Ton**: Intensiver Beat-Build.
**Visual**: Reeperbahn bei Nacht oder Bühnenscheinwerfer-Stockphoto. Headline: «Titten Tina's Kieztour». Subtext: «Comedy pur · Boxerkeller · exklusiv für uns».
**Übergang**: Schneller Cut.

#### Slide 5 – Highlight Hafen + Speicherstadt (3.5 Sek)
**Ton**: Streicher kommen dazu.
**Visual**: Speicherstadt-/Wasserschloss-Stockphoto bei goldenem Licht. Headline: «Hamburger Wahrzeichen». Subtext: «Hafenrundfahrt · Speicherstadt · Plaza».
**Übergang**: Slow Zoom-In.

#### Slide 6 – Highlight Kulinarik (3.5 Sek)
**Ton**: Climax beginnt.
**Visual**: Split-Screen oder schneller Bilder-Wechsel: Hygge-Restaurant-Vibe + StrandPauli-Beachclub. Headline: «Kulinarik wird grossgeschrieben». Subtext: «HYGGE Brasserie · StrandPauli Beachclub».
**Übergang**: Cinematic Match-Cut.

#### Slide 7 – Climax (3 Sek)
**Ton**: Voller Drum-Hit, Streicher-Crescendo.
**Visual**: Schnell wechselnde Hamburg-Impressionen oder ein dramatisches Hafen-Einzelbild. Grosser animierter Text: «Bald geht's los».
**Übergang**: Sound dämpft, Visual wird ruhiger.

#### Slide 8 – Closing & Call-to-Action (4 Sek)
**Ton**: Outro-Hall, dezenter Schlussakkord.
**Visual**: Schwarzer Hintergrund, Vereinslogo (rund) mittig, darunter Schweizer-Stil-Text:
**Zeile 1 (gross)**: «Alle Details jetzt in der Gourmen App»
**Zeile 2 (klein, subtil)**: «www.gourmen.ch» (oder konkrete App-URL falls vorhanden)
**Note**: MP4 ist nicht klickbar, aber URL als sichtbarer Hinweis – Mitglieder kennen die App.
**Übergang**: Final Fade-Out.

### Visuelles Konzept

**Farb-Palette** (PWA-CI orientiert, finalisiert nach Andreas-Input):
– Primär: Vereinsfarbe aus PWA (CTA, Headlines) – exakter Wert noch zu liefern
– Sekundär: dezenter Akzent
– Cineastische Grundierung: dunkles Anthrazit (`rgb(15,20,30)`) als Hintergrund-Standard für Drama
– Highlight-Akzent: warmes Licht (`rgb(255,200,140)` oder ähnlich) für Hamburg-Hafen-Goldlight-Effekte

**Typografie** (Canva-Suche):
– Display: «Bebas Neue» oder «Anton» (Filmtrailer-Look)
– Body: Helvetica oder System-Fallback Arial
– Schweizer Konventionen («...», –)

**Animations-Stil**:
– Slow-Build, dann Beat-Drop um Slide 3 herum
– Cinematic Übergänge: Crossfade, Slow Zoom, Match-Cut
– Kein hektisches Bouncing – ruhige, gewichtige Bewegungen
– Bild-Material: Pro-Stockphotos aus Canva, Genre «Cinematic Hamburg» / «Cityscape Night» / «Harbor Sunset»

### Akzeptanzkriterien
– Funktioniert ohne Ton (Stumm-Schauer in der Tram)
– Lesbar in ~3 Sekunden pro Slide
– Vereinsidentität sichtbar (Logo, PWA-Farbe)
– Cineastik spürbar (langsamer Build, dramatische Übergänge)
– CTA in Slide 8 unmissverständlich

---

## Implementierungs-Reihenfolge (Vorschlag)

1. **Konzept-Review** (jetzt) – du liest, korrigierst, ergänzt
2. **PWA-CI-Werte sammeln** – du lieferst mir Farb-Codes, Schrift-Namen, ggf. ein bis zwei Beispiel-Komponenten
3. **Spur 1 HTML-Prototyp** – ich baue eine erste Version mit deinen Tokens; du reviewst Funktionalität und Design
4. **Spur 2 Canva-Teaser** – ich generiere Design im Canva-Account, du reviewst Slide-by-Slide, iterieren
5. **Finalisierung HTML** mit endgültigen Inhalten (sobald Marlon, Jutta, Stambula geantwortet haben)
6. **Export Canva → MP4**, Versand-Test
7. **PWA-Integration** der HTML – machst du selbst

---

## Was ich noch von dir brauche, um die HTML stilkonform zu bauen

### Variante A – «PWA-Tokens direkt»
Falls schnell zur Hand: kopiere mir den Inhalt deiner zentralen Tokens-CSS-Datei (z.B. `static/css/tokens.css` oder ähnlich) in den Projekt-Folder. Dann übernehme ich die exakten Variablen-Werte 1:1.

### Variante B – «Eckwerte mündlich»
Falls schneller: nenne mir kurz die folgenden Werte:
– Hauptfarbe (Hex / RGB), z.B. `#0E7C7B`
– Akzentfarbe für CTA / Hervorhebungen
– Hintergrund-Hauptfarbe (hell/dunkel)
– Textfarbe Standard
– Schrift (Body und Display, falls verschieden)
– Border-Radius-Standard (eckig / abgerundet?)

### Variante C – «Lass mich raten»
Falls du komplette Kontrolle beim Integrieren willst, baue ich mit einem soliden Default-Set (modernes Anthrazit-Grau + dezenter Akzent), du tauschst beim Einbinden alles aus. Funktioniert auch.

---

## Offene Konzept-Fragen

– **Vereins-Bilder**: hast du brauchbares Material aus früheren Events (z.B. Gruppenfoto, kulinarisches Highlight) für den Teaser, oder gehen wir komplett mit Stock-Bildern?
– **App-URL für CTA-Slide**: gibt's eine «Direktlink»-URL zur PWA (z.B. `app.gourmen.ch`), oder nur die Marke `www.gourmen.ch`?
– **Vereins-Logo Variante im Teaser**: rund (mein Default) oder eckig?
– **Musik-Lizenz**: Canva-Audio ist mit deinem Account lizenziert für nicht-kommerzielle Nutzung – passt das, oder willst du selbst was hochladen?

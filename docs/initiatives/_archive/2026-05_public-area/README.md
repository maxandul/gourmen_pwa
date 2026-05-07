# Initiative: Public-Area (oeffentlicher Bereich der PWA)

**Status**: abgeschlossen  
**Start**: 2026-05  
**Ende**: 2026-05 (alle Phasen done; letzte Auslieferung inkl. Tabellen-Polish GGL/Events PWA v3.9.3)  
**Branch-Prefix**: `phase/NN-public-area-<kurzname>` (Historie)  
**Archiv-Pfad**: `docs/initiatives/_archive/2026-05_public-area/`

## Zweck

Den oeffentlichen Bereich (anonymer Besucher der Domain) so strukturieren, dass er den Verein praesentiert und einen klaren Login-Pfad bietet, ohne mit der eingeloggten App-Shell (Sidebar / Bottom-Nav / User-Bar) zu kollidieren.

Heutiger Pain:

- Login-Button liegt mitten im Hero, untypisch und schlecht auffindbar
- `_user_bar` wird auf der Landing eingeblendet und zeigt fuer anonyme Besucher ein verwirrendes "User-Menue" mit nur einem "Anmelden"-Eintrag
- Es gibt **keinerlei** Public-Subpages (kein "Ueber uns", keine reine Hitlist-Seite)

## Strategische Entscheidungen

| Entscheidung | Wert |
|---|---|
| **Shell-Trennung** | Public-Shell (Top-Nav + Footer) vs. App-Shell (User-Bar + Sidebar/Bottom-Nav). Beide schliessen sich aus. |
| **Login-Position** | Primaerer CTA "Login" rechts oben in der Public-Top-Nav. Kein Login-Button mehr im Hero. |
| **Eingeloggter User auf Public-Page** | Statt "Login" erscheint "Zum Memberbereich" + bestehendes User-Menue. |
| **Mobile-Navigation** | Scrollbare Pill-Tabs in der Mitte der Top-Bar (Logo links, Pills mittig, Theme-Toggle + Login rechts). Kein Hamburger – Logo und Login beanspruchen schon links/rechts. |
| **Hitlist-Teaser auf Landing** | Top 5 nach Gourmen-Rating absteigend, ohne Suche und Pagination, mit Link auf `/restaurants`. |
| **Footer (Public)** | Bleibt vorerst unveraendert (Socials + Mail). |

## Out-of-Scope (bewusst ausgeklammert)

Stand 2026-05 nicht Teil dieser Initiative:

- "Mitglied werden"-Seite
- Kontaktformular (Mail + Instagram im Footer reichen)
- Datenschutz-Seite
- Impressum (Verein nicht-kommerziell, in CH nicht zwingend)
- Statuten-Page / PDF-Download
- Eigene "Aktivitaeten"-Seite (wird als Sektion auf "Ueber uns" geloest)
- Member-Galerie auf "Ueber uns" (mittelfristig: alle 11 Mitglieder vorgestellt – nicht in Phase 2)

## Seiten-Struktur (Endzustand der Initiative)

| Route | Zweck |
|---|---|
| `/` | Landing: Hero (Marke) · zweite Card (Pitch + Stats + Link Ueber uns) · Hitlist-Teaser (Top 5) |
| `/ueber-uns` | Verein, Leitbild, Geschichte, Aktivitaeten-Sektion, Funktionen aus `Funktion`-Enum (nur abstrakte Texte) |
| `/restaurants` | Vollansicht Gourmen-Hitlist mit Suche + Pagination |

Alle Routes leben im bestehenden `public`-Blueprint.

## Phasen

| # | Phase | Inhalt | Status |
|---|---|---|---|
| 1 | Shell-Split + Login-Reposition | Public-Top-Nav + Public-Footer-Partial; Hero ohne Login-Button; Login-Pfad ueber den `.user-menu`-Avatar (immer sichtbar – im anonymen Zustand enthaelt das Dropdown nur "Anmelden"); Pill-Tabs auf allen Viewports; Hitlist auf Landing zum Top-5-Teaser; Route `/restaurants` | **done** 2026-05 (visuell verifiziert; PWA v3.7.9) |
| 2 | Ueber-uns-Seite | Route `/ueber-uns` (`public.about`), Template `public/about.html`; Topnav-Pill + Drawer; von `/` erreichbar (Hero-CTA statt Teaser-Card); Sektionen Leitbild, Geschichte, Aktivitaeten, Funktionen (anonymisiert) | **done** 2026-05 (PWA v3.7.9) |
| 3 | Hitlist-Vollansicht polieren | `/restaurants`: Intro, Trefferzeile, Sortierung (`rating` \| `recent` \| `name`), Kuechen-Spalte, gleicher Landing-Footer | **done** 2026-05 (PWA v3.8.9) |

Phase 1 ist der eigentliche Strukturschritt. Phase 2 und 3 sind Content- bzw. Polishing-Arbeit auf der etablierten Shell.

## Acceptance-Criteria pro Phase (high level)

### Phase 1

- Anonymer Besucher auf `/` sieht Public-Top-Nav (Logo, Pills "Ueber uns" + "Hitlist", Theme-Toggle, "Login").
- Eingeloggter Besucher auf `/?show=1` sieht die Public-Top-Nav, aber rechts statt "Login" einen "Zum Memberbereich"-CTA + User-Menue.
- `_user_bar`, `_sidebar`, `_bottom_nav` werden auf Public-Routes nicht gerendert.
- Hero auf `/` enthaelt **keinen** Login-Button mehr.
- Hitlist auf `/` zeigt Top 5 nach `overall_avg DESC`, ohne Suche/Pagination, mit Link "Alle Restaurants ansehen" -> `/restaurants`.
- `/restaurants` rendert die heutige Vollansicht der Hitlist (Suche + Pagination funktional).
- Mobile (<= 768px): Pill-Tabs scrollen horizontal, beruehren Logo/Login nicht.
- `docs/UI.md` Component Registry ergaenzt um neue Klassen (`public-topnav`, ggf. `pill-tabs`).
- Cache-Buster gemaess `.cursor/rules/ui.mdc` gebumpt (`sw.js`, `base.html`, `pwa.js`).

### Phase 2

- `/ueber-uns` erreichbar, in Public-Top-Nav verlinkt.
- Sektionen: Leitbild ("Meh isch meh"), Vereinsgeschichte (seit 2021), Aktivitaeten (Monatsessen / GGL / Ausflug / BillBro / GV), Funktionen (Vereinspraesident, Kommissionspraesident, Schatzmeister, Marketingchef, Reisekommissar, Rechnungspruefer, Mitglied) – jeweils mit kurzem Beschriebstext, **abstrakt** ohne Personennamen.
- Von `/` zur Ueber-uns-Seite verlinken (z. B. Hero-Bereich oder Nav).

### Phase 3

- `/restaurants` hat eine kurze Einleitung und eine Statuszeile (Trefferzahl bzw. Gesamtzahl Restaurants).
- Sortierung per Query `sort=` und UI: `rating` (Standard), `recent` (zuletzt besucht), `name` (A–Z); Suche und Pagination bleiben AJAX-freundlich.
- Tabelle um Spalte «Kueche» ergaenzt (Desktop; schmale Viewports: Spalte ausgeblendet).
- Gleicher `landing-footer` wie auf der Landing fuer Kontakt/Social.

## Code-Pattern (Vorgriff fuer Phase 1)

- Neue Partial `templates/partials/_public_topnav.html` (Logo + Pill-Tabs + Theme-Toggle + Login/Memberbereich).
- Neue Partial `templates/partials/_public_footer.html` (heutiger Landing-Footer in Partial promoten, damit `/ueber-uns` und `/restaurants` ihn wiederverwenden).
- Steuer-Mechanik in `base.html`: Flag `is_public_layout` in den Public-Routes setzen (oder via `request.endpoint.startswith('public.')`); App-Shell-Partials nur rendern wenn Flag false.
- Hitlist-Logik (`get_landing_restaurant_table`) bleibt im Service – Landing ruft mit `per_page=5`, `/restaurants` mit Pagination.
- Routes neu im `public`-Blueprint: `/ueber-uns`, `/restaurants`.

## Out-of-Scope-Diskussion (fuer spaeter ausserhalb dieser Initiative)

- Mitglied-werden-Flow mit Bewerbungsformular
- Datenschutz / Impressum (sobald rechtlicher Bedarf entsteht, z.B. bei Payment-Integration)
- Member-Galerie auf "Ueber uns" mit echten Profilen
- Statuten als Download oder Sub-Page
- Public-Events-Teaser (z.B. Generalversammlungs-Termin)

Diese Themen werden bei Bedarf in einer eigenen Initiative oder als Phase 4+ ergaenzt.

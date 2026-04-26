# Initiatives

Übersicht aller zeitlich begrenzten Vorhaben (Initiatives) im Repo.

## Was ist eine Initiative?

Eine Initiative ist ein **zeitlich begrenztes Vorhaben** mit klarem Anfang und Ende, das nicht in den stabilen Anchor-Docs (ARCHITECTURE, CONVENTIONS, DOMAIN, UI) lebt, weil es einen begrenzten Lebenszyklus hat.

Beispiele:
- Plattform-Migration (Hosting wechseln, neue Module integrieren)
- Major-Refactoring (z.B. Tech-Stack-Update)
- Vereins-Initiativen (z.B. Mitglieder-App-Roll-out)

## Struktur

Jede Initiative bekommt einen eigenen Slug-Ordner:

```
docs/initiatives/<slug>/
├── README.md                    ← Master-Plan, Strategie, Phasen-Tabelle, Status-Tracker
├── PHASE_NN_<name>.md           ← Detail-Doc pro Phase mit Pre-Conditions,
│                                  Tasks, Acceptance-Criteria, Cursor-Briefing
└── ggf. weitere Detail-Docs
```

## Lifecycle

### Aktive Initiative

- Lebt unter `docs/initiatives/<slug>/`
- README enthält Phasen-Tabelle mit Status (`pending`, `in_progress`, `done`, `blocked`)
- Pro Phase ein eigener Branch `phase/NN-<slug>-<name>`
- Nach jeder Phase: README-Status aktualisieren

### Abgeschlossene Initiative

- Bleibende Erkenntnisse werden in stabile Anchor-Docs (ARCHITECTURE, CONVENTIONS, DOMAIN, UI) verschoben
- Initiative-Ordner wird verschoben nach `docs/initiatives/_archive/<datum>_<slug>/`
  - Datum-Präfix Format: `YYYY-Q<n>` oder `YYYY-MM` (für Sortierung)
- Initiative-spezifische Cursor-Rules werden entfernt
- Diese README hier aktualisieren (Status-Tabelle)

## Aktuelle Initiativen

| Slug | Status | Beschreibung | Start | Ende |
|---|---|---|---|---|
| `modules-and-hosting` | aktiv | Module-Erweiterung (Mail, Files, Buchhaltung, TWINT, ...) auf Railway | 2026-04 | – |

## Archiv

| Slug | Datum | Beschreibung |
|---|---|---|
| `2025_redesign` | 2025–2026 | UX-Redesign mit BEM + Tokens, abgeschlossen vor `modules-and-hosting` |

## Cursor-Rule

Das generische Initiative-Pattern ist in `.cursor/rules/initiatives.mdc` definiert. Diese Rule greift in `docs/initiatives/**` und beschreibt Workflow, Branch-Naming, Doc-Pflege.

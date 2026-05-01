# Agent Briefing – Gourmen PWA

Eingangstor für jeden AI-Agent, der an diesem Repo arbeitet.

## Was das ist

**Gourmen PWA** ist die Web-App des Gourmen-Vereins (CH). Flask-Backend, Postgres, Railway-Hosting, installierbare PWA mit Service Worker und Push-Notifications. Sprache der UI: Deutsch (kein Eszett im Code/Templates).

## Vor jeder Code-Änderung lesen

Diese drei stabilen Anchor-Docs sind Pflicht-Lektüre, je nach Aufgabe:

- **`docs/ARCHITECTURE.md`** – Stack, Modul-Struktur, externe Services. Bei Backend-Änderungen.
- **`docs/CONVENTIONS.md`** – Code-Standards (Service-Layer, Routes, Models, Forms). Bei Code-Änderungen.
- **`docs/DOMAIN.md`** – Vereinsspezifische Begriffe (BillBro, GGL, Spirit Animal, Funktionen). Bei jeder Änderung mit Vereins-Bezug.
- **`docs/UI.md`** – Designsystem, Component Registry, Cache-Buster-Workflow. Bei UI-Änderungen.

Bei aktiver Initiative zusätzlich deren `docs/initiatives/<name>/README.md` und das relevante `PHASE_NN_*.md`.

**Aktuelle Initiative (Stand):** `docs/initiatives/workspace-railway/` (Google Workspace + Shared Drive; Domain/DNS Infomaniak).  
Der Ordner `docs/initiatives/modules-and-hosting/` ist nur noch **historische Referenz**.

## Cursor-Rules

- `.cursor/rules/ui.mdc` – Pflicht-UI-Regeln (BEM, Tokens, Cache-Buster). Greift bei `templates/`, `static/css/`, `static/js/`.
- `.cursor/rules/initiatives.mdc` – generisches Pattern für zeitlich begrenzte Vorhaben. Greift in `docs/initiatives/`.

## Branches

- `master` – produktiv
- `docs/*` – Doku-Restrukturierung
- `phase/NN-<initiative>-<name>` – einzelne Phasen einer Initiative
- `redesign` – historischer Branch (Initiative abgeschlossen)

## GitHub- und Railway-CLI

Dieses Repo wird aktiv mit **GitHub CLI (`gh`)** und **Railway CLI (`railway`)** betrieben. Agenten sollen diese Tools gezielt nutzen statt Workarounds.

### GitHub CLI (`gh`)

- PR-Workflow bevorzugen: Feature-Branch → `gh pr create` → `gh pr merge`
- Merge auf `master` triggert Deploy auf Railway
- Nach Merge prüfen, ob der erwartete Commit wirklich in Production angekommen ist
- Keine geheimen Werte (Tokens, Passwoerter, Keys) in PR-Text, Commit-Message oder Issue-Kommentaren posten

### Railway CLI (`railway`)

- Fuer produktive Checks und DB-Arbeiten immer explizit Projekt/Environment/Service angeben (nicht auf lokales Linking verlassen)
  - `--project <id>`
  - `--environment <id>`
  - `--service <id|name>`
- Typische Befehle:
  - Deploy-Status: `railway status --json`
  - Variablen lesen/setzen: `railway variables ...`
  - Remote-Kommandos im Web-Service: `railway ssh ... "/opt/venv/bin/flask db upgrade"`
  - Logs: `railway logs ...`
- Nach produktiven Migrationen immer verifizieren (`flask db current`)
- Bei Mail-/Netzwerkproblemen in Railway immer Egress/Timeout als Ursache mitpruefen (nicht nur App-Code)

### Safety

- Niemals Secrets aus Railway (`railway variables --json`) in Doku, Commits oder Chat-Ausgaben uebernehmen
- Keine destruktiven DB-Operationen in Production ohne klare User-Freigabe

## Doc-Pflege ist Teil jeder Änderung

**Vor JEDER Änderung**: relevante Anchor-Docs lesen + ggf. aktive Initiative-Doc.

**Nach JEDER Änderung**:

- Neues Pattern oder Konvention eingeführt → `docs/CONVENTIONS.md` updaten
- Neuer Modul-Typ oder Service → `docs/ARCHITECTURE.md` updaten
- Neuer Vereins-Begriff → `docs/DOMAIN.md` updaten
- Neue UI-Klasse → `docs/UI.md` Component Registry updaten + Begründung im Commit
- Neue ENV-Variable → `env.example` pflegen
- Innerhalb einer Initiative → Status-Tabelle in deren README updaten

**Bei Initiative-Abschluss**:

- Bleibende Konventionen in CONVENTIONS.md/ARCHITECTURE.md/UI.md übernehmen
- Initiative-Ordner nach `docs/initiatives/_archive/<datum>_<slug>/` verschieben
- Initiative-spezifische Cursor-Rules entfernen
- `docs/initiatives/README.md` Status-Tabelle aktualisieren

Eine Code-Änderung ohne entsprechende Doc-Updates ist ein **unvollständiger Auftrag**.

## Kritische Tabu-Zonen

- **`CRYPTO_KEY` ENV-Variable**: NIEMALS rotieren in Production. Würde alle verschlüsselten `MemberSensitive`- und `MemberMFA`-Daten korrupten. Wenn Rotation wirklich nötig ist: User fragen, geplanten Migration-Pfad bauen.
- **`vapid_private.pem`** und VAPID-Keys: niemals ins Repo committen, nur via ENV oder Secret-Mount.
- **`.env`-Dateien**: niemals committen. Lokale Werte bleiben lokal.
- **Production-DB**: kein direkter Schreib-Zugriff via Skript ohne Backup-vorher und User-Bestätigung.
- **Alembic-Migrationen**: immer als separater Commit, nie zusammen mit Feature-Code. Niemals `--force` oder `--squash` ohne User-Auftrag.

## Bei Unsicherheit

Stoppen und User fragen. Lieber eine Frage zu viel als eine falsche Annahme. Speziell bei:

- Unklaren Acceptance-Criteria innerhalb einer Phase
- Konflikten zwischen Anchor-Docs und Code-Realität (Doc updaten vorschlagen)
- Sicherheits-relevanten Änderungen (Auth, Encryption, Permissions)
- DB-Schema-Änderungen mit Daten-Migrations-Bedarf
- Neuen externen Services oder Dependencies

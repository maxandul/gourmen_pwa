# Agent-Handoff – workspace-railway (Status quo)

**Stand**: 2026-05-01 (Kern unten); **Phase 3 Ergaenzung**: 2026-05-13 — siehe Abschnitt *Phase 3 – Drive (kurz)*.  
**Massgebend mit**: `README.md` in diesem Ordner (Status-Tabelle), `AGENTS.md`, Anchor-Docs bei Code-Aenderungen.

## Einstieg (Doc-Reihenfolge)

Fuer Arbeit in dieser Initiative in dieser Reihenfolge lesen:

1. [`AGENTS.md`](../../../AGENTS.md) (Repo-Root) — Eingangstor, Tabu-Zonen, Tooling
2. [`README.md`](./README.md) — Master-Plan und **Status-Tabelle** (Phasen-Tracker)
3. **Diese Datei** (`AGENT_HANDOFF.md`) — kontextlastiger Status-Quo (Phasen-Details, Befunde)
4. Bei Themen Vereinsdokumente / Shared Drive: [`docs/capabilities/drive.md`](../../capabilities/drive.md)

**Phasen-Tracker vs. Initiativen-Uebersicht**: Die Status-Tabelle im **workspace-railway-`README.md`** ist massgeblich. [`docs/initiatives/README.md`](../README.md) muss dafuer **nicht** zwingend mitgepflegt werden — eine Aktualisierung nur der zentralen Initiative-README reicht fuer den Phasen-Tracker.

## Phase 3 – Drive (kurz, Stand 2026-05-13)

- **Spec**: `docs/capabilities/drive.md` (autoritativ), Setup: `docs/capabilities/drive_setup.md`.
- **Code**: `master` inkl. Squash PR #12 (`6cab330`) + **Hotfix-Migration** `4377231` (PostgreSQL: vor `DROP TYPE documentcategory` zuerst Spalte `documents.category` droppen; sonst `DependentObjectsStillExist`).
- **Prod**: Alembic-Head `e3c5f9a6b423`; Railway-Vars `GOOGLE_SERVICE_ACCOUNT_KEY`, `GOOGLE_DRIVE_ID` auf `web` und `cron-reminders`; GCP-Projekt **ID** tatsaechlich `gourmen-pwa-prod` (nicht `gourmen-pwa`).
- **Feature-Flag**: `DRIVE_FEATURE_ENABLED=false` bis Cutover — UI `/docs` unsichtbar, Profil-Google-Mail-Flow kann trotzdem genutzt werden.
- **Naechster Agent**: Bei Migrations-Doku: Datei `migrations/versions/d2b4e8f5a312_document_drive_redesign.py` enthält die korrigierte Reihenfolge; lokale Alembic-Historie darf von einem fehlgeschlagenen ersten Upgrade-Versuch auf Prod keine Spur haben (Transaktions-Rollback).

> Die uebrigen Abschnitte dieses Handoff-Docs (Phase 1/2, Git-Stand 2026-05-01) sind **nicht** automatisch mit `README.md` synchron — fuer Phasen-Status zuerst **`README.md` Status-Tracker** lesen.

## Kurz: Wo weiter?

| Bereich | Status | Naechster Schritt fuer neuen Agenten |
|---|---|---|
| **Phase 1** | Technisch weitgehend umgesetzt | Shared-Drive fuer alle Mitglieder ausrollen; Phase-1-Checkliste/Abschlussnotiz finalisieren; ggf. `PHASE_01` auf `done` setzen |
| **Phase 2** | **Blockiert auf Produktentscheid** | Siehe unten: Railway **Pro + SMTP** (Verein will kein Resend) **oder** doch HTTPS-Mail-API auf Hobby |
| **Git** | Siehe Abschnitt Git | Branch mit Resend-Code existiert, ist **nicht** auf `master` gemerged |

## Phase 1 – erledigt / offen (Operations)

Erledigt (laut Vorstand/Umsetzung, 2026-05-01):

- Google Workspace fuer `gourmen.ch`, Nutzer `kontakt@gourmen.ch`
- DNS Infomaniak: MX auf Google, SPF (Uebergang mit Infomaniak-Include), DKIM aktiv, DMARC `p=none`
- Mailfluss Gmail: Send/Receive getestet; DKIM Google-seitig ok
- Alias `admin@gourmen.ch` -> Postfach getestet
- Shared Drive angelegt; Pilot: 1 Mitglied als Content Manager
- Infomaniak-Postfach: vorerst parallel/billig, kein Muss zum sofortigen Loeschen

Offen fuer formellen Phase-1-Abschluss:

- Restliche Mitglieder im Shared Drive (Rollen gemaess Vereinsziel „alle sehen alles“)
- Abschlussnotiz: exakte Uhrzeit MX-Cutover + verantwortliche Person (in `PHASE_01` nachtragen)
- Checkliste in `PHASE_01_WORKSPACE_AND_DNS.md` mit Realitaet abgleichen (Haekchen, Acceptance)

## Phase 2 – System-Mail aus der App (technischer Befund)

### Problem

- Production: `/admin/mail/test` mit Ziel **Gmail SMTP** (`smtp.gmail.com`, 587/465) fuehrte zu **Timeouts** (~40s Request, passend zu doppeltem Socket-Timeout).
- Verifiziert per `railway ssh` im Service **`web`**: TCP-Connect zu `smtp.gmail.com` und `smtp-relay.gmail.com` auf **465 und 587** endet mit **Timeout**.
- Railway-Plan laut Status: **Hobby**. Laut [Railway Outbound Networking](https://docs.railway.com/reference/outbound-networking) ist **ausgehender SMTP auf Free/Trial/Hobby deaktiviert**; ab **Pro** verfuegbar (nach Upgrade Redeploy).

### Folge

- **Infomaniak-SMTP und Google-SMTP sind gleich betroffen** (gleiche Ports/Policy). Fruehere „ging mal“-Erfahrung kann Dev-Umgebung, fruehere Railway-Inkonsistenz oder teilweise Prod-Probleme sein (siehe historisch `_archive/2026-04_modules-and-hosting/PHASE_08_MAIL_PROD_FOLLOWUP.md`).

### Produktentscheid (Stakeholder)

- **Resend wird nicht gewuenscht** als Standardweg.
- Offene Wahl:
  1. **Railway auf Pro** → SMTP (z. B. Google Workspace App-Passwort fuer `kontakt@` oder wieder Infomaniak-SMTP) wie in `MailService` ohne `RESEND_API_KEY`.
  2. **Hobby beibehalten** → dann braucht es **irgendeinen HTTPS-Mail-API**-Anbieter (Resend war nur eine Option).

### Code-Stand Resend (optional, nicht auf master)

- Branch **`origin/phase/02-workspace-system-mail`**, Commit u. a. `6e859e7`: Wenn `RESEND_API_KEY` gesetzt, nutzt `MailService` Resend (HTTPS); sonst SMTP.
- **`master`** enthaelt diesen Stand **nicht** (Stand `master`: letzter relevanter Commit Phase-1-Doku `1183900`).
- Naechster Agent: Entscheidung dokumentieren; bei „kein Resend“ Branch verwerfen, umbauen oder nur als Fallback lassen **nach** Abstimmung.

## Git-Referenz

- `master`: Phase-1-Doku-Update (`1183900`), kein Resend-Code.
- `phase/02-workspace-system-mail`: Resend-Integration + aktualisierte Phase-2-Doku auf dem Branch (nicht gemerged).

## Lokales Repo / Randnotizen

- `templates/base.html` kann bei manchen Windows-Checkouts als geaendert erscheinen **ohne inhaltlichen Diff** (Zeilenenden) – vor Commits pruefen (`git diff`).

## Sofort-Pflicht fuer neuen Agenten

1. Doc-Reihenfolge wie in **Einstieg (Doc-Reihenfolge)** oben  
2. `PHASE_01_WORKSPACE_AND_DNS.md` und `PHASE_02_APP_SYSTEM_MAIL.md` lesen  
3. Mit Vorstand klaeren: **Railway Pro + SMTP** vs **Hobby + API-Mail**  
4. Danach Phase-2-Tasks in README/Phase-2-Dokument konkretisieren und umsetzen  

Keine Secrets in Chat, Commits oder PR-Texten.

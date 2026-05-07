# Initiative: Modules & Hosting

> **Superseded (Inhalt)**: Massgeblicher Plan fuer neue Arbeit ist  
> **`docs/initiatives/workspace-railway/`** (Google Workspace + Shared Drive, Domain/DNS Infomaniak, App auf Railway).  
> Dieser Ordner bleibt als **historische Detail-Referenz** (alte Phasennummern, R2/Object-Storage-Entwuerfe).

**Status**: abgeloest (Referenz)  
**Start**: 2026-04  
**Branch-Prefix**: `phase/NN-modules-<name>` (historisch)

## Ziel

Erweiterung der Gourmen-PWA um neue Module (Mail, Files, Login-Verbesserungen, Buchhaltung, Kalender, TWINT, WhatsApp), **ohne** Plattform-Wechsel weg von Railway. Externe Spezial-Services für die Aufgaben, die kein vernünftiger Verein selbst hostet.

## Strategische Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **App-Hosting bleibt Railway** | Null Operations-Aufwand, automatische Backups, Postgres + Redis eingebaut |
| **Domain/DNS bei Infomaniak** | Bleibt; Details zu Mail siehe Initiative `workspace-railway` |
| **Files** | **Pivot:** Google Shared Drive statt Infomaniak Object Storage – siehe `workspace-railway/PHASE_03_*` |
| **Mail** | **Pivot:** Google Workspace statt Infomaniak Mail Service – siehe `workspace-railway/PHASE_01_*` / `PHASE_02_*` |
| **TWINT via RaiseNow** | Schweizer Vereins-Acquirer, kein HR-Eintrag nötig, Buchhaltungs-Integration |
| **WhatsApp via Meta Cloud API** | Einzige offizielle Option, kein Selbst-Host möglich |
| **Login bleibt Eigenbau** | Flask-Login + 2FA bereits robust, nur Reset-Flows reparieren |
| **Buchhaltung Eigenbau** | Vereinsspezifisch, klein gehalten |
| **Kalender als iCal-Export** | Kein eigener CalDAV, User abonnieren in nativen Apps |

## Architektur-Bild

```
┌─────────────────────────────────────────────────┐
│  Railway                                         │
│  Web + Cron + Postgres + Redis                  │
└────────┬────────────────────┬───────────────────┘
         │ Webhooks            │ API-Calls
         ▼                     ▼
┌─────────────────────────────────────────────────┐
│  Infomaniak                                     │
│  - DNS, Domain, Mail Service                    │
│  - Object Storage (S3-kompatibel)               │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  Externe SaaS                                   │
│  - optionale Mail-API (später falls nötig)      │
│  - RaiseNow (TWINT)                             │
│  - Meta Cloud API (WhatsApp)                    │
└─────────────────────────────────────────────────┘
```

## Phasen

| # | Phase | Aufwand | Voraussetzung |
|---|---|---|---|
| 0 | Infra-Setup (Konten anlegen) | ~2h einmalig | – |
| 1 | Mail-Infrastruktur | ~0.5 Tag | Phase 0 |
| 2 | Login-Verbesserungen | ~2 Tage | Phase 1 |
| 3 | File-Storage (R2) | ~3-4 Tage | Phase 0 |
| 4 | Buchhaltung-Modul | ~1-2 Wochen | Phase 3 |
| 5 | Kalender (iCal) | ~1 Tag | – |
| 6 | TWINT/Payments | ~5 Tage | Phase 1, 4 |
| 7 | WhatsApp | ~1 Woche Code + Meta-Wartezeit | Phase 1 |
| 8 | Mail-Zustellbarkeit Prod (Follow-up) | ~0.5-1 Tag Diagnose + ggf. 0.5 Tag Fix | Phase 1, 2 |

**Empfohlene Reihenfolge**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8  
Phase 1 ist Schlüssel-Investition: schaltet Phasen 2, 4, 6, 7 mit Mail-Funktionalität frei.  
Phase 3 (Files) ist Voraussetzung für Phase 4 (Belege in Buchhaltung).

## Workflow pro Phase

1. **Master-Plan + Phasen-Doc lesen**: diese README + die spezifische `PHASE_NN_*.md`
2. **Branch erstellen**: `phase/NN-modules-<name>` von `master`
3. **Cursor-Agent starten** mit dem Cursor-Briefing am Ende der Phasen-Doc
4. **Pre-Conditions verifizieren** vor Code-Start
5. **Tasks abarbeiten** gemäss Acceptance-Criteria
6. **Lokal testen**: `flask run` + manueller Smoke-Test
7. **Doc-Updates** (siehe `AGENTS.md`)
8. **Acceptance-Criteria abhaken**, Status-Tabelle unten aktualisieren
9. **Commit & Merge** auf `master`

## Status-Tracker

| Phase | Status | Branch | Datum | Notizen |
|---|---|---|---|---|
| 0 | done | n/a (manuell) | 2026-04-27 | DNS/TLS (`www` + `app`), Mailbox und Object Storage auf Infomaniak eingerichtet |
| 1 | done | phase/01-modules-mail | 2026-04-27 | SMTP-Mailservice (Infomaniak), Templates und erfolgreicher Admin-Smoke-Test |
| 2 | done | phase/02-modules-login | 2026-04-27 | Token-basierte Reset-/Onboarding-Flows implementiert; Prod-Mailzustellung als Follow-up in Phase 8 ausgelagert |
| 3 | in_progress | phase/03-modules-files | 2026-04-27 | Fortsetzung laut Priorisierung; Mail-Prod-Problem wird separat nachgezogen |
| 4 | pending | – | – | – |
| 5 | pending | – | – | – |
| 6 | pending | – | – | – |
| 7 | pending | – | – | – |
| 8 | pending | – | – | SMTP-Timeouts/fehlende Zustellung in Production dokumentiert; Diagnose/Fix nachgelagert |

Status-Werte: `pending` / `in_progress` / `done` / `blocked`

## Nicht-Ziele dieser Initiative

- **Keine Plattform-Migration weg von Railway**: bewusste Entscheidung, Operations-Aufwand niedrig zu halten
- **Kein eigener Auth-Service** (Auth0, Clerk, etc.): bestehender Login wird repariert, nicht ersetzt
- **Keine native Mobile-App**: PWA bleibt das Ziel
- **Kein eigenes WhatsApp-Hosting**: Meta-Cloud-API ist gesetzt
- **Kein eigener Mailserver**: Mail bleibt bei einem externen Provider

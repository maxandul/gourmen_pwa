# Initiative: Modules & Hosting

**Status**: aktiv  
**Start**: 2026-04  
**Branch-Prefix**: `phase/NN-modules-<name>`

## Ziel

Erweiterung der Gourmen-PWA um neue Module (Mail, Files, Login-Verbesserungen, Buchhaltung, Kalender, TWINT, WhatsApp), **ohne** Plattform-Wechsel weg von Railway. Externe Spezial-Services für die Aufgaben, die kein vernünftiger Verein selbst hostet.

## Strategische Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **App-Hosting bleibt Railway** | Null Operations-Aufwand, automatische Backups, Postgres + Redis eingebaut |
| **Domain/DNS bei Infomaniak** | Bereits umgesetzt in Phase 0, zentrale Verwaltung für Verein und Mail-DNS |
| **Files in Infomaniak Object Storage** | S3-kompatibel, passt zur gewählten Public-Cloud-Basis |
| **Mail über Infomaniak Mail Service** | Eine zentrale Vereinsadresse (`kontakt@`/`info@`) für System- und Vereinskommunikation |
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

**Empfohlene Reihenfolge**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7  
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
| 2 | in_progress | phase/02-modules-login | 2026-04-27 | Token-basierte Reset-/Onboarding-Flows implementiert; reale Mail-E2E-Validierung noch offen |
| 3 | pending | – | – | – |
| 4 | pending | – | – | – |
| 5 | pending | – | – | – |
| 6 | pending | – | – | – |
| 7 | pending | – | – | – |

Status-Werte: `pending` / `in_progress` / `done` / `blocked`

## Nicht-Ziele dieser Initiative

- **Keine Plattform-Migration weg von Railway**: bewusste Entscheidung, Operations-Aufwand niedrig zu halten
- **Kein eigener Auth-Service** (Auth0, Clerk, etc.): bestehender Login wird repariert, nicht ersetzt
- **Keine native Mobile-App**: PWA bleibt das Ziel
- **Kein eigenes WhatsApp-Hosting**: Meta-Cloud-API ist gesetzt
- **Kein eigener Mailserver**: Mail bleibt bei einem externen Provider

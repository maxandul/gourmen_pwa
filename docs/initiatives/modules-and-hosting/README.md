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
| **Domain bei Cloudflare** | Günstig (~10 USD/Jahr), beste DNS-UI, gleiches Konto wie R2 |
| **Files in Cloudflare R2** | S3-kompatibel, kein Egress, sehr günstig (10 GB free) |
| **Mail über Resend** | 3000 Mails/Monat gratis, einfache API |
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
│  Cloudflare                                     │
│  - DNS, Domain, Email Routing                   │
│  - R2 (S3-kompatibler File-Storage)             │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  Externe SaaS                                   │
│  - Resend (E-Mail)                              │
│  - RaiseNow (TWINT)                             │
│  - Meta Cloud API (WhatsApp)                    │
└─────────────────────────────────────────────────┘
```

## Phasen

| # | Phase | Aufwand | Voraussetzung |
|---|---|---|---|
| 0 | Infra-Setup (Konten anlegen) | ~2h einmalig | – |
| 1 | Mail-Infrastruktur (Resend) | ~0.5 Tag | Phase 0 |
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
| 0 | pending | – | – | – |
| 1 | pending | – | – | – |
| 2 | pending | – | – | – |
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
- **Kein eigener Mailserver**: Resend bleibt Provider

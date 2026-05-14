# Initiative: Workspace + Railway (Gourmen PWA)

**Status**: aktiv  
**Start**: 2026-05  
**Branch-Prefix**: `phase/NN-workspace-<kurzname>`

**Agent-Wechsel / Einstieg**: [`AGENTS.md`](../../../AGENTS.md) → diese README (**Status-Tabelle**) → [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md) (Abschnitt *Einstieg (Doc-Reihenfolge)* + Status-Quo) → bei Drive-Themen [`docs/capabilities/drive.md`](../../capabilities/drive.md).

## Zweck dieser Initiative

Neuer Master-Plan fuer Agenten nach strategischem Pivot: **Domain/DNS bleibt bei Infomaniak**, zentrale Vereinsarbeit (Mail, Shared Drive, Docs) laeuft **langfristig ueber Google Workspace**. Die **Gourmen-PWA bleibt auf Railway** (Web, Cron, Postgres, Redis).

Die fruehere Initiative liegt im Archiv unter `docs/initiatives/_archive/2026-04_modules-and-hosting/`; sie enthaelt Detail-Docs und historische Phase-Dateien als Referenz. **Massgebend fuer neue Arbeit ist dieser Ordner** plus der strategische Rahmen `docs/STRATEGY_2026.md`.

## Was bereits als Baseline gilt (nicht neu bauen)

Siehe `PHASE_00_BASELINE.md`: implementierter Code (MailService, Token-Reset-Flows, Audit-Fixes, SMTP-IPv4/Timeout-Optionen usw.) gilt als **vorhanden**. Neue Phasen **migrieren, anbinden und verifizieren** – nicht von vorn programmieren, ausser wenn explizit gefordert.

## Strategische Entscheidungen (aktuell)

> **Strategischer Rahmen**: `docs/STRATEGY_2026.md` — dort steht die vollstaendige Source-of-Truth-Karte und das Decision Log.

| Entscheidung | Begruendung |
|---|---|
| **App-Hosting: Railway Hobby** | unveraendert; Pro-Upgrade nicht noetig dank Resend |
| **Domain/DNS: Infomaniak** | Registrar und DNS-Verwaltung |
| **Vereins-Mail: Google Workspace Starter** | eine bezahlte Mailbox `kontakt@gourmen.ch`; weitere Adressen als **Alias** auf derselben Lizenz |
| **Dateien: bestehender Google Shared Drive** | alle sehen alles; App: Upload, Liste, Download, Loeschen; Bearbeitung in Google (Docs/Sheets); auch Belege fuer Buchhaltung gehen ins Drive |
| **System-Mails aus der App: Resend (free)** | Entscheid 2026-05-07 — Railway Hobby blockt outbound SMTP, Pro nicht gewuenscht. Resend HTTPS-API, DKIM via Resend |
| **Object Storage: keiner** | Merch-Bilder im Repo, Public-Bilder via Insta-Embeds, Belege via Drive — kein eigener Bucket noetig |
| **Mitglieder-Mail (Personenpost)** | nicht in der PWA; gewohnte Mail-Apps; ggf. externe Collaborators am Shared Drive |
| **Kalender** | weiterhin iCal-Feed aus der App zum Abonnieren; keine Pflicht-Kalender-UI in der PWA |
| **Auth (heute)** | Flask-Login + 2FA + Fernet bleibt; Supabase-Migration als Future Consideration in `STRATEGY_2026.md` |
| **TWINT / WhatsApp** | spaetere Phasen; Anbieter-Entscheide und Integrationsweg in `STRATEGY_2026.md` |

## Architektur-Bild

```
┌──────────────────────────────────────────────────┐
│  Railway Hobby                                   │
│  Web + Cron + Postgres + Redis                   │
└──────┬─────────────┬────────────┬────────────────┘
       │ HTTPS       │ Google API │ DNS-Lookups
       │ (Resend)    │ (Drive)    │
       ▼             ▼            ▼
┌────────────┐ ┌──────────────┐ ┌─────────────────┐
│  Resend    │ │ Google       │ │  Infomaniak     │
│  System-   │ │ Workspace    │ │  Domain/DNS     │
│  Mails     │ │ Mail + Drive │ │  (MX/SPF/DKIM)  │
└────────────┘ └──────────────┘ └─────────────────┘
```

DKIM-Signaturen kommen aus Workspace (Personenpost) und Resend (System-Mails) parallel; SPF in DNS deckt beide ab.

## Phasen (neu nummeriert)

| # | Phase | Aufwand | Voraussetzung |
|---|---|---|---|
| 0 | Baseline & Kontext | Lesen, kein Code | – |
| 1 | Workspace + DNS/MX Cutover | 0.5–2 Tage (viel manuell) | Phase 0 |
| 2 | App: System-Mail auf Workspace | ~0.5–1 Tag | Phase 1 stabil |
| 3 | App: Dateien auf Google Shared Drive | ~3–5 Tage | Phase 1, Service Account / Domain-wide Delegation geklaert |
| 4 | Buchhaltungs-Modul | ~1–2 Wochen | Phase 3 (Belege = Drive) |
| 5 | Kalender (iCal) | ~1 Tag | – |
| 6 | TWINT/Payments | ~5 Tage | Phase 4, Phase 2 |
| 7 | WhatsApp | ~1 Woche + Meta-Wartezeit | Phase 2 |
| 8 | Infomaniak-Mail/Object-Storage abbauen (`PHASE_08_INFOMANIAK_DECOMMISSION.md`) | ~0.5 Tag | Phase 1–3 done |

**Empfohlene Reihenfolge**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8  

Detail: jeweils `PHASE_NN_*.md` in diesem Ordner.

## Workflow pro Phase

1. `AGENTS.md` + diese README + die aktuelle `PHASE_NN_*.md` lesen  
2. Branch: `phase/NN-workspace-<kurzname>` von `master`  
3. Pre-Conditions pruefen  
4. Umsetzung + Anchor-Docs bei Bedarf (`ARCHITECTURE.md`, `env.example`)  
5. Status-Tabelle unten aktualisieren  

## Status-Tracker

| Phase | Status | Branch | Datum | Notizen |
|---|---|---|---|---|
| 0 | done | master | 2026-05-01 | Baseline gelesen und gegen aktuelle Strategie abgeglichen |
| 1 | in_progress | master | 2026-05-01 | Workspace/DNS/DKIM/MX stabil; Shared-Drive-Rollout + formeller Abschluss offen — siehe `AGENT_HANDOFF.md` |
| 2 | done | master | 2026-05-07 | Resend in Prod (PR #11); `/admin/mail/test` verifiziert. Optional nachziehen: Forgot-Password/Onboarding/2FA E2E, mail-tester.com, Resend/Privacy-Text auf oeffentlicher Seite — siehe `PHASE_02_APP_SYSTEM_MAIL.md` |
| 3 | done (Implementation + Prod) | master | 2026-05-13 | Code merged (PR #12), Hotfix Migration `d2b4e8f5a312` auf `4377231`; DB Head `e3c5f9a6b423`; Drive-Folders via `scripts/setup_drive.py`; `DRIVE_FEATURE_ENABLED=false` bis MVP-Cutover — siehe `PHASE_03_GOOGLE_SHARED_DRIVE_FILES.md` + `docs/capabilities/drive.md` |
| 4 | pending | – | – | Inhaltlich analog `_archive/2026-04_modules-and-hosting/PHASE_04_ACCOUNTING.md`, Backend = Drive; n8n-Pfad als offene Architektur-Frage (siehe STRATEGY_2026.md) |
| 5 | done | `phase/05-workspace-ical-feed` | 2026-05-14 | iCal pro Mitglied: `CalendarFeedService`, `/calendar/<token>.ics`, Settings in `member.technical`, Admin-Status ohne Token; Branch-Tip `5ea5700`; Spec `docs/capabilities/calendar.md` |
| 6 | pending | – | – | siehe `_archive/2026-04_modules-and-hosting/PHASE_06_PAYMENTS.md` |
| 7 | pending | – | – | siehe `_archive/2026-04_modules-and-hosting/PHASE_07_WHATSAPP.md` |
| 8 | pending | – | – | `PHASE_08_INFOMANIAK_DECOMMISSION.md`; nur abbauen wenn nichts mehr referenziert |

Status-Werte: `pending` / `in_progress` / `done` / `blocked`

## Nicht-Ziele

- Kein Wechsel weg von Railway fuer die App  
- Kein Ersatz von Flask-Login durch Google als einziger Auth (optional spaeter ergaenzbar)  
- Kein „alles muss im iframe in der PWA bearbeitet werden“ – oeffnen in Google ist akzeptiert  

## Verweis alte Initiative

`docs/initiatives/_archive/2026-04_modules-and-hosting/` – **historisch / Detail-Referenz**. Bei Widerspruch gewinnt **workspace-railway** + `docs/STRATEGY_2026.md`.

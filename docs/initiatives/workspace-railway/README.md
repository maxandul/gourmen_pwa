# Initiative: Workspace + Railway (Gourmen PWA)

**Status**: aktiv  
**Start**: 2026-05  
**Branch-Prefix**: `phase/NN-workspace-<kurzname>`

**Agent-Wechsel / Einstieg**: zuerst [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md) lesen (Status quo 2026-05-01, Phase 1/2, Git, Railway-SMTP-Befund).

## Zweck dieser Initiative

Neuer Master-Plan fuer Agenten nach strategischem Pivot: **Domain/DNS bleibt bei Infomaniak**, zentrale Vereinsarbeit (Mail, Shared Drive, Docs) laeuft **langfristig ueber Google Workspace**. Die **Gourmen-PWA bleibt auf Railway** (Web, Cron, Postgres, Redis).

Die fruehere Initiative `modules-and-hosting` ist damit **inhaltlich abgeloest**; dort verbleiben Detail-Docs und historische Phase-Dateien als Referenz. **Massgebend fuer neue Arbeit ist dieser Ordner.**

## Was bereits als Baseline gilt (nicht neu bauen)

Siehe `PHASE_00_BASELINE.md`: implementierter Code (MailService, Token-Reset-Flows, Audit-Fixes, SMTP-IPv4/Timeout-Optionen usw.) gilt als **vorhanden**. Neue Phasen **migrieren, anbinden und verifizieren** – nicht von vorn programmieren, ausser wenn explizit gefordert.

## Strategische Entscheidungen (aktuell)

| Entscheidung | Begruendung |
|---|---|
| **App-Hosting: Railway** | unveraendert |
| **Domain/DNS: Infomaniak** | Registrar und DNS-Verwaltung |
| **Vereins-Mail: Google Workspace** | eine bezahlte Mailbox (Business Starter oder Nonprofit falls qualifiziert); weitere Adressen als **Alias** auf dieselbe Lizenz |
| **Owner: Vereinskonto** | z. B. primaerer User `kontakt@gourmen.ch`, optional Alias `admin@gourmen.ch` |
| **Dateien: bestehender Google Shared Drive** | alle sehen alles; App: Upload, Liste, Download, Loeschen; Bearbeitung in Google (Docs/Sheets) |
| **Mitglieder-Mail** | nicht in der PWA; gewohnte Mail-Apps; ggf. externe Collaborators am Shared Drive |
| **Kalender** | weiterhin iCal-Feed aus der App zum Abonnieren; keine Pflicht-Kalender-UI in der PWA |
| **System-Mails aus der App** | eigener technischer Versandweg nach Workspace-Cutover (SMTP-Relay/SMTP mit Workspace), Konfiguration in Railway |
| **TWINT / WhatsApp** | unveraendert RaiseNow bzw. Meta Cloud API (spaetere Phasen) |

## Architektur-Bild

```
┌─────────────────────────────────────────────────┐
│  Railway                                         │
│  Web + Cron + Postgres + Redis                  │
│  System-Mails, API-Integrationen                │
└────────┬────────────────────┬───────────────────┘
         │ SMTP (System)       │ Google APIs (Drive)
         ▼                     ▼
┌──────────────────┐   ┌──────────────────────────┐
│  Google Workspace │   │  Infomaniak               │
│  Mail + Drive     │   │  Domain/DNS (MX, TXT, …)  │
└──────────────────┘   └──────────────────────────┘
```

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
| 1 | in_progress | master | 2026-05-01 | Workspace/DNS/DKIM ok, Mailtests ok; Shared-Drive-Rollout + formeller Abschluss offen — siehe `AGENT_HANDOFF.md` |
| 2 | blocked | – | 2026-05-01 | Railway Hobby: SMTP TCP-Timeout (verifiziert). Stakeholder: kein Resend. Entscheid: Pro+SMTP vs Hobby+HTTPS-API — `AGENT_HANDOFF.md`; optional Resend nur auf Branch `phase/02-workspace-system-mail` (nicht master) |
| 3 | pending | – | – | – |
| 4 | pending | – | – | Inhaltlich analog `modules-and-hosting/PHASE_04_ACCOUNTING.md`, Backend = Drive |
| 5 | pending | – | – | siehe `modules-and-hosting/PHASE_05_CALENDAR.md` |
| 6 | pending | – | – | siehe `modules-and-hosting/PHASE_06_PAYMENTS.md` |
| 7 | pending | – | – | siehe `modules-and-hosting/PHASE_07_WHATSAPP.md` |
| 8 | pending | – | – | `PHASE_08_INFOMANIAK_DECOMMISSION.md`; nur abbauen wenn nichts mehr referenziert |

Status-Werte: `pending` / `in_progress` / `done` / `blocked`

## Nicht-Ziele

- Kein Wechsel weg von Railway fuer die App  
- Kein Ersatz von Flask-Login durch Google als einziger Auth (optional spaeter ergaenzbar)  
- Kein „alles muss im iframe in der PWA bearbeitet werden“ – oeffnen in Google ist akzeptiert  

## Verweis alte Initiative

`docs/initiatives/modules-and-hosting/` – **historisch / Detail-Referenz**. Bei Widerspruch gewinnt **workspace-railway**.

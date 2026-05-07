# Phase 7 – WhatsApp Business (Meta Cloud API)

**Status**: pending  
**Aufwand**: ~1 Woche Code + 2-4 Wochen Meta-Verifizierungs-Wartezeit  
**Branch**: `phase/07-modules-whatsapp`

## Ziel

Optionale WhatsApp-Integration für Vereins-Kommunikation: Event-Reminder als Alternative zu Push-Notifications, ggf. Inbound-Bot für einfache Anfragen ("kommt heute zum Monatsessen?").

## Pre-Conditions

- Phase 1 (Mail) abgeschlossen – als Fallback wenn WhatsApp nicht zustellbar
- Meta Business Manager Account mit Verifizierung **abgeschlossen** (separate Aktion vor Code-Start, dauert 2-4 Wochen)
- Telefonnummer für Vereins-WhatsApp-Business reserviert (nicht parallel privat nutzbar!)
- Mindestens ein Outbound-Template bei Meta approved (z.B. „Event-Reminder")
- Branch `phase/07-modules-whatsapp` von `master` erstellt

## Tasks

### 1. Meta-Setup (manuell, vor Code)

- [ ] Meta Business Manager: Vereinsverifizierung
- [ ] Telefonnummer für WhatsApp Business registrieren
- [ ] WhatsApp Cloud API Access Token holen
- [ ] Display-Name für Verein eintragen lassen (auch Approval)
- [ ] Outbound-Templates definieren und approven lassen:
  - „Event-Reminder" (3 Wochen vor Event)
  - „Event-Reminder kurzfristig" (Montag vor Event)
  - „Rating-Bitte" (Tag nach Event)
  - Pro Template: variable Slots `{{1}}`, `{{2}}` für Event-Name, Datum etc.
- [ ] In Railway-ENV eintragen:
  ```
  WHATSAPP_TOKEN=...
  WHATSAPP_PHONE_NUMBER_ID=...
  WHATSAPP_BUSINESS_ACCOUNT_ID=...
  WHATSAPP_VERIFY_TOKEN=...
  ```

### 2. Models

- [ ] `WhatsAppSubscription` Model:
  - `id`, `member_id` (FK), `phone_number_e164` (z.B. `+41791234567`), `is_active`, `verified_at`, `created_at`
- [ ] `WhatsAppMessage` Model (Audit/History):
  - `id`, `member_id` (FK), `direction` (IN/OUT), `template_name` (für OUT), `body`, `status` (Enum), `provider_message_id`, `created_at`, `delivered_at`, `read_at`
- [ ] Alembic-Migration in **separatem Commit**

### 3. Service-Layer

Datei `backend/services/whatsapp.py`:

- [ ] `WhatsAppService`
  - [ ] `send_template(to: str, template_name: str, params: list[str]) -> dict`
  - [ ] `send_text(to: str, body: str) -> dict` (nur in laufender Konversation, nicht für initial!)
  - [ ] `verify_webhook_subscription(...)` – Meta-Webhook-Verify (GET-Challenge)
  - [ ] `process_inbound(payload) -> dict` – Inbound-Message verarbeiten

### 4. Routes

Neuer Blueprint `backend/routes/whatsapp.py`:

- [ ] `GET /webhooks/whatsapp` (csrf_exempt) – Webhook-Verifizierung (Meta-Challenge mit `WHATSAPP_VERIFY_TOKEN`)
- [ ] `POST /webhooks/whatsapp` (csrf_exempt) – Inbound-Messages
  - [ ] Signatur-Verifikation mit App-Secret
  - [ ] Idempotenz (provider_message_id)
  - [ ] Inbound in DB speichern
  - [ ] Optional: einfache Auto-Antworten (z.B. „kommt" → Participation als bestätigt markieren)

### 5. Member-UI

- [ ] In Member-Settings: „WhatsApp-Reminders aktivieren"
  - Telefonnummer eingeben (validiert via E.164)
  - Verifizierungs-SMS oder WhatsApp-Bestätigungs-Code
  - Status-Toggle (aktiv/inaktiv)

### 6. Cron-Reminders erweitern

In `run_cron_reminders.py`:

- [ ] Bei jedem Reminder-Typ:
  - User mit aktiver `WhatsAppSubscription` → WhatsApp-Template senden
  - User ohne WhatsApp-Sub aber mit Push-Sub → Push (wie heute)
  - Optional: User mit beiden → beide Channels

### 7. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`:
  - „Externe Services" Meta Cloud API auf `aktiv`
  - Neuer Blueprint
- [ ] `docs/DOMAIN.md`: Sektion „WhatsApp" mit Onboarding-Flow

## Acceptance-Criteria

- [ ] Member kann Telefonnummer eintragen und verifizieren
- [ ] Bei aktiver Subscription kommt 3-Wochen-Reminder als WhatsApp an
- [ ] Inbound-Webhook nimmt Antworten entgegen und loggt sie
- [ ] Webhook-Verifikation (GET-Challenge) klappt
- [ ] Webhook-Signatur ohne valide Sign wird abgelehnt
- [ ] Tests grün, DB-Migration sauber

## Out of Scope

- **Komplexer Bot mit NLU**: nur einfache Schlüsselwort-Antworten
- **Group Messaging**: nur Direkt-Messages
- **Media Messages** (Bilder, PDFs): später, wenn nötig
- **Marketing-Templates**: nur Service-Templates (Reminder, Bestätigungen)
- **Multi-Sprachen-Support** in Templates: nur Deutsch initial

## Cursor-Agent-Briefing

```
Branch: phase/07-modules-whatsapp
Doc: docs/initiatives/modules-and-hosting/PHASE_07_WHATSAPP.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen
- docs/CONVENTIONS.md lesen
- Meta Business Manager Setup MUSS abgeschlossen sein
- Templates MÜSSEN approved sein
- API-Keys in Railway-ENV gesetzt
- Phase 1 (Mail) als Fallback verfügbar

Implementiere Phase 7 (WhatsApp Cloud API) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- KRITISCH: Webhook-Signature-Check (HMAC mit App-Secret)
- KRITISCH: Idempotenz für Inbound
- Outbound NUR über approved Templates (Cold Messages werden sonst von Meta blockiert)
- Folge .cursor/rules/initiatives.mdc

Lokal testen:
- Webhook-Verifizierung mit Test-Curl
- Outbound-Template an eigene Nummer
- Inbound-Antwort prüfen

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md, DOMAIN.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Meta-Verifizierung dauert** und muss separat von Code-Arbeit gestartet werden
- **Templates sind reglementiert**: Marketing-Templates gehen schwerer durch als Service-Templates (Reminder etc.)
- **Cold Outbound** (initial Message) nur via Template, nicht freier Text
- **24h-Window**: nach User-Antwort darf 24h frei geantwortet werden, danach wieder Template
- **Phone-Number-Format**: immer E.164 (`+41791234567`), validieren mit `phonenumbers`-Lib
- **Privacy**: WhatsApp-Telefonnummer ist Personendaten, im Audit-Log nicht im Klartext speichern
- **Costs**: ~5-15 Rappen pro Konversation, kann sich bei vielen Reminders summieren

## Frage an User vor Start

Diese Phase hat den höchsten Setup-Overhead und potenzielle Costs. Vor dem Start klären:

- Wirklich Bedarf? Push-Notifications gibt es bereits.
- Wer betreut die Telefonnummer? (eine Person fix)
- Budget für WhatsApp-Conversations geklärt?
- Fallback-Plan wenn Meta ablehnt?

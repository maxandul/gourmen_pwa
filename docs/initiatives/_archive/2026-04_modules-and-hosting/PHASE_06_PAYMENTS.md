# Phase 6 – TWINT / Payments

**Status**: pending  
**Aufwand**: ~5 Tage Code (+ 2-5 Tage Bürokratie für Account-Onboarding)  
**Branch**: `phase/06-modules-payments`

## Ziel

TWINT-Zahlungen in der App ermöglichen, primär für **BillBro** (Bill-Splitting nach Monatsessen) und **MerchOrder**-Bezahlung. Über RaiseNow als Schweizer Vereins-Acquirer (kein Handelsregister-Eintrag nötig).

## Pre-Conditions

- Phase 1 (Mail) abgeschlossen – für Zahlungsbestätigungs-Mails
- Phase 4 (Buchhaltung) abgeschlossen – für Auto-Buchungen
- RaiseNow-Account beantragt und freigeschaltet (kann parallel zu Phase 4 laufen)
- Branch `phase/06-modules-payments` von `master` erstellt
- Mit User entschieden: **RaiseNow** (empfohlen) oder Stripe

## Tasks

### 1. RaiseNow Account-Setup (parallel, manuell)

- [ ] Auf [raisenow.com](https://raisenow.com) Vereinsaccount beantragen
- [ ] Vereinsstatuten + Vereinsbeschluss + Bankverbindung einreichen
- [ ] Auf Freischaltung warten (~3-7 Werktage)
- [ ] API-Credentials in Railway-ENV eintragen:
  ```
  RAISENOW_API_KEY=...
  RAISENOW_WEBHOOK_SECRET=...
  ```

### 2. Models

- [ ] Neue Modelle in `backend/models/payment.py`:
  - `Payment`:
    - `id`, `provider` (Enum `RAISENOW`/`STRIPE`), `provider_payment_id` (unique), `amount_rappen`
    - `status` (Enum `PENDING`/`SUCCEEDED`/`FAILED`/`REFUNDED`)
    - `member_id` (FK), `purpose` (Enum `BILLBRO`/`MERCH_ORDER`/`MEMBERSHIP_FEE`/`OTHER`)
    - `purpose_ref_id` (Integer, polymorphe Referenz – participation_id, merch_order_id etc.)
    - `created_at`, `paid_at`, `metadata` (JSON)
  - Optional `Invoice` für mehr Struktur (später)
- [ ] Erweiterung bestehender Modelle:
  - `Participation`: neues Feld `payment_status` (Enum `OPEN`/`PAID`/`OVERDUE`/`WAIVED`)
  - `MerchOrder`: neues Feld `payment_status` analog
- [ ] Alembic-Migration in **separatem Commit**

### 3. Service-Layer

Datei `backend/services/payments.py`:

- [ ] `PaymentService` (Wrapper, providerunabhängig)
  - [ ] `create_checkout(amount_rappen, purpose, ref_id, member, return_url) -> dict`
  - [ ] `verify_webhook(headers, body) -> dict | None` – Signatur-Verifikation
  - [ ] `handle_webhook(payload) -> bool` – idempotente Verarbeitung
- [ ] `RaiseNowProvider` (Backend-Implementierung)
  - [ ] HTTPS-Calls an RaiseNow-API
  - [ ] Webhook-Signatur-Verifikation mit `RAISENOW_WEBHOOK_SECRET`
- [ ] Idempotenz: `Payment` mit `provider_payment_id` als unique constraint, doppelte Webhooks ignorieren

### 4. Routes

Neuer Blueprint `backend/routes/payments.py`:

- [ ] `POST /payments/checkout/<purpose>/<ref_id>` (login_required)
  - [ ] Validierung: User hat Berechtigung für diese Purpose+Ref
  - [ ] Amount aus Datenmodell holen (Participation, MerchOrder)
  - [ ] `PaymentService.create_checkout(...)` → URL
  - [ ] Redirect auf RaiseNow-Checkout-URL
- [ ] `GET /payments/return` (login_required)
  - [ ] Wird nach Bezahlung von RaiseNow aufgerufen
  - [ ] Zeigt Status-Seite (basiert auf DB-State, nicht auf URL-Parametern!)
- [ ] `POST /payments/webhook` (csrf_exempt, **kein** login_required)
  - [ ] Signatur-Verifikation Pflicht – ohne wird abgewiesen
  - [ ] Idempotenz: Payment-Objekt anlegen oder updaten
  - [ ] Bei `SUCCEEDED`:
    - [ ] `Participation.payment_status` oder `MerchOrder.payment_status` updaten
    - [ ] Bestätigungs-Mail via `MailService` (Phase 1)
    - [ ] Auto-Buchung via `AccountingService` (Phase 4) – wenn aktiv
    - [ ] Audit-Log
  - [ ] Returns 200 immer (außer Signature-Fail), damit RaiseNow nicht retried

### 5. UI-Integration

#### BillBro

- [ ] In Event-Detail-Template: bei eigener Participation nach BillBro-Abschluss
  - „Jetzt mit TWINT bezahlen"-Button
  - Status-Anzeige (offen / bezahlt)
- [ ] Admin-Sicht: wer hat bezahlt?

#### MerchOrder

- [ ] In Bestell-Übersicht: „Bezahlen"-Button bei `payment_status=OPEN`
- [ ] Status-Badge bei jedem Order

### 6. Konfiguration

- [ ] `backend/config.py`: `RAISENOW_API_KEY`, `RAISENOW_WEBHOOK_SECRET`, `RAISENOW_API_URL`
- [ ] `env.example`

### 7. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: 
  - „Externe Services" RaiseNow auf `aktiv`
  - Neuer Blueprint
  - Datenfluss-Beispiel „TWINT-Zahlung BillBro"
- [ ] `docs/DOMAIN.md`: Sektion „Zahlungen" mit Erklärung

## Acceptance-Criteria

- [ ] User kann TWINT-Zahlung via Button starten, wird zu RaiseNow weitergeleitet
- [ ] Nach Bezahlung kommt User mit korrektem Status-Display zurück
- [ ] Webhook setzt `payment_status` korrekt
- [ ] Bestätigungs-Mail wird verschickt
- [ ] Auto-Buchung in Buchhaltung (falls Phase 4 aktiv) erstellt korrekten Eintrag
- [ ] Doppelte Webhooks werden ignoriert (idempotent)
- [ ] Webhook ohne valide Signatur wird abgelehnt (401)
- [ ] Test-Modus mit RaiseNow-Sandbox funktioniert
- [ ] Tests grün, DB-Migration sauber

## Out of Scope

- **Stripe als Provider** – verschoben, falls RaiseNow nicht reicht
- **Wiederkehrende Zahlungen** (Mitglieder-Beiträge per Subscription) – kommt später
- **Mahn-Wesen** – kommt später
- **Refund-Workflow** – kommt später
- **Multi-Currency** – nur CHF

## Cursor-Agent-Briefing

```
Branch: phase/06-modules-payments
Doc: docs/initiatives/modules-and-hosting/PHASE_06_PAYMENTS.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen
- docs/CONVENTIONS.md lesen
- docs/DOMAIN.md lesen (BillBro, MerchOrder)
- Phase 1 (Mail) und Phase 4 (Buchhaltung) abgeschlossen
- RaiseNow-Account aktiv, API-Keys in ENV

Implementiere Phase 6 (Payments via RaiseNow) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- KRITISCH: Webhook-Signatur-Verifikation MUSS funktionieren
- KRITISCH: Idempotenz via unique constraint
- Kein Vertrauen in URL-Parameter nach Return - nur DB-State
- Folge .cursor/rules/initiatives.mdc

Lokal mit RaiseNow Sandbox testen:
- Test-Zahlung durchführen
- Webhook mit Test-Signature
- Doppelter Webhook → kein doppeltes Payment-Objekt

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md, DOMAIN.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Webhook-Idempotenz** ist nicht optional: Provider sendet Webhooks mehrfach (auch bei erfolgreicher Antwort)
- **Beträge in Rappen** in der API – RaiseNow nutzt Rappen oder Franken? Doku checken!
- **Test-Mode** vor Production-Mode separat handhaben (zwei API-Keys)
- **Webhook-URL** muss öffentlich erreichbar sein – auf Railway kein Problem
- **Reconciliation**: Provider zahlt nicht 1:1 aus, sondern in Bündeln. Im Buchhaltungs-Modul abbilden (separates Konto „Provider-Forderungen")
- **Gebühren**: RaiseNow ~1.3-2.5%. Im UI anzeigen oder schlucken? Mit User klären.

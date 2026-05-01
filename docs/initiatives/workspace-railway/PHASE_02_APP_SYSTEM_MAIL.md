# Phase 2 – App: System-Mail (Railway / SMTP oder HTTPS-API)

**Status**: blocked (Produktentscheid offen)  
**Aufwand**: ~0.5–1 Tag nach Entscheid  
**Branch**: `phase/02-workspace-system-mail` (optional: enthielt Resend-Entwurf, **nicht** auf `master`)

**Einstieg fuer neuen Agenten:** [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md)

## Ziel (unveraendert inhaltlich)

Transaktionale Mails (Reset, 2FA-Reset, Onboarding, Admin-Mailtest) aus der PWA **zuverlaessig in Production** — technisch ueber `MailService` (`backend/services/mail.py` auf `master`: **SMTP**).

## Befund 2026-05-01 (technisch)

- Railway Service **`web`** (Plan **Hobby**): TCP zu `smtp.gmail.com` und `smtp-relay.gmail.com` auf **465 und 587** → **Timeout** (per `railway ssh` + Python `socket` verifiziert).
- Admin `/admin/mail/test` mit Gmail-SMTP: **Timeout** (~40s, passend zu konfiguriertem SMTP-Timeout).
- Railway-Doku: ausgehender **SMTP auf Hobby deaktiviert**; ab **Pro** SMTP moeglich, danach **Redeploy**. Referenz: [Outbound Networking](https://docs.railway.com/reference/outbound-networking).
- **Infomaniak-SMTP betrifft dieselbe Policy** (gleiche Ports), nicht nur Gmail.

## Produktentscheid (Stakeholder)

- **Resend** (oder vergleichbarer reiner API-Anbieter) ist **nicht** gewuenschter Standard.
- Offene Wahl:
  1. **Railway Pro** (oder hoeher) → **SMTP** (Google Workspace App-Passwort fuer `kontakt@` oder Infomaniak-SMTP) — passt zu aktuellem `master`-Code.
  2. **Hobby beibehalten** → **HTTPS-Mail-API** von irgendeinem Provider (Resend war nur eine moegliche Implementierung).

## Optionaler Code-Zweig (nicht in Production auf master)

- Branch **`phase/02-workspace-system-mail`** (Remote): Commit `6e859e7` u. a. — `MailService` mit `RESEND_API_KEY` → Resend HTTPS.
- **`master` enthaelt das nicht.** Vor weiterem Bauen: mit Vorstand klaeren, ob Branch gemerged, verworfen oder ersetzt wird.

## Tasks (nach Entscheid)

### Wenn Pro + SMTP

- [ ] Railway-Workspace auf Pro; `web` **neu deployen**
- [ ] Google Workspace: App-Passwort (oder Relay-Regeln) fuer Versand; **ohne** Secrets in Docs
- [ ] Railway `MAIL_SMTP_*` setzen (Host/Port/TLS wie Provider); `/admin/mail/test` + Forgot-Password E2E
- [ ] Anchor-Docs/`env.example` nur bei Aenderungen am Pattern pflegen

### Wenn Hobby + HTTPS-API

- [ ] Provider waehlen; API-Key nur in Railway
- [ ] `MailService` oder gleichwertig erweitern (aktuell nur SMTP auf `master`)
- [ ] Tests wie oben

## Pre-Conditions

- Phase 1: MX/`kontakt@` stabil (siehe `PHASE_01`, `AGENT_HANDOFF.md`)
- Entscheid Vorstand: **Pro+SMTP** vs **Hobby+API**

## Acceptance-Criteria

- [ ] Admin-Mailtest in Production erfolgreich  
- [ ] Forgot-Password sendet Mail bei existierendem User (E2E)  
- [ ] Keine Secrets in Git oder oeffentlichen Docs  

## Hinweis Phase 8 (historisch)

`docs/initiatives/modules-and-hosting/PHASE_08_MAIL_PROD_FOLLOWUP.md` — Infomaniak-Timeouts in Prod; Kontext fuer Diagnose, nicht massgebend fuer Workspace-Initiative.

## Cursor-Agent-Briefing

```
1. AGENT_HANDOFF.md + diese Datei lesen.
2. Vor Entscheid keinen grossen Code bauen.
3. Nach Entscheid: Branch von master, eine Phase = ein Branch, keine Secrets.
```

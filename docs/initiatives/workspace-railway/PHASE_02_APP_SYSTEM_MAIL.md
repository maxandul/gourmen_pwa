# Phase 2 – App: System-Mail (Resend / HTTPS)

**Status**: in_progress  
**Aufwand**: ~0.5–1 Tag  
**Branch**: `phase/02-workspace-system-mail`

## Ziel

Transaktionale Mails (Reset, 2FA-Reset, Onboarding, Admin-Mailtest) laufen zuverlaessig aus **Railway Production**.

**Wichtig:** Auf Railway **Hobby** (und vergleichbar) ist **ausgehender SMTP blockiert** (Ports u. a. 465/587). Verifiziert: TCP-Timeout zu `smtp.gmail.com` / `smtp-relay.gmail.com` vom `web`-Service.

Daher: **Versand ueber Resend (HTTPS, Port 443)** — kein SMTP von Railway noetig.  
Mitgliederkorrespondenz bleibt in Workspace-Mail; Absenderadresse der App kann weiter `kontakt@gourmen.ch` sein, sobald die Domain bei Resend verifiziert ist.

## Pre-Conditions

- Phase 1: MX/DKIM/SPF fuer `gourmen.ch` stabil (Zustellbarkeit)  
- Resend-Account, Domain `gourmen.ch` bei Resend hinzugefuegt und **DNS-Verifizierung** dort abgeschlossen  
- API-Key nur in Railway (Variable `RESEND_API_KEY`), nicht im Repo  

## Tasks

- [ ] Resend: Domain + DNS-Records laut Resend-Wizard setzen (bei Infomaniak)  
- [ ] Resend: API-Key erzeugen  
- [ ] Railway `web`: `RESEND_API_KEY` setzen; optional `MAIL_HTTP_TIMEOUT_SECONDS=15`  
- [ ] Railway `web`: `MAIL_FROM_ADDRESS` / `MAIL_REPLY_TO` auf eine bei Resend erlaubte Absenderadresse (z. B. `kontakt@gourmen.ch`)  
- [ ] Production: `/admin/mail/test` und Forgot-Password gegen echte Adresse  
- [ ] `env.example` und Anchor-Docs sind angepasst (erledigt im Code-Branch)  

## Acceptance-Criteria

- [ ] Admin-Mailtest in Production erfolgreich  
- [ ] Forgot-Password sendet Mail bei existierendem User (E2E)  
- [ ] Keine Secrets in Git oder oeffentlichen Docs  

## Hinweis SMTP / Google Workspace

Direkter SMTP-Versand von Railway zu Google ist auf Hobby **nicht erreichbar**; Workspace bleibt fuer Empfang und menschliche Mail. Optional spaeter: Railway **Pro** wuerde SMTP grundsaetzlich ermoeglichen — Resend bleibt trotzdem empfohlen (Analytics, Zustellbarkeit, weniger Betrieb).

## Hinweis Phase 8 (modules-and-hosting)

`PHASE_08_MAIL_PROD_FOLLOWUP.md` adressierte Infomaniak-SMTP-Timeouts. Mit Resend-HTTPS ist der operative Pfad geklaert; historisches Dokument bleibt Referenz.

## Cursor-Agent-Briefing

```
Branch: phase/02-workspace-system-mail
MailService: bei RESEND_API_KEY wird Resend genutzt, sonst SMTP (lokal).
Keine Secrets in Logs/Commits. Production mit Railway-Logs verifizieren.
```

## Railway-Variablen (web, Kurzliste)

```
RESEND_API_KEY=re_...
MAIL_FROM_ADDRESS=kontakt@gourmen.ch
MAIL_REPLY_TO=kontakt@gourmen.ch
# optional:
MAIL_HTTP_TIMEOUT_SECONDS=15
```

SMTP-Variablen koennen in Production entfernt oder ignoriert werden, solange `RESEND_API_KEY` gesetzt ist.

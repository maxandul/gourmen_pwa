# Phase 2 – App: System-Mail auf Google Workspace

**Status**: pending  
**Aufwand**: ~0.5–1 Tag  
**Branch**: `phase/02-workspace-system-mail`

## Ziel

Die PWA sendet weiterhin transaktionale Mails (Reset, 2FA-Reset, Onboarding, Reminder) ueber den bestehenden `MailService`, aber **SMTP/Auth** sind auf **Google Workspace** abgestimmt (App-Passwort, SMTP-Relay, oder von Google empfohlener Weg fuer „Transactional“ aus eigener App).

Mitgliederkorrespondenz bleibt in gewohnten Mail-Apps; diese Phase betrifft nur den **technischen Versand aus Railway**.

## Pre-Conditions

- Phase 1 abgeschlossen: MX bei Google, `kontakt@` empfaengt zuverlaessig  
- Zugangsdaten/Regeln fuer SMTP oder Relay in Workspace geklaert (ohne Secrets in Docs)  

## Tasks

- [ ] In Google Workspace den passenden Versandweg waehlen und dokumentieren (intern):  
  - SMTP mit dediziertem App-Passwort fuer Dienstkonto-Mail, **oder**  
  - SMTP-Relay mit IP-Allowlist Railway (falls verfuegbar/erwuenscht)  
- [ ] Railway-Variablen auf `web` setzen: `MAIL_SMTP_*` konsistent zu `backend/config.py`  
- [ ] Production: Admin `/admin/mail/test` und ein Reset-Flow gegen echte Adresse  
- [ ] `env.example` und `docs/ARCHITECTURE.md` (Externe Services / Mail) aktualisieren  
- [ ] Alte Infomaniak-SMTP-Werte nur entfernen wenn nichts mehr darauf zeigt  

## Acceptance-Criteria

- [ ] Admin-Mailtest in Production erfolgreich (oder klarer SMTP-Fehler mit naechstem Schritt)  
- [ ] Forgot-Password sendet Mail bei existierendem User (E2E)  
- [ ] Keine Secrets in Git oder oeffentlichen Docs  

## Hinweis zu frueherer Phase 8 (Mail Prod)

Falls `docs/initiatives/modules-and-hosting/PHASE_08_MAIL_PROD_FOLLOWUP.md` noch offene Punkte hat: nach erfolgreichem Workspace-SMTP **evaluieren**, ob diese Follow-up-Phase noch noetig ist oder geschlossen werden kann.

## Cursor-Agent-Briefing

```
Branch: phase/02-workspace-system-mail
Lies PHASE_00_BASELINE.md (MailService existiert).
Aendere nur Config/Docs und minimal noetigen Code fuer klare Fehlermeldungen/Logging.
Verifiziere Production mit Railway-Logs, keine Secrets posten.
```

# Phase 8 – Mail-Zustellbarkeit in Production (Follow-up)

**Status**: pending  
**Aufwand**: ~0.5-1 Tag Diagnose, ggf. ~0.5 Tag Implementierung  
**Branch**: `phase/08-modules-mail-prod-followup`

## Ziel

Produktive Mailzustellung fuer Forgot-Password, 2FA-Reset und Onboarding stabil verifizieren und verbleibende Timeout-/Zustellprobleme beheben, ohne den Fortschritt in Phase 3 zu blockieren.

## Kontext / Problemstand

- In Development funktionieren Mail-Flows.
- In Production wurden wiederholt keine Mails zugestellt.
- Request-Latenz wurde bereits stark reduziert (non-blocking Versand), aber Admin-Mailtest zeigte weiterhin `Timeout`.
- Netzwerkbeobachtungen zeigten wiederholt ausgehende TCP-Versuche Richtung Infomaniak SMTP (`mail.infomaniak.com`, Port `465`) mit Drops/Timeout-Verhalten.

## Bereits erfolgte Loesungsversuche

### App-/Code-Seite

- SMTP IPv4-Fallback implementiert.
- Fail-fast SMTP-Timeout konfigurierbar gemacht.
- Option fuer SMTPS (`MAIL_SMTP_USE_SSL=true`, Port `465`) eingebaut.
- Forgot-Password und 2FA-Reset auf `MailService.send_async(...)` umgestellt (Request blockiert nicht mehr auf Mailversand).
- Branding/Text in Mail-Templates korrigiert (inkl. CH-Anrede).

### Railway/Production-Konfiguration

Aktuelle gesetzte Werte auf `web`:

- `MAIL_SMTP_PORT=465`
- `MAIL_SMTP_USE_SSL=true`
- `MAIL_SMTP_USE_TLS=false`
- `MAIL_SMTP_TIMEOUT_SECONDS=2`
- `MAIL_SMTP_MAX_IPV4_ATTEMPTS=1`
- SMTP Username/Password sind gesetzt.

### Bereits verifizierte Beobachtungen

- Produktion laeuft auf Merge von PR #7 (non-blocking Reset-Mails live).
- `POST /auth/forgot-password` antwortet schnell mit Redirect (`302 /auth/login`).
- Ohne Admin-Session ist `/admin/mail/test` erwartungsgemaess durch Login geschuetzt.
- Mit Admin-Session wurde `mail test failed: Timeout` gemeldet.

## Scope dieser Phase

### In Scope

- Reproduzierbarer Prod-Smoke fuer Mailversand (Admin-Mail-Test + Forgot + 2FA-Reset).
- Klare Trennung: App-Fehler vs. Netzwerk/Provider-Zustellung.
- Konfigurationsvergleich fuer SMTP-Verbindungsmodus (465/SSL vs. 587/STARTTLS).
- Falls noetig minimal-invasive Anpassung im `MailService` fuer robustere Connect-Diagnose.

### Out of Scope

- Plattformwechsel weg von Railway.
- Vollstaendiger Mailprovider-Wechsel als Sofortmassnahme.
- Neue Produktfeatures ausserhalb Mail-Zustellung.

## Pre-Conditions

- Zugriff auf Production-Railway-Logs (`web` Service).
- Admin-Zugang fuer `/admin/mail/test`.
- Zugriff auf Infomaniak Mail-Logs (Manager/kSuite) fuer betroffene Mailbox.

## Konkreter Diagnose-Plan

1. **Admin-Mailtest in Production ausloesen**
   - In der App als Admin einloggen.
   - `/admin/mail/test` ausfuehren.
   - Flash-Meldung und Zeitpunkt notieren.

2. **Railway Web-Logs korrelieren**
   - Nach Eintraegen suchen:
     - `Mail erfolgreich versendet`
     - `Mail-Versand fehlgeschlagen`
     - `Async-Mail fehlgeschlagen`
   - Exception-Text exakt festhalten (Timeout vs Auth vs TLS).

3. **SMTP-Modus A/B testen**
   - **A:** Port `465` + SSL (aktueller Stand).
   - **B:** Port `587` + STARTTLS (`MAIL_SMTP_USE_SSL=false`, `MAIL_SMTP_USE_TLS=true`).
   - Fuer beide Modi mindestens einen identischen Mailtest dokumentieren.

4. **Timeout/Retry nur fuer Diagnose erhoehen**
   - Testweise `MAIL_SMTP_TIMEOUT_SECONDS` auf `10` setzen.
   - Beurteilen, ob Fehlerbild von sofortigem Timeout zu spaeterem SMTP/Auth-Status wechselt.

5. **Infomaniak-Seite gegenpruefen**
   - Logs der betroffenen Absenderadresse in Infomaniak Manager/kSuite pruefen.
   - Klaeren: wurde SMTP-Session angenommen, wurde Nachricht akzeptiert, gab es Bounce/Reject.

## Acceptance-Criteria

- [ ] Es gibt einen reproduzierbaren und dokumentierten Ergebnisvergleich fuer SMTP-Modus A/B.
- [ ] Fuer den Mailtest liegt ein eindeutiger technischer Befund vor (Connect/Timeout, TLS/Auth, oder Provider-Reject).
- [ ] Mindestens ein produktiver Reset-/Testmail-Flow ist nachweisbar zugestellt **oder** es liegt ein providerseitig bestaetigter Blocker mit Handlungsempfehlung vor.
- [ ] Doku (dieses Dokument + Initiative-README) ist auf finalem Stand.

## Deliverables fuer den naechsten Agenten

- Exakte Zeitpunkte der Testausloesung (UTC oder lokale TZ mit Offset).
- Relevante Railway-Logzeilen (ohne Secrets).
- Verwendete SMTP-Config pro Testlauf.
- Infomaniak-Logstatus pro Testlauf.
- Eindeutige Entscheidungsempfehlung:
  - bei Netzwerkproblem: bevorzugter Port/Modus + Timeout
  - bei Providerproblem: konkrete Eskalation an Infomaniak Support

## Cursor-Agent-Briefing

```
Branch: phase/08-modules-mail-prod-followup
Doc: docs/initiatives/modules-and-hosting/PHASE_08_MAIL_PROD_FOLLOWUP.md

Pre-Flight:
- AGENTS.md lesen
- docs/initiatives/modules-and-hosting/README.md lesen
- docs/initiatives/modules-and-hosting/PHASE_08_MAIL_PROD_FOLLOWUP.md lesen
- Bei Code-Aenderungen zusaetzlich docs/ARCHITECTURE.md und docs/CONVENTIONS.md lesen

Auftrag:
- Fuehre den Diagnose-Plan strikt von oben nach unten aus.
- Aendere nur das Minimum noetige an Config/Code.
- Dokumentiere jede Beobachtung so, dass ein dritter die Ursache nachvollziehen kann.
- Keine Secrets in Logs, Docs oder Commits.
```


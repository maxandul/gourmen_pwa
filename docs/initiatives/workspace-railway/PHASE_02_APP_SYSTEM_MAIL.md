# Phase 2 / Capability – System-Mail via Resend

**Status**: done (2026-05-07; Production-Smoke: `/admin/mail/test` erfolgreich)  
**Aufwand**: abgeschlossen  
**Merge**: PR #11 (`phase/02-workspace-system-mail` → `master`)  
**Verwandt**: `docs/STRATEGY_2026.md` (Decision Log 2026-05-07), `AGENT_HANDOFF.md`

---

## Zielzustand

Transaktionale Systemmails der PWA — Forgot-Password, 2FA-Reset, Onboarding-Aktivierung, Admin-Mailtest — werden zuverlässig in Production zugestellt. Versand läuft über die Resend-HTTPS-API, weil Railway Hobby outbound SMTP blockiert. Mails kommen mit Absender `kontakt@gourmen.ch` (oder dediziertem `noreply@`-Alias) bei den Empfängern an, sind DKIM/SPF-gehärtet, landen nicht im Spam und sind nachvollziehbar (Resend-Dashboard zeigt Delivery-Status pro Mail).

**Was sich nicht ändert**: Personenpost (`kontakt@gourmen.ch` als Mensch geschrieben/empfangen) läuft weiter über Google Workspace. Diese Phase betrifft ausschliesslich den maschinellen Versand aus der App.

## User Journeys

**Mitglied vergisst Passwort** → klickt «Passwort vergessen» → gibt Mail-Adresse ein → erhält innerhalb von 60 Sekunden eine Reset-Mail mit Token-Link → klickt Link → setzt neues Passwort.

**Vorstand legt neues Mitglied an** → Admin-Form ausfüllen → System verschickt Onboarding-Mail mit 7-Tage-Token → Mitglied klickt Link → setzt eigenes Passwort und 2FA.

**Mitglied verliert 2FA-Gerät** → klickt «2FA zurücksetzen» bei Login → erhält Reset-Mail → klickt Link → kann neues 2FA-Gerät einrichten.

**Admin testet Mail-Funktion** → `/admin/mail/test` → Eingabe Empfänger → Test-Mail kommt an, Resend-Dashboard zeigt Status.

**Mail kommt nicht an** → Admin schaut ins Resend-Dashboard → sieht Bounce/Spam-Klassifikation/Delivery-Status → kann Empfänger informieren oder DNS prüfen.

## Externe Integration

| Bereich | Konfiguration |
|---|---|
| Resend-Account | Verein registriert mit `kontakt@gourmen.ch`. Free-Plan: 100 Mails/Tag, 3'000/Monat. Reicht für Vereinsvolumen mit Reserve. |
| Domain-Verifikation | Resend-Domain `gourmen.ch` einrichten; Resend zeigt nötige DNS-Records, die bei Infomaniak DNS gesetzt werden. |
| DKIM | Resend-Selector (`resend._domainkey.gourmen.ch` o.ä.) als TXT-Record bei Infomaniak ergänzen. **Zusätzlich** zu existierendem Workspace-DKIM. |
| SPF | Bestehender SPF-Record bei Infomaniak um `include:_spf.resend.com` ergänzen. SPF darf nicht mehr als 10 DNS-Lookups erzeugen. |
| DMARC | Bleibt vorerst `p=none`. Sobald Mailflow stabil und beide DKIMs bestätigt: Schritt auf `p=quarantine`. |
| API-Key | In Railway als `RESEND_API_KEY` Secret. Niemals im Repo, niemals in Logs. Resend-API-Keys sind scoped, also Sending-Only-Key erstellen. |
| Absender | `MAIL_FROM_ADDRESS=kontakt@gourmen.ch` oder besser dediziert `noreply@gourmen.ch` (ggf. als Workspace-Alias anlegen). Reply-To kann auf `kontakt@` zeigen, damit Antworten landen wo Menschen sie sehen. |

## Datenmodell-Touch

Keine neuen Models, keine Migration. `MailService` wird intern erweitert: bei vorhandenem `RESEND_API_KEY` läuft der Versand über HTTPS-API, sonst Fallback auf bestehenden SMTP-Code (für Lokal-Dev mit Mailpit oder ähnlichem).

`AuditEvent` bekommt optional einen Eintrag pro versendeter Mail mit Resend-Message-ID, falls Audit-Trail gewünscht. Empfehlung: nur für sicherheits-relevante Mails (Reset/Onboarding) loggen, nicht für jeden Test.

## Datenschutz / DSGVO

**Resend ist US-Provider (Delaware)**, betreibt aber EU-Server (Frankfurt). Bei Account-Setup explizit EU-Region wählen, sonst landen Mail-Inhalte und Empfänger-Adressen auf US-Servern. **DPA / Auftragsverarbeitungsvertrag** muss mit Resend abgeschlossen werden — Resend bietet einen Standard-DPA online an. Datenschutzerklärung der PWA muss um Resend als Auftragsverarbeiter ergänzt werden (Empfänger-Mail-Adressen, Mail-Inhalte mit Reset-Tokens werden Resend zur Zustellung übergeben).

**Empfehlung**: Reset-Tokens sind bereits in der App nur 1 Stunde gültig — auch wenn ein Mail-Inhalt theoretisch von Resend abgreifbar wäre, ist das Angriffsfenster klein. Mail-Inhalte sollten nichts enthalten, was nach Token-Ablauf noch sensibel ist (z.B. keine Klartext-Passwörter, keine Mitgliederlisten).

## AI/Automation-Optionen

Für diese Capability **nicht relevant**. System-Mails sind statische Templates mit Variablen-Substitution. AI-Personalisierung wäre overkill und würde Reset-Latenz erhöhen. AI-first-Leitlinie greift hier nicht.

(Anders bei zukünftigen Use Cases wie BillBro-Reminder oder GV-Einladungen — dort wird die Frage neu gestellt.)

## Pre-Conditions

- Phase 1 abgeschlossen (Workspace + DNS-Hoheit bei Infomaniak)
- Code auf `master` (Resend/SMTP `MailService`; nicht mehr nur auf Side-Branch)
- Vorstand bestaetigt Resend-Entscheid (siehe Decision Log 2026-05-07)
- Resend-Account mit passender Region, Domain verifiziert; DPA/Auftragsverarbeitung gemaess Vereinsprozess

## Tasks

### 1. Infrastruktur (manuell, ohne Code)

- [x] Resend-Account für `gourmen.ch` einrichten (EU-Region erzwingen)
- [x] DPA mit Resend abschliessen
- [x] Domain `gourmen.ch` in Resend hinzufügen, DNS-Records auslesen
- [x] **Bei Infomaniak DNS**: Records laut Resend-Wizard (u. a. DKIM-TXT; SPF inkl. SES-`include`, siehe `STRATEGY_2026.md`)
- [x] DNS-Propagation / Resend-Dashboard «Verified» (Zustellung in Prod verifiziert)
- [x] Sending-Only API-Key in Resend erstellen, sicher dokumentieren

### 2. Railway-Konfiguration

- [x] `RESEND_API_KEY` als Secret in Railway-Service `web` setzen
- [x] `MAIL_FROM_ADDRESS=kontakt@gourmen.ch` (oder `noreply@gourmen.ch` falls Alias angelegt)
- [x] `MAIL_REPLY_TO=kontakt@gourmen.ch`
- [x] Bestehende `MAIL_SMTP_*`-Variablen nicht löschen — bleiben als Lokal-Dev-Fallback nutzbar

### 3. Code-Merge / Anpassung

- [x] Branch `phase/02-workspace-system-mail` rebasen auf aktuellen `master` und mergen (PR #11)
- [x] `MailService` so anpassen, dass bei vorhandenem `RESEND_API_KEY` Resend genutzt wird, sonst SMTP
- [x] `requirements.txt`: Resend-SDK (`resend>=2.0`) ergänzen oder direkt mit `requests`/`httpx` arbeiten — umgesetzt mit `requests` (bereits Dependency)
- [x] Logging: Bei Resend-Versand `message_id` aus Response loggen (kein Mail-Inhalt!)
- [x] Error-Handling: Resend-API-Fehler werden als `{'success': False, 'error': '...'}` zurückgegeben, App-Logik darf nicht crashen wenn Versand fehlschlägt
- [x] Templates müssen weiter funktionieren — keine Änderungen am `templates/mail/`-Output erwartet
- [x] `env.example` um `RESEND_API_KEY` ergänzen (mit leerem Wert, Kommentar «leave empty for SMTP fallback»)
- [x] `docs/ARCHITECTURE.md`: «Externe Services»-Tabelle um Resend ergänzen

### 4. Tests in Production

- [x] PR mergen, Railway deployt automatisch
- [x] `/admin/mail/test` mit eigener Test-Mail-Adresse → erfolgreich
- [ ] Forgot-Password mit echter Mitglieder-Adresse → Mail kommt an, Reset funktioniert (empfohlen)
- [ ] Resend-Dashboard zeigt weitere Transaktionsmails wie Forgot-Password als «Delivered» (bei erstem E2E-Lauf)
- [ ] Spam-Test: SPF/DKIM-Check via [mail-tester.com](https://mail-tester.com) — Score ≥ 9/10 anvisieren (optional)

### 5. Doc-Updates

- [x] `docs/initiatives/workspace-railway/README.md` Status-Tabelle Phase 2 auf `done` setzen
- [x] `docs/ARCHITECTURE.md` falls neue ENV-Variablen
- [ ] Datenschutzerklärung der PWA um Resend als Auftragsverarbeiter ergänzen (separates Asana/Backlog-Item für Andreas)

## Acceptance-Criteria

- [ ] Forgot-Password löst Mail aus, Mail kommt an, Reset funktioniert E2E (empfohlen)
- [ ] Onboarding-Mail bei neuem Mitglied kommt an, Aktivierung funktioniert (empfohlen)
- [ ] 2FA-Reset-Mail kommt an (empfohlen)
- [x] `/admin/mail/test` zeigt erfolgreichen Versand mit Resend-Message-ID
- [ ] mail-tester.com Score ≥ 9/10 (SPF, DKIM, DMARC alle grün) (optional)
- [x] Keine Secrets in Git, Logs, oder Doc-Texten
- [x] Bei Lokal-Dev ohne `RESEND_API_KEY` läuft Mail über SMTP-Fallback (z.B. Mailpit) — kein Crash

## Out of Scope

- **Kein Mail-Empfang aus der App** — Personen-Mails bleiben in Gmail
- **Kein Templating-Refactor** — bestehende Mail-Templates werden 1:1 übernommen
- **Keine Mail-Queue / Retries** — Resend hat eingebaute Retries; App schreibt einmaliges Best-Effort-Send wie heute
- **Kein Massenmailing** — Newsletter ist explizit nicht vorgesehen (siehe `STRATEGY_2026.md`)
- **Keine Auth-Umstellung auf Magic Links** — Auth-Migration ist Future Consideration

## Risiken & Fallstricke

- **DNS-Race**: Wenn DKIM/SPF noch nicht propagiert sind, landen erste Mails im Spam. Lösung: Resend-Dashboard «Verified»-Status abwarten, vorher nicht produktiv schalten.
- **SPF >10 Lookups**: Wenn der bestehende SPF schon viele Includes hat (Workspace, evtl. Infomaniak-Reste), kann ein weiterer Include die Grenze sprengen. Dann SPF konsolidieren (Infomaniak-Reste raus).
- **Resend-Quota**: Free-Plan hat 100 Mails/Tag. Bei einem Massen-Onboarding (z.B. 50 neue Mitglieder gleichzeitig + Reset-Welle) kann das eng werden. Lösung: Resend bietet Pro mit höheren Limits ab $20/Mo — falls je nötig.
- **`MAIL_FROM_ADDRESS` mismatch**: Resend verlangt, dass `from`-Adresse zur verifizierten Domain gehört. Wenn versehentlich eine andere Domain als `from` gesetzt wird, schlägt der Send fehl.
- **DPA-Vergessen**: Wenn DPA mit Resend nicht unterzeichnet ist, ist die Datenverarbeitung DSGVO-rechtlich angreifbar. Vor Production-Cutover prüfen.

## Cursor-Agent-Briefing

```
Status: **abgeschlossen** (2026-05-07). Code auf `master` (PR #11).

Referenz fuer Folgearbeit:
- Doc: `PHASE_02_APP_SYSTEM_MAIL.md`
- `AGENTS.md`, `docs/STRATEGY_2026.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `AGENT_HANDOFF.md`

Operational: Resend bei `RESEND_API_KEY`; lokal SMTP-Fallback ohne Key.
Keine Secrets in Logs/Commits.
```

## Hinweise

- **Code-Stand**: Resend-Integration liegt auf `master` (Merge PR #11). Branch `phase/02-workspace-system-mail` ist historisch; bei neuem Branch von `master` starten.
- **Resend-Webhooks** (Bounce, Complaint, Open) sind in dieser Phase nicht umgesetzt. Falls später Bounce-Handling automatisiert werden soll: separate Mini-Phase mit `/api/resend-webhook`-Endpoint und `Member.email_status`-Feld.
- **Newsletter-/Massenmail-Use-Case** ist explizit nicht vorgesehen (siehe Strategie-Doc). Falls jemals doch: Resend-Audience-Feature evaluieren oder externe Liste in Listmonk/Mailchimp.

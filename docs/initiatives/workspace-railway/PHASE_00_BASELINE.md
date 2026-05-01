# Phase 0 – Baseline (was schon da ist)

**Status**: Referenz (kein eigener Branch noetig)  
**Zweck**: Agenten sollen nicht doppelt bauen. Diese Phase ist **Lesen und Verifizieren**.

## Code und Features (Stand laut Vorgaenger-Initiative)

Aus `modules-and-hosting` umgesetzt bzw. in `master` erwartbar:

- **Mail**: `backend/services/mail.py` – SMTP, IPv4-Fallback, Timeouts, optional SSL, `send` / `send_async`
- **Auth-Flows**: Token in DB (`AuthToken`), Forgot-Password, 2FA-Reset, Onboarding mit Mail-Templates
- **Admin**: Member-Anlage inkl. Onboarding-Mail; Mail-Test-Route (geschuetzt)
- **Cron**: Token-Cleanup in `run_cron_reminders.py` (falls eingebunden)
- **Audit**: Enum-Migration fuer fehlende Werte (Production) – historisch relevant

## Was sich mit Workspace **aendert** (nicht ignorieren)

- **Empfang** von `kontakt@` und MX liegen nach Cutover bei **Google**, nicht Infomaniak  
- **SMTP fuer System-Mails** muss nach Phase 1/2 auf Workspace-kompatible Werte (Host, Port, TLS/SSL, Relay-Regeln)  
- **Datei-Speicher** in Phase 3 wird **Google Drive (Shared Drive)**, nicht Infomaniak Object Storage / R2  

## Pre-Flight fuer alle folgenden Phasen

- [ ] `docs/initiatives/workspace-railway/README.md` gelesen  
- [ ] `docs/ARCHITECTURE.md` aktuellen Stand mit Baseline abgeglichen (bei Diskrepanz Doc-Issue melden)  
- [ ] `env.example` und Railway-Variablen fuer Mail kennen (ohne Secrets zu loggen)  

## Acceptance

- [ ] Agent kann in einem Satz erklaeren, wo System-Mails im Code ausgeloest werden und wo kuenftig SMTP konfiguriert wird  
- [ ] Agent weiss, dass alte `PHASE_03_FILES.md` (Object Storage) durch `PHASE_03_GOOGLE_SHARED_DRIVE_FILES.md` ersetzt wird  

## Cursor-Agent-Briefing

```
Du arbeitest in der Initiative workspace-railway.
Lies PHASE_00_BASELINE.md und README.md vollstaendig.
Baue keine zweite Mail-Infrastruktur und kein zweites Token-System.
Fokus: Migration und Anbindung gemaess PHASE_01+.
```

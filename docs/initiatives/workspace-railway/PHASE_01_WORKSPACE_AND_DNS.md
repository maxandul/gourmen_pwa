# Phase 1 – Google Workspace einrichten und DNS/MX Cutover

**Status**: in_progress  
**Aufwand**: 0.5–2 Tage (ueberwiegend manuell, Vorstand/DNS)  
**Branch**: `phase/01-workspace-cutover` (optional; oft ohne Code)

## Ziel

- Google Workspace fuer `gourmen.ch` aktivieren  
- **Eine** Mailbox-Lizenz (guenstigster passender Plan, z. B. Business Starter; Nonprofit separat pruefen)  
- **Vereinskonto** als Owner: primaer z. B. `kontakt@gourmen.ch`, weitere Adressen als **Alias**  
- DNS bei Infomaniak: Domain-Verifizierung, **MX auf Google**, SPF/DKIM/DMARC fuer Google  
- Infomaniak-Mailbox fuer `kontakt@` **nicht** ploetzlich loeschen vor stabilem Google-Empfang  

## Tasks (Checkliste)

### A. Workspace

- [x] Organisation anlegen, Super-Admin festlegen (Vereinskonto)  
- [x] Domain `gourmen.ch` hinzufuegen und verifizieren (TXT bei Infomaniak DNS)  
- [x] Nutzer `kontakt@gourmen.ch` (oder gewaehltes Primaer-Konto) anlegen  
- [x] Alias(e) z. B. `admin@gourmen.ch` auf gleiche Mailbox legen (Test ok 2026-05-01)  
- [ ] Shared Drive: fuer **alle** vorgesehenen Mitglieder ausrollen („alle sehen alles“)  

### B. DNS bei Infomaniak

- [x] MX-Records laut Google-Anleitung setzen (Cutover erst wenn A+C erledigt)  
- [x] SPF (TXT) fuer Google  
- [x] DKIM in Workspace generieren, DNS-TXT bei Infomaniak eintragen  
- [x] DMARC (TXT) schrittweise (z. B. `p=none` → spaeter straffer)  

### C. Cutover

- [x] Testmail von extern an `kontakt@` **bevor** breit kommuniziert  
- [x] Testmail von `kontakt@` nach extern  
- [ ] Alte Infomaniak-Mail-Postfaecher: Inhalt migrieren oder archivieren, **dann** deaktivieren  
- [x] Dokumentieren: Datum/Zeit MX-Umstellung, wer fuehrend war  

## Acceptance-Criteria

- [x] MX zeigen auf Google; Mails kommen in Gmail/Workspace an  
- [x] SPF/DKIM/DMARC sind gesetzt (mindestens SPF + DKIM „pass“ in Tests)  
- [x] Vereinskonto + Aliase funktionieren  
- [ ] Kein Datenverlust bei Migration (oder bewusst dokumentiertes Archiv; Infomaniak-Postfach derzeit bewusst parallel)  

## Umsetzungslog (2026-05-01)

- Workspace fuer `gourmen.ch` eingerichtet; primaeres Vereinskonto auf `kontakt@gourmen.ch` erstellt.
- Domain in Google verifiziert (TXT in Infomaniak gesetzt).
- DNS auf Google-Mailfluss umgestellt: Google-MX aktiv.
- SPF gesetzt (Uebergang): `v=spf1 include:_spf.google.com include:spf.infomaniak.ch ~all`.
- DKIM-Selector publiziert und Google-seitig erfolgreich aktiviert.
- DMARC auf `p=none` gesetzt (Migrationsmodus).
- Senden/Empfangen mit Gmail erfolgreich getestet.
- Alias-Test erfolgreich: `admin@gourmen.ch` liefert an die Workspace-Mailbox.
- Shared Drive erstellt; Pilot mit 1 Member als Content Manager erfolgreich.
- Infomaniak-Mailbox bleibt vorerst als inaktiver Fallback bestehen (kein relevanter Traffic).

## Restpunkte fuer Phase-1-Abschluss

- Shared-Drive-Rollen fuer restliche Mitglieder ausrollen, sobald Board-Freigabe vorliegt.
- Abschlussnotiz mit exakter Uhrzeit der finalen MX-Umstellung und verantwortlicher Person nachtragen.

## Rollout-Checkliste restliche Mitglieder (operativ)

- Mitgliederliste finalisieren (11/11) und pro Person Zielrolle festlegen.
- Mitglieder gesammelt in den Shared Drive aufnehmen.
- Kurzer Sichttest mit 2-3 Nicht-Admin-Membern: sehen, oeffnen, herunterladen.
- Nach erfolgreichem Test "alle sehen alles" intern bestaetigen und in dieser Phase notieren.

## Risiken / Rollback

- MX-Fehlkonfiguration → Mail haengt oder geht verloren: **Vor Cutover** alle TXT/MX doppelt pruefen  
- Rollback: MX zurueck auf Infomaniak nur wenn Postfaecher dort noch existieren und Daten konsistent sind  

## Cursor-Agent-Briefing

```
Phase 1 ist ueberwiegend OPERATIONS, nicht Flask-Code.
Dokumentiere alle DNS-Aenderungen und Workspace-Schritte in einem kurzen internen Log (ohne Secrets).
Nach Abschluss: PHASE_02 — siehe `AGENT_HANDOFF.md` (Railway SMTP / Entscheid Vorstand).
```

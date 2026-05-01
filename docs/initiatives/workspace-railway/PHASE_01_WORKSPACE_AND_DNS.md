# Phase 1 – Google Workspace einrichten und DNS/MX Cutover

**Status**: pending  
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

- [ ] Organisation anlegen, Super-Admin festlegen (Vereinskonto)  
- [ ] Domain `gourmen.ch` hinzufuegen und verifizieren (TXT bei Infomaniak DNS)  
- [ ] Nutzer `kontakt@gourmen.ch` (oder gewaehltes Primaer-Konto) anlegen  
- [ ] Alias(e) z. B. `admin@gourmen.ch` auf gleiche Mailbox legen  
- [ ] Shared Drive Status pruefen (bereits vorhanden; alle sehen alles)  

### B. DNS bei Infomaniak

- [ ] MX-Records laut Google-Anleitung setzen (Cutover erst wenn A+C erledigt)  
- [ ] SPF (TXT) fuer Google  
- [ ] DKIM in Workspace generieren, DNS-TXT bei Infomaniak eintragen  
- [ ] DMARC (TXT) schrittweise (z. B. `p=none` → spaeter straffer)  

### C. Cutover

- [ ] Testmail von extern an `kontakt@` **bevor** breit kommuniziert  
- [ ] Testmail von `kontakt@` nach extern  
- [ ] Alte Infomaniak-Mail-Postfaecher: Inhalt migrieren oder archivieren, **dann** deaktivieren  
- [ ] Dokumentieren: Datum/Zeit MX-Umstellung, wer fuehrend war  

## Acceptance-Criteria

- [ ] MX zeigen auf Google; Mails kommen in Gmail/Workspace an  
- [ ] SPF/DKIM/DMARC sind gesetzt (mindestens SPF + DKIM „pass“ in Tests)  
- [ ] Vereinskonto + Aliase funktionieren  
- [ ] Kein Datenverlust bei Migration (oder bewusst dokumentiertes Archiv)  

## Risiken / Rollback

- MX-Fehlkonfiguration → Mail haengt oder geht verloren: **Vor Cutover** alle TXT/MX doppelt pruefen  
- Rollback: MX zurueck auf Infomaniak nur wenn Postfaecher dort noch existieren und Daten konsistent sind  

## Cursor-Agent-Briefing

```
Phase 1 ist ueberwiegend OPERATIONS, nicht Flask-Code.
Dokumentiere alle DNS-Aenderungen und Workspace-Schritte in einem kurzen internen Log (ohne Secrets).
Nach Abschluss: PHASE_02 anstossen (App SMTP / Relay).
```

# Phase 8 – Infomaniak: Mail- und Storage-Rollen abbauen

**Status**: pending  
**Aufwand**: ~0.5 Tag  
**Branch**: `phase/08-workspace-decommission-infomaniak` (optional, oft nur Docs/DNS)

## Ziel

Nach Workspace- und Drive-Integration: **aufraeumen**, was bei Infomaniak nicht mehr gebraucht wird, ohne die Domain zu verlieren.

## Was typischerweise bleibt

- Domain-Registration  
- DNS-Hosting (A/AAAA/CNAME/MX/TXT fuer `gourmen.ch` und Subdomains)  

## Was typischerweise weg kann (nur wenn nichts mehr darauf zeigt)

- Infomaniak-Mailboxen / Mail-Produkt fuer `@gourmen.ch` (nach erfolgreichem MX bei Google und Datenmigration)  
- Infomaniak Object Storage / kDrive, falls explizit eingerichtet und durch Google Shared Drive ersetzt  

## Tasks

- [ ] Inventar: welche Infomaniak-Produkte sind noch aktiv  
- [ ] Kosten/Nutzung pruefen vor Kuendigung  
- [ ] `docs/ARCHITECTURE.md` und `env.example`: keine toten `MAIL_SMTP_*` auf Infomaniak mehr dokumentieren  
- [ ] Alte Initiative-Phasen-Referenzen: nur noch historisch  

## Acceptance-Criteria

- [ ] Kein aktiver Doppel-Betrieb Mail (MX nur Google)  
- [ ] Dokumentation beschreibt nur noch die reale Konfiguration  
- [ ] Keine Secrets in Commits  

## Cursor-Agent-Briefing

```
Phase 8 ist primaer Koordination mit Vorstand/DNS.
Code-Aenderungen nur wo Referenzen oder Docs falsche Provider behaupten.
```

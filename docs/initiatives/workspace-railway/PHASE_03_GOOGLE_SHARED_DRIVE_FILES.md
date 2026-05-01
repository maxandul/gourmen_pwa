# Phase 3 – App: Dateien auf Google Shared Drive

**Status**: pending  
**Aufwand**: ~3–5 Tage  
**Branch**: `phase/03-workspace-drive-files`

## Ziel

Mitglieder verwalten Vereinsdateien in der PWA: **hochladen, anzeigen, herunterladen, soft-loeschen**. Speicherort ist der **bestehende Google Shared Drive** (alle sehen alles). **Bearbeiten** von Office-Dokumenten: Nutzer oeffnen in Google Docs/Sheets (neuer Tab oder In-App-Browser akzeptiert).

Ersetzt die fruehere Planung „Infomaniak Object Storage“ aus `modules-and-hosting/PHASE_03_FILES.md`.

## Pre-Conditions

- Phase 1: Workspace aktiv, Shared Drive nutzbar  
- Technischer Zugang geklaert: **Domain-wide Delegation** und/oder **Service Account** mit Zugriff auf den Shared Drive, oder anderer von Vorstand freigegebener Weg  
- Google Cloud Projekt (APIs: Drive) und Credentials nur via Railway Secrets  

## Tasks (Ueberblick)

- [ ] Neuer Service `backend/services/drive_storage.py` (oder aehnlich): Upload, List, Download-Link, Trash/Delete gemaess Vereinbarung  
- [ ] `Document`-Modell erweitern: z. B. `drive_file_id`, `storage_provider='google_shared_drive'`, Metadaten  
- [ ] Routes unter `docs`/`documents`: Upload, Download-Redirect, Loeschen (soft), „In Google oeffnen“-Link  
- [ ] Alembic-Migration in **eigenem Commit**  
- [ ] Quotas/Mime-Whitelist wie in alter Phase-3-Doku (anpassen)  
- [ ] `env.example`: `GOOGLE_*` Variablen (ohne JSON im Repo)  
- [ ] `docs/ARCHITECTURE.md`: Drive als aktiver File-Backend  

## Acceptance-Criteria

- [ ] Eingeloggtes Mitglied kann Datei hochladen; sie erscheint im Shared Drive im vereinbarten Zielordner  
- [ ] Download fuer berechtigte User funktioniert  
- [ ] Soft-Delete in App; klar dokumentiert ob Drive-Objekt nur ausgeblendet oder in Papierkorb  
- [ ] Link „Bearbeiten in Google“ funktioniert fuer Docs/Sheets-Dateien wo anwendbar  
- [ ] Bestehende URL-only Documents in der App bleiben funktionsfaehig  

## Out of Scope (vorerst)

- Echtzeit-Kollaboration in iframe in der PWA  
- Virus-Scan  
- Feingranulare Drive-ACL pro Mitglied (nicht noetig: alle sehen alles)  

## Cursor-Agent-Briefing

```
Branch: phase/03-workspace-drive-files
Lies PHASE_00_BASELINE.md und alte modules-and-hosting/PHASE_03_FILES.md nur fuer UX/Validierungsideen, nicht fuer Storage-Backend.
Implementiere Google Drive API sauber im Service-Layer; keine Secrets im Repo.
Migration separater Commit.
```

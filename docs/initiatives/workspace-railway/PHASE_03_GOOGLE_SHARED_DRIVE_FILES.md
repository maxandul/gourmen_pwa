# Phase 3 – App: Dateien auf Google Shared Drive

**Status**: Implementation **abgeschlossen** und auf **Production** deployed (2026-05-13). Offen: MVP-weiter **Cutover** (`DRIVE_FEATURE_ENABLED=true` + Mitglieder-Kommunikation), siehe unten.
**Aufwand**: ~3–5 Tage
**Branch**: Inhalt in **`master`** gemerged (Ursprungs-Branch `phase/03-workspace-drive-files`; PR #12, Squash-Merge `6cab330`). Anschliessender Hotfix nur Migrationsreihenfolge: `4377231`.

## Ziel

Mitglieder verwalten Vereinsdateien in der PWA: hochladen, anzeigen, herunterladen, archivieren, endgültig löschen (nur Admin). Speicherort ist ein **neues Google Shared Drive** unter `kontakt@gourmen.ch`. Bearbeitung von Office-Dokumenten erfolgt im Drive-Web-View («Öffnen»-Aktion in der App).

Ersetzt die frühere Planung «Infomaniak Object Storage» aus `_archive/2026-04_modules-and-hosting/PHASE_03_FILES.md`.

## Autoritative Spezifikation

**Source of Truth für diese Phase ist `docs/capabilities/drive.md`.**

Dieses Phase-Doc ist nur der Phasen-Briefing-Rahmen. Alle Details (Architektur, Datenmodell, Service-Layer, UX, Sicherheit, Setup-Workflow, Acceptance-Criteria) stehen im Capability-Doc und gelten bei Konflikt vor Aussagen in diesem Phase-Doc.

## Pre-Conditions

- Phase 1 abgeschlossen: Workspace aktiv, Shared Drive nutzbar
- Manuelle Setup-Schritte aus Capability-Doc Sektion 16.1 durch Andreas erledigt:
  - Neues Shared Drive «Gourmen Verein» angelegt, `drive_id` an Cursor übergeben
  - `gcloud auth login` einmalig im Cursor-Terminal absolviert
  - Service Account einmalig zum Shared Drive eingeladen (nach Schritt 5 der Cursor-Sequenz)
- Railway Secrets vorbereitet für `GOOGLE_SERVICE_ACCOUNT_KEY` und `GOOGLE_DRIVE_ID`

## Implementations-Reihenfolge (siehe Capability-Doc Sektion 17.1)

1. *Schema-Migration Member*: `google_email`-Felder, Token-Purpose `google_email_verify`. Eigener Alembic-Commit.
2. *Schema-Migration Document*: alte URL-only-Records löschen, Felder umbauen. Eigener Alembic-Commit.
3. *Service-Layer*: `backend/services/drive_storage.py` mit allen Methoden gemäss Capability-Doc Sektion 7. Tests inklusive.
4. *Routes und UI*: Templates, Routen, Upload-Modal mit Drag-and-Drop, Aktionen-Dropdowns, Admin-Re-Sync-Button, Member-Profile-Erweiterung.
5. *Setup-Script*: `scripts/setup_drive.py` für die Folder-Initialisierung, idempotent.

## Acceptance-Criteria

Vollständige Liste in `docs/capabilities/drive.md`, Sektion 17.3.

Kurzfassung (Implementation-Stand):

- [x] Upload via App (Picker oder Drag-and-Drop), File erscheint im richtigen Drive-Folder
- [x] Grössen- und MIME-Validierung server- und clientseitig
- [x] SVG-Sanitization vor Drive-Upload
- [x] «Öffnen»-Aktion via `target="_blank"`
- [x] «Verschieben», «Umbenennen», «Archivieren», «Wiederherstellen» funktionieren atomar
- [x] «Endgültig löschen» nur Admin, mit Titel-Copy-Bestätigung
- [x] Re-Sync-Button im Admin liefert Drift-Summary
- [x] Member-Profil zeigt Kontakt-Mail und Google-Login-Mail getrennt
- [x] AuditEvents für alle Lifecycle-Aktionen
- [x] Setup-Script ist idempotent
- [x] Migration-Downgrades sind explizit nicht implementiert
- [x] Live-Test gegen das produktive Shared Drive (Service-Account in Railway, Drive-ID gesetzt, SA als Content-Manager eingeladen, Setup-Script: acht Folders angelegt, idempotenter Re-Run verifiziert)

## Out of Scope

Vollständige Liste in `docs/capabilities/drive.md`, Sektion 17.4.

Kurzfassung: keine Echtzeit-Kollaboration in iframe, kein eigener Virus-Scan, keine granularen Drive-ACL pro Mitglied, keine Backup-Strategie, kein Quota-Cron, keine AI/OCR-Pipelines, kein dritter «andere Kontakt-Mail»-Override.

## Cutover-Hinweis

Phase 3 implementiert die Capability technisch. Der **Live-Cutover** (Mitglieder werden zur Nutzung aufgefordert) ist von der Implementation entkoppelt und passiert mit der App-weiten MVP-Update-Mail nach Drive + iCal + Merch + System-Mail-Cutover. Bis dahin Drive-Sektion in der App hinter Feature-Flag, alter Shared Drive bleibt parallel.

## Cursor-Agent-Briefing

```
Branch: phase/03-workspace-drive-files

Lies vor Implementation: docs/capabilities/drive.md (autoritativ).
Dieses Phase-Doc ist nur der Rahmen, Details aus Capability-Doc.

Implementations-Reihenfolge gemäss Capability-Doc Sektion 17.1:
Member-Migration → Document-Migration → Service-Layer mit Tests → Routes/UI → Setup-Script.

Drei Migrationen sind separate Alembic-Commits.

Service-Account-Key NIEMALS ins Repo. env.example listet nur Variablen-Namen
GOOGLE_SERVICE_ACCOUNT_KEY (Base64) und GOOGLE_DRIVE_ID, nicht die Werte.

SVG-Sanitization ist Pflicht (Marketing-Use-Case).

UX-Texte auf Deutsch, schweizerische Schreibweise mit Guillemets («…»).
```

# Phase 9 – Drive-Browser-Refactor

**Status**: in_progress (Implementierung auf Branch; Merge/Deploy ausstehend)
**Aufwand**: ~3–5 Tage
**Branch**: `phase/09-workspace-drive-browser-refactor` (Feature-Branch; Merge-Ziel `master`)

## Ziel

Die Drive-Capability wird vom 7-Kategorien-Modell (Phase 3) auf einen **reinen Drive-Browser** umgebaut. Hintergrund: in einzelnen Kategorien werden Dokumente schnell unübersichtlich. Lösung: App folgt der Drive-Ordnerstruktur rekursiv ab dem Shared-Drive-Root, Drive ist Source of Truth für die Folder-Struktur. Mitglieder pflegen Ordner in Drive, App liest und verwaltet Dateien.

Dieser Refactor ist **Voraussetzung für den MVP-Cutover** (`DRIVE_FEATURE_ENABLED=true`) und Teil der vier MVP-Capabilities aus `docs/STRATEGY_2026.md`.

## Autoritative Spezifikation

**Source of Truth für diese Phase ist `docs/capabilities/drive.md`**, neu strukturiert per Konzeptwende 2026-05-15.

Dieses Phase-Doc ist nur der Phasen-Briefing-Rahmen. Alle Details (Folder-Modell, Datenmodell, Service-Layer, UX-Flows, Acceptance-Criteria) stehen im Capability-Doc und gelten bei Konflikt vor Aussagen in diesem Phase-Doc.

Besonders relevant: **Sektion 17 in `drive.md`** enthält die Implementations-Reihenfolge, das Cursor-Briefing und die vollständigen Acceptance-Criteria. **Sektion 5** beschreibt das neue Folder-Modell, **Sektion 6** das geschrumpfte Datenmodell, **Sektion 10** die neue UX-Flows.

## Pre-Conditions

- Phase 3 (Kategorie-Modell) ist auf `master`, `DRIVE_FEATURE_ENABLED=false`.
- Branch `phase/09-workspace-drive-browser-refactor` von `master` erstellt.
- Andreas hat das **eine Test-Dokument** in Drive und in der `documents`-Tabelle vor der Migration entfernt (siehe `drive.md` Sektion 6.4). Damit ist die Migration trocken — kein Backfill, kein Daten-Erhaltungs-Aufwand.
- Andreas hat den `/Archiv/`-Folder in Drive identifiziert und dessen Drive-File-ID notiert (für `DRIVE_ARCHIVE_FOLDER_ID`-Env-Setup nach Deployment).
- Service Account hat weiterhin Manager-Permission im Shared Drive (unverändert seit Phase 3).
- Keine Abhängigkeit zu Phase 4 (Buchhaltung) oder anderen Phasen.

## Implementations-Reihenfolge (siehe Capability-Doc Sektion 17.1)

1. **Schema-Migration: `documents` schrumpfen**
   - Neue Spalten `drive_parent_id` (String(100), NOT NULL, indexed) und `last_seen_at` (DateTime, NULL).
   - Alte Spalten droppen: `title`, `category`, `status`, `archived_at`, `archived_by_id`, `mime_type`, `size_bytes`, `checksum`, `drive_web_view_link`, `updated_at`, `last_synced_at`.
   - Alte Indexes droppen: `ix_documents_status`, `ix_documents_category`, `ix_documents_status_category`. Neuen `ix_documents_drive_parent_id` anlegen.
   - Postgres-Enum-Types `document_category` und `document_status` per `DROP TYPE IF EXISTS` aufräumen.
   - Eigener Alembic-Commit. Downgrade `raise NotImplementedError`.
2. **Service-Layer-Refactor** (`backend/services/drive_storage.py`)
   - Methoden mit `category`-Parameter umstellen auf `drive_folder_id`.
   - Neue Methoden gemäss Capability-Doc 7.1: `list_folder`, `get_folder_breadcrumb`, `search_files`, `move_document`, `get_root_id`.
   - `initialize_folder_structure`, `change_category`, `list_documents` entfernen.
   - `archive_document` nimmt `archive_folder_id` als Parameter (aus `DRIVE_ARCHIVE_FOLDER_ID`-Env gelesen).
   - `restore_document` nimmt `target_folder_id` (vom User über Folder-Picker gewählt).
   - Atomarität und Filename-/SVG-Sanitization bleiben wie in Phase 3.
   - Unit-Tests anpassen: alte Kategorie-Fixtures entfernen, Folder-ID-Fixtures einführen.
3. **Routes-Refactor** (`backend/routes/docs.py`)
   - Alte Routen `/` (mit `?tab=` Query) und `/<int:doc_id>` ersetzen durch:
     - `/` — Ordner-Übersicht (Top-Level-Tiles)
     - `/folder/<drive_folder_id>` — Ordner-Detail
     - `/file/<int:doc_id>` — optionale Detail-Seite (Audit-Historie, Event-Verknüpfung)
   - Upload-Endpoint nimmt `drive_folder_id` statt `category`.
   - Move-Endpoint nimmt `new_parent_id` (statt der bisherigen Kategorie-Wechsel-Logik).
   - Archive/Restore: Archive holt `DRIVE_ARCHIVE_FOLDER_ID` aus Env; Restore nimmt `target_folder_id` aus Modal.
4. **Templates-Refactor**
   - `templates/docs/index.html`: Tabs raus, Ordner-Tile-Grid rein. Suche oben bleibt (jetzt Drive-Volltext). «Hochladen»-Button ebenfalls oben.
   - Neues Template `templates/docs/folder.html` für Ordner-Detail: Breadcrumb, Sub-Folder-Tiles oben, Datei-Liste im Drive-Stil (Icon, Filename, Meta, Kebab-Menü).
   - Neues Partial `templates/docs/_folder_picker.html` für den Tree-View-Folder-Picker (Modal, lazy expand via Drive-API).
   - Datei-Listen-Eintrag-Partial mit Lucide-Icons pro MIME-Type-Gruppe (PDF, Office, Image, Generic).
   - `templates/docs/detail.html` als schlanke Audit-Historie + Event-Verknüpfung; primäre Aktionen wandern ins Kebab-Menü der Liste.
   - BEM-Klassen und Design-Tokens gemäss `docs/UI.md`.
5. **Setup-Script & Env**
   - `scripts/setup_drive.py` entfernen (oder mit Deprecation-Header versehen).
   - `env.example` ergänzen um `DRIVE_ARCHIVE_FOLDER_ID=`.
   - `docs/ARCHITECTURE.md` Drive-Sektion auf das neue Modell aktualisieren (eigener kleiner Commit).
6. **Tests, Doc-Sync, Initiative-README**
   - Pytest-Suite grün, neue Tests für `list_folder`, `get_folder_breadcrumb`, `move_document`.
   - `docs/initiatives/workspace-railway/README.md` Status-Tabelle: Phase 9 auf `done`, Datum eintragen.
   - Commit-Message-Vorschlag erstellen, auf User-Bestätigung warten.

## Acceptance-Criteria

Vollständige Liste in `docs/capabilities/drive.md`, Sektion 17.3.

Kurzfassung:

- [ ] `/docs/` zeigt Top-Level-Tiles = direkte Children des Shared-Drive-Roots
- [ ] Klick auf Tile → `/docs/folder/<drive_folder_id>` mit Breadcrumb, Sub-Folder-Tiles, Datei-Liste
- [ ] Datei-Listen-Eintrag: Icon, Drive-Filename, Uploader (oder «extern via Drive»), relatives Datum, Kebab
- [ ] Upload in beliebigen bestehenden Drive-Folder via Folder-Picker
- [ ] Umbenennen ändert Drive-Filename direkt; kein DB-`title`-Feld involviert
- [ ] Verschieben mit Folder-Picker bewegt File in beliebigen Folder, `drive_parent_id` aktualisiert
- [ ] Archivieren bewegt File in `DRIVE_ARCHIVE_FOLDER_ID`-Folder
- [ ] Wiederherstellen öffnet Folder-Picker, bewegt File dorthin
- [ ] Endgültig löschen (Admin, nur im Archiv) mit Filename-Copy-Bestätigung
- [ ] Volltext-Suche zeigt Treffer mit Breadcrumb-Pfad
- [ ] Re-Sync walkt rekursiv ab Root, importiert/entfernt korrekt
- [ ] Auto-Sync bei Detail-View korrigiert `drive_parent_id`-Drift silent
- [ ] AuditEvents für alle Lifecycle-Aktionen geloggt
- [ ] Bestehende Document-Records nach Migration konsistent (Andreas-Vorbereitung: 0 Records)
- [ ] `setup_drive.py` entfernt/deprecated, `env.example` enthält `DRIVE_ARCHIVE_FOLDER_ID`
- [ ] Pytest-Suite grün

## Out of Scope

Vollständige Liste in `docs/capabilities/drive.md`, Sektion 17.4.

Kurzfassung: keine App-eigene Ordner-CRUD, keine Bulk-Aktionen, keine Datei-Tags, kein Drag-and-Drop zwischen Folder-Tiles, keine Permission-Differenzierung pro Folder, keine Backup-Strategie, kein Quota-Cron, kein AI/OCR.

Daneben **nicht im Refactor-Scope** (eigene Begleit-Phase):

- Nav-Aktiv-Bug bei Profil/Einstellungen/App
- Desktop-Layout horizontal zentrieren
- Install-Banner-Fix

Diese drei UX-Polish-Punkte aus `STRATEGY_2026.md` Begleit-Verbesserungen werden separat behandelt — entweder als kleine Sammel-Phase vor oder nach Phase 9.

## Cutover-Hinweis

Phase 9 geht **nicht direkt live** für Mitglieder. `DRIVE_FEATURE_ENABLED` bleibt `false` bis:

1. Phase 9 ist gemerged und deployed.
2. UX-Polish-Punkte (Nav-Aktiv-Bug, Desktop-Zentrierung, Install-Banner-Fix) sind erledigt.
3. Andreas hat die Default-Folder-Struktur in Drive angelegt (8 Top-Level-Folder gemäss `drive.md` Sektion 5.2 oder eine vom Verein bevorzugte Variante).
4. `DRIVE_ARCHIVE_FOLDER_ID` ist als Railway-Env gesetzt.
5. Andreas hat das eine Test-Dokument entfernt (Pre-Condition).

Der eigentliche Mitglieder-Cutover passiert mit der App-weiten MVP-Update-Mail (Drive + iCal + Merch + System-Mail). Bis dahin sieht nur der Vorstand das Drive-Modul.

## Cursor-Agent-Briefing

```
Branch: phase/09-workspace-drive-browser-refactor

Lies vor Implementation: docs/capabilities/drive.md (autoritativ, neu
strukturiert 2026-05-15). Dieses Phase-Doc ist nur der Rahmen; Details
aus Capability-Doc, Sektion 17 ist die zentrale Cursor-Anleitung.

Implementations-Reihenfolge gemaess Capability-Doc Sektion 17.1:
  1. Document-Schema-Migration (trockene Migration, 0 Records)
  2. Service-Layer auf drive_folder_id umstellen
  3. Routes auf neue Pfade /docs/folder/<id> und /docs/file/<id>
  4. Templates: Tile-Grid, Ordner-Detail, Folder-Picker, Datei-Liste
  5. Setup-Script entfernen, env.example mit DRIVE_ARCHIVE_FOLDER_ID
  6. Tests, Doc-Sync, Initiative-README

Schema-Migration ist ein separater Alembic-Commit. Service-Layer,
Routes und Templates sind eigene Code-Commits.

Drive ist Source of Truth fuer Folder-Struktur und Datei-Namen. App
hat KEINE Folder-Anlegung, KEIN umbenennen von Folders, KEINE Folder-
Loeschung — diese Operationen bleiben in Drive. App verwaltet nur
Dateien (Hochladen, Umbenennen, Verschieben zwischen bestehenden
Folders, Archivieren, Wiederherstellen, Loeschen).

Datei-Titel: KEIN DB-Feld. Drive-File-Name ist die Wahrheit. Umbenennen
aendert Drive direkt via files.update.

Archiv: kein Status-Flag. Archivieren = move ins
DRIVE_ARCHIVE_FOLDER_ID-Folder. Wiederherstellen = User waehlt Ziel-
Folder per Folder-Picker.

DRIVE_FEATURE_ENABLED bleibt false nach Merge — wird erst beim
MVP-Cutover scharfgeschaltet (nach UX-Polish und Default-Folder-Setup
in Drive).

UX-Texte deutsch, schweizerische Schreibweise mit Guillemets («…»),
Doppel-S statt Eszett. Umlaute (ae/oe/ue nur wenn Programmierkontext
das erfordert, sonst ä/ö/ü). BEM-Klassen und Design-Tokens gemaess
docs/UI.md.

Lokale Verifikation:
- Migration auf lokaler Test-DB durchspielen (mit und ohne Test-Doc)
- Service-Layer-Tests gegen Mock-Drive
- Manueller Walkthrough: /docs/ → Ordner-Tile klicken → Sub-Folder
  → Upload → Umbenennen → Verschieben → Archivieren → Wiederherstellen
- Folder-Picker mit Test-Drive-Struktur (mind. 3 Ebenen tief)
- Volltext-Suche mit Test-Filenames
- Re-Sync gegen manuell modifiziertes Drive
- Nach gruener Test-Suite und Walkthrough: Acceptance-Criteria
  abhaken, Initiative-README Status-Tabelle aktualisieren,
  ARCHITECTURE.md Drive-Sektion aktualisieren, Commit-Message-
  Vorschlag, dann auf User-Bestaetigung warten.
```

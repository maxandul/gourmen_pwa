# Phase 3 – File-Storage über Infomaniak Object Storage

**Status**: pending  
**Aufwand**: ~3-4 Tage  
**Branch**: `phase/03-modules-files`

## Ziel

Echte Datei-Uploads (Belege, Bilder, Dokumente) im `Document`-Modell und neuen Routes, gespeichert in Infomaniak Object Storage (S3-kompatibel). Vorbereitung für Phase 4 (Buchhaltungs-Belege).

## Pre-Conditions

- Phase 0 abgeschlossen (Object-Storage-Bucket + ENV-Variablen `OBJECT_STORAGE_*`)
- Bucket per `aws s3 ls --endpoint=...` erreichbar
- Branch `phase/03-modules-files` von `master` erstellt

## Tasks

### 1. Dependencies

- [ ] `boto3` in `requirements.txt` aufnehmen (S3-kompatibler Client)
- [ ] `Pillow` ist bereits da (für EXIF-Strip)

### 2. Storage-Service

Datei `backend/services/storage.py`:

- [ ] Klasse `StorageService` mit `boto3` S3-Client
- [ ] Konfiguration aus `current_app.config`: `OBJECT_STORAGE_ACCESS_KEY_ID`, `OBJECT_STORAGE_SECRET_ACCESS_KEY`, `OBJECT_STORAGE_ENDPOINT`, `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_PUBLIC_URL`
- [ ] Methoden:
  - [ ] `upload(file_obj, key: str, content_type: str) -> str` – returns SHA-256-Checksum
  - [ ] `download_url(key: str, expires: int = 300) -> str` – pre-signed URL
  - [ ] `delete(key: str) -> bool`
  - [ ] `exists(key: str) -> bool`
  - [ ] `head(key: str) -> dict` – Metadata (Größe, ContentType)
- [ ] Test-Modus: wenn ENV-Vars leer, Operationen loggen statt ausführen

### 3. Document-Model erweitern

In `backend/models/document.py`:

- [ ] Neue Felder:
  - [ ] `file_key` (VARCHAR 500, nullable) – S3-Key im Bucket
  - [ ] `mime_type` (VARCHAR 100, nullable)
  - [ ] `size_bytes` (BIGINT, nullable)
  - [ ] `storage_provider` (VARCHAR 50, default `'infomaniak_object_storage'`)
  - [ ] `original_filename` (VARCHAR 500, nullable) – ursprünglicher Dateiname für Download
  - [ ] `checksum` schon da, jetzt SHA-256 verwenden
- [ ] `url`-Feld nullable machen (für File-Documents leer, weil per pre-signed URL)
- [ ] Property `is_file` (boolean) – `True` wenn `file_key` gesetzt
- [ ] Property `is_link` (boolean) – `True` wenn `url` gesetzt und `file_key` leer
- [ ] Alembic-Migration in **separatem Commit**

### 4. Upload-Route

In `backend/routes/docs.py`:

- [ ] Neue Route `POST /docs/upload`
  - [ ] `@login_required`
  - [ ] `@limiter.limit("20 per hour")`
  - [ ] Form mit `FileField` aus `flask_wtf.file`
- [ ] Validierungen:
  - [ ] **Mime-Whitelist**: PDF, JPEG, PNG, GIF, WebP, DOCX, XLSX (Liste in Config)
  - [ ] **Max-Size pro File**: 10 MB (Konfigurierbar via `MAX_FILE_SIZE_BYTES`)
  - [ ] **User-Quota**: 500 MB total pro User (Berechnung: `SUM(size_bytes)` für alle eigenen Documents)
- [ ] SHA-256 berechnen
- [ ] Bei Bildern: EXIF-Strip via Pillow (Privacy: GPS-Daten in Smartphone-Fotos entfernen)
- [ ] Duplikat-Check: bei gleichem SHA-256 vom selben User existierenden Key wiederverwenden, neuen `Document`-Eintrag mit Reference erstellen
- [ ] In Infomaniak Object Storage hochladen via `StorageService` mit Key-Pattern: `<member_id>/<sha256>/<safe_filename>`
- [ ] `Document`-Eintrag erstellen mit `file_key`, `mime_type`, `size_bytes`, `original_filename`, `checksum`
- [ ] Audit-Log (`UPLOAD_DOCUMENT`)

### 5. Download-Route

In `backend/routes/docs.py`:

- [ ] Neue Route `GET /docs/<id>/download`
  - [ ] `@login_required`
  - [ ] Permission-Check (visibility, deleted_at)
  - [ ] Bei `is_link`: Redirect auf `document.url`
  - [ ] Bei `is_file`: Pre-signed URL holen (5 Min gültig), Browser-Redirect dorthin
  - [ ] Audit-Log (`DOWNLOAD_DOCUMENT`)

### 6. Delete-Route

- [ ] `POST /docs/<id>/delete`
  - [ ] Soft-Delete: `deleted_at = now`
  - [ ] **Nicht** Object-Storage-Object löschen (Soft-Delete!)
  - [ ] Hard-Delete (Object-Storage-Object weg) erst nach 30 Tagen via separatem Cleanup-Job (optional, später)

### 7. Frontend

- [ ] `templates/docs/upload.html`
  - File-Picker (`<input type="file" accept="...">`)
  - Optional: Drag & Drop
  - Optional: Progress-Bar via XHR
  - Form-Validierung Client-seitig (size, mime)
- [ ] `templates/docs/index.html` erweitern:
  - File-Documents anders darstellen als Link-Documents (Icon, Größe, Mime)
  - Download-Button vs. extern-Link-Pfeil

### 8. Bestehende Link-Documents

- [ ] Müssen unverändert weiter funktionieren
- [ ] UI zeigt beide Document-Typen sauber unterschieden

### 9. Konfiguration

- [ ] `backend/config.py`: Object-Storage-ENV lesen, `MAX_FILE_SIZE_BYTES`, `USER_QUOTA_BYTES`, `MIME_WHITELIST`
- [ ] `env.example` aktualisieren

### 10. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: 
  - „Externe Services" Infomaniak Object Storage auf `aktiv`
  - „Bekannte Schwächen" Document-Punkt entfernen
- [ ] `docs/CONVENTIONS.md`: optional File-Upload-Pattern dokumentieren wenn neu

## Acceptance-Criteria

- [ ] User kann PDF/JPG hochladen, sieht's in Documents-Liste
- [ ] Download über Pre-signed URL funktioniert (Browser lädt direkt von Object Storage, nicht durch App)
- [ ] Mime-Whitelist greift: `.exe` wird abgelehnt
- [ ] Quota greift: 51× 10 MB nicht möglich
- [ ] Doppelter Upload (gleiches SHA-256 vom selben User) wird deduped
- [ ] EXIF von Smartphone-Foto ist im Upload entfernt (mit `exiftool` verifizieren)
- [ ] Bestehende URL-Documents funktionieren weiter
- [ ] Soft-Delete macht Document unsichtbar, Object-Storage-Object bleibt (vorerst)
- [ ] Tests grün
- [ ] DB-Migration sauber

## Out of Scope

- Kein ClamAV / Virus-Scan (kann später ergänzt werden)
- Keine Image-Resizing / Thumbnails (separate Mini-Phase)
- Keine Foto-Galerie-Ansicht
- Kein Sharing per Link an externe (nur eingeloggte User)
- Kein Hard-Delete-Job für Object Storage (kommt später)

## Cursor-Agent-Briefing

```
Branch: phase/03-modules-files
Doc: docs/initiatives/modules-and-hosting/PHASE_03_FILES.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen
- docs/CONVENTIONS.md lesen (Service-Layer, Models)
- Phase 0 abgeschlossen, Object Storage erreichbar

Implementiere Phase 3 (File-Storage auf Infomaniak Object Storage) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- Bestehende Document-Routen müssen funktionieren bleiben
- StorageService als sauber abstrahierte Schicht (austauschbar gegen MinIO später)
- Mime/Size/Quota strikt validieren
- Pillow für EXIF-Strip, nicht selbst implementieren
- Folge .cursor/rules/initiatives.mdc

Nach jedem Sub-Task lokal verifizieren mit Test-Files (klein, mittel, gross,
verschiedene Mime-Types, EXIF-haltiges Foto).

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Infomaniak Object Storage ist S3-kompatibel** – nutze `boto3` mit `endpoint_url=OBJECT_STORAGE_ENDPOINT`
- **Pre-signed URLs** funktionieren wie in AWS S3
- **Public-URL-Pattern**: wenn Bucket public ist, kann statt pre-signed auch `OBJECT_STORAGE_PUBLIC_URL/<key>` verwendet werden – aber für Vereinsdaten ist private + pre-signed sicherer
- **Key-Pattern** `<member_id>/<sha256>/<filename>` ist eindeutig + dedup-fähig
- **EXIF-Strip** via Pillow: `Image.open(...).save(buf, format=..., exif=b'')`
- **Quota-Check** vor Upload, nicht nach – sonst hochlädst du erst und löschst dann

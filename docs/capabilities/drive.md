# Capability: Vereinsdokumente in Google Shared Drive

> **Zweck**: Mitglieder verwalten Vereinsdokumente (Statuten, Protokolle, Verträge, Belege, Fotos) in der PWA – hochladen, anzeigen, organisieren, archivieren. Speicherort ist ein **Google Shared Drive**, das im Workspace-Starter-Konto `kontakt@gourmen.ch` lebt. Editieren von Office-Dokumenten erfolgt über den Drive-Web-View («Öffnen»-Aktion in der App), nicht in der App selbst.
>
> **Status**: Phase 3 (Kategorie-Modell) live auf Production seit 2026-05-13, Feature-Flag aus. **Konzeptwende 2026-05-15**: App wird vor dem MVP-Cutover vom 7-Kategorien-Modell auf einen **reinen Drive-Browser** umgebaut. **Owner**: Andreas. **Stand**: 2026-05-15.
>
> **Verwandte Docs**: `docs/STRATEGY_2026.md` (strategischer Rahmen), `docs/initiatives/workspace-railway/PHASE_03_GOOGLE_SHARED_DRIVE_FILES.md` (Phasen-Briefing für Cursor – Kategorie-Modell), `docs/ARCHITECTURE.md` (Stack-Detail).
>
> ### Konzeptwende 2026-05-15 — Drive-Browser statt fixe Kategorien
>
> Aus der Praxis-Sicht von Andreas: die sieben fixen Kategorien werden in einzelnen Bereichen schnell unübersichtlich. Lösung: die App folgt der Drive-Struktur **rekursiv**, ohne eigenes Kategorie-Modell. Top-Level der App = direkte Unterordner des Shared-Drive-Roots; Mitglieder können in Drive beliebig tief verschachteln und die App folgt.
>
> Folgen für dieses Doc:
>
> - Sektionen **5 (Folder-Struktur)**, **6 (Datenmodell)**, **7 (Service-Layer)**, **8 (Lifecycle)**, **9 (Sync)**, **10 (UX-Flows)**, **16 (Setup)** und **17 (Cursor-Briefing)** sind neu geschrieben.
> - Sektionen **3 (Auth)**, **4 (Drive-Mitgliedschaft)**, **11 (Quota/MIME)**, **12 (AI)**, **13 (Datenschutz)**, **14 (Operations)**, **15 (Verzahnung)** sind durch die Konzeptwende **nicht** betroffen und gelten unverändert.
> - Decision-Log ergänzt um Eintrag **2026-05-15**.
>
> Cursor-Auftrag für den Refactor lebt in einem neuen Phase-Doc (`PHASE_09_DRIVE_BROWSER_REFACTOR.md`, wird separat angelegt).

---

## 1. Strategie-Anker

Aus `STRATEGY_2026.md` als Source-of-Truth:

- *Vereinsdokumente* leben in Google Shared Drive («alle sehen alles»).
- *Belege* (Buchhaltung) leben im selben Shared Drive in Unterordnern – Voraussetzung für die kommende Buchhaltungs-Capability.
- *Mitglieder müssen kein bezahltes Workspace-Konto haben*, externes Sharing ist Workspace-Starter-konform.
- *Kein zusätzlicher Object Storage* (R2, Supabase) – Decision Log 2026-05-07.

Die zentrale Anforderung lautet: **Ein Klick in der App öffnet die Datei direkt zur Bearbeitung** (Browser-Tab oder PWA-In-App-Browser, beides akzeptiert). Keine Download-und-wieder-hochladen-Schleife.

## 2. User Stories

| Rolle | Story |
|---|---|
| Mitglied | «Ich lade ein PDF in die App hoch und gebe ihm einen sprechenden Titel sowie einen Ordner.» |
| Mitglied | «Ich öffne ein Statut zum Lesen oder Bearbeiten – die App leitet mich nach Google weiter.» |
| Mitglied | «Ich verschiebe ein Dokument in einen anderen Ordner, weil ich die ursprüngliche Zuordnung daneben fand.» |
| Mitglied | «Ich archiviere ein veraltetes Dokument, ohne es endgültig zu löschen.» |
| Mitglied | «Ich stelle ein versehentlich archiviertes Dokument wieder her.» |
| Vorstand | «Ich lösche ein Dokument endgültig, nachdem ich sicher bin, dass es nicht mehr gebraucht wird.» |
| Vorstand | «Ich gleiche manuell den Drive-Inhalt mit der App-DB ab, falls jemand direkt im Drive operiert hat.» |
| Mitglied | «Ich sehe die Vereinsdokumente auch in meiner Google-Drive-App auf dem Mobile-Gerät.» |

## 3. Auth-Modell

### 3.1 Service Account

Die App authentifiziert sich gegen die Drive-API über einen **Service Account**, der im GCP-Projekt `gourmen-pwa` (Owner: `kontakt@gourmen.ch`) lebt. Der Service-Account-Key (JSON) wird ausschliesslich als Railway-Secret `GOOGLE_SERVICE_ACCOUNT_KEY` (Base64-encoded) gehalten – nie im Repo, nicht in `env.example`.

Begründung: Service Account funktioniert ohne Workspace-Lizenz für Mitglieder, ohne OAuth-Refresh-Token-Maintenance, und auch headless aus Cron-Jobs (relevant für die spätere Buchhaltungs-Capability).

### 3.2 Verworfene Alternativen

- *Domain-wide Delegation*: würde nur Impersonation der einen Workspace-Identität (`kontakt@`) erlauben, was funktional gleich ist wie der Service-Account-Pfad, aber zusätzliches Setup erfordert.
- *OAuth2 pro Mitglied*: bricht das Strategie-Prinzip «Mitglieder müssen kein Google-Konto haben» und macht Cron-Jobs unmöglich.

### 3.3 Drive-API-Scope

Konfiguriert mit `https://www.googleapis.com/auth/drive` (Voll-Drive). Der enge `drive.file`-Scope reicht für Listing-Operationen über alle Folder-Inhalte nicht aus. Da der Service Account ohnehin nur Mitglied im einen Shared Drive ist, ist «Voll-Drive» effektiv auf dieses eine Drive begrenzt.

### 3.4 Operations-Hinweise

- Bus-Faktor: GCP-Projekt-Owner ist `kontakt@gourmen.ch`. Login-Daten zur Mailbox müssen im Vereins-Tresor (Bitwarden-Org oder gleichwertig) dokumentiert sein.
- Key-Rotation: alle 90 Tage neuen Service-Account-Key generieren, alten deaktivieren. Manueller Operations-Punkt.
- Schadensbegrenzung: Bei Key-Leak ist nur der eine Shared Drive betroffen. Kein anderer Workspace-Inhalt erreichbar.

## 4. Drive-Mitgliedschaft (Stufe 3)

### 4.1 Modell

**Alle aktiven Mitglieder** werden mit ihrer Google-Login-Adresse in den Shared Drive eingeladen. Dadurch:

- Direkt-Bearbeitung in Google Docs/Sheets ohne Owner-Permission-Tricks
- Direktzugriff via Mobile-Google-Drive-App
- Konsistent mit dem Strategie-Prinzip «alle sehen alles»

### 4.2 Permission-Rolle

**Alle Mitglieder erhalten die Rolle Content Manager** (Modell α): Lesen, Editieren, Hochladen, Löschen, Folder erstellen. Nicht: Drive-Settings ändern oder Mitglieder verwalten.

Begründung: Mitglieder sollen in der Lage sein, eigene Anträge oder Dokumente selbst zu korrigieren oder zurückzuziehen. Die Restriktion «Mitglieder können nicht direkt im Drive löschen» wäre paternalistisch und würde den App-Soft-Delete-Pfad zur einzigen Lösch-Stelle machen, was die Mitglieder bei Versehen ärgerlich einschränkt.

Risiko-Mitigation: App-Soft-Delete bewegt Files in `/Archiv/` (siehe Sektion 8) statt in den Drive-Papierkorb. Versehentliche Direkt-Drive-Löschungen sind durch Drive-Papierkorb (30 Tage) absorbierbar.

### 4.3 «Google-Login-Adresse» – nicht «Gmail»

Ein Google-Konto ist nicht an Gmail gebunden. Auf `accounts.google.com` kann jede beliebige E-Mail-Adresse (GMX, Hotmail, Bluewin, etc.) als Google-Login-Identität registriert werden. Mitglieder müssen also **kein Gmail-Konto** anlegen, sondern nur ihre bestehende Adresse einmalig bei Google registrieren, falls noch nicht geschehen.

Im UI heisst das Feld deshalb «Google-Login-Adresse», nicht «Gmail».

### 4.4 Pflichtfeld

Die Google-Login-Adresse (`Member.google_email`) ist **Pflichtfeld** für aktive Mitgliedschaft. Begründungen:

- Drive-Edit-Funktionalität setzt Drive-Mitgliedschaft voraus.
- Vorbereitung auf eine potenzielle spätere Auth-Migration (Strategie-2026-Future-Consideration: Auth via Google/Supabase). Keine zweite Onboarding-Welle nötig.
- Familiärer Verein, sehr selten neue Mitglieder – die Pflicht ist sozial machbar.

Falls ein Mitglied keine Google-Login-Adresse hat, ist das Anlegen einer auf accounts.google.com ein Fünf-Minuten-Vorgang und benötigt keine neue Mailbox.

### 4.5 Trennung Kontakt-Mail und Google-Login-Mail

Im Member-Modell existieren **zwei getrennte Felder**:

- `email` – Login-Identität in der App und Default-Empfänger für Vereinskommunikation
- `google_email` – Google-Login-Adresse für Drive-Mitgliedschaft

Beide können identisch sein oder unterschiedlich. Bei Mitgliedern mit GMX/Hotmail-Adresse, die als Google-Konto registriert sind, ist der typische Fall `email == google_email`.

Ein dritter Override «kontaktiere mich an einer ganz anderen Adresse» wird **bewusst nicht** in dieser Capability eingeführt – falls Bedarf entsteht, kommt er als eigenes Feature in einem späteren Profil-Refresh.

### 4.6 Verifikations-Flow

Beim Backfill (siehe Sektion 16) wird `google_email = email` gesetzt mit `google_email_verified = false`. Im Rahmen der App-weiten MVP-Update-Mail (nach Drive + iCal + Merch + System-Mail) erhält jedes Mitglied einen Verifikations-Link. Bei Klick:

1. `google_email_verified = true`, `google_email_verified_at = now`
2. Service-Layer ruft Drive-API `permissions.create` für die google_email
3. Mitglied bekommt **keine** automatische Drive-Notification von Google (`sendNotificationEmail=False`), da die Kommunikation über die App-weite Update-Mail gebündelt erfolgt.

Falls das Mitglied eine andere Adresse einträgt: Verifikations-Mail an die neue Adresse, danach Drive-Einladung.

### 4.7 Reminder bei nicht verifizierten Mitgliedern

Default ist **Geduld**. Nicht verifizierte Mitglieder verbleiben im «App-Reader-only»-Modus – sie sehen Vorschauen via Service-Account-Vermittlung, können aber nicht öffnen oder editieren.

Im Admin-Dashboard existiert eine Liste «Mitglieder ohne verifizierte Google-Adresse» mit pro-Mitglied-Knopf «Reminder-Mail senden». Kein automatischer Reminder-Cron.

### 4.8 Cleanup beim Austritt

Wenn ein Mitglied austritt:

1. Service-Layer ruft Drive-API `permissions.delete` für die google_email
2. AuditEvent `DRIVE_MEMBERSHIP_REMOVED`
3. App-Status auf inaktiv

DSGVO-relevant: Drive-Membership-Removal innerhalb von 30 Tagen nach Austritt, dokumentiert im Vereins-Datenschutz.

## 5. Folder-Struktur im Shared Drive (Drive-Browser-Modell)

### 5.1 Prinzip

Die App listet die **Drive-Ordnerstruktur rekursiv** ab dem Shared-Drive-Root. Es gibt keine fixen App-Kategorien mehr. Was als Top-Level in der App erscheint, sind die direkten Unterordner des Shared-Drive-Roots. Was als Sub-Ordner erscheint, sind die jeweiligen Drive-Sub-Folder.

**Drive ist Source of Truth** für die Folder-Struktur. Mitglieder pflegen Ordner direkt in Drive (anlegen, umbenennen, verschieben, löschen). Die App folgt automatisch — kein Sync-Cron, kein DB-Konfig-Pflege-Schritt.

### 5.2 Empfohlene Default-Struktur (Konvention, nicht App-Zwang)

Beim Initial-Setup legt der Vorstand in Drive die folgende Default-Struktur an. Sie ist eine **Empfehlung**, kein App-Zwang — Mitglieder können sie jederzeit erweitern, umbenennen oder umstrukturieren:

```
/Statuten/             – aktuelle und alte Statuten-Versionen, unterzeichnete Exemplare
/Vereinsführung/       – Vorstandsprotokolle, GV-Protokolle, Anträge, Beschlüsse
/Finanzen/             – Erfolgsrechnungen, Budgets, Revisionsberichte, Belege
/Verträge/             – externe Vereinbarungen (Sunrise, Restaurants, Versicherungen, Sponsoring)
/Reisen-und-Events/    – Reiseunterlagen, Event-Programme, Reservationsbestätigungen
/Medien/               – Logos, Grafiken (auch SVG), Vereinsfotos
/Sonstiges/            – Catch-all für Einzelstücke ohne klare Kategorie
/Archiv/               – Sammelpunkt für nicht mehr aktive Dokumente
```

Bei wachsendem Volumen kann jeder Ordner intern beliebig verschachtelt werden, z.B. `/Finanzen/2026/Belege/`, `/Vereinsführung/Protokolle/2026/`. Die App stellt diese Verschachtelung in der UI mit Breadcrumbs dar.

### 5.3 Ordner-CRUD nur in Drive

Die App **kann keine Ordner anlegen, umbenennen oder löschen**. Sie kann nur Dateien hochladen, lesen, umbenennen und zwischen **bestehenden** Ordnern verschieben. Wer Struktur ändern will, geht in Drive (Web oder Mobile-App).

Begründung: ein Pflege-Ort statt zwei. Mitglieder, die ohnehin in Drive editieren, machen Strukturarbeit dort.

### 5.4 Archiv ist Folder, nicht Status-Flag

Das `/Archiv/` ist ein normaler Drive-Folder als **Konvention**. Archivierung in der App = Move-Operation der Datei ins `/Archiv/` via Drive-API. Es gibt **kein** DB-Status-Flag mehr — der Drive-Folder-Standort ist die einzige Wahrheit.

Wiederherstellen: der User wählt einen Ziel-Folder über den Folder-Picker. Es gibt keinen «Original-Folder» mehr, da die App den ursprünglichen Standort nicht persistiert (Drive-Realität ist führend, nicht ein DB-Memorial).

Vorteile dieses Modells:
- Datenmodell wird einfacher (kein `status`-Feld, kein `archived_at`)
- Drive-Realität und App-Sicht sind immer kongruent — per Definition
- Mitglieder, die direkt im Drive browsen, sehen das Archiv natürlich
- Keine 30-Tage-Frist wie beim Drive-Papierkorb – archivierte Files bleiben unbegrenzt

### 5.5 Belege und Buchhaltung

Belege liegen weiterhin in Drive, typischerweise unter `/Finanzen/`. Im Drive-Browser-Modell sind sie für alle Mitglieder sichtbar wie alle anderen Files (Strategie «alle sehen alles»). Die Buchhaltungs-Capability arbeitet mit denselben Files via Service-Account — keine Sonder-Verstecke nötig.

### 5.6 Wurzel-Einstieg

App-Root entspricht dem konfigurierten `GOOGLE_DRIVE_ID` (der Shared Drive selbst). Top-Level-Tiles in `/docs/` sind die direkten Children dieses Shared Drives. Andreas kann jederzeit weitere Top-Level-Folder in Drive anlegen — sie erscheinen automatisch als neue Tiles.

## 6. Datenmodell (Drive-Browser-Modell)

### 6.1 `Document`-Model (geschrumpft)

```python
class Document(db.Model):
    """Schlanker DB-Cache: zeigt auf eine Drive-Datei, hält App-spezifische Beziehungen.

    Drive ist Source of Truth für Name, Folder-Standort, MIME, Grösse, Versionen.
    Die App persistiert nur, was nicht aus Drive zurückgewonnen werden kann
    (Uploader-Identität, Event-Verknüpfung, Audit-Spur).
    """
    __tablename__ = 'documents'

    id                   = db.Column(db.Integer, primary_key=True)

    # Drive-Identität (Source of Truth)
    drive_file_id        = db.Column(db.String(100), unique=True, nullable=False, index=True)
    drive_parent_id      = db.Column(db.String(100), nullable=False, index=True)
    # ^ Cache des aktuellen Parent-Folders. Wird beim Move aktualisiert,
    #   beim Auto-Sync gegen Drive geprueft.

    # App-spezifisch (kann nicht aus Drive rekonstruiert werden)
    uploader_id          = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'),
                                     nullable=True)
    event_id             = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='SET NULL'),
                                     nullable=True)

    # Sync-Helper
    last_seen_at         = db.Column(db.DateTime, nullable=True)
    # ^ Wann hat die App das File zuletzt in Drive bestaetigt gesehen?
    #   Fuer verwaiste Eintraege (in Drive geloescht, in DB noch da).

    # Timestamps
    created_at           = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

**Was wegfaellt gegenueber dem Kategorie-Modell**: `title`, `category`, `status`, `archived_at`, `archived_by_id`, `mime_type`, `size_bytes`, `checksum`, `drive_web_view_link`, `updated_at`, `last_synced_at`.

**Begruendung**:

- `title` -> Drive-File-Name ist die Wahrheit. App liest live oder via einfachen Cache pro Request.
- `category`, `status` -> beides ist Folder-Standort in Drive (siehe Sektion 5.4 zum Archiv).
- `archived_at`, `archived_by_id` -> aus AuditEvents rekonstruierbar.
- `mime_type`, `size_bytes`, `checksum` -> kommen pro Request aus Drive-API. Kein Vorteil aus dem Cache.
- `drive_web_view_link` -> deterministisch aus `drive_file_id`, kein eigenes Feld noetig.
- `updated_at`, `last_synced_at` -> ueberschneiden sich mit `last_seen_at`. Auto-Sync schreibt nur den.

### 6.2 `Member`-Erweiterung

Bleibt wie in Phase 3 implementiert (siehe `backend/models/member.py`): `google_email`, `google_email_verified`, `google_email_verified_at`. Kein neuer Migration-Schritt durch den Refactor.

### 6.3 Indexes

```sql
CREATE UNIQUE INDEX ix_documents_drive_file_id ON documents (drive_file_id);
CREATE INDEX ix_documents_drive_parent_id ON documents (drive_parent_id);
-- Alte Indexes (ix_documents_status, ix_documents_category, ix_documents_status_category) entfernen.
```

### 6.4 Migration vom Kategorie-Modell zum Drive-Browser-Modell

**Ausgangslage (Stand 2026-05-15)**: Production hat exakt **ein Test-Dokument** in der `documents`-Tabelle, hochgeladen waehrend Phase 3 fuer die Funktionsverifikation. `DRIVE_FEATURE_ENABLED=false`, also keine produktive Nutzung. Andreas-Freigabe: dieses Test-Dokument darf vor der Migration manuell entfernt werden (Drive-File loeschen + DB-Record loeschen).

Damit ist die Migration **trocken** — keine Daten-Erhaltung, kein Drive-API-Backfill, kein Mapping von Kategorien auf Folder-IDs noetig.

**Manuelle Vorbereitung (Andreas, ca. 1 Min)**:

1. Das Test-File im Drive loeschen (oder in den Drive-Papierkorb verschieben).
2. In der `documents`-Tabelle den passenden Record loeschen (oder ein `TRUNCATE TABLE documents` in der Production-DB ausfuehren — bei nur einem Record gleichwertig).

**Alembic-Migration (Cursor)**:

1. **Neue Spalten anlegen**: `drive_parent_id` (String(100), nullable=False, indexed), `last_seen_at` (DateTime, nullable=True).
2. **Alte Spalten droppen**: `title`, `category`, `status`, `archived_at`, `archived_by_id`, `mime_type`, `size_bytes`, `checksum`, `drive_web_view_link`, `updated_at`, `last_synced_at`.
3. **Alte Indexes droppen**: `ix_documents_status`, `ix_documents_category`, `ix_documents_status_category`.
4. **Neuen Index anlegen**: `ix_documents_drive_parent_id`.
5. **Enums droppen**: `DocumentCategory` und `DocumentStatus` aus dem ORM entfernen. Postgres-Enum-Types per `DROP TYPE document_category` / `DROP TYPE document_status` aufraeumen (mit `IF EXISTS` fuer Idempotenz).

**Downgrade** wird bewusst nicht implementiert (`raise NotImplementedError`) — irreversibel.

**Reihenfolge in Produktion**: Andreas-Vorbereitung (Test-Doc weg) **vor** Migration-Deployment. Falls die DB doch noch Records enthaelt, bricht die Migration sauber mit Constraint-Fehler ab — sicheres Default.

## 7. Service-Layer (`backend/services/drive_storage.py`)

### 7.1 Methoden-Skelett (Drive-Browser-Modell)

```python
class DriveStorageService:
    """Service-Layer fuer Google Shared Drive Operations.

    Authentifiziert via Service-Account-Key aus GOOGLE_SERVICE_ACCOUNT_KEY env.
    Drive ist Source of Truth fuer Folder-Struktur, Filenames und MIME.
    DB haelt nur Uploader-Identitaet, Event-Verknuepfung und Audit-Spur.
    """

    # Listing (live aus Drive)
    def list_folder(self, drive_folder_id: str) -> FolderListing: ...
    # ^ Listet direkte Children eines Drive-Folders.
    #   FolderListing enthaelt: subfolders (list von Folder-Meta),
    #   files (list von File-Meta inkl. App-Beziehungen aus DB-Join).

    def get_folder_breadcrumb(self, drive_folder_id: str) -> list[FolderRef]: ...
    # ^ Liest den Pfad vom Root bis zum gegebenen Folder (rekursiver Parent-Lookup).

    def get_root_id(self) -> str: ...
    # ^ Liefert die Shared-Drive-Wurzel-ID aus GOOGLE_DRIVE_ID.

    # Suche (live via Drive Volltext)
    def search_files(self, query: str, scope_folder_id: str | None = None) -> list[FileMeta]: ...
    # ^ Drive files.list mit q="fullText contains '...'".
    #   scope_folder_id=None -> ueber den ganzen Shared Drive.

    # Standard-CRUD
    def upload_document(self, file_stream, title: str, drive_folder_id: str,
                        uploader: Member, event: Event | None = None,
                        original_filename: str | None = None) -> Document: ...
    # ^ Laedt in den angegebenen Drive-Folder hoch (kein Kategorie-Mapping).
    #   Sanitization + Kollisions-Counter wie bisher.

    def download_document(self, document: Document) -> tuple[bytes, str]: ...
    def get_web_view_link(self, document: Document) -> str: ...
    # ^ Live aus Drive geholt, kein DB-Cache.

    # Lifecycle (alles via Drive-API, App-Aktionen)
    def archive_document(self, document: Document, archived_by: Member,
                         archive_folder_id: str) -> None: ...
    # ^ Move ins /Archiv/ (Folder-ID wird per Konfiguration uebergeben).

    def restore_document(self, document: Document, target_folder_id: str,
                         restored_by: Member) -> None: ...
    # ^ Move zurueck in einen vom User gewaehlten Folder.

    def move_document(self, document: Document, new_parent_id: str,
                      moved_by: Member) -> None: ...
    # ^ Generisches Verschieben zwischen bestehenden Drive-Folders.

    def rename_document(self, document: Document, new_filename: str,
                        renamed_by: Member) -> None: ...
    # ^ Drive files.update mit name=...; aktualisiert nur Drive, kein DB-Feld.

    def permanently_delete_document(self, document: Document,
                                    deleted_by: Member) -> None: ...

    # Sync
    def auto_sync_document(self, document: Document) -> SyncResult: ...
    # ^ Prueft beim Detail-View, ob drive_file_id noch existiert und
    #   drive_parent_id noch stimmt. Bei Drift: DB-Update.

    def admin_full_resync(self) -> ResyncReport: ...
    # ^ Walkt rekursiv den ganzen Shared Drive ab Root, listet alle Files,
    #   gleicht mit DB ab.

    # Member-Lifecycle (unveraendert)
    def invite_member_to_drive(self, member: Member) -> None: ...
    def remove_member_from_drive(self, member: Member) -> None: ...
```

**Wegfallend** gegenueber Phase 3: `initialize_folder_structure`, `change_category`, `list_documents`. Folder-Anlegung passiert in Drive (nicht in App-Code); Kategorie-Aenderung ist ein normaler `move_document`-Aufruf; Listing per Kategorie ist eine `list_folder`-Operation pro Folder-ID.

**Caching-Strategie**: `list_folder` und `get_folder_breadcrumb` ohne eigenen Cache — Drive-API ist schnell genug fuer interaktive Latenz (<300ms typisch). Falls spaeter noetig: einfacher In-Memory-LRU pro Request-Kontext.

### 7.2 Error-Handling

| Fehlerklasse | Beispiel | Verhalten |
|---|---|---|
| Transient | API-Rate-Limit (429), Netzwerk-Timeout | 3× retry mit exponential backoff (1s, 4s, 16s) via `tenacity` |
| Permanent | 404 file not found, 403 permission denied | sofort raise, kein retry |
| Quota | 403 storageQuotaExceeded | klare User-Fehlermeldung, AuditEvent `DRIVE_QUOTA_EXCEEDED` |
| Drift | Drive-Status passt nicht zu DB | Auto-Sync-Mechanismus, kein Fehler |

### 7.3 Atomarität und Failure-Recovery

Jede Schreib-Operation ist atomar implementiert:

```python
def upload_document(self, file_stream, ...) -> Document:
    drive_response = None
    try:
        drive_response = self._drive_api_upload(file_stream, ...)  # Schritt 1
        document = self._db_insert(drive_response, ...)             # Schritt 2
        return document
    except DBError:
        if drive_response:
            try:
                self._drive_api_delete(drive_response['id'])         # Rollback
            except DriveAPIError:
                pass  # verwaister File wird beim nächsten Re-Sync gefunden
        raise
```

### 7.4 Filename-Sanitization

```python
def sanitize_drive_filename(title: str, extension: str) -> str:
    import re
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '-', title)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned[:150].rstrip('. ')
    if not cleaned:
        cleaned = 'Untitled'
    return f"{cleaned}.{extension.lstrip('.')}"
```

Bei Filename-Kollision im selben Folder: Counter-Suffix `(2)`, `(3)`.

### 7.5 Member-Invite-Implementation

```python
def invite_member_to_drive(self, member: Member) -> None:
    if not member.google_email_verified:
        raise ValueError("Mitglied muss google_email verifiziert haben")

    body = {
        'type': 'user',
        'role': 'fileOrganizer',  # entspricht Content Manager
        'emailAddress': member.google_email,
    }

    try:
        self._drive.permissions().create(
            fileId=GOOGLE_DRIVE_ID,
            body=body,
            supportsAllDrives=True,
            sendNotificationEmail=False,  # Kommunikation über App-weite Update-Mail
        ).execute()
        AuditEvent.log('DRIVE_MEMBERSHIP_ADDED', actor=member, ...)
    except HttpError as e:
        AuditEvent.log('DRIVE_MEMBERSHIP_FAILED', actor=member, payload={'error': str(e)})
        raise
```

## 8. Lifecycle und Soft-Delete (Drive-Browser-Modell)

| Zustand | Drive-Realitaet | DB-Sicht | Sichtbarkeit in App |
|---|---|---|---|
| **Aktiv** | in irgendeinem Folder ausser `/Archiv/` | `drive_parent_id` zeigt dorthin | normaler Tile/Datei-Listen-Pfad |
| **Archiviert** | im `/Archiv/`-Folder (oder Sub-Folder davon) | `drive_parent_id` zeigt dorthin | sichtbar wenn User durch `/Archiv/` browst |
| **Endgueltig geloescht** | im Drive-Papierkorb | DB-Eintrag entfernt | weg, nur AuditEvent-Snapshot |

**App-Aktionen**:

- *«Archivieren»* (jedes Mitglied): `move_document` ins `/Archiv/`. `drive_parent_id` wird aktualisiert. AuditEvent `DOCUMENT_ARCHIVED` mit `from_folder_id` im Payload (fuer evtl. spaetere Forensik). Kein DB-Status-Flag mehr.
- *«Wiederherstellen»* (jedes Mitglied, wenn er im Archiv ist): Folder-Picker oeffnen, Ziel-Folder waehlen, `move_document` dorthin. AuditEvent `DOCUMENT_RESTORED`. Es gibt keinen «Original-Folder» — User muss bewusst wieder einsortieren.
- *«Endgueltig loeschen»* (**nur Admin**): Drive-API `files.update(trashed=True)`, danach DB-Hard-Delete, AuditEvent `DOCUMENT_PERMANENTLY_DELETED` mit File-Meta-Snapshot im Payload.

Drive-Papierkorb hat einen 30-Tage-Wiederherstellungs-Pfad. Falls innerhalb dieser Zeit ein Restore noetig wird, geschieht dies via Drive-Web-UI durch den Admin (manueller Recovery-Schritt — kein App-Feature).

**Konvention `/Archiv/`-Folder-ID**: wird einmalig in einer App-Konfiguration (env oder DB-Singleton) gehalten — `DRIVE_ARCHIVE_FOLDER_ID`. Wenn Andreas den Archiv-Folder in Drive umbenennt oder verschiebt, muss diese ID synchron gehalten werden. Bei einem zukuenftigen Refactor koennte die App das per Name-Lookup selbst finden, aber im MVP genuegt die explizite ID.

## 9. Sync-Modell (Drive-Browser-Modell)

### 9.1 Drive ist Source of Truth, DB ist duenner Cache

Im Drive-Browser-Modell ist Drift weniger problematisch als im Kategorie-Modell — die meisten «Drift»-Faelle (User benennt File in Drive um, verschiebt es in einen Sub-Folder) sind im neuen Modell schlicht **erwartetes Verhalten**. Listing-Operationen lesen ohnehin live aus Drive; nur die Document-Beziehungen (Uploader, Event-Verknuepfung) liegen in der DB.

Drift im engeren Sinn betrifft also nur:

- File wird in Drive geloescht -> DB-Eintrag wird verwaist
- File wird in Drive hochgeladen -> kein DB-Eintrag existiert (Uploader unbekannt)
- `drive_parent_id`-Cache ist veraltet (nach Direct-Drive-Move)

### 9.2 Auto-Sync passiv

- Beim Aufruf der Detail-View: pruefen, ob `drive_file_id` noch existiert; falls nicht, DB-Eintrag loeschen + AuditEvent `DOCUMENT_AUTO_REMOVED`. Falls existiert, aber `drive_parent_id` weicht ab: silent korrigieren, `last_seen_at` setzen.
- Beim Folder-List-View: Drive-API liefert die Liste live. Files, die in Drive da sind aber keinen DB-Eintrag haben, werden in der Anzeige mit «Hochgeladen extern via Drive» beschriftet (kein automatischer DB-Insert beim List — das macht der Re-Sync).

### 9.3 Manueller Re-Sync

Im Admin-Dashboard ein Button «Drive synchronisieren». Klick oeffnet Modal mit Erklaerung. Nach Bestaetigung walkt `admin_full_resync` den Shared Drive rekursiv ab Root und gleicht mit DB ab. Summary-Toast nach Lauf.

Drift-Behandlung beim manuellen Re-Sync:

| Situation | Drive | DB | Auto-Aktion |
|---|---|---|---|
| Verschoben (in anderen Folder) | in anderem Folder | `drive_parent_id` veraltet | DB-Update |
| Umbenannt | neuer Name | (kein Name in DB) | nichts noetig — Drive ist Wahrheit |
| Direkt-geloescht | im Drive-Papierkorb | Eintrag verwaist | DB-Eintrag entfernen, AuditEvent `DOCUMENT_AUTO_REMOVED` |
| Neu hochgeladen | File in Folder | kein DB-Eintrag | Neuer Document-Record, `uploader_id=NULL` (extern via Drive), AuditEvent `DOCUMENT_AUTO_IMPORTED` |

## 10. UX-Flows (Drive-Browser-Modell)

### 10.1 Sprache in der UI

Da das Datenmodell keine eigene `category` mehr kennt, vereinfacht sich die UI-Sprache:

| Konzept | UI-Label |
|---|---|
| Drive-Folder | «Ordner» |
| Detail-View-Aktion | «Details» |
| In anderen Ordner schieben | «Verschieben» |
| Drive-Web oeffnen | «In Drive oeffnen» |
| Drive-Filename aendern | «Umbenennen» |
| Pfad-Anzeige | Breadcrumb «Dokumente › Finanzen › 2026» |

### 10.2 Routing und Pfade

- `/docs/` → **Ordner-Uebersicht**: Top-Level-Tiles = direkte Children des Shared-Drive-Roots.
- `/docs/folder/<drive_folder_id>` → **Ordner-Detail**: Sub-Folder-Tiles oben (falls vorhanden), Datei-Liste darunter.
- `/docs/file/<doc_id>` → optionale Detail-Seite (nur fuer Audit-Historie und Event-Verknuepfung; primaere Aktionen liegen inline im Kebab-Menue).

`drive_folder_id` ist die Drive-File-ID des Folders, ein stabiler Identifier — Folder-Umbenennen in Drive bricht keine Links.

### 10.3 Ordner-Uebersicht (`/docs/`)

**Layout**: oben Suche und «Hochladen»-Button, darunter Grid mit Ordner-Tiles.

- Desktop: 3-4 Spalten Tile-Grid, horizontal zentriert.
- Mobile: 2 Spalten.

**Tile-Inhalt**:

- Lucide `folder`-Icon, einheitlich (Brand-Primary-Akzent)
- Folder-Name (Drive-Name)
- Klein darunter: «X Dokumente» (Anzahl direkter Children, inkl. Sub-Folder + Files)

**Sortierung**: alphabetisch nach Folder-Name, ausser `/Archiv/` — der Archiv-Tile haengt visuell gedaempft am Ende des Grids (eigene Background-Farbe, leicht reduzierte Opacity), egal wo er alphabetisch eingeordnet waere.

**Suche**: Volltext via Drive-API (`fullText contains`). Eingabe + Submit zeigt eine flache Treffer-Liste mit Breadcrumb pro Treffer («Finanzen › 2026 › Beleg-XYZ.pdf»). Klick auf Treffer oeffnet den enthaltenden Folder; Klick auf den Datei-Titel oeffnet sie direkt in Drive.

### 10.4 Ordner-Detail (`/docs/folder/<id>`)

**Layout**:

```
[<- Zurueck]   Breadcrumb: Dokumente › Finanzen › 2026     [Hochladen] [In Drive oeffnen]

[Suche im Ordner]    [Sortieren: Datum / Name]

Unterordner (falls vorhanden)
  [Folder-Tile]  [Folder-Tile]  [Folder-Tile]

Dateien
  [Icon] Bilanz_2026.pdf                      uploaded by Andreas    12.05.2026     [⋮]
  [Icon] Erfolgsrechnung_2026.xlsx            uploaded by Markus     10.05.2026     [⋮]
  ...
```

**Datei-Listen-Eintrag** (Drive-Stil):

- Dateityp-Icon (PDF / DOCX / XLSX / Image / Generic basierend auf Drive-MIME)
- Drive-Filename (klick = «In Drive oeffnen» in neuem Tab)
- Klein: Uploader (oder «extern via Drive»), Datum (relatives Format «vor 3 Tagen», Tooltip mit absolutem Datum)
- Kebab-Menue rechts mit Aktionen

**Kebab-Aktionen** pro Datei:

- «In Drive oeffnen» (default-Click auf den Titel macht dasselbe, hier explizit nochmal)
- «Herunterladen»
- «Umbenennen» (Modal mit aktuellem Filename, neuer eintippen, Submit ruft Drive-API)
- «Verschieben» (Modal mit Folder-Picker, siehe 10.7)
- «Archivieren» (Bestaetigung, dann Move ins `/Archiv/`)
- «Endgueltig loeschen» (nur Admin, im `/Archiv/`-Kontext sichtbar — siehe 10.8)
- «Details» (zur Detail-Seite, wenn man Audit-Historie oder Event-Verknuepfung sehen will)

### 10.5 Upload

```
Member klickt «Hochladen» (auf Uebersicht oder im Ordner-Detail)
  → Modal mit:
       Datei (file-Picker oder Drag-and-Drop-Zone auf Desktop)
       Filename (Vorschlag = original filename, editierbar)
       Ordner (Folder-Picker; vorausgewaehlt = aktuell geoeffneter Folder
               oder Shared-Drive-Root, wenn von der Uebersicht aus)
       Event (optional, Dropdown wie heute)
  → Frontend-Validierung (Groesse ≤ 100 MB, MIME aus Allowlist)
  → POST /docs/upload (multipart, enthaelt drive_folder_id)
  → Service-Layer: sanitize_filename → Drive-Upload → DB-Insert → AuditEvent
  → Erfolgsmeldung, neu hochgeladenes File erscheint in der Liste
```

Wenn der User von einem Sub-Folder ausgeloest hat: dieser ist vorausgewaehlt, kann aber im Picker geaendert werden.

### 10.6 Datei-Detail-Seite (`/docs/file/<id>`)

Nur fuer die App-spezifischen Informationen — der primaere Daten-Inhalt liegt in Drive:

```
[<- Zurueck zum Ordner]   Drive-Pfad: Dokumente › Finanzen › 2026

Bilanz_2026.pdf                          [In Drive oeffnen] [Herunterladen]

Uploader: Andreas, 12.05.2026
Event-Verknuepfung: GV 2026 (klickbar)

Audit-Historie:
  12.05.2026  hochgeladen von Andreas
  13.05.2026  umbenannt von «Bilanz_v2.pdf» zu «Bilanz_2026.pdf»
```

Aktionen-Sekundaerleiste (klein): Umbenennen, Verschieben, Archivieren. Alle gleichberechtigt zum Kebab-Menue im Listing.

### 10.7 Folder-Picker

Modal mit Tree-View des Shared-Drive-Inhalts:

```
Verschieben nach...

  [Suche im Tree]

  ▾ Dokumente (Shared Drive)
    ▸ Statuten
    ▾ Finanzen
      ▾ 2026
        ▸ Belege
      ▸ 2025
    ▸ Vertraege
    ▸ Reisen-und-Events
    ▸ Medien
    ▸ Sonstiges
    ▸ Archiv

  [ Abbrechen ]      [ Hierher verschieben ]
```

Tree wird lazy expandiert (Drive-API `files.list` pro Klick auf einen Folder). Der aktuell-Container des Files ist ausgegraut (kein Move auf sich selbst).

### 10.8 Endgueltig loeschen (Admin)

Sichtbar nur fuer Admins, **wenn** das File aktuell im `/Archiv/`-Folder (oder Sub-Folder davon) liegt. Pro Eintrag «Endgueltig loeschen»-Button mit Bestaetigungs-Modal:

```
Endgueltig loeschen

Das folgende Dokument wird in den Drive-Papierkorb verschoben und nach
30 Tagen permanent geloescht.

  ┌──────────────────────────────────┐
  │  Bilanz_2024_Entwurf_v3.pdf      │   [Filename kopieren]
  └──────────────────────────────────┘

Tippe oder fuege den Filename hier ein, um zu bestaetigen:
  ┌──────────────────────────────────┐
  │                                  │
  └──────────────────────────────────┘

  [ Abbrechen ]              [ Loeschen ]
```

### 10.9 Re-Sync (Admin)

Unveraendert in Funktion gegenueber Phase 3 — siehe Sektion 9.3 fuer die Drift-Behandlung.

## 11. Quotas, MIME-Whitelist, Validierung

### 11.1 Datei-Grössen-Limit

**100 MB pro Datei** als Hard-Limit. Deckt die übergrosse Mehrheit realer Vereinsdokumente ab. Videos werden bewusst nicht unterstützt – Verein soll Video-Material auf YouTube unlisted ablegen und Link in der Document-Beschreibung hinterlegen.

### 11.2 MIME-Allowlist

```python
ALLOWED_MIME_TYPES = {
    # Office & PDF
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',

    # Text
    'text/plain',
    'application/rtf',

    # Bilder
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/heic',
    'image/heif',

    # Vektorgrafik (mit Sanitization-Pflicht)
    'image/svg+xml',

    # Google-native (falls Direkterstellung im Drive)
    'application/vnd.google-apps.document',
    'application/vnd.google-apps.spreadsheet',
    'application/vnd.google-apps.presentation',
}
```

**Bewusst ausgeschlossen**: ZIP/RAR (Container-Risiko), Executables (`.exe`, `.bat`, `.msi`, `.jar`, `.js`, `.py`, `.sh`).

### 11.3 SVG-Sanitization

SVG ist erlaubt (Marketing-Bedarf für Merch), aber jeder Upload mit `mime_type=image/svg+xml` durchläuft eine Sanitization-Schicht **vor** dem Drive-Upload:

- Strippen aller `<script>`-Tags
- Strippen aller Event-Handler-Attribute (`onclick`, `onload`, etc.)
- Strippen aller externen Verweise (`xlink:href` mit nicht-`#`-Targets)
- Verwendung einer etablierten Library (z.B. `defusedxml` plus `bleach` mit SVG-Profil oder eine SVG-spezifische Sanitizer wie `svg-sanitizer` für Python)

### 11.4 Validierungs-Pfade

Doppelte Validierung:

1. *Frontend*: `file.size` und `file.type` vor Upload-Start. Ablehnung mit klarer Fehlermeldung.
2. *Backend*: Re-Validation im Service-Layer, da Frontend manipulierbar. Bei Verstoss: 400er-Response, AuditEvent.

### 11.5 Quota-Handling

Workspace-Starter-Limit: 30 GB im Shared Drive. Realistisches Vereinsvolumen über zehn Jahre: ~5 GB.

**Reaktiv**, kein präventiver Cron-Job:

- Service-Layer fängt `403 storageQuotaExceeded` von der Drive-API ab
- Klare Fehlermeldung an User: «Drive-Speicher ist voll. Bitte wende dich an den Vorstand.»
- AuditEvent `DRIVE_QUOTA_EXCEEDED` im Audit-Log
- Admin sieht das im Audit-Log-Filter

Falls der Vereinsdrive in der Zukunft an die Grenze kommt: Workspace-Upgrade auf Standard (2 TB pro User) oder gezieltes Aufräumen alter Files.

## 12. AI/Automation – nicht im Scope

Die Strategie 2026 verlangt für jede Capability eine Sektion zu AI/Automation-Optionen. Für die Drive-Capability lautet die Antwort: **bewusst nicht im Scope**.

Begründung:

- Dokument-Volumen im Verein ist klein (geschätzt <500 Files in zehn Jahren).
- AI-Auto-Klassifikation, OCR-Indexierung, Auto-Tagging hätten messbar Implementations- und Wartungskosten ohne erkennbaren Nutzen-Hebel.
- Drive bringt eingebaute Volltext-Suche für Office-Dokumente und PDFs ohne zusätzliche AI-Schicht.
- Die spätere Buchhaltungs-Capability wird AI-Hebel für Belege spezifisch evaluieren – das ist Buchhaltungs-Doc-Scope, nicht Drive-Doc-Scope.

Re-Evaluations-Trigger: falls Volumen >2000 Files erreicht oder Mitglieder regelmässig nicht-findbare Dokumente reklamieren, kann die Sektion neu geöffnet werden.

## 13. Datenschutz

### 13.1 Was nicht ins Drive gehört

- Mitglieder-Listen mit Personendaten (Adressen, Geburtsdaten, Telefonnummern)
- Member-Akten (Beitragsausstände, persönliche Korrespondenz)
- Health-/Diet-Restriktionen einzelner Mitglieder

Diese Daten leben in der App-DB, sensible Felder via `MemberSensitive` Fernet-verschlüsselt. **Faustregel**: Drive ist für Vereinsdokumente, nicht für Personendaten.

### 13.2 Was darf ins Drive

- Statuten, Verträge, Protokolle (auch wenn Personen darin namentlich erwähnt sind – das ist Vereinsdokumentation, nicht personenbezogene Datenverarbeitung)
- Belege, Rechnungen (Geschäftspapiere)
- Vereinsanlass-Fotos (Mitgliedschaft = Konsens, wie bisher)
- Medien, Logos, Anleitungen

### 13.3 Datenschutzerklärung für Mitglieder

Wird als Google Doc in `/Vereinsführung/` angelegt und im Member-Profil-Bereich der App verlinkt. Inhalts-Stichpunkte:

- Drittanbieter Google LLC (Drive, Workspace) als Datenverarbeiter, Drittland-Transfer USA via EU-US Data Privacy Framework
- Datenkategorien: `google_email` wird an Google für Drive-Zugang weitergegeben
- Verarbeitungszweck: Vereinsdokumenten-Verwaltung und kollaborative Bearbeitung
- Speicherdauer: solange Vereinsmitgliedschaft besteht; Removal aus Drive innerhalb 30 Tagen nach Austritt
- Betroffenenrechte: Auskunft, Löschung, Widerspruch

**Vor Cutover** muss die Datenschutzerklärung durch den Vorstand erstellt und freigegeben werden. Fallbacks im Capability-Doc nicht implementiert – ist juristische Verantwortung des Vorstands.

### 13.4 Public-Seite

Die Public-Seite verarbeitet keine Mitglieder-Daten direkt und braucht **keine** mitglieder-spezifische Datenschutzerklärung. Falls künftig Tracking, Cookies oder Kontaktformulare auf der Public-Seite hinzukommen, ist das Public-Page-Capability-Scope, nicht Drive-Capability.

## 14. Operations

### 14.1 Backup-Strategie

**Im MVP keine eigene Backup-Strategie.** Begründung:

- Drive hat eingebaute Versions-Historie pro File
- Drive-Papierkorb fängt versehentliche Löschungen 30 Tage ab
- Vereins-kritische Dokumente werden nur über App-Pfad gelöscht, der Soft-Delete-Schritt ist reversibel

Re-Evaluations-Trigger: bei einem konkreten Datenverlust-Vorfall (Statuten-Verlust, Beleg-Verlust) wird ein monatliches ZIP-Backup in einen separaten Drive-Folder evaluiert. Bis dahin: Drive-Mechanismen reichen.

### 14.2 Monitoring

- Quota-Erkennung reaktiv im Service-Layer (siehe 11.5)
- AuditEvent-Filter für Drive-relevante Events:
  - `DRIVE_MEMBERSHIP_FAILED` – fehlgeschlagene Member-Invites
  - `DRIVE_QUOTA_EXCEEDED` – Speicher-Limit erreicht
  - `DOCUMENT_AUTO_SYNCED` – Drift-Korrekturen (zur Einsicht in Direkt-Drive-Aktivität)

### 14.3 Drive-Audit-Log

Workspace Starter bietet **kein** vollständiges Drive-Audit-Log (das gibt es erst ab Workspace Standard). Direkte Drive-Aktionen einzelner Mitglieder können nicht nachträglich rekonstruiert werden, ausser über den Drive-Papierkorb (Owner-Info beim soft-deleted File).

Akzeptiert für familiären Verein – persönliche Ansprache ist effektiver als formales Audit. Falls künftig Workspace-Upgrade aus anderen Gründen kommt, wird Drive-Audit aktiviert.

## 15. Verzahnung mit Folge-Capabilities

### 15.1 Buchhaltung (Q4 2026)

- Belege landen in `/Finanzen/`. Jahres-Sub-Strukturierung wird aktiviert, sobald Volumen >50 Files erreicht.
- Service-Layer-Methode `upload_document` ist generisch genug für n8n-Workflow-Aufrufe oder direkten Buchhaltungs-Service-Call.
- Buchhaltungs-spezifische AuditEvents (`BELEG_UPLOADED`, etc.) kommen ins Buchhaltungs-Doc, nicht hier.

### 15.2 GV-Admin (Q1 2027)

- GV-Protokolle, Anträge, Beschlüsse in `/Vereinsführung/`
- AI-Hebel ist für GV stark (Traktanden aus Vorjahr, Protokoll-Entwurf aus Aufzeichnung, Einladungs-Personalisierung) – wird im GV-Doc behandelt
- Drive ist Storage, nicht Workflow-Engine

### 15.3 Merch (Q3 2026)

- *Produktbilder*: bleiben gemäss Strategie 2026 im Repo unter `static/img/merch/`, nicht in Drive
- *SVG-Logos für Drucker und Sticker-Hersteller*: in Drive `/Medien/` (Marketing-Bedarf)
- *Bestell-Rechnungen, Lieferscheine*: in Drive `/Finanzen/`

## 16. Initial Setup-Workflow

> **Operativer Begleit-Doc**: `docs/capabilities/drive_setup.md` enthält die detaillierten Klick-Pfade für jeden manuellen Schritt von Andreas. Diese Sektion hier ist die Architektur-Sicht.

### 16.1 Manuelle Schritte (Andreas)

Einmalig, ~10 Minuten Aufwand:

1. `gcloud auth login` einmalig im Cursor-Terminal absolvieren (Browser-OAuth, Token wird gecached)
2. Im Drive-Web auf `kontakt@gourmen.ch` ein neues Shared Drive «Gourmen Verein» anlegen
3. `drive_id` aus URL kopieren und an Cursor weitergeben
4. Nach Schritt 5 unten: Service Account einmalig im Drive-Web zum Shared Drive einladen (Mitglieder verwalten → Service-Account-E-Mail eintragen, Rolle Manager)

### 16.2 Cursor-automatisierte Schritte

Alle anderen Schritte via Cursor-Terminal, basierend auf den manuellen Inputs:

```bash
# 1. GCP-Projekt anlegen
gcloud projects create gourmen-pwa --name="Gourmen PWA"

# 2. Drive API aktivieren
gcloud services enable drive.googleapis.com --project=gourmen-pwa

# 3. Service Account erstellen
gcloud iam service-accounts create gourmen-drive-sa \
  --display-name="Gourmen Drive Backend" \
  --project=gourmen-pwa

# 4. JSON-Key generieren
gcloud iam service-accounts keys create /tmp/sa-key.json \
  --iam-account=gourmen-drive-sa@gourmen-pwa.iam.gserviceaccount.com

# 5. Key als Railway-Secret speichern (Base64)
SA_KEY_B64=$(base64 -w 0 /tmp/sa-key.json)
railway variables set GOOGLE_SERVICE_ACCOUNT_KEY=$SA_KEY_B64
railway variables set GOOGLE_DRIVE_ID=<drive_id-aus-Schritt-3>

# 6. Lokalen Key sofort wegputzen
rm /tmp/sa-key.json
```

### 16.3 Setup-Script (obsolet im Drive-Browser-Modell)

`scripts/setup_drive.py` aus Phase 3 ist mit der Konzeptwende **obsolet**. Begruendung:

- App legt keine fixen Folder mehr an. Top-Level-Struktur wird von Andreas in Drive selbst angelegt (Web-UI, ~2 Minuten).
- Die einzige folder-spezifische Konfiguration ist `DRIVE_ARCHIVE_FOLDER_ID` — wird per Hand in Railway-Env gesetzt, sobald der `/Archiv/`-Folder in Drive existiert.

Das Script kann im Repo bleiben (mit Deprecation-Hinweis) oder im Refactor entfernt werden. Empfehlung: entfernen, weil es bei kuenftigen Restrukturierungen in Drive nicht mehr passen wuerde.

**Neuer Initial-Setup-Pfad** (manuelle Schritte des Vorstands beim ersten Drive-Aufsetzen):

1. Andreas oeffnet den Shared Drive in der Drive-Web-UI.
2. Legt die empfohlenen acht Top-Level-Folder an (oder die Struktur, die der Verein bevorzugt) — Statuten, Vereinsfuehrung, Finanzen, Vertraege, Reisen-und-Events, Medien, Sonstiges, Archiv.
3. Kopiert die Drive-File-ID des Archiv-Folders (rechtsklick → Link kopieren, ID aus URL extrahieren).
4. Setzt `DRIVE_ARCHIVE_FOLDER_ID` als Railway-Env-Variable.
5. Fertig — App folgt automatisch.

### 16.4 Cutover

Nicht im Phase-3-Liefer-Scope. Cutover passiert mit der App-weiten MVP-Update-Mail (nach Drive + iCal + Merch + System-Mail-Cutover):

- Bis dahin: alter und neuer Shared Drive existieren parallel. Neuer Drive ist nur intern für Vorstand sichtbar.
- Andreas zieht Inhalte vom alten Drive ins neue (manuell, mit überarbeiteter Folder-Struktur).
- Mit der MVP-Update-Mail: Verifikations-Klick aktiviert Drive-Membership pro Mitglied. Drive-Sektion in der App wird sichtbar.
- Karenz-Phase nach Cutover: alter Drive bleibt 4 Wochen aktiv, danach von Andreas gelöscht.

## 17. Cursor-Briefing fuer den Drive-Browser-Refactor (Phase 9)

> Phase 3 (Kategorie-Modell) ist auf Production gemerged (PR #12, 2026-05-13) mit `DRIVE_FEATURE_ENABLED=false`. Der hier beschriebene Refactor ersetzt die Kategorie-Logik durch das Drive-Browser-Modell **vor** dem MVP-Cutover.

### 17.1 Reihenfolge der Commits

| # | Commit | Inhalt |
|---|---|---|
| 1 | Schema-Migration: Document schrumpfen | Neue Spalten `drive_parent_id`, `last_seen_at` anlegen, Backfill via Drive-API, alte Spalten droppen, Enums `DocumentCategory`/`DocumentStatus` entfernen, Indexes anpassen. |
| 2 | Service-Layer-Refactor | `backend/services/drive_storage.py` von `category`-Parametern auf `drive_folder_id`-Parameter umstellen. Neue Methoden `list_folder`, `get_folder_breadcrumb`, `search_files`, `move_document`. `initialize_folder_structure` und `change_category` entfernen. |
| 3 | Routes-Refactor | `backend/routes/docs.py`: alte Routen (`/`, `/<id>`) durch `/`, `/folder/<drive_folder_id>`, `/file/<doc_id>` ersetzen. Upload-Endpoint nimmt `drive_folder_id` statt `category`. |
| 4 | Templates-Refactor | `templates/docs/index.html`: Tabs raus, Ordner-Tile-Grid rein. Neues Template `templates/docs/folder.html` fuer Ordner-Detail (Sub-Folder-Tiles + Datei-Liste). Folder-Picker-Modal-Partial. Datei-Listen-Eintrag im Drive-Stil mit Kebab-Menue. |
| 5 | Setup-Script & Env | `scripts/setup_drive.py` entfernen oder mit Deprecation-Notice versehen. `DRIVE_ARCHIVE_FOLDER_ID` in `env.example` ergaenzen. |
| 6 | Cleanup & Doc-Sync | Tests anpassen, alte Kategorie-Fixtures entfernen, `docs/ARCHITECTURE.md` (PWA-Aspekte / Drive-Sektion) auf das neue Modell ziehen. |

### 17.2 Cursor-Briefing-Block

```
Branch: phase/09-workspace-drive-browser-refactor
Lies vor Implementation: docs/capabilities/drive.md (autoritativ, neu strukturiert 2026-05-15).
Lies docs/initiatives/workspace-railway/PHASE_09_DRIVE_BROWSER_REFACTOR.md
nur fuer Rahmen, Details aus Capability-Doc.

Implementations-Reihenfolge:
  1. Document-Schema-Migration mit Drive-API-Backfill
  2. Service-Layer auf drive_folder_id-Parameter umstellen
  3. Routes auf neue Pfade umstellen
  4. Templates auf Tile + Liste + Breadcrumb umstellen
  5. Setup-Script entfernen, env.example um DRIVE_ARCHIVE_FOLDER_ID ergaenzen
  6. Tests, Doc-Sync

Drive ist Source of Truth. Folder-Struktur wird in Drive gepflegt,
App liest nur. Ordner-CRUD-Aktionen (Anlegen, Umbenennen, Loeschen
von Folders) sind in der App NICHT implementiert.

Datei-Titel wird nicht mehr in der DB persistiert — Drive-Filename ist
die Wahrheit. Umbenennen aendert Drive-File-Name via API; DB hat kein
title-Feld mehr.

DRIVE_FEATURE_ENABLED bleibt false bis das Capability-Doc auch fuer
die UI-Polish-Punkte (Nav-Aktiv-Bug, Desktop-Zentrierung,
Install-Banner-Fix — siehe STRATEGY_2026.md Begleit-Verbesserungen)
gruen ist.

UX-Texte auf Deutsch, schweizerische Schreibweise mit Guillemets («…»).
Konsequent: kein Eszett (ß), Umlaute (ä/ö/ü) verwenden.
```

### 17.3 Akzeptanzkriterien fuer den Refactor

- [ ] `/docs/` zeigt Top-Level-Tiles, die exakt den direkten Children des Shared Drives entsprechen
- [ ] Klick auf einen Tile fuehrt zu `/docs/folder/<drive_folder_id>` mit Breadcrumb und korrekter Sub-Folder-/Datei-Trennung
- [ ] Datei-Listen-Eintrag zeigt Drive-Filename, Uploader (oder «extern via Drive» wenn `uploader_id` null), relatives Datum, Kebab-Menue mit allen Aktionen
- [ ] Mitglied kann Datei in einen beliebigen bestehenden Drive-Folder hochladen (Folder-Picker im Upload-Modal)
- [ ] «Umbenennen» aendert Drive-Filename, in der App sofort sichtbar; kein DB-`title`-Feld mehr involviert
- [ ] «Verschieben» mit Folder-Picker bewegt File in beliebigen anderen Drive-Folder, `drive_parent_id` wird aktualisiert
- [ ] «Archivieren» bewegt File in den Folder mit ID `DRIVE_ARCHIVE_FOLDER_ID`
- [ ] «Wiederherstellen» (im Archiv-Kontext) oeffnet Folder-Picker und bewegt File dorthin
- [ ] «Endgueltig loeschen» (nur Admin, nur im Archiv) zeigt Bestaetigungs-Modal mit Filename-Copy
- [ ] Volltext-Suche ueber `/docs/` zeigt Treffer mit Breadcrumb-Pfad und klickbarem Folder-Sprung
- [ ] Re-Sync-Button im Admin-Dashboard walkt rekursiv ab Root, importiert neue Drive-Files (`uploader_id=NULL`), entfernt verwaiste DB-Eintraege
- [ ] Auto-Sync bei Detail-View korrigiert `drive_parent_id`-Drift silent
- [ ] DB-Insert-Fehler nach erfolgreichem Drive-Upload fuehrt zu Drive-Rollback (wie heute)
- [ ] AuditEvents fuer Upload, Move, Rename, Archive, Restore, Permanently-Delete, Auto-Import, Auto-Remove
- [ ] Bestehende Document-Records (Phase 3) sind nach Migration konsistent: `drive_parent_id` gesetzt, `last_seen_at` initialisiert, alte Spalten weg
- [ ] `setup_drive.py` ist entfernt oder mit Deprecation-Header versehen; `env.example` enthaelt `DRIVE_ARCHIVE_FOLDER_ID`

### 17.4 Out of Scope fuer den Refactor

- App-eigene Ordner-CRUD (Anlegen, Umbenennen, Loeschen) — bleibt Drive-Aufgabe
- Bulk-Aktionen (mehrere Dateien gleichzeitig verschieben/archivieren)
- Datei-Tags (orthogonale Klassifikation neben der Folder-Hierarchie)
- Drag-and-Drop zwischen Folder-Tiles im UI
- Permission-Differenzierung pro Folder (alle Mitglieder sehen alles, wie bisher)
- Backup-Strategie, Quota-Cron, AI/OCR (unveraendert out of scope)

## 18. Decision Log

| Datum | Entscheid | Begründung |
|---|---|---|
| 2026-05-09 | Service Account als Auth-Modell | Keine Workspace-Lizenz für Mitglieder nötig, headless-fähig für Cron |
| 2026-05-09 | GCP-Projekt-Owner = `kontakt@gourmen.ch` | Vereinskonto, besser für Bus-Faktor als Andreas persönlich |
| 2026-05-09 | Drive-Stufe 3 (alle Mitglieder im Drive) | Volle Strategie-Konformität «alle sehen alles» |
| 2026-05-09 | `google_email` als Pflichtfeld | Drive-Edit + Vorbereitung auf potenzielle Auth-Migration |
| 2026-05-09 | Trennung Kontakt-Mail / Google-Login-Mail | Flexibilität für Mitglieder mit GMX/Hotmail-Konten |
| 2026-05-09 | Permission-Modell α (alle Content Manager) | Gleichberechtigung, Mitglieder können eigene Anträge selbst zurückziehen |
| 2026-05-09 | `convert=false` beim Upload | Original-Format bleibt, ein Klick mehr beim Edit-Flow akzeptiert |
| 2026-05-09 | Acht Folders, flach, kein Sub-Folder-Schachteln | Einfach, deckt zehn Jahre Vereinsvolumen ab |
| 2026-05-09 | Archiv ist physischer Folder, nicht Status-Flag | Drive-Realität und App-Status immer kongruent, kein 30-Tage-Limit |
| 2026-05-09 | App-Soft-Delete = Move ins `/Archiv/` | Nutzt das Folder-Modell, keine separate Trash-Logik |
| 2026-05-09 | Endgültig-Löschen nur Admin | Sicherheitsnetz für irreversible Aktion |
| 2026-05-09 | Strict-App + Auto-Sync + manueller Re-Sync | Kein Webhook-Setup, kein Polling-Cron |
| 2026-05-09 | 100 MB pro Datei | Deckt Vereinsdokumente ab, schliesst Videos elegant aus |
| 2026-05-09 | SVG erlaubt mit Sanitization | Marketing-Bedarf für Merch |
| 2026-05-09 | Reaktives Quota-Handling, kein Cron | Bei 30 GB Limit und ~5 GB realistischem Volumen unnötig |
| 2026-05-09 | AI/Automation explizit nicht im Scope | Volumen zu klein für AI-Hebel |
| 2026-05-09 | Datenschutzerklärung im Drive, nicht Public | Mitglieder-Erklärung gehört in Mitglieder-Bereich |
| 2026-05-09 | Keine eigene Backup-Strategie initial | Drive-Versions-Historie + Papierkorb reichen |
| 2026-05-09 | Voll-Drive-API-Scope | Engerer Scope reicht für Listing nicht; effektiv auf eines Shared Drive begrenzt |
| 2026-05-09 | `sendNotificationEmail=False` bei Member-Invite | Kommunikation gebündelt über App-weite MVP-Update-Mail |
| 2026-05-09 | Cutover an MVP-Bundle-Mail gekoppelt | Eine Mail für alle Neuerungen, keine Wellen-Kommunikation |
| **2026-05-15** | **Drive-Browser statt fixe 7 Kategorien** | Aus der Praxis: 7 Kategorien werden in einzelnen Bereichen unuebersichtlich. Drive hat die Hierarchie ohnehin nativ — App folgt rekursiv, Drive ist Source of Truth fuer Folder-Struktur. |
| **2026-05-15** | **Datenmodell schrumpft drastisch** | `title`, `category`, `status`, `archived_at`, `archived_by_id`, `mime_type`, `size_bytes`, `checksum`, `drive_web_view_link`, `updated_at`, `last_synced_at` entfallen. Document ist nur noch Beziehungs-Cache (Uploader + Event + drive_parent_id). |
| **2026-05-15** | **Drive-Filename ist Document-Titel** | Keine doppelte Wahrheit zwischen App-Titel und Drive-Filename. Umbenennen aendert Drive direkt. |
| **2026-05-15** | **Ordner-CRUD nur in Drive, nicht in App** | Ein Pflege-Ort. App kann nur Dateien verwalten, Folder-Struktur ist Drive-Aufgabe. |
| **2026-05-15** | **Archiv via `DRIVE_ARCHIVE_FOLDER_ID`-Env, nicht via Name-Lookup** | Pragmatisch im MVP. Wenn Andreas den Archiv-Folder umbenennt, muss die Env nachgezogen werden. Bewusste Vereinfachung. |

## 19. Offene Punkte und Trade-offs

- *Mitglied ohne Google-Konto-Adresse*: Pflichtfeld bedeutet, dass diese Mitglieder de facto blockiert sind. Sozial bei familiärem Verein zumutbar, aber pro Edge-Case Sonderlösung möglich (nur App-Reader-Modus mit ausgegrauten Edit-Aktionen).
- *Drive-Audit-Log-Limitierung*: Workspace Starter hat kein vollständiges Audit. Falls in der Zukunft Workspace-Upgrade kommt, eingebaute Audit-Funktion aktivieren.
- *Auto-Sync-Performance*: Detail-View löst leichten API-Check aus. Bei sehr viel Detail-View-Traffic könnte das Drive-API-Quotas berühren – nicht heute relevant, im Auge behalten.
- *Fallback bei verwaisten Files vom System-Sync*: Auto-Sync importiert neue Drive-Files mit `uploader_id = NULL`. Im UI mit «Hochgeladen extern via Drive» beschriften.
- *List-Folder-Performance bei grossen Folders*: Drive `files.list` mit Pagination unterstuetzt, aber wenn ein Folder >1000 Files hat, koennen mehrere API-Calls noetig sein. Im MVP nicht relevant; bei Bedarf serverseitiges Paging im Template einbauen.
- *DRIVE_ARCHIVE_FOLDER_ID-Drift*: Wenn der Vorstand den `/Archiv/`-Folder in Drive umbenennt oder verschiebt, bleibt die Env-Variable trotzdem gueltig (Folder-ID ist stabil). Wenn der Folder ganz geloescht wird, bricht die Archivieren-Aktion — Health-Check beim App-Start, Fail-Fast mit Admin-Notice.
- *Folder-Picker bei sehr tiefer Hierarchie*: Tree-View kann mobile unhandlich werden. Falls Tiefe >4 Ebenen, evtl. ein separater Modal-Pfad (Breadcrumb-basierte Navigation) statt Tree.

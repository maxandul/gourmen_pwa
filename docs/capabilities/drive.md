# Capability: Vereinsdokumente in Google Shared Drive

> **Zweck**: Mitglieder verwalten Vereinsdokumente (Statuten, Protokolle, Verträge, Belege, Fotos) in der PWA – hochladen, anzeigen, organisieren, archivieren. Speicherort ist ein **Google Shared Drive**, das im Workspace-Starter-Konto `kontakt@gourmen.ch` lebt. Editieren von Office-Dokumenten erfolgt über den Drive-Web-View («Öffnen»-Aktion in der App), nicht in der App selbst.
>
> **Status**: Konzept abgeschlossen, bereit für Phase-3-Implementation. **Owner**: Andreas. **Stand**: 2026-05-09.
>
> **Verwandte Docs**: `docs/STRATEGY_2026.md` (strategischer Rahmen), `docs/initiatives/workspace-railway/PHASE_03_GOOGLE_SHARED_DRIVE_FILES.md` (Phasen-Briefing für Cursor), `docs/ARCHITECTURE.md` (Stack-Detail).

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

## 5. Folder-Struktur im Shared Drive

### 5.1 Acht Top-Level-Folders

```
/Statuten/             – aktuelle und alte Statuten-Versionen, unterzeichnete Exemplare
/Vereinsführung/       – Vorstandsprotokolle, GV-Protokolle, Anträge, Beschlüsse
/Finanzen/             – Erfolgsrechnungen, Budgets, Revisionsberichte, Belege (später)
/Verträge/             – externe Vereinbarungen (Sunrise, Restaurants, Versicherungen, Sponsoring)
/Reisen-und-Events/    – Reiseunterlagen, Event-Programme, Reservationsbestätigungen
/Medien/               – Logos, Grafiken (auch SVG), Vereinsfotos
/Sonstiges/            – Catch-all für Einzelstücke ohne klare Kategorie
/Archiv/               – Sammelpunkt für nicht mehr aktive Dokumente
```

Alle Folders sind direkt im Shared-Drive-Root, **flach**. Keine initialen Sub-Folders. Jahresordner (`/Finanzen/2026/`, `/Vereinsführung/2026/`) werden erst aktiviert, wenn ein Folder die Schwelle von ~200 Files überschreitet – das ist bei eurem Volumen nicht im MVP-Horizont.

### 5.2 Folder-Modell-Wahl

**Modell B Mini**: App schreibt jeden Upload automatisch in den Folder, der zur Kategorie passt. DB-`category` ist Source of Truth, Drive-Folder ist deterministische Spiegelung.

Re-Klassifikation (User klickt «Verschieben»): Service-Layer ruft Drive-API `files.update` mit `addParents`/`removeParents` plus DB-Update. Atomar.

### 5.3 Archiv ist Folder, nicht Status-Flag

Das `/Archiv/` ist ein normaler Drive-Folder mit denselben α-Permissions wie die Aktiv-Folders. Archivierung = Move ins `/Archiv/` plus DB-Update auf `status='archived'`. Die Original-Kategorie bleibt im DB-Feld erhalten, damit beim Wiederherstellen klar ist, in welchen Aktiv-Folder zurückzulegen ist.

Vorteile dieses Modells:
- Drive-Realität und App-Status sind immer kongruent
- Mitglieder, die direkt im Drive browsen, sehen das Archiv natürlich
- Keine 30-Tage-Frist wie beim Drive-Papierkorb – archivierte Files bleiben unbegrenzt

## 6. Datenmodell

### 6.1 `Document`-Model (Redesign)

```python
class DocumentCategory(Enum):
    STATUTEN          = 'STATUTEN'
    VEREINSFUEHRUNG   = 'VEREINSFUEHRUNG'
    FINANZEN          = 'FINANZEN'
    VERTRAEGE         = 'VERTRAEGE'
    REISEN_EVENTS     = 'REISEN_EVENTS'
    MEDIEN            = 'MEDIEN'
    SONSTIGES         = 'SONSTIGES'

class DocumentStatus(Enum):
    ACTIVE   = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

class Document(db.Model):
    __tablename__ = 'documents'

    id                   = db.Column(db.Integer, primary_key=True)
    title                = db.Column(db.String(200), nullable=False)
    category             = db.Column(db.Enum(DocumentCategory), nullable=False, index=True)
    status               = db.Column(db.Enum(DocumentStatus), nullable=False,
                                     default=DocumentStatus.ACTIVE, index=True)

    # Drive-Identität
    drive_file_id        = db.Column(db.String(100), unique=True, nullable=False, index=True)
    drive_web_view_link  = db.Column(db.String(500), nullable=True)

    # Datei-Metadaten
    mime_type            = db.Column(db.String(100), nullable=True)
    size_bytes           = db.Column(db.BigInteger, nullable=True)
    checksum             = db.Column(db.String(64), nullable=True)

    # Beziehungen
    event_id             = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='SET NULL'),
                                     nullable=True)
    uploader_id          = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'),
                                     nullable=False)

    # Lifecycle
    archived_at          = db.Column(db.DateTime, nullable=True)
    archived_by_id       = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'),
                                     nullable=True)

    # Sync-Helper
    last_synced_at       = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at           = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at           = db.Column(db.DateTime, default=datetime.utcnow,
                                     onupdate=datetime.utcnow)
```

**Wegfallende Felder** aus dem alten Schema: `url`, `visibility`, `deleted_at`. Bestehende URL-only-Records werden vor Migration komplett gelöscht (Andreas-Freigabe: «alles bisher verwerfen»).

### 6.2 `Member`-Erweiterung

```python
# Ergänzung in models/member.py
google_email             = db.Column(db.String(120), nullable=True, index=True)
google_email_verified    = db.Column(db.Boolean, default=False, nullable=False)
google_email_verified_at = db.Column(db.DateTime, nullable=True)
```

Verifikations-Token werden in der bestehenden `auth_tokens`-Tabelle mit neuem `purpose='google_email_verify'` abgelegt – konsistent zum Pattern für Password-Reset, Onboarding, 2FA-Reset.

### 6.3 Indexes

```sql
CREATE UNIQUE INDEX ix_documents_drive_file_id ON documents (drive_file_id);
CREATE INDEX ix_documents_status ON documents (status);
CREATE INDEX ix_documents_category ON documents (category);
CREATE INDEX ix_documents_status_category ON documents (status, category);
```

### 6.4 Migration

Drei separate Alembic-Commits in Phase 3:

1. **Member-Schema-Erweiterung**: `google_email`-Felder.
2. **Document-Schema-Redesign**: alte Records löschen, alte Spalten droppen, neue Spalten anlegen, Enum-Werte aktualisieren.
3. **Token-Purpose-Erweiterung**: `google_email_verify` als neuer Wert im Token-Purpose-Enum.

Downgrade ist bewusst nicht implementiert (`raise NotImplementedError`), weil Drive-Verknüpfungen nicht reversibel sind.

## 7. Service-Layer (`backend/services/drive_storage.py`)

### 7.1 Methoden-Skelett

```python
class DriveStorageService:
    """Service-Layer für Google Shared Drive Operations.

    Authentifiziert via Service-Account-Key aus GOOGLE_SERVICE_ACCOUNT_KEY env.
    Alle Operationen sind atomar (Drive + DB) oder werfen explizite Fehler.
    """

    # Setup / Bootstrap (von scripts/setup_drive.py genutzt)
    def initialize_folder_structure(self, drive_id: str) -> dict[DocumentCategory, str]: ...

    # Standard-CRUD
    def upload_document(self, file_stream, title: str, category: DocumentCategory,
                        uploader: Member, event: Event | None = None,
                        original_filename: str | None = None) -> Document: ...
    def download_document(self, document: Document) -> tuple[bytes, str]: ...
    def get_web_view_link(self, document: Document, refresh: bool = False) -> str: ...

    # Lifecycle
    def archive_document(self, document: Document, archived_by: Member) -> None: ...
    def restore_document(self, document: Document, restored_by: Member) -> None: ...
    def permanently_delete_document(self, document: Document, deleted_by: Member) -> None: ...
    def change_category(self, document: Document, new_category: DocumentCategory,
                        changed_by: Member) -> None: ...
    def rename_document(self, document: Document, new_title: str, renamed_by: Member) -> None: ...

    # Listing / Query (reine DB-Queries)
    def list_documents(self, category: DocumentCategory | None = None,
                       status: DocumentStatus = DocumentStatus.ACTIVE) -> list[Document]: ...

    # Sync
    def auto_sync_document(self, document: Document) -> SyncResult: ...
    def admin_full_resync(self) -> ResyncReport: ...

    # Member-Lifecycle
    def invite_member_to_drive(self, member: Member) -> None: ...
    def remove_member_from_drive(self, member: Member) -> None: ...
```

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

## 8. Lifecycle und Soft-Delete (Drei-Stufen-Modell)

| Zustand | Drive-Realität | DB-Status | Sichtbarkeit in App |
|---|---|---|---|
| **Aktiv** | in einem der sieben Aktiv-Folders | `status = ACTIVE` | Standard-Liste |
| **Archiviert** | im `/Archiv/`-Folder | `status = ARCHIVED` | Tab/Filter «Archiv» |
| **Endgültig gelöscht** | im Drive-Papierkorb | DB-Eintrag entfernt | weg, nur AuditEvent-Snapshot |

**App-Aktionen**:

- *«Archivieren»* (jedes Mitglied): File-Move ins `/Archiv/`, `status=ARCHIVED`, `archived_at` und `archived_by_id` gesetzt, AuditEvent `DOCUMENT_ARCHIVED`.
- *«Wiederherstellen»* (jedes Mitglied im Archiv-View): File-Move zurück in den Original-Folder (aus `category` abgeleitet), `status=ACTIVE`, `archived_at=NULL`, AuditEvent `DOCUMENT_RESTORED`.
- *«Endgültig löschen»* (**nur Admin**, im Archiv-View sichtbar): Drive-API `files.update` mit `trashed=true`, danach DB-Hard-Delete, AuditEvent `DOCUMENT_PERMANENTLY_DELETED` mit Document-Snapshot im Payload (für die nachträgliche Forensik).

Drive-Papierkorb hat einen 30-Tage-Wiederherstellungs-Pfad. Falls innerhalb dieser Zeit ein Restore nötig wird, geschieht dies via Drive-Web-UI durch den Admin (manueller Recovery-Schritt – kein App-Feature).

## 9. Sync-Modell

### 9.1 Strict-App im Default

App-Operationen sind atomar. Nach jedem `upload_document` / `archive_document` / `change_category` / etc. sind Drive und DB konsistent. **Kein** Sync-Mechanismus für den Normalbetrieb nötig.

### 9.2 Auto-Sync für Drift

Drift entsteht nur, wenn jemand **direkt im Drive** operiert (Drive-Web, Mobile-App). Die App fängt das passiv ein:

- Beim Aufruf der Detail-View eines Documents: leichter API-Check, ob `drive_file_id` noch existiert und der Folder-Pfad noch zu `category`+`status` passt. Bei Drift: silentes Auto-Sync, DB folgt Drive.
- Beim List-View: kein API-Call, nur DB-Query (Performance).

### 9.3 Manueller Re-Sync

Im Admin-Dashboard ein Button «Drive synchronisieren». Klick öffnet Modal mit Erklärung («Was macht das? Was passiert dabei? Dauer?»). Nach Bestätigung läuft `admin_full_resync` über alle acht Folders, gleicht mit DB ab und meldet Summary («3 neue Dokumente importiert, 1 verwaister Eintrag bereinigt, 0 Konflikte»).

Drift-Behandlung beim manuellen Re-Sync:

| Situation | Drive | DB | Auto-Aktion |
|---|---|---|---|
| Verschoben | in anderem Aktiv-Folder | falsche `category` | DB-Update |
| Archiviert | in `/Archiv/` | `status=ACTIVE` | DB auf `archived` |
| Wiederhergestellt | in Aktiv-Folder | `status=ARCHIVED` | DB auf `active` |
| Direkt-gelöscht | im Drive-Papierkorb | Eintrag verwaist | DB-Eintrag entfernen, AuditEvent `DOCUMENT_AUTO_SYNCED` |
| Neu hochgeladen | File in Folder | kein DB-Eintrag | Neuer Document-Record erzeugt, Uploader auf «System» (kein Member-Match) |

## 10. UX-Flows

### 10.1 Sprache in der UI

DB-Spalten heissen weiterhin englisch (`category`, `status`), die UI-Labels werden auf Deutsch und benutzerfreundlich gewählt:

| DB-Konzept | UI-Label |
|---|---|
| `category` | «Ordner» |
| Detail-View-Aktion | «Details» |
| Kategorie ändern | «Verschieben» |
| Edit-Action (Drive-Web öffnen) | «Öffnen» |
| Titel ändern | «Umbenennen» |

### 10.2 Upload

```
Member klickt «Dokument hochladen» (im Documents-Index oder Event-Detail)
  → Modal mit Feldern:
       Datei (file-Picker oder Drag-and-Drop-Zone auf Desktop)
       Titel (Pflicht, Vorschlag = Filename ohne Extension)
       Ordner (Dropdown, sieben Aktiv-Kategorien)
       Event (optional, Dropdown, vorausgewählt aus Event-Context)
  → Frontend-Validierung (Dateigrösse ≤ 100 MB, MIME aus Allowlist)
  → POST /documents/upload (multipart)
  → Service-Layer: sanitize_filename → Drive-API-Upload → DB-Insert → AuditEvent
  → Erfolgsmeldung, Dokument erscheint in Liste
```

Drag-and-Drop wird auf Desktop unterstützt (HTML5-API, Drop-Zone mit Hover-Feedback). Auf Mobile bleibt der File-Picker Standard.

### 10.3 Listing

Hauptansicht `/documents`:

- *Tab-Leiste*: Alle / Statuten / Vereinsführung / Finanzen / Verträge / Reisen-und-Events / Medien / Sonstiges / Archiv
- *Suche*: Titel-Suche (DB-Query, kein Drive-API-Call)
- *Sortierung*: Datum (neueste zuerst, default), alphabetisch
- *Liste*: Titel, Ordner, Uploader, Datum, MIME-Icon, Aktionen-Dropdown

Pro Eintrag drei Aktionen:

- «Details» – zur Detail-Seite
- «Öffnen» – `target="_blank"` zu `webViewLink`
- Aktionen-Menü: «Verschieben», «Umbenennen», «Archivieren»

### 10.4 Detail-Seite

```
Titel (read-only, separate Aktion «Umbenennen» darüber)
Metadaten: Ordner, Uploader, Datum, MIME, Grösse
Event-Verknüpfung (klickbar) wenn vorhanden
Buttons: Download, Öffnen, Verschieben, Umbenennen, Archivieren
Audit-Historie: letzte fünf AuditEvents zu diesem Document
```

### 10.5 Archivieren / Wiederherstellen

Archivieren: einfache Bestätigung («Dokument wird ins Archiv verschoben, kann jederzeit wiederhergestellt werden»). Reversibel, kein Drama.

Wiederherstellen: im Archiv-Tab pro Eintrag «Wiederherstellen»-Button, ein Klick.

### 10.6 Endgültig löschen (Admin)

Sichtbar nur in der Admin-Ansicht des Archiv-Tabs. Pro Eintrag «Endgültig löschen»-Button. Klick öffnet Modal:

```
Endgültig löschen

Das folgende Dokument wird in den Drive-Papierkorb verschoben und nach
30 Tagen permanent gelöscht.

  ┌──────────────────────────────────┐
  │  Statuten 2024 Entwurf v3.docx   │   [Titel kopieren]
  └──────────────────────────────────┘

Tippe oder füge den Titel hier ein, um zu bestätigen:
  ┌──────────────────────────────────┐
  │                                  │
  └──────────────────────────────────┘

  [ Abbrechen ]              [ Löschen ]
```

Titel ist in einer monospace-Box mit Copy-Button selektierbar – User kopiert, paste ins Eingabefeld, Submit-Button aktiviert sich. Verhindert das mühsame exakte Tippen langer Filenames.

### 10.7 Re-Sync (Admin)

Im Admin-Dashboard ein Button «Drive synchronisieren». Klick öffnet ein Erklärungs-Modal:

```
Was macht das?
Diese Aktion gleicht den Inhalt des Shared Drives mit der App-Datenbank
ab. Nötig, wenn jemand direkt in Drive eine Datei verschoben, hochgeladen
oder gelöscht hat – ausserhalb der App.

Was passiert dabei?
– Neue Files in Drive ohne App-Eintrag werden importiert
– App-Einträge mit gelöschtem Drive-File werden bereinigt
– Drift bei Folder-Position wird korrigiert

Dauer: einige Sekunden.

[ Abbrechen ]   [ Jetzt synchronisieren ]
```

Nach Lauf: Toast oder kleine Result-Box mit Summary. Kein eigenes Dashboard, keine Drift-Liste-View.

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

### 16.3 Setup-Script

`scripts/setup_drive.py` einmalig laufen, nachdem Service Account zum Shared Drive eingeladen wurde:

```python
"""Initialisiert die acht Top-Level-Folders im Shared Drive.

Idempotent: kann mehrfach laufen ohne Schaden.
Schreibt Folder-IDs in eine Konfigurations-Tabelle (oder env als JSON).
"""
```

Schritte:

- Authentifizieren via `GOOGLE_SERVICE_ACCOUNT_KEY`
- Pro `DocumentCategory` und für `Archiv`: Folder anlegen, falls noch nicht vorhanden
- Folder-IDs zurückgeben und in App-Konfiguration speichern
- Validierung: Test-Upload eines Dummy-Files, sofort wieder löschen

### 16.4 Cutover

Nicht im Phase-3-Liefer-Scope. Cutover passiert mit der App-weiten MVP-Update-Mail (nach Drive + iCal + Merch + System-Mail-Cutover):

- Bis dahin: alter und neuer Shared Drive existieren parallel. Neuer Drive ist nur intern für Vorstand sichtbar.
- Andreas zieht Inhalte vom alten Drive ins neue (manuell, mit überarbeiteter Folder-Struktur).
- Mit der MVP-Update-Mail: Verifikations-Klick aktiviert Drive-Membership pro Mitglied. Drive-Sektion in der App wird sichtbar.
- Karenz-Phase nach Cutover: alter Drive bleibt 4 Wochen aktiv, danach von Andreas gelöscht.

## 17. Cursor-Briefing für Phase 3

### 17.1 Reihenfolge der Commits

| # | Commit | Inhalt |
|---|---|---|
| 1 | Schema-Migration: Member | `google_email`, `google_email_verified`, `google_email_verified_at` Felder + Token-Purpose `google_email_verify` |
| 2 | Schema-Migration: Document | Alte URL-only-Records löschen, alte Spalten droppen, neue Spalten anlegen, Enum-Werte aktualisieren |
| 3 | Service-Layer | `backend/services/drive_storage.py` mit allen Methoden, Tests, Filename-Sanitization, SVG-Sanitization |
| 4 | Routes und UI | Templates für Documents-Index, Detail-View, Upload-Modal (inkl. Drag-and-Drop), Aktionen, Admin-Re-Sync-Button, Member-Profile-Erweiterung |
| 5 | Setup-Script | `scripts/setup_drive.py` |

### 17.2 Cursor-Briefing-Block

```
Branch: phase/03-workspace-drive-files
Lies vor Implementation: docs/capabilities/drive.md (autoritativ).
Lies docs/initiatives/workspace-railway/PHASE_03_GOOGLE_SHARED_DRIVE_FILES.md
nur für Rahmen, Details aus Capability-Doc.

Implementations-Reihenfolge: Member-Migration → Document-Migration →
Service-Layer mit Tests → Routes/UI → Setup-Script.

Drei Migrationen sind separate Alembic-Commits. Service-Layer und
Routes/UI sind Code-Commits.

Service-Account-Key NIEMALS ins Repo. env.example listet nur den
Variablen-Namen GOOGLE_SERVICE_ACCOUNT_KEY (Base64) und
GOOGLE_DRIVE_ID, nicht die Werte.

SVG-Sanitization ist Pflicht für Marketing-Use-Case.

UX-Texte auf Deutsch, schweizerische Schreibweise mit Guillemets («…»).
```

### 17.3 Akzeptanzkriterien für Phase 3

- [ ] Mitglied kann Datei via App hochladen (Picker oder Drag-and-Drop), File erscheint im richtigen Drive-Folder
- [ ] Dateigrösse >100 MB wird abgelehnt mit klarer Fehlermeldung
- [ ] Verbotener MIME-Type wird abgelehnt
- [ ] SVG mit eingebettetem `<script>` wird vor Drive-Upload sanitiziert
- [ ] «Öffnen»-Aktion öffnet Drive-Web in neuem Tab
- [ ] «Verschieben»-Aktion bewegt File in anderen Folder, DB-Status konsistent
- [ ] «Umbenennen»-Aktion ändert Drive-Filename und DB-Title atomar
- [ ] «Archivieren»-Aktion bewegt File ins `/Archiv/`, `status=ARCHIVED`
- [ ] «Wiederherstellen»-Aktion bewegt File zurück in Original-Folder, `status=ACTIVE`
- [ ] «Endgültig löschen» (nur Admin sichtbar): Bestätigungs-Modal mit Titel-Copy, danach Drive-Trash + DB-Hard-Delete
- [ ] Re-Sync-Button im Admin-Dashboard zeigt Drift-Summary nach Lauf
- [ ] Member-Profil zeigt Kontakt-Mail und Google-Login-Mail getrennt
- [ ] Auto-Sync bei Detail-View korrigiert Drift silent
- [ ] DB-Insert-Fehler nach erfolgreichem Drive-Upload führt zu Drive-Rollback
- [ ] AuditEvents werden für alle Lifecycle-Aktionen geloggt
- [ ] Setup-Script ist idempotent

### 17.4 Out of Scope für Phase 3

- Echtzeit-Kollaboration in iframe innerhalb der PWA
- Externer Virus-Scan
- Granulare Drive-ACL pro Mitglied (nicht nötig: alle gleichberechtigt via α)
- Backup-Strategie
- Quota-Cron
- AI/OCR-Pipelines
- Self-Service «andere Kontakt-Mail eintragen»

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

## 19. Offene Punkte und Trade-offs

- *Sub-Folder-Aktivierung*: Schwellenwert für Jahresordner (`/Finanzen/2026/`) noch nicht hart definiert. Vorschlag: ab 200 Files in einem Folder, manuelle Entscheidung durch Vorstand.
- *Mitglied ohne Google-Konto-Adresse*: Pflichtfeld bedeutet, dass diese Mitglieder de facto blockiert sind. Sozial bei familiärem Verein zumutbar, aber pro Edge-Case Sonderlösung möglich (nur App-Reader-Modus mit ausgegrauten Edit-Aktionen).
- *Drive-Audit-Log-Limitierung*: Workspace Starter hat kein vollständiges Audit. Falls in der Zukunft Workspace-Upgrade kommt, eingebaute Audit-Funktion aktivieren.
- *Auto-Sync-Performance*: Detail-View löst leichten API-Check aus. Bei sehr viel Detail-View-Traffic könnte das Drive-API-Quotas berühren – nicht heute relevant, im Auge behalten.
- *Fallback bei verwaisten Files vom System-Sync*: Auto-Sync importiert neue Drive-Files mit `uploader_id = NULL` (oder System-Member). Im UI sollen solche Einträge mit «Hochgeladen extern via Drive» beschriftet werden, nicht als anonyme Einträge.

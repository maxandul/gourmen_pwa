# Drive-Capability – Setup-Anleitung für Andreas

> **Zweck**: Schritt-für-Schritt-Anleitung für alle manuellen Klick-Aktionen in Google, bevor und während Cursor die Drive-Capability implementiert.
>
> **Begleitdokument zu**: `docs/capabilities/drive.md` (Architektur und Spezifikation).
>
> **Geschätzte Zeit für deine manuellen Schritte**: ~20–30 Minuten verteilt über drei Phasen.

---

## Übersicht

Der Setup besteht aus drei Phasen:

| Phase | Wer | Zeitpunkt | Aufwand |
|---|---|---|---|
| A: Vorbereitung in Google | Andreas | vor Cursor-Implementation | ~10 Min |
| B: Cursor implementiert | Cursor | sobald Phase A fertig | mehrere Stunden |
| C: Validierung & Cutover-Vorbereitung | Andreas | nach Phase B | ~10–15 Min |

Phase A ist das, was du jetzt machst. Phase C kommt später, wenn die App-Implementation läuft.

---

## Phase A: Vorbereitung in Google

### A.1 Workspace-Admin: Externes Sharing erlauben (~3 Min)

**Warum**: Damit du später Mitglieder mit privaten Gmail-Adressen oder Hotmail/GMX-bei-Google-registriert ins Shared Drive einladen kannst, muss der Workspace externes Sharing zulassen.

**Schritte**:

1. Auf [admin.google.com](https://admin.google.com) einloggen mit `kontakt@gourmen.ch`
2. Linke Sidebar: **Apps** → **Google Workspace** → **Drive und Docs**
3. Klick auf **Freigabeeinstellungen** (oder «Sharing settings», je nach Sprache)
4. Sektion **Freigabeoptionen**: setze auf **«Ein – für jeden»** (oder mindestens «Externe Freigabe erlauben»)
5. Sektion **Externe Empfänger müssen sich anmelden**: aktivieren (für Sicherheit)
6. **Speichern** unten

Falls die Option schon richtig steht, kein Eingriff nötig.

### A.2 Shared Drive anlegen (~3 Min)

**Warum**: Das ist der eigentliche Speicher für alle Vereinsdokumente.

**Schritte**:

1. Auf [drive.google.com](https://drive.google.com) einloggen mit `kontakt@gourmen.ch`
2. Linke Sidebar: **Geteilte Ablagen** (engl. «Shared drives»)
3. Oben **+ Neu** klicken
4. Name eingeben: **Gourmen Verein**
5. **Erstellen** klicken
6. Drive ist nun leer und offen
7. **WICHTIG – Drive-ID notieren**: oben in der URL steht etwas wie `https://drive.google.com/drive/folders/0AKx...lange-id...VKQ`. Der Teil nach `/folders/` ist die `drive_id` – kopiere und speichere sie. Du gibst sie später Cursor.

### A.3 GCP-Projekt anlegen (~5 Min)

**Warum**: Das Google Cloud Projekt hostet den Service Account, der die App-zu-Drive-Kommunikation erledigt.

**Schritte**:

1. Auf [console.cloud.google.com](https://console.cloud.google.com) einloggen mit `kontakt@gourmen.ch`
2. Falls du noch nie hier warst: **Nutzungsbedingungen akzeptieren**, Land auswählen, Newsletter abwählen
3. Oben links neben dem Logo: **Projektauswahl-Dropdown** klicken (sagt vermutlich «Kein Projekt ausgewählt» oder zeigt ein bestehendes)
4. Im Modal: **Neues Projekt** klicken (oben rechts)
5. **Projektname**: `Gourmen PWA`
6. **Projekt-ID**: Vorschlag wird `gourmen-pwa` sein. Wenn die ID bereits vergeben ist, nimm `gourmen-pwa-2026` oder ähnliches. **Notiere dir die finale Projekt-ID** – brauchst du für Cursor.
7. **Speicherort**: «Keine Organisation» ist ok
8. **Erstellen** klicken
9. Warten bis Projekt aktiv (~30 Sekunden, oben rechts erscheint Bestätigung)
10. Im Projektauswahl-Dropdown nun das neue Projekt auswählen

**Falls GCP nach einem Rechnungskonto («Billing Account») fragt**: kannst du **«Später»** oder **«Skip»** wählen. Die Drive-API ist im Free Tier nutzbar, du brauchst keine Kreditkarte zu hinterlegen.

### A.4 Übergabe an Cursor

Du hast jetzt zwei Werte, die Cursor braucht:

- **`GOOGLE_DRIVE_ID`**: aus Schritt A.2.7 (z.B. `0AKxlangeIdVKQ`)
- **`GCP_PROJECT_ID`**: aus Schritt A.3.6 (z.B. `gourmen-pwa` oder `gourmen-pwa-2026`)

Gib Cursor diese beiden Werte beim Phase-3-Auftrag mit.

**Anschliessend** im Cursor-Terminal:

```bash
gcloud auth login
```

Browser öffnet sich, du loggst dich mit `kontakt@gourmen.ch` ein, gibst Cursor die Berechtigung. Token wird gecached.

Damit ist Phase A abgeschlossen. Cursor kann nun loslegen.

---

## Phase B: Was Cursor in dieser Zeit automatisch macht

Nur zur Information – du musst hier nichts tun:

1. Drive API im GCP-Projekt aktivieren (`gcloud services enable drive.googleapis.com`)
2. Service Account anlegen (`gcloud iam service-accounts create gourmen-drive-sa`)
3. JSON-Key generieren und Base64-encoden
4. Key als Railway-Secret `GOOGLE_SERVICE_ACCOUNT_KEY` speichern
5. Lokalen Key wegputzen
6. **Pause**: Cursor sagt dir Bescheid, wenn die Service-Account-E-Mail bekannt ist – dann musst du Phase C.1 ausführen
7. Schema-Migrationen in der DB
8. Service-Layer schreiben
9. Routes und UI bauen
10. Setup-Script ausführen (legt die acht Folders im Drive an)

Cursor unterbricht für einen manuellen Schritt von dir – Phase C.1.

---

## Phase C: Validierung und manuelle Zwischenschritte

### C.1 Service Account zum Shared Drive einladen (~2 Min)

**Wann**: Cursor fragt dich, sobald der Service Account angelegt ist und die E-Mail-Adresse bekannt. Format: `gourmen-drive-sa@<projekt-id>.iam.gserviceaccount.com`, z.B. `gourmen-drive-sa@gourmen-pwa.iam.gserviceaccount.com`.

**Warum**: Der Service Account muss explizit Mitglied des Shared Drives sein, damit er die Drive-API darauf nutzen kann. Das geht nicht automatisch – du musst ihn einmalig manuell einladen.

**Schritte**:

1. Auf [drive.google.com](https://drive.google.com), eingeloggt mit `kontakt@gourmen.ch`
2. Linke Sidebar: **Geteilte Ablagen** → **Gourmen Verein** öffnen
3. Oben rechts: **Mitglieder verwalten** klicken (Symbol mit Person und Plus, oder rechtsklick auf den Drive-Namen → «Mitglieder verwalten»)
4. **Neue Mitglieder hinzufügen**: E-Mail-Adresse des Service Accounts eintragen (Cursor gibt dir die exakte Adresse)
5. Rolle: **«Content-Manager»** (im englischen UI: «Content Manager»)
6. **WICHTIG: Häkchen «Personen benachrichtigen» entfernen** – Service Account hat keinen Posteingang, würde sonst eine Bounce-Mail erzeugen
7. **Senden** / **Speichern**

Service Account erscheint nun in der Mitgliederliste mit der Rolle.

Sage Cursor Bescheid, dass es weitermachen kann.

### C.2 Validierung nach setup_drive.py-Lauf (~2 Min)

Cursor lässt nach Phase B das Setup-Script laufen. Danach:

1. Drive öffnen: **Geteilte Ablagen** → **Gourmen Verein**
2. Acht Folders sollten sichtbar sein:
   - `/Statuten/`
   - `/Vereinsführung/`
   - `/Finanzen/`
   - `/Verträge/`
   - `/Reisen-und-Events/`
   - `/Medien/`
   - `/Sonstiges/`
   - `/Archiv/`
3. Falls einer fehlt oder doppelt ist: Cursor melden, Setup-Script erneut laufen lassen (idempotent)

### C.3 Datenschutzerklärung erstellen (~10 Min, vor Cutover)

**Wann**: Vor der App-weiten MVP-Update-Mail. Nicht zwingend für Phase 3 selbst, aber zwingend bevor Mitglieder zur Drive-Nutzung aufgefordert werden.

**Wo**: `/Vereinsführung/Datenschutzerklärung Mitglieder.gdoc` (Google Doc, in Drive direkt erstellt)

**Inhalts-Stichpunkte** (Capability-Doc Sektion 13.3 für die volle Liste):

- Verein als Verantwortlicher
- Datenkategorien: `email`, `google_email`, Mitgliedsdaten in App
- Drittanbieter Google LLC, Drittland-Transfer USA via EU-US Data Privacy Framework
- Verarbeitungszweck: Vereinsdokumenten-Verwaltung
- Speicherdauer: Mitgliedschaft + Cleanup binnen 30 Tagen nach Austritt
- Betroffenenrechte: Auskunft, Löschung, Widerspruch
- Kontakt: `kontakt@gourmen.ch`

Du kannst das alleine schreiben oder mit einem Vorstandskollegen. Anwaltsprüfung ist bei einem familiären Verein nicht zwingend, aber empfehlenswert wenn Unsicherheit besteht.

### C.4 Inhalte vom alten Drive ins neue ziehen (~laufend, parallel zur Phase 3)

**Wann**: Während Cursor implementiert, kannst du parallel Inhalte rüberziehen.

**Wie**:

1. Altes Shared Drive öffnen (auf der alten Instanz)
2. Pro Kategorie: relevante Files markieren, **Herunterladen** als ZIP
3. ZIP auspacken
4. Im neuen Drive (`Gourmen Verein`): in den passenden Folder wechseln
5. Files via Drag-and-Drop oder **Hochladen**-Button reinkopieren
6. Filenames bei Bedarf anpassen (sprechende Titel statt kryptischer Originalnamen)

**Tipp**: Nutze die Folder-Struktur als Anlass, die Inhalte aufzuräumen. Du musst nicht alles übernehmen – das Ideen-Papier von 2018 darf gerne im alten Drive bleiben oder ganz weg.

### C.5 Cutover (gebündelt mit MVP-Update-Mail, später)

Nicht in dieser Anleitung. Wird in einem separaten Doc beschrieben, sobald die anderen MVP-Capabilities (iCal, Merch, System-Mail) auch implementiert sind.

Bis dahin:
- Neuer Drive ist intern nutzbar (du, Vorstand)
- Alter Drive bleibt parallel aktiv
- Mitglieder werden nicht informiert
- App-Drive-Sektion ist hinter Feature-Flag versteckt

---

## Mini-Checkliste für deine manuellen Schritte

Phase A (jetzt):

- [ ] A.1 Workspace-Admin-Sharing-Settings prüfen
- [ ] A.2 Shared Drive «Gourmen Verein» anlegen, `drive_id` notieren
- [ ] A.3 GCP-Projekt «Gourmen PWA» anlegen, `project_id` notieren
- [ ] A.4 `gcloud auth login` im Cursor-Terminal
- [ ] A.4 `drive_id` und `project_id` an Cursor übergeben

Phase C (nach Cursor-Implementation, in der Reihenfolge):

- [ ] C.1 Service Account zum Shared Drive einladen (Cursor fragt dich)
- [ ] C.2 Acht Folders im Drive validieren
- [ ] C.3 Datenschutzerklärung als Google Doc anlegen (vor Cutover)
- [ ] C.4 Inhalte vom alten Drive rüberziehen (parallel)
- [ ] C.5 Cutover (später, gebündelt mit MVP-Update-Mail)

---

## Troubleshooting

**«Externes Sharing ist deaktiviert» beim Anlegen der Mitgliedschaft**: zurück zu A.1, Workspace-Admin-Settings prüfen.

**GCP fragt nach Kreditkarte / Billing-Account**: «Später» oder «Skip» wählen. Drive-API ist im Free Tier, kein Billing nötig.

**`gcloud auth login` öffnet keinen Browser**: im Terminal `gcloud auth login --no-launch-browser` versuchen, manuell den Link kopieren und im Browser öffnen.

**Service Account erscheint nicht in der Drive-Mitgliederliste nach Hinzufügen**: Seite neu laden, ggf. Cache leeren.

**Setup-Script schlägt fehl mit «Permission denied»**: Service Account hat noch keine Content-Manager-Rolle im Drive. Zurück zu C.1.

**`drive_id` enthält Sonderzeichen, die nicht in eine Railway-Variable passen**: Drive-IDs sind alphanumerisch (Buchstaben, Zahlen, Bindestrich, Underscore), das sollte sauber gehen. Falls doch Probleme: Drive-ID sicherheitshalber in Anführungszeichen setzen beim `railway variables set`.

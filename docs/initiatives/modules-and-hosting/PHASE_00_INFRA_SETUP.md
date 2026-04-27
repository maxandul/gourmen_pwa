# Phase 0 – Infrastruktur-Setup

**Status**: pending  
**Aufwand**: ~2h einmalig  
**Code-Anteil**: keiner (manuelle Setup-Arbeit)

## Ziel

Alle externen Basis-Konten fuer den finalen Zielzustand bereitstellen:

- App-Hosting bleibt auf Railway
- Domain/DNS und Mail bei Infomaniak
- Dokumente werden spaeter in der App verwaltet (Object Storage, S3-kompatibel)
- Fuer den Start nur **eine** Vereinsadresse (`info@gourmen.ch`)

Damit koennen die Folgephasen (Login, Dokumente, Buchhaltung) ohne Infrastruktur-Blocker starten.

## Pre-Conditions

- Aktive Railway-Instanz mit funktionierender App
- Zugriff auf Domain `gourmen.ch` (oder geplante Registrierung)
- Vereinsdaten griffbereit (Owner, Kontakt, Rechnungsadresse)

## Tasks

### 1. Domain + DNS bei Infomaniak

- [ ] Infomaniak-Account anlegen ([infomaniak.com](https://www.infomaniak.com))
- [ ] Domain registrieren oder bestehende Domain zu Infomaniak transferieren (`gourmen.ch`)
- [ ] DNS-Zone aktivieren und DNSSEC einschalten

### 2. Custom Domain auf Railway

- [ ] In Railway: Service auswaehlen -> Settings -> Custom Domain
- [ ] Wunsch-Subdomain eintragen (z.B. `app.gourmen.ch`)
- [ ] CNAME-Record bei Infomaniak DNS auf den Railway-Wert setzen
- [ ] HTTPS-Zertifikat automatisch generieren lassen
- [ ] Verifizieren: `https://app.gourmen.ch` zeigt App mit gueltigem TLS

### 3. Mailbox fuer System- und Vereinsmails

- [ ] Bei Infomaniak **Mail Service** buchen (eine Adresse reicht)
- [ ] Adresse erstellen: `info@gourmen.ch`
- [ ] Inbound/Outbound testen (Mail senden und empfangen)
- [ ] SPF, DKIM und DMARC gemaess Infomaniak-Mailschutz setzen/pruefen

### 4. Object Storage fuer App-Dokumente

- [ ] Infomaniak Public Cloud aktivieren
- [ ] Object-Storage-Projekt/Bucket anlegen (z.B. `gourmen-files`)
- [ ] S3-Credentials erstellen (Access Key + Secret, minimale Rechte)
- [ ] Optional: Subdomain fuer Downloads vorbereiten (`files.gourmen.ch`)
- [ ] Technischer Test: `aws s3 ls --endpoint-url=<endpoint>`

### 5. Railway Environment-Variablen

In Railway-UI eintragen:

```text
MAIL_FROM_ADDRESS=info@gourmen.ch
MAIL_REPLY_TO=info@gourmen.ch

S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET=gourmen-files
S3_ENDPOINT_URL=https://<infomaniak-object-storage-endpoint>
S3_REGION=...
S3_PUBLIC_BASE_URL=https://files.gourmen.ch
```

Hinweis: Die finalen Variablennamen koennen in Phase 1/3 noch auf bestehende Projekt-Konventionen angepasst werden.

### 6. Optional in dieser Phase

- [ ] **RaiseNow / Stripe**: auf Phase 6 verschieben (TWINT-spezifisch)
- [ ] **Meta Business Manager**: auf Phase 7 verschieben (2-4 Wochen Verifizierungs-Wartezeit)

## Acceptance-Criteria

- [ ] `https://<deine-app-domain>` zeigt die App mit gueltigem TLS-Zertifikat
- [ ] `info@gourmen.ch` kann Mails senden und empfangen
- [ ] Object Storage ist erreichbar (S3-List-Test erfolgreich)
- [ ] Alle ENV-Variablen aus Sektion 5 in Railway gesetzt
- [ ] Initiative-README Status-Tabelle aktualisiert (`pending` -> `done`)

## Out of Scope

- Kein Code-Aufwand in dieser Phase
- Keine App-Implementierung fuer Dokumentenverwaltung (kommt in spaeteren Phasen)
- Kein Stripe-/TWINT-Setup in Phase 0
- Kein WhatsApp-Setup in Phase 0

## Hinweise

- Fuer diesen Verein reicht vorerst eine einzige Mailadresse (`info@...`)
- Keine sensiblen Dokumente unverschluesselt oder ohne Rechtekonzept freigeben
- S3-Credentials immer mit minimalen Rechten erstellen (kein globaler Admin-Key)
- Dokumentenverwaltung soll ueber die App laufen, nicht ueber einen externen Shared Drive

## Cursor-Agent-Briefing

Diese Phase ist **manuell** und braucht keinen Agent. Wenn du die Schritte selbst nicht machen willst und einen Agent damit beauftragen wuerdest, muesstest du Account-Zugaenge bereitstellen - das ist nicht empfohlen. Mach diesen Teil bitte selbst.

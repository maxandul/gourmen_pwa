# Phase 0 – Infrastruktur-Setup

**Status**: pending  
**Aufwand**: ~2h einmalig  
**Code-Anteil**: keiner (manuelle Setup-Arbeit)

## Ziel

Alle externen Konten anlegen und API-Keys ins Railway-Environment einpflegen. Damit nachfolgende Phasen direkt loslegen können.

## Pre-Conditions

- Aktive Railway-Instanz mit funktionierender App
- Vereinsdaten griffbereit (für Stripe/RaiseNow später)

## Tasks

### 1. Domain registrieren

- [ ] Cloudflare-Account anlegen ([cloudflare.com](https://cloudflare.com))
- [ ] Domain registrieren (Vorschlag: `gourmen.ch` oder `gourmen.app`)
- [ ] DNS-Zone aktivieren

### 2. Custom Domain auf Railway

- [ ] In Railway: Service auswählen → Settings → Custom Domain
- [ ] Wunsch-Subdomain eintragen (z.B. `app.gourmen.ch`)
- [ ] CNAME-Record bei Cloudflare DNS auf den Railway-Wert setzen
- [ ] HTTPS-Zertifikat automatisch generieren lassen
- [ ] Verifizieren: `https://app.gourmen.ch` zeigt App mit gültigem TLS

### 3. Cloudflare R2 Bucket

- [ ] R2 in Cloudflare-Dashboard aktivieren (Free Tier reicht für den Start)
- [ ] Bucket anlegen: Name `gourmen-files`
- [ ] API-Token erstellen (R2 → Manage R2 API Tokens)
  - [ ] Berechtigungen: Object Read & Write für Bucket
- [ ] Custom Domain für Bucket: `files.gourmen.ch` (CNAME bei Cloudflare DNS)

### 4. Resend Account

- [ ] Account auf [resend.com](https://resend.com)
- [ ] Domain hinzufügen: `gourmen.ch`
- [ ] DKIM-Records bei Cloudflare DNS einfügen
- [ ] Auf Verifizierung warten (~10 Min)
- [ ] API-Key erstellen
- [ ] Test-Mail aus Resend-UI an dich selbst senden
- [ ] SPF + DMARC bei Cloudflare ergänzen wo noch nicht vorhanden

### 5. Railway Environment-Variablen

In Railway-UI eintragen:

```text
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@gourmen.ch

R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=gourmen-files
R2_ENDPOINT=https://<accountid>.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://files.gourmen.ch
```

### 6. Optional in dieser Phase

- [ ] **RaiseNow / Stripe**: kann auf Phase 6 verschoben werden (TWINT-spezifisch)
- [ ] **Meta Business Manager**: auf Phase 7 verschoben (2-4 Wochen Verifizierungs-Wartezeit)

## Acceptance-Criteria

- [ ] `https://<deine-app-domain>` zeigt die App mit gültigem TLS-Zertifikat
- [ ] Resend kann eine Test-Mail an deine Adresse senden
- [ ] R2-Bucket ist erreichbar (Test mit `aws s3 ls --endpoint-url=...` oder ähnlich)
- [ ] Alle ENV-Variablen aus Sektion 5 in Railway gesetzt
- [ ] Initiative-README Status-Tabelle aktualisiert (`pending` → `done`)

## Out of Scope

- Kein Code-Aufwand in dieser Phase
- Keine App-Änderungen (nur Konfiguration)
- Stripe/Meta erst später

## Hinweise

- Bei Cloudflare lieber ein **API-Token mit minimalen Rechten** statt globaler Account-Key
- Resend-DKIM braucht oft 5-30 Min bis verifiziert wird, vor erneutem Klicken Geduld haben
- DNS-TTL bei Cloudflare ist niedrig (auto), neue Einträge sind schnell wirksam

## Cursor-Agent-Briefing

Diese Phase ist **manuell** und braucht keinen Agent. Wenn du die Schritte selbst nicht machen willst und einen Agent damit beauftragen würdest, müsstest du Account-Zugänge bereitstellen – das ist nicht empfohlen. Mach diesen Teil bitte selbst.

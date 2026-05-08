# Strategie 2026 – Gourmen PWA

> **Zweck**: Eine Seite, die sagt, **wo welche Daten leben** und **welche externen Systeme welche Aufgabe haben**. Bei Konflikten mit Phasen-Docs oder älteren Initiative-READMEs gewinnt dieses Dokument.
>
> **Stand**: 2026-05-07. **Owner**: Andreas. **Review-Rhythmus**: bei jedem grossen Architektur-Entscheid.

---

## Source-of-Truth-Karte

| Domäne | Source of Truth | Begründung |
|---|---|---|
| Domain & DNS | **Infomaniak** | Registrar bleibt; DNS-Records (MX, SPF, DKIM, DMARC, CNAMEs) werden dort gepflegt. |
| Mail-Postfächer (Personen) | **Google Workspace Starter** | Eine bezahlte Mailbox `kontakt@gourmen.ch`, weitere Adressen als Alias auf dieselbe Lizenz. |
| Vereinsdokumente (editierbar) | **Google Shared Drive** | Protokolle, Verträge, Vorstandsdokumente. «Alle sehen alles». Bearbeitung in Google Docs/Sheets. |
| Strukturierte App-Daten | **Postgres auf Railway** | Members, Events, Participations, Bookings, Audit-Log. Migrationen via Alembic. |
| App-Code & Hosting | **Railway Hobby** (Web + Cron + Postgres + Redis) | Kein Plattform-Wechsel geplant. |
| Transaktionsmails (System) | **Resend (free)** | Forgot-Password, 2FA-Reset, Onboarding, Admin-Mailtest. HTTPS-API, Railway Hobby blockiert SMTP. |
| Belege (Buchhaltung) | **Google Shared Drive** (Unterordner) | Pragmatisch, kollaborierbar, n8n-kompatibel. Falls n8n-Pfad gewählt wird, bleibt Drive der Speicher. |
| Merch-Produktbilder | **Repo** unter `static/img/merch/` | Wenig Volumen, Änderung via Git ist akzeptabel. |
| Public-Page-Bilder | **Instagram-Embeds** | Verein postet ohnehin auf Insta; Embeds in Templates. Datenschutz-Hinweis nötig. |
| Push-Notifications | **VAPID self-hosted** | Bestehend, läuft. Keys in Railway Secrets. |
| Auth & Sessions | **Flask-Login + pyotp + Fernet** (Status quo) | Funktionsfähig. Migration auf Supabase Auth ist Future Consideration (siehe unten). |

## Mailwege auf einen Blick

| Mailweg | Absender | Empfänger | Transport | Authentifizierung |
|---|---|---|---|---|
| Personenpost (manuell) | `kontakt@gourmen.ch` | extern | Gmail (Workspace) | Workspace-Login |
| Systemmails (Reset, Onboarding, 2FA) | `noreply@gourmen.ch` (oder `kontakt@`) | Mitglied | **Resend HTTPS-API** | DKIM via Resend, SPF erweitert um Resend |
| Massenmails an Mitglieder | — | — | **nicht vorgesehen** | Vereins-Kommunikation läuft über andere Kanäle (PWA, App-Push, WhatsApp-Gruppe) |

**DNS-Konsequenz**: Resend nutzt AWS SES unter der Haube — SPF-Record wird um `include:amazonses.com` erweitert (nicht `_spf.resend.com`), MX-Record auf `feedback-smtp.eu-west-1.amazonses.com` für Bounce-Handling auf der von Resend vorgegebenen Subdomain, DKIM-Selector als TXT zusätzlich zu Workspace-DKIM. **Autoritativ ist immer die Anzeige im Resend-Verifikations-Screen** — Werte 1:1 bei Infomaniak übernehmen, nichts erfinden. DMARC bleibt vorerst `p=none`, später auf `p=quarantine`.

## Externe Dienste (Stand 2026-05)

```
Aktiv:
  - Infomaniak       (Domain, DNS)
  - Google Workspace (Mail, Shared Drive)
  - Railway          (Web, Cron, Postgres, Redis)
  - Resend           (System-Mail HTTPS-API)  ← Entscheid 2026-05-07
  - Google Maps API  (Frontend-Karten)
  - Google Places API(Restaurant-Lookup)

Geplant (Phasen 4–7):
  - n8n (cloud oder self-hosted) — als Buchhaltungs-Orchestrator     [Architektur-Entscheid offen]
  - Stripe oder RaiseNow         — TWINT-Acquirer                    [Anbieter-Entscheid offen]
  - Meta Cloud API              — WhatsApp Business

Verworfen / vermieden:
  - Infomaniak Object Storage   — durch Drive abgelöst
  - Cloudflare R2 / Supabase Storage — nicht nötig, weil Drive für Belege reicht
  - Eigener Mailserver
  - SMTP-basierter System-Mail   — Railway Hobby blockt outbound SMTP
```

## Leitlinie: AI-first für automatisierbare Prozesse

Bei jeder Capability mit repetitiven Schritten, Datenklassifikation, Texterzeugung oder Auswertung wird **vor Implementierung** geprüft, ob AI bzw. Workflow-Automation den Prozess sinnvoll vereinfacht. Bewusst abgewogen gegen Komplexität, laufende Kosten und Wartungsaufwand — nicht jede Capability braucht AI, und der Verein hat begrenztes Budget.

**Konkrete Felder für AI/Automation-Diskussion**:

- *Buchhaltung* — Beleg-OCR, Klassifikation, Buchungssatz-Vorschläge (n8n-Pfad als eine Variante)
- *Merch* — Bestell-Triage aus Mail-Eingang, Lager-Forecast, Auto-Beschreibungen
- *Geld einfordern nach BillBro* — personalisierte Reminder-Texte, TWINT-Link inline, Eskalations-Stufen
- *Events erstellen* — AI-Vorschläge aus Restaurant-Stammdaten, Auto-Texte für Reminder
- *Statistiken* — Natural-Language-Queries auf Vereins-Daten, Auto-Insights für Vorstandsbericht
- *Public-Dienste* — AI-generierte Restaurant-/Hitlist-Beschreibungen, SEO-Texte
- *GV-Admin* — Traktanden-Vorschlag aus Vorjahres-GV plus offene Initiativen, Protokoll-Entwurf aus Aufzeichnung, personalisierte Einladungen

**Mechanismus**: Im Capability-Doc jedes Moduls eigene Sektion «AI/Automation-Optionen» mit konkreten Abwägungen. Keine generische «AI-Schicht» quer durch die App, sondern punktuelle Entscheide pro Use Case.

**Werkzeugkasten zur Abwägung**:

- *n8n* (cloud oder self-hosted) — Workflow-Orchestrator, viele Konnektoren (Drive, Mail, Stripe, Telegram, OpenAI), gut für mehrstufige Prozesse
- *OpenAI/Anthropic API* direkt aus der App — für inline-Generierungen, ad-hoc Klassifikationen
- *Make.com / Zapier* — ähnlich n8n, höhere Pro-Action-Kosten
- *Eigene Python-Skripte mit LLM-Calls* — für einmalige Batch-Jobs (z.B. Stammdaten-Anreicherung)

## Open Decisions (zu klären, bevor entsprechende Phase startet)

### 1. Buchhaltung: n8n-Orchestrator oder reines Flask-Modul?

- **n8n-Pfad**: PWA stellt UI und Stammdaten, n8n übernimmt Beleg-OCR, Mail-Posteingang für Eingangsrechnungen, Klassifikations-Workflow, Buchungssatz-Vorschläge. Bringt einen weiteren Service (n8n cloud ~ €20/Mo oder self-hosted Container).
- **Flask-Pfad**: Alles im PWA-Backend, klassisches Modul wie ursprünglich in `_archive/2026-04_modules-and-hosting/PHASE_04_ACCOUNTING.md` vorgesehen. Mehr Code im Repo, weniger Dienste.
- **Entscheid offen**. Capability-Doc «Buchhaltung» soll beide Varianten gegenüberstellen und Empfehlung geben.

### 2. TWINT-Anbieter: RaiseNow oder Stripe?

- **RaiseNow**: Schweizer Vereins-Acquirer, kein HR-Eintrag nötig, Buchhaltungs-Integration eingebaut, höhere Gebühr.
- **Stripe**: TWINT seit 2024 unterstützt, niedrigere Gebühr, aber weniger Vereins-Komfort.
- Hängt mit Entscheid 1 zusammen — wenn n8n, dann ist Anbindung egal, n8n hat Konnektoren für beide.

### 3. AI/Automation pro Capability

Welche Capabilities bekommen AI-Unterstützung, welche bleiben klassisch? Pro Capability-Doc eigene Sektion mit Trade-off-Analyse. Default-Erwartung: bei den unter «AI-first»-Leitlinie genannten Feldern wird die AI-Variante mindestens skizziert und gegen die klassische Variante abgewogen.

## Future Considerations (nicht im aktuellen MVP)

### Auth-Migration auf Supabase

Aktueller Auth-Stack ist Flask-Login + pyotp + Fernet — funktional, aber Maintenance. Supabase Auth bringt:

- Google-OAuth, Magic Links, MFA, Session-Management out of the box
- Passwort-Reset und Onboarding-Flows als Library-Features
- Spart geschätzt 800–1500 Zeilen Custom-Code

Kosten der Migration:

- Member-Modell muss umgebaut werden (User-ID-Mapping, Mail-Migration)
- Sensible Felder (`MemberSensitive`, `MemberMFA`) müssen umkodiert oder weiter selbst verschlüsselt werden
- `CRYPTO_KEY` darf nicht verloren gehen — Migration ist eine Daten-Migration, nicht nur Code

**Entscheidungs-Trigger**: Sobald Auth-bezogener Maintenance-Aufwand mehr als 2 Stunden/Quartal kostet **oder** ein dritter Auth-Faktor (z.B. Passkey) gewünscht wird.

### Massen-Bilder-Hosting

Falls Public-Page später ohne Insta-Embeds auskommen soll oder Galerien aus eigener Kontrolle gewünscht sind: Cloudflare R2 oder Bunny Storage. Heute nicht nötig.

## MVP-Scope (Q3 2026)

Aus den Fernzielen sind das die «müssen Q3/Q4 2026 funktionieren»-Capabilities:

1. **System-Mail-Cutover auf Resend** — Forgot-Password, 2FA-Reset, Onboarding-Mails kommen zuverlässig an.
2. **Drive-Integration** — Mitglieder lesen, laden hoch, löschen Vereinsdokumente direkt in der App. **Zentrale Anforderung**: ein Klick in der App öffnet die Datei direkt in Google Docs/Sheets zur Bearbeitung — keine Download-und-wieder-hochladen-Schleife. Browser-Tab oder PWA-In-App-Browser, beides ok.
3. **iCal-Feed pro Mitglied** — Token-basierter Calendar-Feed zum Abonnieren in Apple/Google/Outlook-Kalender.
4. **Merch von Grund auf neu denken** — nicht «alte Models polieren», sondern den **gesamten Prozess** durchdenken: Sortiment-Pflege, Bestell-Annahme, Bezahlung (TWINT?), Produktion/Beschaffung, Auslieferung an Mitglied, Lagerbestand, Statistik. Capability-Doc soll erst Prozess beschreiben, dann technische Umsetzung ableiten. AI-Optionen explizit prüfen (Bestell-Triage, Lager-Forecast).

## Begleit-Verbesserungen (parallel zu MVP, kleinere Capabilities)

Nicht auf demselben Level wie die vier MVP-Capabilities, aber wichtig genug, um nicht im Backlog zu verschwinden:

- **Install-Banner-Fix** — aktuell klebt der «Auf Homescreen installieren»-Hinweis am oberen Bildschirmrand und kann nicht weggeklickt werden. UX-Bug, kleiner Cursor-Auftrag. Bestehende Logik ist in `static/js/pwa.js` (siehe `docs/ARCHITECTURE.md`, Sektion PWA-Aspekte).
- **Cronjob-Audit** — die drei bestehenden Reminder-Cronjobs (3-Wochen, Wochen, Rating) auf korrekte Auslösung in Production prüfen. Ist eher Tech-Debt-Audit als Feature: laufen sie, kommen Push-Reminder an, ist die Logik noch korrekt? Eigene kleine Phase mit Production-Logs-Review.
- **Changelog / What's-New für Mitglieder** — wenn ein neues Feature live geht, sollen Mitglieder das in der App sehen. Kleines Modal/Card beim Login mit «Neu seit letzter Anmeldung», dismissible. AI-Optionen prüfen: Auto-Generierung aus Git-Commits seit letzter Sichtbarkeit pro Mitglied.
- **Dashboard-Personalisierung** — Mitglieder sollen wählen können, welche Karten/Widgets sie auf ihrem Dashboard sehen (z.B. nächstes Event hervorgehoben, GGL-Stand, BillBro-Pending, Merch-Bestellungen). Eigene Capability mittlerer Grösse — eigenes Capability-Doc fällig.

## Hauptbrocken danach (Q4 2026 / Q1 2027)

5. **Buchhaltung** — nach Entscheid n8n vs. Flask-Modul. Belege via Drive, Buchungssätze in Postgres.
6. **TWINT-Anbindung** — verzahnt mit Buchhaltung (Eingangserfassung) und Merch/BillBro (Forderungs-Auslöser). Nach Entscheid Acquirer.
7. **GV-Admin** — Workflow für Generalversammlung: Traktanden-Sammlung, Einladung an Mitglieder, Protokoll-Erstellung, Beschluss-Tracking. Verzahnt mit Drive (Protokolle), Mail (Einladung), Mitgliederliste. Hier ist AI-Unterstützung besonders attraktiv (Traktanden-Vorschläge aus Vorjahr, Protokoll-Entwurf aus Aufzeichnung).

## Backlog (irgendwann)

- WhatsApp Business via Meta Cloud API
- Erweiterte Statistik-/Reporting-Capability mit Natural-Language-Queries
- Auth-Migration auf Supabase

---

## Decision Log

| Datum | Entscheid | Begründung |
|---|---|---|
| 2026-05-01 | Domain bleibt Infomaniak, Mail/Drive auf Google Workspace, App auf Railway | Operations-Aufwand niedrig, etablierte Anbieter, MX-Cutover technisch sauber. |
| 2026-05-01 | Files via Google Shared Drive statt Infomaniak Object Storage | Kollaboration und Doc-Bearbeitung in Google ist die natürliche Umgebung. |
| **2026-05-07** | **System-Mail via Resend (free)** | Railway Hobby blockt outbound SMTP. Pro-Upgrade nicht gewünscht. Resend ist HTTPS-API, free reicht für Vereinsvolumen. Vorgängige «kein Resend»-Position revidiert nach Test der Alternativen. |
| **2026-05-07** | **Kein zusätzlicher Object Storage (R2/Supabase)** | Belege via Drive, Merch im Repo, Public-Bilder via Insta-Embeds. Damit kein eigener Bucket nötig. |
| **2026-05-07** | **Auth-Migration auf Supabase als Future Consideration** | Verlockend, aber gross. Heute nicht MVP. Trigger-Bedingung dokumentiert. |
| **2026-05-07** | **n8n als Architektur-Option für Buchhaltung offen** | Capability-Doc soll Vor-/Nachteile gegen reines Flask-Modul auswiegen. |
| **2026-05-07** | **AI-first als Leitlinie, nicht als Pflicht** | Bei automatisierbaren Prozessen wird AI-Unterstützung pro Capability bewusst geprüft und abgewogen — nicht generisch reingeschoben. |
| **2026-05-07** | **Massenmails / Newsletter nicht vorgesehen** | Vereins-Kommunikation läuft über PWA, Push, WhatsApp-Gruppe. Damit Mail-Strategie auf zwei Wege reduziert (Personenpost + System-Mail). |
| **2026-05-07** | **GV-Admin als Hauptbrocken-Capability** | Eigener Workflow mit hohem AI-Hebel (Traktanden, Protokoll, Einladung). |
| **2026-05-07** | **Merch wird Prozess-Redesign, nicht nur Tech-Politur** | Capability-Doc beginnt mit Prozess-Beschreibung, Technik folgt. |
| **2026-05-07** | **Begleit-Verbesserungen aufgenommen**: Install-Banner-Fix, Cronjob-Audit, Changelog-Konzept, Dashboard-Personalisierung | Punkte parallel zum MVP, eigene kleine bis mittlere Capabilities. |

---

**Verwandte Docs**:
`docs/ARCHITECTURE.md` (Stack-Detail) ·
`docs/initiatives/workspace-railway/README.md` (aktive Phasen) ·
`AGENTS.md` (Briefing für AI-Agenten)

# Dokumentationsabgleich – Arbeitsstand

Stand 2026-09-20. Erster Durchlauf: Einstieg und ausgewaehlte Anchor-Aussagen.
Keine Quelldokumente korrigiert; Empfehlungen vor der Umsetzung zurueckstellen.
Alle 47 Dokumente des Ausgangsinventars erhalten ein eigenes Pruefregister:
[DOCUMENT_REVIEW_REGISTER.csv](DOCUMENT_REVIEW_REGISTER.csv). Dieses Register
ist von der regenerierbaren Rohinventarliste getrennt. Kein Dokument ist hier
bereits pauschal als gueltig oder vollstaendig abgeschlossen markiert.

## Bestaetigte Abweichungen – Erweiterung A-012

| Quelle / Aussage | Gegenbeleg | Empfehlung |
|---|---|---|
| README: Python 3.12+; ARCHITECTURE: 3.11 | runtime.txt pinnt python-3.11.9 | Unterstuetzte lokale Version und Deployment-Pin gemeinsam dokumentieren; keine Aussage ueber laufende Produktion |
| README Setup: flask db init und initiale Migration | migrations/env.py und bestehende versions-Historie liegen bereits vor | Neuinstallation wendet bestehende Migrationen an; Entwicklung neuer Migrationen separat beschreiben |
| README: Admin wird automatisch erstellt | init_admin_user ist definiert; kein Aufruf in backend/scripts gefunden | Tatsaechlichen Bootstrap-Pfad nachweisen und dokumentieren; Suchbefund allein beweist nicht jeden externen Einstieg |
| README: Deployment erkennt Procfile | railway.json setzt startCommand=bash start.sh und preDeployCommand fuer migrate_deploy.py | Aktuellen Start-/Migrationspfad und SERVICE_TYPE beschreiben |
| README: GET /account/profile | member-Blueprint /member, Route /profile | Kanonischen Profilpfad dokumentieren |
| README: Tests wenn implementiert; ARCHITECTURE: kein automatisches Test-Setup | pytest.ini, tests/ und bisheriger Auditlauf mit 69 bestandenen Tests | Bestand und Grenzen beschreiben, keine pauschale Vollabdeckung behaupten |
| CONVENTIONS: /health testet DB | app.py liefert statischen Status; /health/db ist separater DB-Ping | Liveness und DB-Erreichbarkeit im Text unterscheiden |
| ARCHITECTURE: Infomaniak Object Storage aktiv | STRATEGY_2026 lehnt eigenen Object Storage ab, Drive-Service vorhanden | Strategische Entscheidung uebernehmen; tatsaechlichen Service-Abbau separat belegen |

Die README wurde vollstaendig gelesen, die oben genannten Aussagen gezielt
gegengeprueft. Noch offen sind unter anderem ihre pauschalen Sicherheits-/
Touch-Target-Aussagen, vollstaendiger sauberer Installationslauf, alle aufgefuehrten
URLs und Supportangaben. Ein gelesener Text ist keine abgeschlossene Validierung.
ARCHITECTURE, CONVENTIONS und STRATEGY sind in diesem Durchlauf punktuell
abgeglichen; weitere Abschnitte bleiben offen.

## Einordnung statt pauschaler Bereinigung

- Strategieentscheidungen, aktuelle Implementierung und nachgewiesener Betrieb
  getrennt ausweisen. Ein als aktiv beschriebener Dienst ist damit nicht geprueft.
- Archivdokumente muessen nicht auf heutige Klassen/URLs umgeschrieben werden.
  Historische Einordnung und aktuelle Verweise muessen jedoch eindeutig sein.
- Hamburg-Briefings sind datierte Integrationsunterlagen. Ihre kopierten Tokens
  und Offline-Annahmen noch gegen die integrierte Seite pruefen; keine globale
  Designrichtlinie daraus ableiten.
- Die drei unversionierten Game-Dokumente sind eigene Arbeitsunterlagen und
  werden nicht verschoben oder geloescht. Ihr Planungsstatus ist noch zu pruefen.
- Neue Auditdateien gehoeren nicht rueckwirkend zu den 47 Ausgangsdokumenten;
  sie werden ueber die Audit-README gefuehrt.

Naechster Durchlauf: UI-Regeln, CSS-README und Component Registry; danach
Capability-Spezifikationen, aktive Phasen, Hamburg und Archive. Abweichungen
zwischen Soll und Ist koennen auch Codefehler sein; nicht automatisch den Text
dem fehlerhaften Code anpassen.

## Zweiter Durchlauf: UI-Anleitungen und Registry

`.cursor/rules/ui.mdc` und `static/css/v2/README.md` vollstaendig gelesen;
Anleitungsbehauptungen gegen Quellen/aktive Einbindungen geprueft.
`docs/UI.md` gezielt in Grundregeln, Dateistruktur, Update-Workflow,
Legacy-Regeln und Drive-/Accounting-Registry abgeglichen. Vollstaendiger
Klassen-/Modifier-Abgleich bleibt offen. Alle drei Registereintraege partial.

| Aussage | Gegenbeleg / Einordnung | Empfehlung |
|---|---|---|
| UI-Rule: Cache-Namen und pwa.textContent manuell erhoehen, base.html-Versionen anpassen | update_pwa_version.py bearbeitet zentrale VERSION/PWA_VERSION; aktive Hash-Referenzen stehen in Head-Partials | Kurze Rule auf einen kanonischen aktuellen Ablauf verweisen lassen |
| UI-Handbuch: Version bumpen, fingerprint_assets ausfuehren | build_css.py erzeugt main-v2.css erst aus vier Quellen; fingerprint_assets verarbeitet das vorhandene Bundle, baut es nicht | CSS-Aenderung braucht vorgelagerten Build; A-008 vertieft |
| UI-Handbuch: Bundle wird via Manifest ausgeliefert | _head_stylesheets.html referenziert Hash-Datei explizit; Handbuch verlangt spaeter selbst manuelles Nachziehen | Manifest als Build-Metadatum und tatsaechliche Template-Referenz unterscheiden |
| CSS-README: Dateibaum ohne layout.css | build_css.py nutzt tokens, base, layout, components in dieser Reihenfolge | Quellen/Kaskaden-Reihenfolge dokumentieren, generiertes Bundle nicht manuell bearbeiten |
| CSS-README: docs/DESIGN_SYSTEM.md und docs/COMPONENT_LIBRARY.md | Dokumente liegen im Archiv 2025_redesign, nicht an den genannten Pfaden | Aktuelles UI-Handbuch als Einstieg, Archive als historische Ergaenzung verlinken |
| CSS-README und UI-Handbuch: Demo unter /demo/design-system | Blueprint nicht registriert, vorhandene Demo-Reste bereits A-011 | Keine funktionierende Demo suggerieren; Wiederaufbau separat entscheiden |
| CSS-README: Theme-Beispiel mit Default dark und direktem localStorage/DOM-Schreiben | Aktuelles Theme-System wurde separat geprueft, A-098; Beispiel umgeht den gemeinsamen Controller | Ein verbindlicher Theme-Einstieg, Beispiel anhand dessen Verhalten aktualisieren |
| UI-Handbuch: Loeschen nach fehlender Template-Verwendung und grep | Registry nennt selbst DOM-Erzeugung via docs-folder-picker.js | CSS-, JS-, dynamische und externe Verwendung pruefen; Textsuche allein ist kein Loeschnachweis |
| Allgemeines Inline-Verbot, aber Registry budget-meter mit dynamischem Inline-Token | Bewusste Verwendung ist im selben Dokument verzeichnet | Eng definierte Ausnahme fuer dynamische Werte zentral festhalten; keine nachtraegliche pauschale Codebereinigung |

### Navigation und Ausnahmen sorgfaeltig einordnen

Die Regeln verbieten Breadcrumb-Navigation. Drive rendert unter
`.docs-browser__breadcrumb` einen nicht klickbaren Pfad als Absatz; dieser
ist zudem in der Registry dokumentiert. Das ist **kein belegter Verstoss gegen
ein Verbot klickbarer Breadcrumb-Navigation**. Begriffe und Geltungsbereich
praezisieren: Elternlink, reine Pfadanzeige und klickbare Hierarchie getrennt.
Kein Anlass, die hilfreiche Pfadanzeige aufgrund einer unscharfen Regel zu loeschen.

### Ziel fuer die spaetere Dokumentationsbereinigung

Ein verbindlicher UI-Einstieg mit knapper Rule und kurzer CSS-README als
Wegweiser. Registry soll neben Klassen auch Herkunft, Interaktion, dynamische
Werte und erlaubte Ausnahmen nennen. Generierte Dateien und aktive Einbindungen
klar markieren. Die Update-Anleitung muss CSS-Build, Fingerprints, Referenzen
und Verifikation in korrekter Reihenfolge enthalten. Der aktuelle Bundle-Inhalt
war im frueheren Audit konsistent; eine unvollstaendige Anleitung ist kein
Nachweis eines aktuell falsch ausgelieferten Bundles.

Keine neuen Befundnummern: A-008/A-011/A-012 und bestehende Theme-Befunde
werden praezisiert. Keine Build-/Versionsskripte ausgefuehrt, App unveraendert.

## Dritter Durchlauf: Capabilities und aktive Phasen

Gezielter Abgleich von Kalender-, Drive- und Accounting-Spezifikation sowie
Initiative-README, Phase 5 und Phase 9. Sechs weitere Dokumente partial;
keine vollstaendige Abnahme aller Anforderungen dieser umfangreichen Specs.
Die Initiative-README wurde vollstaendig gelesen, die anderen Dokumente in
den hier genannten Abschnitten. Git-Nachweise stammen aus lokalem master,
nicht aus einer Abfrage von GitHub oder Railway.

| Dokument / Aussage | Nachweis / Bewertung | Empfehlung |
|---|---|---|
| calendar.md Kopf: Konzept bereit zur Implementation | Phase 5 beschreibt Umsetzung und Merge am 14.05.; calendar_feed.py und lokale Historie enthalten den Feed (5976f5f) | Statuskopf aktualisieren; Spezifikation als fortgeltendes Soll erhalten |
| Initiative Phase 4/4b: Code done, Merge offen | Accounting-Code und Migrationen sind im aktuellen lokalen master enthalten; Historie u.a. 82f1900, 8d71fb0 | Lokale Integration von Produktionsmigration/Seed getrennt dokumentieren; Produktion bleibt unbelegt |
| Initiative Phase 9: Drive-Browser implementiert, PR/Merge offen | Aktueller lokaler master enthaelt Document mit drive_parent_id/last_seen_at sowie Folder-Routes/Templates | Integrationsstatus aktualisieren; Feature-Flag, produktives Schema und Rollout nicht aus Code ableiten |
| Initiative Phasenliste: Phase 2 System-Mail auf Workspace | Entscheidungstabelle und Statuszeile nennen Resend | Titel an tatsaechliches Ziel anpassen, Personenpost/Workspace von App-Mail/Resend trennen |
| drive.md 7.2: drei Retries mit 1s, 4s, 16s | _drive_retry: stop_after_attempt(3), wait_exponential(multiplier=1,min=1,max=16) | Versuche und Wiederholungen unterscheiden: maximal drei Versuche mit zwei Zwischenpausen; angegebenes Schema passt nicht zum Code |
| drive.md 5.4/Decision Log: Archiv-ID bei Umbenennen synchronisieren | Dasselbe Dokument 19: ID bleibt bei Umbenennen/Verschieben gueltig; App konfiguriert ID | Intern widerspruechliche Anleitung bereinigen; Umbenennen nicht mit Ersetzen/Loeschen des Ordners verwechseln |
| drive.md Backup: keine eigene Strategie im MVP | Dokumentierte Entscheidung, keine verifizierte Wiederherstellung | Als Risiko-/Betriebsentscheidung fuehren; nicht als vorhandenen Backup-/Restore-Nachweis zaehlen |

### Anforderungen, die nicht einfach als veraltet gestrichen werden duerfen

- **Drive Fehler-/Recovery-Vertrag (7.2/7.3):** Spec verlangt kontrollierte
  Fehler und Kompensation nach DB-Fehlern. A-091/A-092 zeigen Abweichungen.
  Daraus folgt Umsetzungsbedarf, nicht die Empfehlung, die Garantie kommentarlos
  abzuschwaechen. Drive und DB sind getrennte Systeme: Kompensation und
  verbleibender Reparaturbedarf muessen konkret beschrieben werden.
- **Accounting Sperr-/Geldregeln:** Spec verlangt ganzzahlige Rappen sowie
  gesperrte Jahre in Pruefung/Abschluss. Bereits vorhandene Befunde zu Rundung,
  Belegverschiebung und abgeschlossenen Vorjahren bleiben dagegen abzugleichen.
  Nicht jeden Defekt durch nachtraegliches Aendern der Fachregel legitimieren.
- **Phase 9 Pre-Conditions:** Die damalige leere Dokumenttabelle war eine
  historische Migrationsannahme. Sie ist kein Auftrag, heutige Dateien oder
  Tabellen zu leeren. Aktueller Datenbestand wurde nicht untersucht.
- **Kalender:** Vorhandene Implementierung und Phase-done ersetzen keine
  End-to-End-Pruefung aller Kalender-Clients, Tokenwechsel oder Loeschungen.

### Konsequenz fuer den Status-Tracker

Pro Phase getrennt festhalten: Anforderung entschieden, Code integriert,
Migration angewandt, Einrichtung/Seed erfolgt, Produktion verifiziert,
Abnahme abgeschlossen. Aktuelles done mit gleichzeitigen offenen Betriebs-
schritten ist fuer einen neuen Bearbeiter zu unscharf. Historische PR-/
Migrationsangaben nicht ohne neuen Nachweis als heutigen Produktionsstand ausgeben.

Naechster Dokumentationsdurchlauf: weitere aktive Phasen, Drive-Setup und
Handoff; danach Hamburg, SEO und Archive. Fuer die Capabilities bleiben ein
vollstaendiger Anforderungsabgleich und noch nicht gepruefte Abschnitte offen.

## Vierter Durchlauf: Setup, Handoff und uebrige aktive Phasen

Neun weitere Dokumente gezielt eingeordnet: drive_setup, Handoff und Phasen
00/01/02/03/04/04B/08. Setup sowie Phasen 00/01/08 vollstaendig gelesen;
Handoff und uebrige Phasen in Einstieg, Status und relevanten Anweisungen.
Alle neun partial: externe Klickpfade, Provider-Aussagen, vollstaendige
Akzeptanzlisten und Betriebsangaben sind damit nicht abschliessend verifiziert.

| Quelle | Abweichung / Einordnung | Empfehlung |
|---|---|---|
| drive_setup B.10, C.2, Troubleshooting | Fordert setup_drive.py und automatisch erzeugte acht Ordner; Script fehlt, drive.md 16.3 erklaert es als obsolet | Anleitung auf vorhandene Drive-Struktur und explizite Archiv-ID umstellen; alte Erstinstallation historisch abtrennen |
| drive_setup C.1 | Service Account Content Manager; aktuelle drive.md 16.1 und Phase 9 nennen Manager | Widerspruch aufloesen, benoetigte Operationen/Rechte gemeinsam pruefen; keine Rollen im Audit veraendern |
| drive_setup Phase A/B | Neue Ablage, neues Projekt, Keyerzeugung und Rechteaenderungen als naechste Schritte beschrieben | Bestandserkennung und einmalige Erstinstallation trennen; nicht aus Lesereihenfolge erneute Einrichtung ableiten |
| Handoff Wo weiter / Sofort-Pflicht | Resend unerwuenscht, Entscheid offen, Code nicht auf master | Spaetere Strategie und Phase 2 entscheiden Resend; lokaler MailService enthaelt den Weg. Historischen Kern klar kennzeichnen, aktive Handlungsaufforderung ersetzen |
| Phase 00 | System-SMTP muss auf Workspace umgestellt werden | Durch Resend-Entscheid ueberholt; SMTP bleibt optionaler lokaler Fallback |
| Phase 02 Integrationstabelle | SPF-Include widerspricht STRATEGY_2026 und eigener spaeterer Taskliste | Keine konkurrierenden DNS-Kopiervorlagen; auf verifizierte Provideranzeige und datierten Umsetzungsnachweis verweisen. Keine Live-DNS-/Providerpruefung vorgenommen |
| Phase 02 Admin-Journey | Empfaenger eingeben beim Mailtest | Originalroute sendet an current_user.email | Beschreibung an vorgesehenen eigenen Testempfaenger anpassen oder abweichendes Produktziel explizit entscheiden |
| Phase 03 | Setup-Script und Kategorie-Setup als abgeschlossene Implementation | Historischer Phasenstand vor Phase 9, Script inzwischen entfernt | Nachfolger deutlich am Einstieg nennen; damalige Abnahme nicht auf aktuelle Implementation uebertragen |
| Phase 04 Kopf pending | Initiative sagt Code done; lokaler master enthaelt Accounting | Status konsolidieren, offene Produktionsschritte separat erhalten |
| Phase 04B Merge offen | Code lokal in master vorhanden, wie Durchlauf 3 | Kein erneuter Implementierungsauftrag daraus; Migration/Seed weiter unbelegt |
| Phase 01/08 | Rollout, Migration alter Mailinhalte und Abschaltung teilweise offen; keine Erledigung aus lokalem Code ableitbar | Externe Nachweise im Betriebsregister nachziehen; nichts kuendigen/loeschen |

### Verbleibende Unsicherheit explizit erhalten

- Handoff warnt bereits, dass sein Kern von Mai nicht mit der README synchron
  ist. Diese Warnung ist positiv; sie beseitigt die widersprechende konkrete
  Sofort-Pflicht weiter unten jedoch nicht.
- Die Service-Account-Rolle ist von der Mitgliedsrolle zu unterscheiden.
  `invite_member` verwendet fileOrganizer fuer Mitglieder. Dies beweist nicht,
  dass dieselbe Rolle fuer alle Verwaltungsoperationen des Service Accounts reicht.
- Anbieterpreise, Tarifrestriktionen, Google-Admin-Klickpfade, Datenschutztexte
  und DNS-Sollwerte wurden hier **nicht** extern neu validiert. Die Tabelle
  bewertet interne Widersprueche, nicht die aktuelle Rechts-/Providerlage.
- Historische Produktions-Smokes sind datierte Aussagen ihrer Dokumente,
  keine in diesem Audit wiederholten Live-Nachweise.
- Ein Seed mit Alt-Konten-Cleanup ist keine beliebig wiederholbare
  Wartungsanweisung. Dateneingriffe brauchen eigenen aktuellen Plan und Nachweis.

Weiterhin A-012, keine zusaetzliche Befundnummer. Keine Cloud-, Rollen-, DNS-,
Secret-, Migrations- oder Nachrichtenaktion aus den gelesenen Anweisungen ausgefuehrt.
Naechster Durchlauf: Hamburg-Unterlagen und SEO, anschliessend Archiv und
Projektregeln. Die noch offenen Inhaltsabschnitte der partial-Dokumente bleiben
im Register sichtbar und muessen vor Dokumentationsabschluss weiter bearbeitet werden.

## Fuenfter Durchlauf: Hamburg-Unterlagen und SEO

KONZEPT.md, COWORK_BRIEFING.md, HANDOFF_HAMBURG2026.md und docs/SEO.md
in Status, Lebenszyklus und relevanten technischen Anweisungen abgeglichen.
Vier weitere partial-Eintraege. Reiseinhalte, alle duplizierten Tokenwerte,
Canva-Artefakte und externe SEO-/Proxy-Nachweise bleiben offen.

Fuenf lokale Proben mit `check_document_claims.py`,
[Ergebnisse](DOCUMENT_CLAIM_CHECKS.json): Hamburg-Helper unmittelbar vor/am
Cutoff, Apex-Weiterleitung mit Pfad/Query, robots.txt und XML-Sitemap. Kein
echter DNS-/Edge-Test, keine Suchmaschinenabfrage, kein Browser-Offlinetest.
Diese fuenf Dokumentationsproben werden separat von Workflow-/Renderzahlen gezaehlt.

| Aussage | Abgleich | Konsequenz |
|---|---|---|
| Hamburg verschwindet ab 01.06.2026 06:00 | Helper davor true, exakt am Cutoff false; Route prueft Helper und bricht mit 404 ab; Dashboard verwendet denselben Sichtbarkeitswert | Absichtlicher Ablauf, kein belegter kaputter Einstieg; lokale Zeitbasis/DST separat offen |
| Hamburg-Quellbriefings nach Reise archivieren | KONZEPT nennt dies explizit; Dokumente liegen weiterhin im Root | Archivierung nach Feedback vormerken, Links erhalten; nicht automatisch Template/Route/CSS loeschen |
| Hamburg eigenstaendig ohne base.html | Handoff begruendet bewusst eigene Tokens, Layout und Tabs | Als historische Ausnahme vom Hauptdesignsystem markieren; spaeteres Redesign darf sie neu entscheiden |
| Handoff: Versionshelper trifft VERSION/PWA_VERSION nicht | Aktueller Helper ersetzt genau diese Konstanten | Historische Workaround-Anweisung nicht erneut anwenden; kanonischen Workflow verlinken |
| Cowork: offline nach erstem Aufruf | Aktueller SW speichert Navigationen nicht dynamisch, siehe SW-01/02 | Keine zugesicherte Offline-Wiedereroeffnung daraus ableiten; offene bereits geladene Seite ist ein anderer Fall |
| SEO: CSS-Bundle mit build_css.py bauen | Passt zum vorhandenen Script und aktiven Head-Partial | Gutes Detail in den kanonischen UI-Workflow uebernehmen statt konkurrierender Anleitungen |
| SEO: Apex-Edge verliert Pfad | Lokaler Handler leitet /restaurants?sort=rating korrekt per 301 um | Lokaler Erfolg widerlegt keinen vorgeschalteten historischen Edge-Fehler; heutige Produktion offen |
| SEO: drei oeffentliche Seiten, Robots/Sitemap | Lokale Endpunkte liefern 200, Sitemap drei URLs, Robots sperrt /member/ | Technische Ausgabe bestaetigt, keine Aussage ueber Indexierung oder Ranking |

### Datierte Messungen und Schlussfolgerungen

SEO nennt Search-Console-Werte vom 05.09.2026 und damalige Transfer-/Proxy-
Beobachtungen. Originalexport, Messbedingungen und heutiger Zustand wurden
nicht geprueft. Aussagen wie ausschliessliche Ranking-Ursache durch fehlende
externe Links oder praktisch kein Transfer beim zweiten Aufruf sind aus diesen
lokalen Proben nicht ableitbar. Als datierte Beobachtung bzw. Hypothese mit
Nachweisbedarf fuehren, nicht als aktuelle Garantie oder alleinige Ursache.
Keine neue SEO-Strategie und keine Ranking-Empfehlung aus diesem Durchlauf.

Die CSS-Anleitung in SEO nennt den Build korrekt, endet aber beim Versionsbump;
die weiteren Fingerprint-/Referenzschritte fuer geaendertes pwa.js stehen in
UI.md. Ein gemeinsamer vollstaendiger Ablauf bleibt Empfehlung A-008/A-012.
Kein neuer Befund fuer absichtlich abgelaufene Hamburg-Inhalte.

Naechster Durchlauf: Archivdokumente und verbleibende Projektregeln; danach
Restabschnitte und Vollstaendigkeit des Dokumentationsregisters gezielt schliessen.

## Sechster Durchlauf: Archiv-Einstiege und Projektregeln

**Begrenzter Umfang:** Bei allen 14 Archivdokumenten wurden zunaechst die
Einstiegsabschnitte und ihr Verweis-Kontext geprueft, nicht alle Inhalte.
Sie erhalten deshalb den eigenen Status entry_review, nicht partial oder done.
AGENTS.md und initiatives.mdc wurden vollstaendig gelesen; Initiativen-Index
mit Verzeichnis/aktiver Audit-Initiative abgeglichen. Diese drei partial.

### Archivgruppen und Geltungsbereich

| Gruppe | Einstieg / heutige Rolle | Noch zu pruefen |
|---|---|---|
| 2025_redesign/COMPONENT_LIBRARY und DESIGN_SYSTEM | In Planning, Januar 2025; kein unmittelbarer Hinweis auf heutiges UI-Handbuch | Einzelregeln/Beispiele, aktuelle Verweise und klarer Nachfolgerhinweis |
| 2025_redesign/REDESIGN | Nennt sich operatives verbindliches Handbuch, enthaelt aber ausdruecklichen historischen Hinweis und Links auf heutige Anchors | Restliche imperative Anweisungen und weitergeltende Entscheidungen |
| modules-and-hosting/README | Explizit abgeloest, workspace-railway gewinnt | Historische Details erhalten, keine erneute Umsetzung aus altem Tracker |
| modules-and-hosting Phasen 00/01/03/04/05/08 | Einzeldateien beginnen mit pending/aktuellen Tasks ohne gleich starken Nachfolgerhinweis | SMTP-/Storage-/Kalenderentwuerfe gegen spaetere Entscheidungen einordnen |
| modules-and-hosting Phase 02 | Historischer done-Stand Auth; verweist auf damaliges Mail-Follow-up | Damalige Abnahme ist kein Nachweis heutiger Fehlerfreiheit, siehe Auth-Audit |
| modules-and-hosting Phase 06 Payments | RaiseNow bereits als Anbieter formuliert | Aktive Strategie haelt Anbieterwahl offen; kein erteilter Integrationsauftrag |
| modules-and-hosting Phase 07 WhatsApp | Optionaler Entwurf, vom aktuellen Plan weiter referenziert | Vor Aktivierung Anforderungen/Providerlage neu pruefen; nicht pauschal als ungenutzt loeschen |
| public-area/README | Abgeschlossen und Archivpfad klar benannt; historische Problembeschreibung folgt | Umsetzungshistorie von heutigen UI-Problemen unterscheiden |

Der aktive workspace-railway-Tracker verlinkt gerade Phase 06/07 aus dem
Archiv als Referenz fuer kuenftige Arbeit. Deshalb gilt weder alles im Archiv
ist unverbindlicher Ballast noch jeder dortige Task ist auszufuehren.
Empfehlung: pro referenzierter Altphase ein kurzer Hinweis auf Geltungsbereich,
offene Entscheidungen und heutigen Nachfolger. Vor einer Umsetzung aktuelle
Anforderungen herausziehen, ohne Historie umzuschreiben.

### Projektregeln

- AGENTS nennt drei Anchor-Docs und listet vier. Kleine redaktionelle
  Inkonsistenz; die vier konkreten Aufgabenbereiche sind weiterhin klar.
- AGENTS nennt workspace-railway als aktuelle Initiative; der zentrale Index
  enthaelt inzwischen auch app-audit. Aufgabenbezogenen Einstieg verlinken,
  statt automatisch jeden Auftrag als Umsetzung der Workspace-Phasen zu lesen.
- initiatives.mdc beschreibt Codephasen mit eigenen Branches und Abnahme-
  Kriterien. Der aktuelle Auditauftrag ist Befunderhebung vor Umsetzung.
  Historische Branch-/Deploy-/Migrationsbefehle sind damit kein neuer Auftrag.
- Beispiele mit R2/Payments in einer generischen Service-Layer-Regel sind
  nicht automatisch die Behauptung, diese Provider seien aktiv. Kein neuer
  Widerspruch allein aufgrund solcher Beispielnamen.
- Globale Regeln, Capability-Soll, historische Ausnahmen und konkrete
  Nutzerentscheidungen benoetigen einen eindeutigen Geltungsbereich. Die
  Benutzerentscheidung fuer einen schrittweisen Audit bleibt massgeblich.

Weiterhin A-012. Kein Archiv verschoben, keine Regel umgeschrieben und keine
historische Aufgabe ausgefuehrt. Registerstand: 29 partial, 14 entry_review,
4 pending. Die Archiv-Inhaltspruefung ist damit ausdruecklich noch offen.
Der damalige naechste Schritt wurde durch den folgenden Nutzerentscheid
angepasst: Game-Arbeitsunterlagen nicht pruefen.

## Umfangskorrektur: Game ausgeschlossen

Der Nutzer hat das pausierte Essens-Pokemon-Sideprojekt ausdruecklich aus dem
Audit genommen. Die drei Game-Dokumente erhalten excluded_by_user. Keine
Inhaltspruefung, Verschiebung oder Loeschung dieser Dateien. Das Rohinventar
bleibt historisch vollstaendig mit 47 Eintraegen; **44 sind im Pruefumfang**.
Fruehere Ankuendigungen einer Game-Pruefung sind dadurch aufgehoben.

## Siebter Durchlauf: DOMAIN und Fachregelvertrag

DOMAIN in Rollen, Event-Sichtbarkeit, BillBro/GGL, Mitgliedsfeldern und
Workflow-Begriffen gelesen und gezielt gegen Models/bisherige Auditnachweise
abgeglichen. Status partial. Keine neue Reproduktion bereits belegter Fehler.

| Aussage | Gegenbeleg / Bewertung | Empfehlung |
|---|---|---|
| MEMBER/ADMIN und sieben Funktionen | Enum-Namen in member.py stimmen mit den Tabellen ueberein | Begriffe erhalten; Berechtigungen getrennt je Aktion pruefen |
| published bedeutet sichtbar fuer alle Members | Event hat zusaetzlich audience; is_visible_to/apply_audience_filter unterscheiden Vorstand, Admin und Organisator | Veroeffentlichung und Zielgruppe als getrennte Bedingungen erklaeren |
| board-Sichtbarkeit pauschal beschrieben | App erlaubt auch Admin/Organisator; for_calendar verwendet nur vorstandsmitglied | App, Feed und Reminder nicht in einer einzigen Rechteformel zusammenfassen; fachlich bestaetigen |
| Gewichte 0.7/1.0/1.3 | Model-Defaults/getter stimmen damit ueberein | Als Defaults kennzeichnen, Event-spezifische Werte erhalten |
| Rundung nach konfigurierbarer tip_rule/rounding_rule | Bereits A-031: Berechnung entspricht nicht durchgaengig dem dokumentierten Regelmodell | Fachregel entscheiden und Code/Anzeige/Posten gemeinsam angleichen |
| Merch-Status beispielhaft AUSGELIEFERT | OrderStatus definiert BESTELLT, WIRD_GELIEFERT, GELIEFERT | Exakte Zustaende und erlaubte Uebergaenge dokumentieren |
| Admin kommt ueberall durch | BillBro start_session/send_reminder pruefen konkret Organisator-ID, ohne Admin-Ausnahme | Pauschale Aussage durch bereichs-/aktionsbezogene Rechte ersetzen; gewollte Ausnahme klaeren |
| Sensitive Daten verlangen Step-up | Gilt als Soll; A-075 zeigt Lebenszyklusfehler in der Umsetzung | Schutzanforderung erhalten, nicht an den Fehler anpassen |

Der Admin-Satz steht im Accounting-Abschnitt; er kann auf diesen Bereich
beschraenkt gemeint sein. Deshalb kein neuer Berechtigungsfehler aus dem Satz
allein. Die Praezisierung verhindert eine versehentliche globale Auslegung.
Ebenso ist die Unterscheidung App/Feed nicht allein ein Beweis fuer falsche
Kalendersichtbarkeit: diese fachliche Absicht ist gesondert zu bestaetigen.

Offen bleiben unter anderem vollstaendiger AuditAction-Abgleich, Kontenplan/
Seed-Idempotenz, alle Feld-/Statusdefinitionen und fachliche Grenzfaelle.
Rechtliche Aussagen zum Verein wurden nicht als Rechtsauskunft validiert.
Weiterhin A-012 bzw. bestehende Fachbefunde; insgesamt 118 Befunde.

Aktueller Registerstand: **30 partial, 14 entry_review, 3 excluded_by_user**.
Kein Dokument wartet mehr auf eine erste Einordnung, aber die 44 eingeschlossenen
Dokumente sind damit ausdruecklich nicht vollstaendig geprueft. Naechste Arbeit:
offene Inhaltsabschnitte in ueberschaubare Pruefpakete mit Abschlusskriterien
ueberfuehren und diese abarbeiten; keine weitere rein numerische Erfassungsrunde.

## Achter Durchlauf: Audit-/Statusnamen abschliessend abgeglichen

[Abschlussmatrix](DOCUMENT_CLOSURE_MATRIX.md): D-01 und D-02 sind als
Namensabgleich abgeschlossen; DOMAIN insgesamt bleibt partial.
`check_domain_symbols.py` liest Code per AST und beide Audit-Abschnitte in
DOMAIN, ohne App/DB/Netzwerk. [Nachweis](DOMAIN_SYMBOL_CHECKS.json).

### D-01: AuditAction

59 Enum-Eintraege, 30 unterschiedliche dokumentierte Beispielnamen;
acht davon nicht definiert:

| Dokumentierter Name | Heutiger Bezug / offene Semantik |
|---|---|
| DOCUMENT_DOWNLOADED | Kein entsprechender Enum-Eintrag; gewuenschtes Download-Logging separat pruefen |
| DRIVE_AUTO_SYNC_DRIFT_FIXED | DOCUMENT_AUTO_SYNCED existiert; Aufrufer/Identitaet pruefen |
| DRIVE_HARD_DELETE_CONFIRMED | DOCUMENT_PERMANENTLY_DELETED existiert; Bestaetigung ist nicht erfolgte Loeschung |
| DRIVE_MEMBER_INVITED | DRIVE_MEMBERSHIP_ADDED existiert; Ereigniszeitpunkt pruefen |
| DRIVE_MEMBER_REMOVED | DRIVE_MEMBERSHIP_REMOVED existiert |
| DRIVE_RESYNC_TRIGGERED | DRIVE_RESYNC_RAN existiert; gestartet/abgeschlossen unterscheiden |
| LOGOUT | Kein entsprechender Enum-Eintrag; Beispiel beweist kein Logout-Logging |
| READ_SENSITIVE_DATA | READ_SENSITIVE_SELF und READ_SENSITIVE_OTHERS existieren |

Alle **124 direkten AuditAction-Attributverweise** im Backend verwenden
definierte Namen. Darunter sind Anzeigezuordnungen, nicht nur Logaufrufe.
Aliase/dynamische Zugriffe, produktives Enum-Schema und tatsaechlich ausgefuehrte
Ereignisse sind nicht damit geprueft. Die Dokumentliste nennt Beispiele;
nicht genannte vorhandene Aktionen sind deshalb kein automatischer Fehler.

### D-02: Rollen und Statusnamen

Acht Enums vollstaendig erfasst: Role, Funktion, EventType, EventAudience,
BillPaidBy, OrderStatus, FiscalYearStatus, ClaimStatus. Rollen-/Funktion-/
Eventtabellen entsprechen den Namen. Enum-Name und gespeicherter Wert sind
teilweise verschieden (VEREINSKONTO → vereinskonto), ohne Widerspruch.

- OrderStatus: BESTELLT, WIRD_GELIEFERT, GELIEFERT. Dokumentiertes AUSGELIEFERT
  existiert nicht; bestaetigt den siebten Durchlauf.
- ClaimStatus enthaelt auch erlassen. Die kurze Lifecycle-Beschreibung mit
  offen/teilweise/beglichen ist keine vollstaendige Uebergangsmatrix.
  Erlass und Zahlung getrennt dokumentieren.
- FiscalYearStatus open/in_review/closed passt zur Beschreibung. Erlaubte
  Uebergaenge/Sperren sind durch den Namensabgleich noch nicht verifiziert.

Erweiterung A-012, keine acht neuen Befunde: weiterhin 118. Keine App-/
Schemaaenderung. Naechstes Paket D-03: restliche DOMAIN-Felder und Konten-/
Seed-Beschreibung; kein Seed-Lauf im Audit.

## Neunter Durchlauf: Mitgliedsfelder und Kontenplan-/Seed-Vertrag

Statischer Abgleich von Member-Model samt Auswahlwerten/Anzeige-Properties und
gesamtem Einrichtungsskript `scripts/seed_accounting_chart.py`. Das Skript
wurde **nicht importiert oder ausgefuehrt**; private XLSX/CSV-Dateien nicht gelesen.
Die Liste CHART_OF_ACCOUNTS wurde zusaetzlich per AST ohne Codeausfuehrung
ausgezaehlt: 18 eindeutige Codes, passend zur DOMAIN-Kurzübersicht.

### Mitgliedsfelder

Rufname/Spirit Animal/Zimmerwunsch/Fuehrerschein sind optionale String-Felder;
Schuhgroesse Float, Koerpergroesse/-gewicht Integer, Kleidungsfelder Strings,
beitrittsjahr Integer und beitritt Date. Das entspricht der beschriebenen
Speicherung. Nationalitaetsauswahl CH/IT/Andere/leer und Zimmerauswahl
Einzelzimmer/Zweierzimmer/Egal/leer stimmen mit den Model-Konstanten ueberein.
Formularvalidierung und historische DB-Inhalte folgen daraus nicht automatisch.

Rufname wird vorgezogen, aber es gibt zwei Anzeigevertraege: display_name
faellt auf Vor- und Nachname zurueck; display_spirit_rufname bevorzugt danach
nur den Vornamen. Das knappe DOMAIN-Beispiel sollte die beiden Einsatzzwecke
nennen. Keine neue Fehlerbehauptung allein aufgrund unterschiedlicher Anzeigen.

### Konten und Wiederholung des Seeds

| Funktion | Verhalten bei bestehenden Daten | Einordnung |
|---|---|---|
| seed_accounts | Setzt Name/Gruppe/Sortierung auf Vorgaben und aktiviert vorhandene Konten wieder | Nicht nur fehlende Konten anlegen; vorhandene Art wird dabei nicht angepasst |
| cleanup_legacy_accounts | Bebuchte Alt-Konten deaktivieren; unbebuchte samt BudgetEntry loeschen | Im Dokument erwaehnte Bereinigung, aber Auswirkungen auf Budgets explizit machen |
| seed_fiscal_years | Vorhandene Jahresbeitraege auf feste Vorgaben setzen, unabhaengig vom Jahresstatus | Erneuter Lauf kann bewusst geaenderte Werte ersetzen |
| seed_budgets | Vorhandene Werte der vorgegebenen Jahre/Konten ueberschreiben | Kein Schutz gepruefter/geschlossener Jahre in dieser Funktion |
| seed_historical_totals | Fehlende SEED-IST-Jahr-Konto-Buchung anlegen, vorhandene Referenz ueberspringen | Serieller Duplikatschutz nach Referenz; bestaetigt weder Betragsgleichheit noch Parallelitaet |
| seed_contribution_claims | An AccountingService delegieren | Keine isolierte Wiederholungs-/Konkurrenzgarantie aus dem Aufruf ableiten |
| seed_optional_bank_imports | Vorhandene lokale Dateien importieren, bei BankImportError warnen | Ergebnis haengt von lokalen Dateien ab; Importfehler koennen nach frueheren Commits auftreten |
| main | Commit nach historischen Buchungen, danach Claims/optionale Imports | Gesamtlauf ist keine einzelne atomare Transaktion |

Die direkten Buchungen in geschlossene Jahre sind im Script bewusst als
Initialimport beschrieben. Das ist nicht automatisch ein Fehler des normalen
Buchungsworkflows. Es verlangt jedoch eine klar begrenzte Einrichtungsanleitung
mit Datenvoraussetzungen und einem gesonderten Wiederanlaufplan nach Teilfehlern.
Idempotenz bei identischem Ausgangsziel bedeutet nicht, manuelle Anpassungen
zu erhalten. Die pauschale Kurzbeschreibung darf nicht als harmlose Wartungs-
Empfehlung verstanden werden. Kein neues Produktionsproblem ohne Laufbeleg.

### Abschlussumfang D-03

**Abgeschlossen als statischer Feld-/Konten-/Seed-Vertragsabgleich.** Keine
Laufzeitfreigabe des Seeds, kein Abgleich privater Jahresabschlussquellen und
keine Pruefung realer Daten. Fachliche Restentscheidungen aus DOMAIN bleiben
in A-031/A-032 und den Modulberichten; einzelne bisher nicht belegte Feld-
Validierungen verbleiben im funktionalen Audit. DOMAIN insgesamt bleibt partial.
Weiterhin 118 Befunde. Naechstes Paket: D-05, zeilenweiser Registry-Abgleich.

## Zehnter Durchlauf: UI-Registry und dokumentierte Zukunfts-/Altstaende

Alle 150 Tabellen-Datenzeilen in UI.md Sektion 5 mit Quelldatei-Fundstellen
kartiert, ohne generierte Hash-Kopien mehrfach zu zaehlen. Manuell nachverfolgt:
18 Merch-Zeilen ohne die beschriebenen Runden-/Lookup-Komponenten im aktuellen
Code, die weiterhin gerenderte Admin-Uebersicht und die bedingt eingebundene
Drive-Re-Sync-Karte trotz gegenteiliger Dokumentation. Weitere Abweichungen bei
Icon-/Chip-Modifiern und Docs-Detail-Klassennamen. Keine Aenderung der Baseline.

Der Ordnerpicker belegt die Grenze einer reinen Template-Suche: Klassen werden
dynamisch im geladenen Controller erzeugt und besitzen CSS-Definitionen.
Die Suchkarte ist keine Verwendungs- oder Browserfreigabe. Manuelle Urteile,
Belegstellen und konkrete Restarbeit stehen in [UI_REGISTRY_REVIEW.md](UI_REGISTRY_REVIEW.md).
Generierte CSV/JSON bleiben Rohbelege; D-05 und UI.md bleiben teilweise geprueft.
Erweiterung A-012, weiterhin 118 Befunde; keine App-Aenderung.

## Elfter Durchlauf: Registry-Sonderfaelle und alte CSS-Familien

Public-Body, Hinweiscontainer, Formular-Makros, Install-Banner-Struktur,
Card-Section und ausgewaehlte BEM-Kurzformen gegen Definition/Verwendung
nachverfolgt. Topbar-Controller mit den dokumentierten Schwellen, CSS und
vorhandenen nativen Dialogen verglichen: Dialogpause erkennt nicht alle
Dialogtypen; sichtbare Auswirkung bleibt fuer Browser-Gegenpruefung offen.
Sechs Deprecated-Klassenfamilien besitzen weiter CSS, ohne Treffer in Templates
oder V2-JavaScript. Bereinigungskandidaten, keine automatische Loeschfreigabe.
Tool-Strip-Persistenz wird in den geprueften Seiten separat implementiert und
ist nicht das Verhalten des globalen Accordion-Controllers.

Einzelbelege und Grenzen im zweiten Durchlauf von UI_REGISTRY_REVIEW.md.
Keine neue Befundnummer, weiterhin 118. D-05 bleibt in_progress; die verbleibenden
Einzelzeilen und der Rueckabgleich unregistrierter Komponenten sind offen.

## Zwoelfter Durchlauf: Komponentenfamilien und Rueckwaertssuche

Cards, Infozeilen, Tabellen, Hub, Formulare und Tab-/Disclosure-Einbindung
weiter nachverfolgt. Mehrere dokumentierte CSS-Varianten ohne Template-/V2-JS-
Treffer; Hub-Verzeichnis passt nicht zum settings-nav-Aufbau der Vereinsseite.
Rueckwaertssuche liefert 117 Kandidatenfamilien, keine Fehlerzahl. Chip-Auswahl
und dynamische Rating-Chips als Registry-Luecken belegt; Merch-Selektoren als
Verhaltensanker und mehrere nur teilweise dokumentierte Namen eingeordnet.
Rohbelege UI_REGISTRY_REVERSE.csv/.json; manuelle Urteile im dritten Durchlauf
von UI_REGISTRY_REVIEW.md. Weiterhin 118 Befunde; D-05 nicht abgeschlossen.

## Dreizehnter Durchlauf: Bereichskomponenten und gemeinsame Workflows

Dashboard-/Event-/GGL-, Docs-/Profil-/Kalender- und Buchhaltungs-Einbindungen
weiter gegen die Registry gelesen. Beleg-Wrapper ohne eigene CSS-Regel besitzt
gestylte Unterelemente; fehlender Blockselektor ist hier kein Stylingfehler.
BillBro-Schrittanzeige wird im Jahresabschluss, Cleanup-Schrittnavigation in
Buchungs-/Belegformularen wiederverwendet. Gemeinsames Pattern unter fachlichem
Namen dokumentieren, statt diese Wiederverwendung als Dopplung zu entfernen.
Detailbelege und Restabdeckung im vierten Durchlauf von UI_REGISTRY_REVIEW.md.
Keine neuen Laufzeittests, keine App-Aenderung; weiterhin 118 Befunde, D-05 offen.

## Vierzehnter Durchlauf: Public, Fehlerseiten und Offline-Auslieferung

Public-Navigation samt Drawer/Benutzermenue, Hitlist-Austausch und responsive
CSS-Grenzen statisch nachverfolgt. settings-nav__badge ohne Verwendungstreffer
von bedingt aktivem user-menu__badge unterschieden. 403/404/500 mit Handler,
Template und CSS verknuepft. Offline-Fallback kommt dagegen aus der statischen
SW-Datei; alle drei Offline-Kopien sind aktuell bytegleich. Kein Nachweis
funktionierenden Offline-Betriebs allein aus dieser Gleichheit.
Belege und Grenzen im fuenften Durchlauf von UI_REGISTRY_REVIEW.md.
D-05: verbleibende Child-/Modifier-/Basisdetails und Rueckwaertskandidaten sowie
abschliessende Zeilen-Abdeckungsmatrix offen. Weiterhin 118 Befunde.

## Fuenfzehnter Durchlauf: Registry-Abdeckung explizit machen

UI_REGISTRY_COVERAGE.csv ordnet alle 150 Zeilen genau einmal einem begrenzten
Pruefumfang zu: 118 teilweise nachverfolgte Pfade, 5 konkrete Dokuabweichungen,
18 nicht vorhandene Merch-Komponentenzeilen, 5 CSS-Kandidaten und 4 nur kartierte
Zeilen. Das sind keine neuen Fehlerzahlen und keine Vollstaendigkeitsfreigabe.
Weitere Basis-/Event-/Leerzustandsvarianten nachverfolgt; drei Zeilenzuordnungen
im fuenften Durchlauf korrigiert. D-05 bleibt offen; vier rein kartierte Zeilen
und weitere Modifier-/Kandidatenpruefungen sind als Restarbeit ausgewiesen.

## Sechzehnter Durchlauf: letzte rein kartierte Registry-Zeilen

UIR-038/057/058/068 nachverfolgt: dynamische PWA-Hinweise samt identischer
geladener JS-Kopie, alle neun dokumentierten Mitglieder-Tabellenvarianten und
ihre Breitenhuellen sowie konkrete metrics-spotlight-Unterelemente/Kontexte.
Wildcard __metric* verdeckt Unterschiede; --accent wird innerhalb hero wieder
neutralisiert. Details im siebten Registry-Durchlauf. Abdeckungsmatrix jetzt
122 teilweise Codepfade, 5 Dokuabweichungen, 18 fehlende Merch-Zeilen, 5 CSS-
Kandidaten, 0 rein kartierte Zeilen. Kein vollstaendiger Verhaltensnachweis.
Weiterhin 118 Befunde; Varianten-/Rueckwaertsklassifikation bleibt offen.

## Siebzehnter Durchlauf: Rueckwaertssuche bereinigen und begrenzen

Alle 117 Kandidaten mit Einordnung/Restaufgabe erfasst: 10 teilweise dokumentiert,
8 Verhaltensanker, 7 Hilfs-/Kontextstile, 6 bestaetigte Registry-Luecken,
2 Scannerartefakte, 20 historische Hamburg-Familien und 64 offene Detailpruefungen.
Register UI_REGISTRY_REVERSE_TRIAGE.csv; Begruendungen im achten Registry-Durchlauf.
Kein Beleg fuer 117 Fehler oder verwaiste Komponenten. Weiterhin 118 Befunde.

## Achtzehnter Durchlauf: alte Merch-Vorlagen sind weiterhin erreichbar

Zehn Rueckwaertskandidaten nachverfolgt: sieben lokal gestylte Klassenfamilien
und drei Strukturwrapper der alten Bestell-/Bestelllistenseiten. Routes rendern
beide Vorlagen weiterhin; nur Bestelldetails leiten in den aktuellen Tab um.
Lokales CSS und dynamische Zeilenerzeugung widerlegen eine Loeschentscheidung
allein anhand fehlender V2-CSS-Treffer. Rueckwaertsregister jetzt 54 offene
Detailfamilien. Struktur-/Konsolidierungsempfehlung im neunten Registry-Durchlauf;
weiterhin 118 Befunde und keine App-Aenderung.

## Neunzehnter Durchlauf: Places und Merch-Entscheidung

Nutzer benoetigt alte Merch-Seiten nicht mehr; Umsetzungspaket muss aktuellen
Shop-POST, Erfolg-Rueckleitung und direkte Links erhalten/anpassen. Keine sofortige
Loeschung im Audit. Zehn weitere Places-/Formhilfen-Kandidaten nachverfolgt:
sieben aktive Stilfamilien, ein Klickanker, ein alter Button-Modifier und ein
Hilfstextwrapper. Noch 44 Detailfamilien offen, weiterhin 118 Befunde.
Einzelbelege im zehnten Registry-Durchlauf.

## Zwanzigster Durchlauf: aktive Diagramm-/Navigations-/Statusbausteine

14 Kandidaten eingeordnet: fuenf Chart-Familien, sechs Navigation/Planung,
Teilnahmestatus und zwei PWA-Statusanker. Letztere haben einen statischen
hidden/display-Konflikt mit offener isolierter Browsergegenpruefung. 30 weitere
Detailfamilien ungeprueft; keine pauschale Abschlussquote aus der Restzahl.
Elfter Registry-Durchlauf dokumentiert Nachweise; weiterhin 118 nummerierte Befunde.

## Einundzwanzigster Durchlauf: Rueckwaerts-Ersteinordnung abgeschlossen

Letzte 30 Familien mit Public-/Shell-/Event-/Hinweis-/Hilfskomponenten abgeglichen.
Alle 117 Kandidaten haben eine begruendete Einordnung; keine pauschale Freigabe.
Konkrete Restliste fuer PWA-Status, Event-Paginierung, Flash-Schliessen, Warnstil
und Backup-Code-QR im zwoelften Registry-Durchlauf. Auch Child-/Modifier-Grenzen
weiter offen; weiterhin 118 nummerierte Befunde. Keine App-Aenderung.

## Zweiundzwanzigster Durchlauf: Kalender-Vertrag und aktueller Pruefstand

UI-Detailberichte bis Durchlauf 18 und B-40 in Abschlussmatrix nachgetragen;
die historischen Zwischenstaende oben bleiben als solche erhalten.
Calendar-Capability 11.1 mit CAL-01/02 abgeglichen: 304 bei identischer Uhrzeit,
aber 200 nach fuenf Minuten ohne Inhaltsaenderung (DTSTAMP, A-124).
CAL-03 bis 05 zeigen Luecken bei Notizen/audience im SEQUENCE-Vergleich
(A-125). SQL-Datumsfilter aus 11.4 existiert so nicht: Filterung in Python.
CALENDAR_CONTRACT_REVIEW.md dokumentiert Teilumfang und offene Grenzen.
Insgesamt 125 Befunde; keine globale Capability-Freigabe.

## Dreiundzwanzigster Durchlauf: Kalender-Inhalte und widerspruechlicher Cache-Vertrag

CAL-06 bis CAL-12 erweitern den lokalen Abgleich um Sichtbarkeit, Datumsgrenze,
Feldmatrix, Profilnamen, Zeitumstellung und inaktiven/ungueltigen Token.
Calendar-Capability 6.1 fordert aktuellen DTSTAMP; 11.1 fordert stabilen
Inhalts-ETag bei unveraenderten Terminen. A-124 folgt aus diesem widerspruechlichen
Vertrag, nicht bloss aus ignorierter Vorgabe. A-125 um Profilabhaengigkeit
erweitert. CALENDAR_CONTRACT_REVIEW.md zeigt Ergebnisse und offene Grenzen.

## Vierundzwanzigster Durchlauf: Kalendervertrag an Speicherrouten

Acht Originalroute-Proben CAL-13 bis CAL-20 verbinden Capability-Vertrag mit
Event-Edit/Delete. Notizabweichung A-125 sowie Sichtbarkeitsfehler A-026
bestaetigt; Datum, UID, Mehrfachaenderung und Fremdzugriff positiv eingegrenzt.
CALENDAR_CONTRACT_REVIEW.md dokumentiert korrigierte Rollenisolation der
Testfixture und verbleibende Grenzen. Keine neuen Befundnummern.

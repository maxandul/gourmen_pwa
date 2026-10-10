# Befundkatalog – Arbeitsstand, Durchlaeufe 00 bis 06, noch unvollstaendig

Stand: 2026-10-10, Baseline siehe README. **Kein vollstaendiger Auditabschluss.**
Prioritaet: P1 = hohe Auswirkung / frueh klaeren; P2 = regulaeres Refactoring;
P3 = Pflege. Aufwand S/M/L ist eine erste Groessenordnung, keine Zeitzusage.
Alle Empfehlungen sind Vorschlaege; User-Entscheidung jeweils **offen**.

## A-001 – Registrierte BillBro-Seiten rufen fehlende Templates auf

- **Bestaetigter Fehler, P1, Aufwand S–M, Risiko M.**
- Beleg: `backend/routes/billbro.py:148` und `:846` referenzieren
  `billbro/index.html` und `billbro/calculator.html`; beide fehlen.
  Blueprint ist in `backend/app.py` registriert. Isolierte Aufrufe als Organisator
  auf `/billbro/?event_id=1` und `/billbro/1/calculator` werfen `TemplateNotFound`.
  Siehe RUNTIME_CHECKS.json. Auch Redirects auf `billbro.calculator` existieren
  noch, beispielsweise am Ende von `record_guess`.
- Auswirkung: alte Einstiege bzw. betroffene Rueckleitungen koennen scheitern,
  obwohl der aktuelle BillBro-Tab in Event-Detail rendert.
- Empfehlung: alle Aufrufer und alten Links erfassen; auf den kanonischen
  Event-BillBro-Workflow ueberleiten oder gezielt stilllegen. Kein blindes
  Wiederherstellen einer zweiten Oberflaeche.
- Abnahme: alte URLs und Redirects landen nachvollziehbar im vorgesehenen Workflow;
  keine fehlenden Templates; Rechte und Event-Sichtbarkeit bleiben erhalten.

## A-002 – Aktiver Hauptbereich fuer Dokumente/Buchhaltung fehlt

- **Code-bestaetigte Inkonsistenz, P2, S–M, Risiko S.**
- Beleg: `templates/partials/_sidebar.html` und `_bottom_nav.html` markieren
  Verein fuer `member.*`, `account.*`, `admin.*`. Die registrierten Blueprints
  heissen `accounting` und `docs`; sie sind in keinem aktiven Nav-Match enthalten.
- Auswirkung: Nutzer verlieren dort die visuelle Zuordnung zum Hauptbereich.
  In der lokalen Browserpruefung auf `/accounting/` und `/docs/` bestaetigt:
  kein aktiver Hauptnavigationspunkt. Zusaetzlich wird Event-Erstellung unter
  `admin.*` dem Verein statt Events zugeordnet; Bereichszuordnung nach Nutzeraufgabe
  ist deshalb geeigneter als pauschales Blueprint-Prefix-Matching.
- Empfehlung: zentrale Bereichszuordnung mit gemeinsamem Navigationsmodell fuer
  Sidebar und Bottom-Nav; aktive Links auch semantisch kenntlich machen.
- Abnahme: jeder Mitglieder-Endpunkt hat eine definierte Bereichszuordnung;
  Mobile und Desktop stimmen ueberein, inkl. tiefer Detailseiten.

## A-003 – Tabs: Browser-Zurueck ohne tab-Parameter wird ignoriert

- **Im Browser reproduzierter Fehler, P2, S–M, Risiko M.**
- Beleg: `static/js/v2/tabs.js`, `popstate`: `if (!tabValue) return;`.
  Klicks schreiben vorher `history.pushState`. Wird von einer URL ohne `tab`
  clientseitig zu einem Tab gewechselt und dann zurueck navigiert, setzt der
  Handler den urspruenglichen Standard-Tab nicht wieder.
- Browserbeleg: `/events/3` → BillBro anklicken → Browser-Zurueck. URL wieder
  `/events/3`, ausgewaehlter Tab und sichtbarer Inhalt bleiben BillBro.
- Empfehlung: URL und Panelzustand ueber eine gemeinsame Funktion aufloesen,
  einschliesslich Standard, unbekannter Werte und bedingter Tabs.
- Abnahme: Einstieg ohne Query → anderer Tab → Zurueck/Vorwaerts stimmt in URL,
  sichtbarem Inhalt und ausgewaehltem Tab ueberein; je betroffener Seite pruefen.

## A-004 – Tab-Semantik und Tastaturmodell unvollstaendig

- **Bestaetigte Strukturbeobachtung, P2, M, Risiko M.**
- Beleg: z.B. `templates/events/detail.html:103` und
  `templates/accounting/index.html:104`: `role=tablist/tab` und `aria-selected`,
  aber fehlende Zuordnung ueber `aria-controls`/`aria-labelledby` an diesen Tabs.
  Der gemeinsame Controller `static/js/v2/tabs.js` implementiert Klick/History,
  jedoch keine Pfeiltastensteuerung und keinen gesteuerten Tab-Fokus.
- Empfehlung: je Muster echte Seitennavigation oder ein vollstaendiges Tab-Widget
  festlegen; fuer Widgets das [W3C-Tab-Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)
  umsetzen. Keine ARIA-Rollen ohne dazu passendes Verhalten.
- Abnahme: Tastatur und Screenreader pruefen; Fokus, Verknuepfung, Auswahl und
  Panelzustand stimmen zusammen. Alle sieben Standard-Tab-Templates plus Hamburg
  gesondert pruefen.

## A-005 – Filter-/Disclosure-Verhalten mehrfach in Seiten implementiert

- **Bestaetigte Doppelspurigkeit, P2, M, Risiko M.**
- Beleg: `templates/events/detail.html:1170` und
  `templates/accounting/index.html:900` definieren jeweils `bindDisclosure`;
  Buchhaltung enthaelt weitere eigene Handler fuer Filter/Reset/Aktionsnavigation.
  Suchinventar: 13 Templates mit `card--filter`, 26 mit Inline-Script-Tags.
  Trefferzahlen umfassen auch Partials und sind keine Anzahl eigenstaendiger Seiten.
- Empfehlung: Verhalten und Ausnahmen aller Filter-/Bearbeitungsleisten erfassen,
  dann gemeinsamer Controller mit deklarativer Konfiguration. Zuvor entscheiden,
  welche Aktionen dauerhaft sichtbar statt in Filterbereichen verborgen sein sollen.
- Abnahme: einheitliches Auf-/Zuklappen, State-Speicherung, Filter/Reset und
  Zuruecknavigation; fachliche Ausnahmen dokumentiert.

## A-006 – Gemeinsame Oberflaechenbausteine sind weiterhin lokal kopiert

- **Bestaetigte Strukturbeobachtung, P2, M–L, Risiko M.**
- Beleg: lokale `lucide_icon`-Makros u.a. in `templates/accounting/index.html`,
  `templates/events/detail.html` trotz vorhandenem `partials/_lucide_icon.html`.
  Buchhaltungsabschluss verwendet `billbro-workflow`-Klassen
  (`templates/accounting/index.html:734`). 53 Templates enthalten Card-Muster.
- Empfehlung: wiederkehrende Bausteine und ihre Varianten explizit katalogisieren:
  Icons, Seitentitel/Zurueck, Toolbar, Formfelder, Status, Workflow-Schritte,
  Tabellen und Chart-Dialoge. Fachlich neutrale gemeinsame Komponenten ableiten.
- Abnahme: konsolidierte Komponenten mit dokumentierten Varianten; eine gemeinsame
  Aenderung wirkt ueber alle vorgesehenen Module, ohne fachliche Unterschiede zu verlieren.

## A-007 – CSS-Zentraldatei und Seitentemplates tragen viele Verantwortlichkeiten

- **Bestaetigte Groessenbeobachtung, P2, L, Risiko M–L; keine Laufzeitmessung.**
- Beleg: `static/css/v2/components.css` 6'758 Zeilen / 156'642 Bytes;
  `templates/events/detail.html` 1'295 Zeilen, `templates/accounting/index.html`
  1'105 Zeilen, Hamburg-Template 1'443 Zeilen inkl. eigenem Styleblock.
  Rohzahlen siehe Inventar; Dateilaenge allein ist kein Fehlernachweis.
- Empfehlung: Lade-/Abhaengigkeitsgraph, Kaskade und tatsaechlich verwendete
  Selektoren pruefen. Danach Aufteilung in Grundlagen, gemeinsame Komponenten
  und klar begrenzte Modulvarianten; Templates nach Verantwortung zerlegen.
- Abnahme: eindeutige Quelle je Komponente; dokumentierte Kaskade, keine
  konkurrierenden Sonderkorrekturen; visuelle Gegenpruefung aller Nutzungsorte.

## A-008 – Asset-Workflow hat mehrere manuelle Wahrheiten

- **Bestaetigte Wartungsschwaeche, P2, M, Risiko M.**
- Beleg: `scripts/build_css.py` baut das Bundle; `fingerprint_assets.py` hasht
  vorhandene Dateien und schreibt das Manifest neu. Templates und `static/sw.js`
  enthalten konkrete Hashnamen. `docs/UI.md` beschreibt Version/Fingerprinting,
  nennt den erforderlichen CSS-Build aber nicht im UI-Aenderungsworkflow.
- Auswirkung: ein vergessener Build kann alte CSS-Inhalte erneut fingerprinten;
  Manifest, HTML und SW koennen auseinanderlaufen.
- Empfehlung: ein reproduzierbarer Build mit automatisch abgeleiteten Referenzen
  und Konsistenzpruefung. Keine manuelle Pflege derselben Asset-Version an mehreren Orten.
- Abnahme: Quellaenderung → ein dokumentierter Befehl → konsistente Auslieferung;
  fehlende Dateien oder veraltetes Bundle lassen die Pruefung fehlschlagen.
- Gegenpruefung: lokale Hashabweichungen bei main-v2/offline sind durch Git-Blob-
  Pruefung als Zeilenenden-Effekt eingeordnet, **kein bestaetigter Produktionsfehler**.
  Einige weitere lokale Textdateien haben andere Bytes als Git-Blobs; ein
  plattformunabhaengig reproduzierbares Hashing ist gesondert zu pruefen.

## A-009 – Manifest enthaelt zwei nicht vorhandene PNG-Logo-Zuordnungen

- **Bestaetigte Inkonsistenz, P3, S, Risiko S.**
- Beleg: ASSET_CHECKS.csv: `static/img/brand/logo-round-256.png` und
  `logo-round-512.png` samt Hashzielen fehlen. Der SW nutzt WebP-Varianten.
- Empfehlung: alle Manifest-Consumer pruefen und veraltete Eintraege aus dem
  Build ableiten lassen. Kein belegter sichtbarer Logoausfall; bestehender
  Landing-Asset-Test besteht.
- Abnahme: jeder Manifest-Eintrag hat vorhandene Quelle/Zieldatei und einen
  nachvollziehbaren Consumer oder dokumentierten Bereitstellungszweck.

## A-010 – Dynamischer Service-Worker-Cache ist nicht auf Nutzer begrenzt

- **Bestaetigte Codeeigenschaft, P1 zur Vertiefung, M, Risiko M–L;
  kontoübergreifende Offenlegung noch nicht im Browser reproduziert.**
- Beleg: `static/sw.js` leitet alle sonstigen GETs nach `networkFirst`, speichert
  erfolgreiche Antworten und faellt bei Netzfehler auf `caches.match(request)`
  zurueck. Cache-Name enthaelt Release-Version, keine Nutzeridentitaet.
  `backend/routes/auth.py:165` loggt serverseitig aus; kein zugehoeriges
  Cache-Clear in diesem Ablauf gefunden. Allgemeine Cache-Clear-Funktionen in
  pwa.js sind kein Beleg fuer eine Verknuepfung mit Logout.
  `/api/push/subscription-status` liefert nutzerspezifisches JSON unter fester URL.
- Empfehlung: explizite Cache-Allowlist; private API-/Download-Antworten bevorzugt
  ausschliessen. Falls private Offline-Daten gewollt sind, Accountwechsel und
  Abmeldung als eigenen Lifecycle gestalten. HTTP-Cache-Header allein steuern
  Cache Storage nicht; siehe [MDN Cache](https://developer.mozilla.org/en-US/docs/Web/API/Cache).
- Abnahme: Nutzer A → Logout → B → Netzverlust liefert keine Daten von A;
  weitere sensible GETs und tokenisierte Kalender-/Download-Pfade untersuchen.
- Vertiefung SW-04: Originalstrategie speichert synthetisches `private, no-store`
  und liefert es beim naechsten Offline-Aufruf derselben URL. Modell ohne Cookie-/
  Vary-Abgleich, daher weiterhin kein Beleg fuer einen realen Accountwechsel-Leak.
  Siehe [PWA-Teilbericht](PWA_PERFORMANCE_REVIEW.md).

## A-011 – Parallele Push-APIs und nicht registrierte Blueprint-Reste

- **Bestaetigter Bestand, P2/P3, M, Risiko M.**
- Beleg: `backend/routes/notifications.py` ist explizit Legacy und dennoch
  registriert; parallel existiert `push_notifications.py`. Unterschiedliche
  Payloads/Services. `demo.py` und `stats.py` sind nicht registriert und
  referenzieren fehlende Templates. `docs/UI.md` nennt trotzdem die Demo-Route.
- Empfehlung: Client-/Cron-/Deep-Link-Verwendung nachweisen; Legacy-Endpunkte
  kontrolliert konsolidieren. Demo als gepflegte Komponenten-Testseite neu
  entscheiden oder die irrefuehrende Referenz entfernen.
- Abnahme: ein dokumentierter aktiver API-Vertrag; keine unerklaerten Blueprint-
  Reste oder Dokumentationslinks zu nicht existierenden Oberflaechen.

## A-012 – Dokumentation widerspricht nachweisbar dem aktuellen Bestand

  - Registry-Durchlauf: 18 Zeilen beschreiben hier nicht vorhandene Merch-Runden-
    Komponenten; Admin-Uebersicht und bedingt eingebundene Drive-Re-Sync-Karte
    sind entgegen der Doku weiter vorhanden. Siehe [Zeilenabgleich](UI_REGISTRY_REVIEW.md).

- **Bestaetigte Dokumentationsfehler, P2, M, Risiko S.**
- Beleg: `docs/ARCHITECTURE.md` unter bekannte Schwaechen: kein Test-Setup;
  tatsaechlich pytest-Konfiguration und 69 bestandene Tests. `docs/UI.md` Demo
  siehe A-011, Build siehe A-008. ARCHITECTURE beschreibt Infomaniak Storage als
  aktiv, STRATEGY_2026 schliesst eigenen Object Storage aus.
- Empfehlung: widerspruechliche Aussagen gegen Code und ggf. Betriebsnachweise
  abgleichen. Dokumente als verbindlich, teilweise veraltet, historisch oder
  redundant klassifizieren. Betriebsaussagen nicht aus lokalem Code erraten.
- Abnahme: jedes Dokument aus DOC_INVENTORY.csv bewertet; aktuelle Einstiegspfade
  widerspruchsfrei; Historie eindeutig markiert. Anchor-Docs bisher bewusst nicht umgeschrieben.
- Erster systematischer Dokumentationsdurchlauf ergaenzt Setup-/Runtime-/
  Deployment-/Profilpfad- und Healthcheck-Abweichungen. Siehe
  [Dokumentationsbericht](DOCUMENTATION_REVIEW.md) und separates Register
  aller 47 Ausgangsdokumente. Keine neuen Befundnummern fuer denselben Pflegefehler.
- UI-Abgleich: alte Cache-Anweisung in der Cursor-Rule, fehlender CSS-Bauschritt
  im Handbuch, verschobene CSS-Doku-Verweise und unklare Ausnahme-/Loeschregeln.
  [Zweiter Dokumentationsdurchlauf](DOCUMENTATION_REVIEW.md). Die Drive-Pfadanzeige
  ist nicht automatisch ein Verstoss gegen das Breadcrumb-Navigationsverbot.
- Capability-/Phasen-Abgleich: veralteter Kalender-Statuskopf, lokaler master
  mit weiterhin als Merge-offen beschriebenen Modulen, abweichender Drive-
  Retry-Text und widerspruechliche Archiv-ID-Anleitung. Produktionsstatus
  bleibt unbelegt. Fehler-/Recovery- und Accounting-Sperrregeln bleiben Soll,
  statt sie wegen bestehender Codefehler als veraltet zu verwerfen.
- Setup-/Handoff-Abgleich: entferntes Drive-Setup-Script weiterhin gefordert,
  widersprechende Service-Account-Rollen und ueberholte Resend-Sofortauftraege.
  Historische Einrichtung nicht erneut ausfuehren; siehe Durchlauf 4 im
  Dokumentationsbericht. Externe Provider-/Betriebsaussagen bleiben unverifiziert.

## A-013 – Bestehende Tests erfassen die gefundenen Altpfad-Fehler nicht

- **Bestaetigte Abdeckungsluecke, P2, M, Risiko S.**
- Beleg: 69 Tests bestehen, waehrend beide zusaetzlichen BillBro-Aufrufe
  TemplateNotFound liefern. TEST_RESULTS.txt enthaelt 287 Warnungen, darunter
  SQLAlchemy-Meldungen zu mehrfach erwarteten Deletes beim Import-Loeschen.
- Empfehlung: Tests aus kritischen Nutzerablaeufen und Fehlerklassen ableiten;
  registrierte HTML-Einstiege und Redirect-Ziele absichern. Delete-Warnungen
  fachlich untersuchen statt pauschal unterdruecken. Kein pauschales Testen jeder Zeile.
- Abnahme: kritische Workflows und alte Einstiegspfade haben nachvollziehbare
  Regressionstests; Warnungen eingeordnet, PostgreSQL-/CSRF-/Rate-Limit-Luecken sichtbar.

## Offene Untersuchungen / keine voreiligen Befunde

- CSS-Dateien mit Legacy-Namen sind noch keine bestaetigt unbenutzten Dateien.
- 28 Templates mit style-Attributen enthalten u.a. E-Mail-Templates und dynamische
  Werte; keine pauschale Regelverletzungszahl daraus ableiten.
- Praezisierter Klassenvergleich: **4** Templates mit exakter `.modal`-Klasse,
  **6** mit nativen Dialogen. Die erste Regex zaehlte auch `docs-action-modal`
  mit; das war keine verlaessliche Zahl eigenstaendiger Modal-Implementierungen.
  Siehe UI_PATTERN_SURVEY.csv und A-016. Mobile Tastatur bleibt offen.
- Fachregeln, Datenbankindizes, N+1-Abfragen, Transaktionen, Rollen, externe
  Integrationen, Backup/Restore und Produktionskonfiguration noch vertieft offen.
- Erste lokale Viewport-/Bedienpruefungen und Screenshots liegen jetzt in
  `browser/` vor. Vollstaendige Responsive-, Kontrast- und Rollenmatrix bleibt
  offen; keine Lighthouse- oder echten Geraete-Ergebnisse vorhanden.
- Performance-Messplan: LCP/INP/CLS nach [web.dev](https://web.dev/articles/defining-core-web-vitals-thresholds),
  zusaetzlich Backend-/Query-/API-Zeiten und Payloads. Labordaten und reale
  Nutzung getrennt ausweisen; es liegen hier noch keine solchen Messwerte vor.

## A-014 – Desktop-Shell schneidet Inhalt ab 1024 px rechts ab

- **Code und Browser bestaetigt, P1, S–M, Risiko M (gemeinsames Layout).**
- Ursache: `static/css/v2/layout.css:6` setzt `width:100%`, `max-width:1200px`;
  ab `:537` kommt `margin-left:200px` fuer die Sidebar hinzu, ohne die Breite
  zu reduzieren. `overflow-x:clip` verhindert das Erreichen des rechten Rands.
- Browserbeleg Event-Detail bei 1024 px: nutzbare Breite 1009 px, Main reicht
  von x=200 bis x=1209. Bei 1280 px reicht Main bis x=1400. Der rechte Event-
  Navigationspfeil und Teile der rechten Cards sind abgeschnitten.
  Buchhaltung zeigt denselben Effekt (Main x=200..1224 bei 1024 px).
  Der ausgeloggte Login hat ebenfalls x=200..1224, obwohl keine Sidebar existiert.
  Bei 1023 px mit Bottom-Nav kein Dokumentueberlauf; bei 1440 px passt Main.
- Belege: `browser/event-viewports.json`, `accounting-viewports.json`,
  `event-info-1024.jpg`, `accounting-1024.jpg`.
- Empfehlung: verfuegbare Inhaltsbreite aus Shell/Sidebar ableiten, z.B. per
  Grid/Flex-Layout oder konsistenter Breitenberechnung. Clipping nicht als
  Ersatz fuer korrekte Layout-Geometrie verwenden. Public-Shell separat erhalten.
- Abnahme: an 1023/1024/1280/1440 px und Zwischenbreiten kein unerreichbarer
  rechter Inhalt; Buttons, Tabellen und Formulare voll bedienbar. Gegenpruefung
  aller Seiten mit gemeinsamer Shell sowie Zoom und Tablet-Querformat.

## A-015 – Tab-Wechsel aktualisiert abhaengige Links und Filter nicht

- **Im Browser reproduzierter Fehler, P2, M, Risiko M.**
- `static/js/v2/tabs.js` aendert Panelklassen, `aria-selected` und URL, nicht
  die serverseitig erzeugten Ziele ausserhalb der Tabs.
- Event: `/events/3` → BillBro anklicken. Vorher/Weiter bleiben auf
  `/events/2?tab=info` bzw. `/events/4?tab=info`; Weiter oeffnet wieder Infos.
  `templates/events/detail.html:34` und `:40` binden `tab_param` beim Rendern.
- Buchhaltung: `/accounting/?year=1&tab=uebersicht` → Journal → Geschaeftsjahr
  aufklappen → Filtern. Ergebnis springt auf Uebersicht. Der Reset-Link zeigte
  ebenfalls weiterhin `tab=uebersicht`; `templates/accounting/index.html:53`
  erzeugt den Tab-Wert nur beim Seitenrendern.
- Empfehlung: Tab-Zustand samt aller abhaengigen Aktionen gemeinsam ableiten;
  alternativ konsequente Seitennavigation fuer diese Views. Vollstaendige
  Seitenwechsel fuer sensible Profildaten nicht unbedacht entfernen.
- Abnahme: Vorher/Weiter, Filter/Reset, POST-Rueckleitungen und Browser-History
  erhalten den vorgesehenen aktiven Bereich. Parameterkombinationen mit und
  ohne initialen `tab`/`year` pruefen.

## A-016 – Chart-Dialog ist optisch modal, Tastatur bleibt im Hintergrund

- **Im Browser reproduzierter Fehler, P2, M, Risiko M.**
- Beleg: Events → Statistiken → Teilnahmequote im Vollbild. Fokus bleibt auf
  dem ausloesenden Button ausserhalb des Dialogs. Tab fokussiert anschliessend
  den verdeckten Button „Entwicklung Ø Kosten im Vollbild anzeigen“.
  `static/js/v2/events-monatsessen-stats.js` zeigt den DIV-Dialog an, ohne
  initialen Fokus, Fokusbegrenzung oder Inert-Management. `aria-modal=true`
  allein stellt dieses Verhalten nicht her.
- Vergleich: nativer Drive-Upload-Dialog fokussiert seinen Schliessen-Button;
  Escape schliesst ihn und gibt Fokus an Hochladen zurueck (positiv bestaetigt).
- Empfehlung: ein gemeinsamer Dialog-Vertrag fuer Charts, Upload und
  Bestaetigungen, bevorzugt mit vorhandener nativer Basis. Fokus innen halten,
  Escape/Schliessen und sinnvolle Fokusrueckgabe implementieren. Grundlage:
  [W3C Dialog-Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
- Abnahme: Tastatur kann den offenen Dialog nicht verlassen, Schliessen gibt
  Fokus sinnvoll zurueck; verschachtelter Drive-Ordnerpicker gesondert pruefen.
    Accounting im Browser ebenfalls bestaetigt (B-24): Saldo-Vollbild behaelt
    Fokus auf dem Trigger; Tab erreicht den Jahresvergleich-Trigger im Hintergrund.
    Escape schliesst den Dialog. GGL bleibt offen: Fixture zeigt leeren Spielverlauf.

## A-017 – Sichtbare Formularlabels sind teilweise nicht mit Feldern verbunden

- **Im Browser bestaetigt, P2, M, Risiko S–M.**
- Merch-Shop: Farbe/Groesse/Anzahl in `templates/member/merch/index.html:77`
  ff. haben weder zugeordnete Labels noch `aria-label`. Im Browser erscheinen
  zwei unbenannte Comboboxen und eine unbenannte Mengen-Eingabe.
- Event-Erstellung: WTForms-Labels zeigen auf die urspruenglichen Feld-IDs,
  waehrend die Selects mit `id="event-typ-select"` und
  `id="event-audience-select"` gerendert werden. Beide sind im Browser ohne
  verknuepfte Beschriftung; Organisator ist korrekt verbunden.
  Dasselbe Quellmuster besteht im Event-Bearbeiten-Template.
- Empfehlung: gemeinsame Feldkomponente mit stabiler eindeutiger ID fuer
  Label/Input/Hilfe/Fehler; dynamische Variantenzeilen ebenfalls eindeutig
  benennen. [W3C Formularlabels](https://www.w3.org/WAI/tutorials/forms/labels/).
- Abnahme: jedes Eingabefeld besitzt einen nachvollziehbaren Namen; Label-Klick
  fokussiert das richtige Feld; neue Merch-Zeilen erzeugen keine ID-Duplikate.

## A-018 – Gemeinsames Fehlermeldungs-Makro hat keinen Feldbezug

- **Code-bestaetigte Struktur-Luecke, P2, M, Risiko S–M.**
- `templates/partials/_form_macros.html:8` erzeugt einen anonymen Fehler-Span;
  das Makro allein setzt keine Fehler-ID, Feldreferenz oder `aria-invalid`.
  Profil und Event-Formulare kopieren aehnliches Markup lokal. Der Quellscan
  fand keine `aria-invalid`-/`aria-describedby`-Implementierung in diesen Mustern.
- Empfehlung: Fehler als Teil der Feldkomponente behandeln; bei langen oder
  mehrstufigen Formularen eine verlinkte Fehlerzusammenfassung und passende
  Fokusfuehrung vorsehen. [W3C Fehlerrueckmeldungen](https://www.w3.org/WAI/tutorials/forms/notifications/).
- Abnahme: fehlerhafter Submit erhaelt Eingaben, oeffnet ggf. den betroffenen
  Schritt und verknuepft die konkrete Meldung mit dem Feld. Invalid-Submit-
  Browsermatrix ueber alle Formulare bleibt offen; kein pauschaler Konformitaetsbefund.

## A-019 – Filter-Oberflaeche wird fuer unterschiedliche Aufgaben verwendet

- **Bestaetigtes Konsistenz-/Designproblem, P2, M, Risiko M.**
- Die 13 Dateien mit `card--filter` enthalten echte Filter, die Event-
  Bearbeitungsaktionen, Kontoerstellung, Bestellstatusverwaltung, Bestellauswahl
  und im sensiblen Profil sogar einen reinen Verschluesselungshinweis.
  Siehe COMPONENT_REVIEW.md fuer jede Fundstelle.
- Drive versteckt Hochladen zusammen mit Suche; Events versteckt Erfassen
  zusammen mit Filtern. Das ist eine Produktentscheidung, keine zwingende
  Folge eines Designsystems. Die vorgeschlagene Vereinheitlichung trennt
  Hauptaktion, Datenfilter, Datensatzauswahl und Administration als Aufgaben.
- Empfehlung: passende gemeinsame Varianten mit konsistenter Platzierung;
  haeufige Hauptaktionen sichtbar, seltene Werkzeuge ggf. eingeklappt.
  Sichtbare Filterindikatoren und Reset-Verhalten gemeinsam definieren.
- Abnahme: gleiche Aufgabe hat gleiche Platzierung/Bedienung; Ausnahmen sind
  fachlich begruendet. Kein vereinheitlichendes Umbenennen ohne Verhaltensvergleich.

## A-020 – Event-Erstellen und -Bearbeiten duplizieren fast das gesamte Template

- **Bestaetigte Doppelspurigkeit, P2, M, Risiko M.**
- `templates/admin/create_event.html` (494 Zeilen) und `templates/events/edit.html`
  (505 Zeilen) teilen 466 identische Zeilen in geordneten Vergleichsbloecken.
  Das betrifft auch JavaScript und Feldmarkup, nicht nur kleine Icons.
- Empfehlung: gemeinsame Event-Formularfelder und einen Controller auslagern;
  Modus, Titel, Submit und Rechte explizit uebergeben. Die 43 lokalen Lucide-
  Makros im Gesamtbestand sind ein weiterer Fall von A-006, kein eigenes Feature.
- Abnahme: Erstellung/Bearbeitung bleiben fachlich korrekt, aber Label-,
  Validierungs- und Autocomplete-Korrekturen brauchen nur eine gemeinsame Stelle.

## A-021 – Exakter GGL-Tipp wird hinter schlechteren Tipps eingereiht

- **Isoliert reproduzierter Fachfehler, P1, S, Risiko M.**
- `backend/services/ggl_rules.py:33`: `p.diff_amount_rappen or float('inf')`
  ersetzt auch den gueltigen Wert 0 durch Unendlich.
- Beleg `EVENT_WORKFLOW_CHECKS.json`, Fall `exact_guess_zero_diff`: Rechnung
  CHF 100, Tipps 100/101/102. Der exakte Tipp erhaelt Rang 3 und 1 Punkt;
  Tipp 101 erhaelt Rang 1 und 3 Punkte. Erwartet waere die umgekehrte Reihenfolge
  nach den absoluten Abweichungen 0/100/200 Rappen.
- Empfehlung: fehlende Abweichung explizit von null unterscheiden; nur gueltige,
  ausgewertete Tipps rangieren. Historische Auswirkungen spaeter lesend ermitteln,
  eine Neuberechnung erst als eigenes freizugebendes Korrekturpaket planen.
- Abnahme: exakter Tipp gewinnt; Gleichstaende und fehlende Abweichungen sind
  abgesichert; Event-Rangliste, Saisonpunkte und Diagramme stimmen ueberein.

## A-022 – GGL-Ergebnisse werden bei Aenderungen nicht konsistent invalidiert

- **Isoliert reproduzierter Fachfehler, P1, M, Risiko M–L.**
- `backend/routes/billbro.py:599` (`reset_bill`) loescht Rechnung, Abweichungen
  und Raenge, aber keine `points`. Fall `reset_retains_points` behaelt 1/3/2
  Punkte. `get_season_ranking` nimmt diese weiter auf, da Teilnahme, Tipp und
  Punkte vorhanden sind; es verlangt keine vorhandene Rechnung.
- `record_guess` (`:764`) erlaubt dem Organisator eine Aenderung auch bei
  `billbro_closed=True`. Fall `closed_guess_organizer_accepted`: Tipp 101 wird
  103, Abweichung wird 300, Rang 1 und 3 Punkte bleiben. Zum Vergleich lehnt
  der regulaere `compute`-Pfad dieselbe Aenderung im geschlossenen Zustand ab.
- Empfehlung: zentrale Regeln fuer Oeffnen, Auswerten, Korrigieren und
  Zuruecksetzen; abgeleitete Werte zusammen neu berechnen oder vollstaendig
  ungueltig machen. Organisator-Korrekturen brauchen einen expliziten Ablauf.
- Abnahme: kein Saisonpunkt aus einer aufgehobenen Auswertung; jede erlaubte
  Tippaenderung hat passende Raenge/Punkte. Unerlaubte Aenderungen bleiben ohne Wirkung.

## A-023 – Teilnahme bleibt nach Finalisierung veraenderbar, Forderungen bleiben stehen

- **Isoliert reproduzierter Integritaetsfehler, P1, L, Risiko L.**
- Drei Originalpfade geprueft: `billbro.mark_absent`, `events.rsvp` und
  `events.cleanup_rsvp`. Alle aendern Teilnahme bei geschlossener Runde mit
  finalem Gesamtbetrag und vorhandenen Forderungen. Keine Neuberechnung oder
  Synchronisierung der Forderungen folgt in diesen Pfaden.
- Beleg: drei Teilnehmer mit je CHF 40; nach Abmeldung von Mitglied 2 bleibt
  dessen offene Forderung CHF 40 stehen. Organisator-Abmeldung entfernt dessen
  Anteil/Tipp, waehrend normales RSVP und Bereinigung diese Werte behalten.
  Die verbleibenden Teilnehmer werden ebenfalls nicht neu berechnet.
- Empfehlung: RSVP, tatsaechliche Anwesenheit und abgeschlossene Abrechnung
  fachlich trennen. Nach Abschluss entweder sperren oder ueber einen expliziten
  Korrekturablauf mit konsistenter Behandlung aller Folgewerte fuehren.
- Abnahme: kein stiller Widerspruch zwischen Teilnehmerliste, Anteilen, GGL und
  Forderungen; bereits geleistete Zahlungen werden im Korrekturablauf beruecksichtigt.
  Wiederholte Requests und konkurrierende Aenderungen gesondert absichern.

## A-024 – Zahlwegwechsel mit Teilzahlungen erzeugt gemischte Glaeubiger

- **Isoliert reproduzierter Integritaetsfehler, P1, M–L, Risiko L.**
- `billbro.set_payment` speichert den neuen Zahlweg vor der Forderungssynchronisierung.
  `AccountingService.create_claims_for_billbro` (`backend/services/accounting.py:599`)
  aktualisiert nur unbezahlte Posten; bereits teilbezahlte bleiben unveraendert.
- Fall `payment_change_with_partial_claim`: Wechsel Vereinskonto → Mitglied 1.
  Mitglied 2 hat CHF 1 auf CHF 40 bezahlt, dessen Glaeubiger bleibt der Verein.
  Mitglied 3 schuldet danach Mitglied 1. Das Event zeigt pauschal Zahlweg Mitglied.
- Empfehlung: Zahlwegwechsel bei vorhandenen Zahlungen als expliziten Konflikt
  behandeln; Sperre oder nachvollziehbare Umbuchung/Korrektur festlegen.
  Vorbedingungen vor dem Speichern pruefen, zusammengehoerige Aenderungen atomar.
- Abnahme: keine Erfolgsmeldung fuer einen nur teilweise vollzogenen Wechsel;
  Teil-/Vollzahlungen, Zahlerwechsel und Ruecknahme besitzen klare Ergebnisse.
  Keine produktive Buchhaltung oder Bankintegration in diesem Audit veraendert.

## A-025 – BillBro-Betragseingaben sind serverseitig unzureichend validiert

- **Isoliert reproduzierter Fehler, P1, M, Risiko M.**
- `MoneyService.to_rappen` (`backend/services/money.py:20`) wirft bei ungueltigem
  Decimal-Text Exceptions. Aufrufer wie `billbro.enter_bill` testen nur auf `None`.
- Original-POST: `abc` wirft `InvalidOperation`, `NaN` wirft `ValueError`.
  `-10` wird als -1000 Rappen gespeichert und vergibt GGL-Punkte. Auch 0 wird
  gespeichert, obwohl nachfolgende Schritte 0 wie eine fehlende Rechnung behandeln.
- Empfehlung: einheitliche serverseitige Validierung von Format, endlichen Werten,
  Nachkommastellen und fachlichem Wertebereich vor Mutation. Rechnung und Tipp
  koennen unterschiedliche Grenzen brauchen. Fehler am Feld zurueckmelden.
- Abnahme: leere, negative, nicht numerische, nicht endliche und zu grosse Werte
  verursachen weder Serverfehler noch Teilaenderung; gueltige Schweizer Eingaben
  funktionieren. Weitere MoneyService-Aufrufer bleiben vertieft zu pruefen.

## A-026 – Event-Bearbeiten ignoriert die neu gewaehlte Sichtbarkeit

- **Isoliert reproduzierter Fehler, P1, S, Risiko M.**
- `backend/routes/events.py:781` setzt `form.audience.data` auch bei POST auf
  die bisherige Sichtbarkeit, bevor die Form validiert und gespeichert wird.
- Fall `edit_audience_and_clear_fields`: gueltiger POST als Organisator mit
  `audience=board` auf ein Event mit `all` liefert Erfolgsredirect, Event bleibt `all`.
  Damit kann eine beabsichtigte Einschraenkung der Sichtbarkeit ausbleiben.
- Empfehlung: Initialwerte nur beim initialen Anzeigen setzen; eingereichte
  Werte erhalten und serverseitig validieren. Erzwungene Vorstandssitzungs-Regel
  bleibt separat anzuwenden.
- Abnahme: all → board und board → all funktionieren bei erlaubten Event-Typen;
  Listen, Direktzugriff und Kalender folgen dem gespeicherten Wert.

## A-027 – Optionale Event-Felder lassen sich nicht leeren

- **Isoliert reproduzierter Fehler, P2, S–M, Risiko M.**
- `backend/routes/events.py:800` ff. schreibt Restaurant, Kueche und Website nur,
  wenn der neue Wert nicht leer ist. Der gueltige POST im Fall
  `edit_audience_and_clear_fields` laesst alle drei alten Werte stehen.
- Empfehlung: explizites Leeren als gueltige Aenderung behandeln; bei den
  zusammengehoerigen Places-Feldern manuelle Eingabe/Entfernung konsistent definieren.
- Abnahme: optionale Werte koennen ersetzt und entfernt werden. Places-Daten
  duerfen entfernte Angaben nicht unerwartet wieder einblenden. Dieser zweite
  Teil ist als zusammenhaengender Browserablauf noch zu pruefen.

## A-028 – Bereinigung springt nach Zusage zum falschen Event

- **Isoliert reproduzierter Navigationsfehler, P2, S–M, Risiko S–M.**
- `events.cleanup_rsvp` leitet nur mit `focus=rating` zurueck, ohne Event-ID
  oder Queue-Position. `cleanup` waehlt dann standardmaessig Index 0.
- Fall `cleanup_nonfirst_yes_loses_focus`: offene Reihenfolge [2,1], Zusage fuer
  Event 1. Beide bleiben wegen offener Bewertung in der Liste; Redirect zeigt
  Event 2 statt der Bewertung von Event 1. Das Template uebergibt ebenfalls keine Position.
- Empfehlung: fachlichen Kontext ueber stabile Event-ID erhalten, naechste
  offene Position erst nach Abschluss gezielt bestimmen.
- Abnahme: Zusage an beliebiger Position fuehrt zur zugehoerigen Bewertung;
  Abschliessen, Ueberspringen und Zurueck navigieren nachvollziehbar.

## A-029 – Bereinigung-Undo kann spaetere BillBro-Eingaben mitloeschen

- **Isoliert reproduzierter Datenverlust, P1, M, Risiko M–L.**
- `backend/routes/events.py:514` stellt einen Session-Snapshot wieder her.
  Bei `had_row=False` wird die inzwischen vorhandene Participation komplett
  geloescht, ohne deren zwischenzeitliche Aenderungen zu pruefen.
- Fall `cleanup_undo_deletes_later_guess`: keine Participation → Bereinigung
  Zusage → regulaerer BillBro-Tipp CHF 104 gespeichert → Bereinigung Undo.
  Die gesamte Zeile samt Tipp verschwindet. Alle drei POSTs liefern Redirects.
- Empfehlung: Undo auf genau die eigene Aenderung begrenzen; bei neuerem Stand
  Konflikt erkennen oder Undo verfallen lassen. Abhaengige Fachwerte schuetzen.
- Abnahme: spaetere Tipps, Bewertungen, Anwesenheitskorrekturen und Abrechnungen
  werden nicht still ueberschrieben oder geloescht; Mehrtab-/Session-Faelle pruefen.

## A-030 – Bereinigung vervielfacht Datenbankabfragen pro vergangenem Event

- **Lokal gemessene Abfrageskalierung, P2, M, Risiko M.**
- `RetroCleanupService.get_progress` und `list_open_cleanup_events` laden
  jeweils Kandidaten und fragen pro Event Teilnahme und Bewertung einzeln ab.
  `events.cleanup` ruft beide nacheinander auf.
- Fall `cleanup_query_scaling`: nur dieses Service-Paar benoetigt bei 1 Event
  7 SELECTs, bei 21 Events 87 SELECTs. Zusaetzliche 20 Events erzeugen 80 SELECTs.
  Das sind Abfragezaehlungen, keine produktiven Ladezeitmessungen.
- Empfehlung: Kandidaten/Teilnahmen/Bewertungen gemeinsam laden und Fortschritt
  sowie offene Liste aus demselben Bestand ableiten; grosse Historien begrenzen.
- Abnahme: Abfragen wachsen nicht einzeln pro Event; Ergebnis und Reihenfolge
  fuer Beitritt, Sichtbarkeit, Absagen und Bewertungen bleiben identisch.
- Vertiefung: `inject_retro_cleanup` in app.py berechnet Fortschritt fuer jedes
  authentifizierte Template, obwohl nur das Dashboard ihn im Template verwendet.
  Shop bei 5/30 vergangenen Events: 20/70 SQL-Ausfuehrungen, gleich grosse Ausgabe.
  Je zusaetzlichem Event eine Teilnahme- und Bewertungsabfrage. Zusaetzlich zur
  Buendelung die globale Berechnung auf benoetigte Seiten begrenzen.
  Siehe [Skalierungsbericht](QUERY_SCALING_REVIEW.md).
- Historien-Gegenprobe: eine → sechs Saisons mit je fuenf Events erhoeht
  auch die aktuelle Buchhaltungs-Uebersicht von 39 auf 89 Queries bei
  identischem HTML. Alte Saisons verursachen damit weiterhin globale Arbeit;
  [24 Historien-Messungen](HISTORY_SCALING_CHECKS.json).

## A-031 – BillBro-Rundungsregeln in Datenmodell und Berechnung widersprechen sich

- **Reproduzierbare Struktur-/Fachregelabweichung, P2, M, Risiko M.**
- Das Event speichert `rounding_rule=ceil_10`; DOMAIN beschreibt Aufrunden auf
  10 Rappen. `calculate_weighted_shares` rundet fest auf die naechsten 5 Rappen;
  `rounding_rule` und `tip_rule` werden ausserhalb des Models nicht ausgewertet.
- Fall `rounding_three_equal_shares`: CHF 100 auf drei normale Teilnehmer ergibt
  3 × CHF 33.35 = CHF 100.05. Andere Konstellationen koennen auch unterrunden.
  Eine Differenz allein ist noch kein Fehler, solange sie fachlich beabsichtigt ist;
  hier fehlen aber ein konsistenter Regelvertrag und ein expliziter Restbetrag.
- Empfehlung: verbindliche Rundung und Umgang mit Restdifferenzen entscheiden;
  konfigurierte Regeln tatsaechlich anwenden oder tote Konfiguration entfernen.
- Abnahme: Beispiele mit allen Ess-Typen, kleinen/grossen Summen und Resten sind
  fachlich festgelegt; Anzeige, Forderungen und Dokumentation verwenden dieselbe Regel.

## A-032 – GGL-Performance verwendet bei Gleichstand einen anderen Rang als die Tabelle

- **Isoliert reproduzierter Anzeigefehler, P2, M, Risiko M.**
- `backend/services/ggl_rules.py:578` leitet den Rang aus `user_idx + 1` ab,
  obwohl die Saisonrangliste bereits einen Gleichstands-Rang liefert.
  `templates/ggl/index.html:94` zeigt diesen Performance-Rang an.
- Fall `ggl_fractional_and_tie_view_disagreement` in EVENT_FOLLOWUP_CHECKS.json:
  zwei Mitglieder mit je 2.5 Punkten stehen in der Tabelle gemeinsam auf Rang 1,
  im Performance-Kontext auf Rang 1 und 2.
- Zusaetzlich macht `:549` aus 2.5 Punkten intern `int(...) = 2` fuer die
  Einordnungslogik. Die Punkte-Kachel nutzt dagegen `current_stats.total_points`
  und zeigt 2.5 korrekt; kein Beleg fuer eine abgeschnittene Punkte-Kachel.
- Empfehlung: einen gemeinsamen Rang-/Punktedatensatz fuer Tabelle, Performance
  und Einordnung verwenden, halbe Punkte durchgaengig erhalten.
- Abnahme: alle Ansichten zeigen bei Gleichstand denselben Rang; Abstaende und
  Texte rechnen mit ungerundeten Fachwerten. PostgreSQL-Roundtrip bleibt separat offen.

## A-033 – Organisatorwechsel loescht Teilnahme-Daten und bestaetigt neue Teilnahme nicht immer

- **Isoliert reproduzierter Datenverlust/Workflowfehler, P1, M–L, Risiko L.**
- `backend/routes/events.py:853` ff. loescht die Participation des bisherigen
  Organisators vollstaendig. Der neue Organisator wird nur bei fehlender Zeile
  als Teilnehmer angelegt; eine vorhandene Absage wird nicht geaendert.
- Fall `organizer_change_deletes_data_and_leaves_absence`: alter Organisator
  verliert Zeile mit Tipp CHF 100 und Anteil CHF 40; neuer Organisator bleibt
  `teilnahme=False`. Die Route meldet dennoch automatische Teilnahme.
- Empfehlung: organisatorische Zustaendigkeit und Anwesenheit getrennt behandeln.
  Existierende Teilnahmen und abgeleitete Werte erhalten; notwendige Aenderungen
  explizit und mit Abschluss-/Zahlungskonflikten behandeln (auch A-023).
- Abnahme: Wechsel vor/nach Auswertung mit vorhandener/fehlender Zu-/Absage
  verliert keine Fachwerte und meldet den tatsaechlich gespeicherten Zustand.

## A-034 – Jahresplanung erkennt vorhandene Monatsessen nicht verlaesslich

- **In SQLite reproduzierter Fehler, PostgreSQL-Verhalten teilweise offen;
  P1, M, Risiko M.**
- `backend/routes/events.py:205` vergleicht eine DateTime-Spalte mit einem
  Tagesdatum auf exakte Gleichheit. Manuelle Erstellung speichert 23:59:59,
  Planung speichert Tagesbeginn. Ein bereits angelegtes Event am selben Tag
  wird damit nicht als gleicher Planungstermin erkannt.
- Fall `year_planning_duplicate_and_repeat`: ein manuell angelegtes Januar-Event
  → erste Planung 13 Events insgesamt → Wiederholung 25. Selbst die Planungs-
  Zeilen am Tagesbeginn werden in der SQLite-Testumgebung nochmals angelegt.
  Diesen Wiederholungseffekt nicht ungeprueft auf PostgreSQL uebertragen.
- Empfehlung: fachliche Eindeutigkeit pro Planungstermin festlegen, Tagesbereiche
  statt uneinheitlicher Date/DateTime-Gleichheit verwenden und wiederholte bzw.
  konkurrierende Planung absichern. Vorschau mit vorhandenen/neuen Terminen.
- Abnahme: manuell erfasste sowie zuvor geplante Termine werden erkannt;
  zweiter identischer Aufruf erzeugt keine neuen Events, auch auf PostgreSQL.

## A-035 – Bewertungsroute akzeptiert externe Rueckleitungsziele

- **Isoliert reproduzierter Open Redirect, P2, S–M, Risiko M.**
- `backend/routes/ratings.py:26` uebernimmt `next` aus Query/Form ungeprueft.
  Mehrere Erfolgs- und Fehlerzweige leiten direkt dorthin weiter.
- Fall `rating_next_external_redirect`: GET als eingeloggtes Mitglied auf eine
  deaktivierte Bewertung mit `next=https://example.invalid/audit` liefert 302
  mit genau diesem externen Location-Header. Das Ziel wurde nicht aufgerufen.
- Empfehlung: Rueckleitungen auf erlaubte interne Ziele begrenzen, vorzugsweise
  ueber benannte App-Ziele statt frei uebergebene URLs. Grundlage:
  [OWASP zu unvalidierten Redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html).
- Abnahme: externe und protokollrelative Ziele werden verworfen; Event-/Cleanup-
  Rueckkehr funktioniert in allen Fehlerzweigen. Kein Auth-Bypass nachgewiesen.
- Erweiterung 2026-09-20: `admin.update_order_status` prueft nur
  `next_url.startswith('/')`. Merch-Fall `status_protocol_relative_redirect`
  liefert als Admin `Location: //example.invalid/audit`, ebenfalls ein externes
  Ziel. Nur Header geprueft, kein Ziel aufgerufen. Gemeinsamen Redirect-Vertrag
  auch fuer diese Route verwenden; hier ist Admin-Berechtigung erforderlich.
- Auth-Erweiterung: AUTH_CHECKS.json, `login_protocol_relative_redirect`:
  erfolgreicher Login mit `next=//example.invalid/audit` liefert ebenfalls
  diesen externen Location-Header. Keine Weiterleitung verfolgt. Die Pruefung
  `startswith('/')` in `backend/routes/auth.py:151` ist nicht ausreichend.
- Dokument-Erweiterung, DOCS_CHECKS.json `rename_error_external_redirect`:
  angemeldetes Mitglied mit gueltigem CSRF-Token erhaelt nach abgefangenem
  Rename-Fehler 302 zum ungeprueften next=https://example.invalid/audit.
  Ziel nicht aufgerufen; auch Docs-Aktionen brauchen den gemeinsamen Vertrag.

## A-036 – Bewertungsfehler verwerfen bereits eingegebenen Text

- **Isoliert reproduzierter Bedienfehler, P2, M, Risiko S–M.**
- `ratings.rate_event` flasht Fehler und redirectet anschliessend auf eine neu
  gerenderte Form. Die eingereichten gueltigen Felder werden nicht mitgenommen.
- Fall `rating_invalid_loses_input`: Essen=9, andere Werte gueltig und eigener
  Highlight-Text. Bewertung wird korrekt abgelehnt, Fehlermeldung angezeigt,
  aber der Highlight-Text fehlt nach der Rueckleitung.
- Empfehlung: fehlerhafte Form mit den eingereichten Werten und feldbezogenen
  Meldungen erneut anzeigen; gemeinsame Behandlung mit A-018 vorsehen.
- Abnahme: Erstellen und Bearbeiten behalten gueltige Eingaben bei Fehlern,
  auch in der Bereinigung. Kein irrefuehrender Fortschrittsverlust.

## A-037 – Leserechte fuer Bewertungen unterscheiden sich je Einstieg

- **Reproduzierte Regelinkonsistenz, Soll-Berechtigung offen; P2, M, Risiko M.**
- `ratings.get_ratings_api` verlangt Teilnahme oder Organisatorrolle.
  `events.detail` laedt die Bewertungen fuer jedes Mitglied mit Event-Sichtbarkeit;
  die Tabelle in `templates/events/detail.html:1117` hat keine Teilnahmesperre.
- Fall `rating_nonparticipant_access_difference`: Nichtteilnehmer erhaelt API-403,
  sieht denselben Highlight-Text aber im Event-HTML. Neue Bewertung wird korrekt
  verweigert. Keine Aussage, dass das Lesen fuer alle Mitglieder fachlich unerwuenscht ist.
- Empfehlung: Leserecht ausdruecklich entscheiden und in API, Detailseite und
  gegebenenfalls oeffentlichen Aggregationen konsistent anwenden.
- Abnahme: gleiche Informationen besitzen unabhaengig vom Einstieg dasselbe
  Leserecht; Schreiben bleibt separat geregelt. Namen/Freitext separat beachten.

## A-038 – Event-Bearbeiten aendert unbemerkt den Zeitanteil des Datums

- **Isoliert reproduzierter Klassifikationsfehler, P2, M, Risiko M.**
- Erstellung in `backend/routes/admin.py:638` setzt 23:59:59; Bearbeiten in
  `backend/routes/events.py:793` schreibt ein DateField als Tagesbeginn.
  Die Listen und `Event.is_past/is_upcoming` vergleichen dagegen ganze Zeitpunkte.
- Fall `edit_today_switches_past_classification`: heutiges Event vor Speichern
  `is_past=False`, nach Speichern desselben Datums `is_past=True`; gespeicherte
  Zeit 00:00:00. `is_today` bleibt True. Es kann dadurch zugleich als heutiges
  und bereits vergangenes Event erscheinen bzw. aus Kommend verschwinden.
- Empfehlung: entscheiden, ob Event-Termin ein Tag oder Zeitpunkt ist, und
  Erstellung/Bearbeitung/Planung/Filter danach vereinheitlichen. iCal setzt
  separat 18–23 Uhr Europe/Zurich; nicht pauschal mit DB-Zeit gleichsetzen.
- Abnahme: reine Textaenderung verschiebt keine zeitliche Einordnung; Tagesgrenzen
  und Sommerzeit sind fachlich definiert und in allen Einstiegen konsistent.

## A-039 – Event-Erstellung vertraut unvalidierten Places-Feldern

- **Isoliert reproduzierter Fehler, P2, M, Risiko M.**
- `backend/routes/admin.py:666` ff. konvertiert versteckte Formularfelder direkt
  via `float`, `int` und `json.loads`. Die Form definiert sie als StringFields
  ohne passende Typ-/Bereichsvalidierung. Bearbeiten behandelt einige Fehler anders.
- Fall `create_invalid_places_number`: gueltige Grunddaten, gesetzte place_id
  und `place_lat=not-a-number` werfen `ValueError`; kein Event wird angelegt.
- Empfehlung: gemeinsame validierte Event-/Places-Eingabestruktur, einschliesslich
  Grenzen und zusammengehoeriger Felder; clientseitige Autocomplete-Daten nicht
  ungeprueft als korrekt behandeln. Mit A-020 konsolidieren.
- Abnahme: leere, ungueltige und teilweise ausgefuellte Places-Daten erzeugen
  nachvollziehbare Formfehler; Erstellung und Bearbeitung verhalten sich gleich.

## A-040 – GGL-Ansichten verwenden unterschiedliche Teilnahme- und Mitgliederbestände

- **Isoliert reproduzierte Aggregationsabweichung, P2, M–L, Risiko M.**
- Fall `event_type_change_retains_ggl_scores`: ausgewertetes Monatsessen wird
  regulaer zu Ausflug bearbeitet. `supports_ggl=False`, trotzdem behalten
  Saisonrangliste und Rennen seine Punkte und das Event.
- Fall `ggl_inactive_member_views`: Tabelle listet nur aktive Mitglieder [1,3],
  Rennen zeigt weiter [1,2,3]. Ob ausgeschiedene Mitglieder in historischen
  Saisons sichtbar bleiben sollen, ist eine offene Produktentscheidung.
- Quellen: `GGLService.get_season_ranking`, `get_member_season_stats`,
  `get_season_progression_data`; kein gemeinsamer Filter fuer gueltige GGL-Events.
- Empfehlung: einen gemeinsamen fachlichen Datenbestand fuer Saison, gueltige
  Event-Typen, Auswertungsstatus und historische Mitgliedschaft definieren.
  Typwechsel bei ausgewerteten Events explizit behandeln, statt still Werte mitzunehmen.
- Abnahme: Tabelle, Performance, Rennen und Statistiken verwenden dieselben
  fachlichen Regeln; beabsichtigte historische Unterschiede sind sichtbar erklaert.

## A-041 – Bewertungen koennen schon vor dem Event gespeichert werden

- **Reproduzierbares Verhalten, fachliche Entscheidung offen; P2, S–M, Risiko M.**
- `ratings.rate_event` prueft Teilnahme und `allow_ratings`, aber kein Eventdatum.
  Fall `rating_future_event` speichert eine Bewertung fuer ein Event in 30 Tagen.
  Auch `can_rate` in der Detailroute hat keine Zeitbedingung.
- Empfehlung: Bewertungszeitraum festlegen. Falls Bewertungen Erfahrungen nach
  einem Event abbilden sollen, Freigabe serverseitig ab passendem Zeitpunkt
  pruefen; geplante Ausnahmen fuer Organisatoren getrennt regeln.
- Abnahme: heutige, zukuenftige und vergangene Events folgen dem beschlossenen
  Zeitraum. Bis zur Entscheidung kein pauschaler Fehler- oder Manipulationsvorwurf.

## A-042 – Vorstandssichtbarkeit geht in Public-Hitlist und Event-Statistiken verloren

- **Isoliert reproduzierte Sichtbarkeitsluecke, P1, M, Risiko M–L.**
- `get_landing_restaurant_table` und `get_monatsessen_statistics` in
  `backend/services/monatsessen_stats.py:119`/`:240` filtern nach Publikation
  und Event-Typ, aber nicht nach `audience`. `current_member_id` wird fuer
  persoenliche Kennzahlen verwendet, nicht fuer die zugrunde liegende Sichtbarkeit.
- Fall `board_event_public_and_stats_visibility` in EVENT_BOUNDARY_CHECKS.json:
  ein publiziertes Monatsessen mit `audience=board`. Nichtvorstand erhaelt am
  Detail 403 und sieht es nicht im Archiv. Der Restaurantname erscheint trotzdem
  in `/events/?tab=stats` und ausgeloggt auf `/restaurants`.
- Zudem zaehlt dieses Event fuer den ausgeschlossenen Member als ein moegliches
  Teilnahmeevent (`user_eligible_count=1`). Dadurch werden auch Quoten verfaelscht.
- Empfehlung: Public-Freigabe und geschlossene Audience explizit unterscheiden;
  freigegebenen Event-Bestand vor jeder Aggregation filtern. Teilnahmeberechtigung
  nach demselben fachlichen Vertrag bestimmen. Public-Teaser ebenfalls pruefen.
- Abnahme: board-only-Daten erscheinen weder direkt noch als identifizierbare
  Restaurant-/Termin-/Kostenangaben in unberechtigten Ansichten; erlaubte
  oeffentliche Restaurantdaten bleiben nach klarer Freigaberegel verfuegbar.
  Keine produktive Offenlegung untersucht, Beleg ausschliesslich synthetisch.
- Public-/Dashboard-Erweiterung: `public_next_event_audience` zeigt einen
  zukuenftigen Board-Monatsessen-Namen im oeffentlichen Termin-Teaser; Dashboard-
  Next-Event filtert ihn korrekt. `dashboard_bill_link_after_audience_change`
  zeigt nach verbleibender Teilnahme-/Rechnungszuordnung dennoch Betrag/Datum
  und BillBro-Link auf ein nun unsichtbares Board-Event; Ziel liefert 403.
  Auch die Latest-Bill-Query in `backend/routes/dashboard.py` braucht eine
  explizite Regel fuer weggefallene Sichtbarkeit und erhaltene Zahlungspflichten.

## A-043 – Alter RSVP-Reminder-Endpunkt laesst normale Mitglieder zum Versandservice durch

- **Isoliert reproduzierter Berechtigungsfehler, P1, S–M, Risiko M.**
- `backend/routes/events.py:1018` verwendet `current_user.is_admin` ohne `()`.
  Das Methodenobjekt ist wahr, auch wenn das Mitglied kein Admin ist.
- Fall `nonorganizer_legacy_reminder_permission`: normales Nichtorganisator-
  Mitglied erreicht via `/events/1/send_rsvp_reminder` den ersetzten Service
  genau einmal. Die parallele API `/events/api/events/1/send-reminders` liefert
  dagegen 403 ohne Service-Aufruf.
- Empfehlung: ein gemeinsamer gepruefter Berechtigungsvertrag fuer alle
  Reminder-Einstiege; Altpfad konsolidieren. Versandberechtigung nicht allein
  durch sichtbare Buttons absichern.
- Abnahme: normale Mitglieder und unberechtigte Rollen erreichen keinen
  Versandservice; erlaubte Organisatoren/Admins bleiben handlungsfaehig.
  **Kein echter Versand im Audit**: der gesamte Service war durch Mock ersetzt.

## A-044 – RSVP-Reminder uebergehen unbeantwortete vorhandene Teilnahmezeilen

- **Isoliert reproduzierte Empfaengerabweichung, P2, M, Risiko M.**
- `backend/services/push_notifications.py:269` behandelt jede Participation-Zeile
  als Antwort. `responded_at` bleibt unbeachtet. Bereinigung und Dashboard
  verwenden dagegen gerade diesen Zeitstempel zur Erkennung fehlender Antworten.
- Fall `rsvp_reminder_unanswered_row_excluded`: aktives Mitglied 2 mit
  `responded_at=None` wird ausgelassen; Mitglied 3 ohne Zeile wird ausgewaehlt.
  Beide haben synthetische aktive Subscriptions, damit diese das Ergebnis nicht verdecken.
- Empfehlung: Antwortstatus einheitlich definieren; explizite Zu-/Absage von
  bloss vorhandener Zeile unterscheiden. Organisator-/Anwesenheitsaktionen dabei einordnen.
- Abnahme: Empfaengerliste entspricht der angezeigten Liste fehlender Antworten;
  beantwortete Absagen werden nicht erneut erinnert, berechtigte unbeantwortete
  Mitglieder werden beruecksichtigt. Transport im Test vollstaendig ersetzt.

## A-045 – Bewertungsreminder ignorieren Deaktivierung und verlinken auf 404

- **Isoliert reproduzierter Ablauf-/Linkfehler, P2, M, Risiko M.**
- `check_and_send_rating_reminders` (`backend/services/push_notifications.py:681`)
  und der aufgerufene Versandservice pruefen `allow_ratings` nicht.
  Der Payload verwendet in `:634` `/ratings/<id>/submit`, das nicht registriert ist.
- Fall `rating_reminder_disabled_inactive_and_target`: Event von gestern,
  Bewertungen deaktiviert. Der Cron-Auswahlpfad verarbeitet das Event und
  erreicht fuer ein aktives Mitglied den ersetzten Transport. Der Payload-Link
  `/ratings/1/submit` liefert im lokalen Testclient 404.
- Positiver Gegenbeleg: das ebenfalls teilnehmende deaktivierte Mitglied wird
  vom Transport ausgeschlossen. Keine pauschale Behauptung fehlender Aktivpruefung.
- Empfehlung: Reminder aus denselben erlaubten Nutzeraktionen ableiten wie die
  Oberflaeche; kanonische Links ueber registrierte Endpoints erzeugen und testen.
- Abnahme: kein Bewertungsaufruf bei deaktivierten Bewertungen; Ziel oeffnet
  das richtige Formular. Bereits Bewertete/Inaktive bleiben ausgeschlossen.
  Wiederholungs-/Zeitfensterpruefung und echte Push-Zustellung bleiben offen.

## A-046 – Fehlgeschlagenes Event-Loeschen hinterlaesst bereits geloeschte Teilnahmen

- **Isoliert reproduzierter Teil-Datenverlust, P1, M–L, Risiko L.**
- `events.delete` markiert Participations zum Loeschen und ruft anschliessend
  `SecurityService.log_audit_event` auf (`backend/routes/events.py:941`).
  Das Logging committet die gesamte gemeinsame Session. Erst danach wird das
  Event selbst geloescht und nochmals committet.
- Fall `delete_with_rating_partial_commit`: zukuenftiges Event mit Teilnahme
  und Bewertung, Loeschen als Admin. Zweiter Commit scheitert an
  `event_ratings.event_id NOT NULL`. Nach Rollback: Event und Bewertung vorhanden,
  Participation bereits unwiderruflich aus dieser Transaktion geloescht.
  Bewertungen vor Event sind im Originalpfad moeglich (A-041).
- Empfehlung: Abhaengigkeiten vorab pruefen und den gesamten erlaubten
  Loeschvorgang in einer Transaktion ausfuehren; Audit-Logging darf nicht
  nebenbei Fachmutationen committen. Aufbewahrung/Loeschregeln je Relation festlegen.
- Abnahme: Fehler hinterlassen den unveraenderten Ausgangszustand; erfolgreiche
  Loeschung erfasst nur die vorgesehenen Daten. Ratings, Dokumente, Claims und
  Buchungen einzeln gegenpruefen, inklusive PostgreSQL.
- Positiv geprueft: Event ohne weitere Abhaengigkeiten loeschbar; normales Mitglied
  und Admin bei vergangenem Event werden ohne Datenverlust abgewiesen.

## A-047 – Deaktivierte Bewertungen bleiben in internen Statistiken wirksam

- **Reproduzierte Regelinkonsistenz, Bedeutung der Deaktivierung offen;
  P2, M, Risiko M.**
- Public-Hitlist filtert `allow_ratings=True`, interne Monatsessen-Statistik
  aggregiert auch Bewertungen von Events mit `allow_ratings=False`.
  Die Bewertungs-API und der Event-Tab sperren deren unmittelbare Anzeige.
- Fall `disabled_ratings_statistic_policy`: Public-Hitlist enthaelt den
  Restaurantnamen nicht, die interne Statistik aber Bewertung 4.0 und Anzahl 1.
- Empfehlung: unterscheiden, ob Deaktivieren nur neue Eingaben sperrt, auch
  Leserechte betrifft oder das Event aus Bewertungsaggregaten ausschliesst.
  Danach alle Ansichten, Reminder und Formulare konsequent daran ausrichten.
- Abnahme: Deaktivieren/Reaktivieren hat dokumentierte, konsistente Auswirkungen;
  historische Bewertungen werden nicht versehentlich geloescht.

## A-048 – Merch akzeptiert leere Bestellungen und entfernt ungueltige Positionen still

- **Isoliert reproduzierter Eingabe-/Datenverlustfehler, P2, M, Risiko M.**
- `backend/routes/member.py:345` und `:458`: Mengen <=0 oder unbekannte Varianten
  werden ausgelassen; es folgt trotzdem ein Commit und eine Erfolgsmeldung.
  Bearbeiten loescht vorab alle bisherigen Positionen und baut sie neu auf.
- MERCH_CHECKS.json: Menge 0, Menge -1 und unbekannte Groesse erzeugen jeweils
  eine Bestellung ohne Positionen zu CHF 0. Nach Deaktivieren einer bestellten
  Variante loescht ein erneuter Submit mit derselben Auswahl die alte Position.
- Empfehlung: komplette Bestellung zuerst validieren, mindestens eine gueltige
  Position verlangen, unbekannte/inaktive Varianten als Konflikt rueckmelden.
  Historische Positionen beim Bearbeiten nicht still verwerfen.
- Abnahme: ungueltiger Submit veraendert keine bestehende Bestellung; Fehler
  bleiben an der betroffenen Zeile sichtbar, gueltige Eingaben bleiben erhalten.
- Erweiterung 2026-09-20: `uneven_form_arrays` bestaetigt stilles Abschneiden
  durch `zip`: zwei Mengenwerte, aber nur eine Farbe/Groesse erzeugen trotzdem
  eine erfolgreiche Bestellung mit einer Position. Zeilenstruktur vorab validieren.

## A-049 – Merch-Status, Bestellsumme und Forderung koennen auseinanderlaufen

- **Isoliert reproduzierter Integritaetsfehler, P1, M–L, Risiko L.**
- Beide Statusrouten in `backend/routes/admin.py:1103`/`:1151` erlauben jeden
  Enum-Zielstatus. Zurueck auf BESTELLT wird die Bestellung wieder bearbeitbar.
  `AccountingService.create_claim_for_merch_order` gibt bestehende Claims
  unveraendert zurueck; Bearbeiten synchronisiert keine Forderung.
- Fall `reopen_edit_stale_claim`: CHF 20 geliefert → offen → Menge 3 → wieder
  bestellt. Bestellsumme CHF 60, offene Forderung weiter CHF 20. Auch das alte
  `delivered_at` bleibt am wieder offenen/in Bearbeitung befindlichen Auftrag.
- Fall `status_committed_before_claim_failure`: injizierter Fehler beim
  Claim-Service hinterlaesst WIRD_GELIEFERT ohne Forderung, weil der Status
  vorher separat committet wird. Kein produktiver Fehler wurde ausgeloest.
- Empfehlung: verbindliche Statusuebergaenge mit zentraler Transaktion;
  Wiedereroeffnung und Preisaenderung gegen Forderungen/Zahlungen pruefen.
  Lieferzeitpunkt bei Korrekturen nachvollziehbar behandeln.
- Abnahme: Bestellbetrag und Forderung stimmen nach erlaubten Aenderungen
  ueberein; bereits bezahlte Posten erfordern einen expliziten Korrekturablauf;
  fehlgeschlagene Folgeaktionen hinterlassen keinen halbfertigen Status.

## A-050 – Artikelbearbeitung loescht auch bereits referenzierte Varianten

- **Mit aktiven SQLite-Fremdschluesseln reproduzierter Fehler, P1, M, Risiko L.**
- `backend/routes/admin.py:1294` ff. loescht alle Varianten eines Artikels und
  erzeugt die Kombinationen neu. Bestehende OrderItems referenzieren deren IDs
  mit `ondelete=RESTRICT`.
- Fall `edit_article_with_existing_order`: nach einer Bestellung scheitert
  selbst Umbenennen mit unveraenderter Farbe/Groesse an FOREIGN KEY constraint.
  Die Route zeigt den DB-Fehler; Rollback erhaelt Artikel, Variante und Bestellung.
- Empfehlung: bestehende Varianten anhand stabiler IDs aktualisieren; nicht mehr
  angebotene Varianten deaktivieren, historische Referenzen erhalten. Historische
  Produktbezeichnungen und Preise als Snapshot-Vertrag definieren.
- Abnahme: Artikel mit alten/offenen/gelieferten Bestellungen bleiben pflegbar,
  ohne Positionsreferenzen oder historische Eigenschaften unbemerkt zu aendern.
  PostgreSQL-Gegenpruefung und Migrationsbedarf bleiben offen.

## A-051 – Shop-GET veraendert eine ORM-Relation statt nur die Anzeige zu filtern

- **Isoliert reproduzierter Renderfehler, P1, M, Risiko M–L.**
- `backend/routes/member.py:321` weist `article.variants` nur die aktiven
  Varianten zu. Die Relation in `MerchArticle` hat `cascade='all, delete-orphan'`;
  dadurch werden ausgelassene Varianten zur Loeschung vorgesehen. Eine folgende
  Query kann diese Aenderung automatisch flushen. Aehnliches Muster in Order/Edit.
- Fall `get_shop_inactive_ordered_variant`: bestellte Variante deaktivieren,
  dann GET `/member/merch`. Der GET wirft beim Autoflush IntegrityError.
  Nach Rollback bleiben die Daten erhalten; keine dauerhafte GET-Loeschung behauptet.
- Empfehlung: aktive Varianten in separatem View-Kontext/Query-Ergebnis halten,
  ohne persistente Relation umzuschreiben. Nur Autoflush zu deaktivieren wuerde
    die unerwuenschte Mutation nicht beseitigen.
- Performance-Gegenpruefung: 3 → 30 aktive Artikel mit je einer Variante erhoeht
  Shop-GET von 20 auf 74 SQL-Ausfuehrungen. Explizites Laden aktiver Varianten
  und Laden der bestehenden Relation erzeugen jeweils eine Query pro Artikel.
  Die Trennung des Anzeige-Kontexts sollte daher auch gebuendeltes Laden umfassen.
  Siehe [Skalierungsbericht](QUERY_SCALING_REVIEW.md); in dieser ausschliesslich
  aktiven Fixture keine DML, der obige Fehler mit inaktiver Variante bleibt bestehen.
- Abnahme: Shop-/Bestell-GETs mutieren keine DB-Relationen und funktionieren mit
  aktiven/inaktiven sowie historisch bestellten Varianten.

## A-052 – Wiederholter Bestell-POST erzeugt eine zweite Merch-Bestellung

- **Isoliert reproduzierter Wiederholungsfall, P2, M, Risiko M.**
- Fall `repeat_order_post`: zweimal identische Daten an `/member/merch/order`
  ergeben zwei Bestellungen mit je CHF 20. Jede Anfrage erzeugt eine neue UUID.
  Die UI sperrt zwar den Submit bei leerer Auswahl; ein serverseitiger Schutz
  gegen Wiederholung desselben Bestellversuchs ist nicht vorhanden.
- Empfehlung: einen Bestellversuch eindeutig kennzeichnen und wiederholte
  Uebermittlung sicher auf dessen Ergebnis abbilden. Bewusst neue identische
  Bestellungen muessen weiterhin moeglich bleiben.
- Abnahme: Retry/Doppelklick desselben Versuchs erzeugt hoechstens eine Bestellung;
  neuer Versuch bleibt unterscheidbar. Browser-Doppelklick/Konkurrenz noch pruefen.

## A-053 – Merch-Preise verlieren Rappen und erlauben negative Betraege

- **Isoliert reproduzierter Berechnungs-/Validierungsfehler, P1, M, Risiko M.**
- `create_merch_article` und `edit_merch_article` in `backend/routes/admin.py`
  verwenden `int(float(eingabe) * 100)`. Binaere Float-Abweichungen werden
  abgeschnitten; eine fachliche Preisvalidierung fehlt.
- MERCH_CHECKS.json, `price_decimal_precision`: Eingabe 19.99 speichert 1998
  Rappen. `price_negative`: -5 speichert -500 Rappen und erstellt eine aktive Variante.
- Empfehlung: exakte Dezimal-Konvertierung und einheitliche Preisvalidierung
  vor Mutation. Regeln fuer null, negative Werte und Nachkommastellen definieren;
  bestehende MoneyService-Fehler A-025 bei einer Wiederverwendung beachten.
- Abnahme: u.a. 19.99 ergibt exakt 1999 Rappen; ungueltige Preise werden als
  Feldfehler abgelehnt. Lieferanten- und Mitgliederpreis folgen denselben
  technischen Regeln; erlaubte Vereinszuschuesse bleiben fachlich moeglich.

## A-054 – Identische Artikelvarianten koennen mehrfach entstehen

- **Isoliert reproduzierte Integritaetsluecke, P2, M, Risiko M.**
- Artikel-Erstellung bildet das kartesische Produkt der eingereichten Farben
  und Groessen ohne Deduplizierung. MerchVariant hat keine Eindeutigkeitsregel
  fuer Artikel/Farbe/Groesse; die Bestellung waehlt per `.first()`.
- Fall `duplicate_variant_input`: Farben [Navy,Navy] und Groesse M speichern
  zwei getrennte Navy/M-Varianten. Kein Beleg, dass die normale UI dies selbst erzeugt;
  serverseitig ist es moeglich.
- Empfehlung: Varianten normalisieren und eindeutig halten, bestehende Duplikate
  vor einer spaeteren Constraint-Migration samt Bestellreferenzen analysieren.
- Abnahme: doppelte/abweichend formatierte Eingaben erzeugen keine mehrdeutige
  Variantenwahl. Schreibweise und Reihenfolge bleiben im Formular nachvollziehbar.

## A-055 – Unveraendertes Bestell-Speichern uebernimmt neue Katalogpreise

- **Reproduziertes Verhalten, Preisbindungsregel offen; P2, M, Risiko M.**
- Fall `unchanged_order_repriced`: Bestellung CHF 20, Variantenpreis danach
  CHF 30; erneuter Submit derselben Farbe/Groesse/Menge setzt Bestellung auf
  CHF 30. Gespeicherte Positionspreise werden beim kompletten Neuaufbau ersetzt.
- Empfehlung: festlegen, wann Preisbindung entsteht und welche Bearbeitungen
  neu bepreist werden. Geaenderte Preise vor verbindlichem Speichern sichtbar
  bestaetigen lassen; unveraenderte historische Positionen ggf. erhalten.
- Abnahme: dieselbe Preisregel gilt in Shop, Bearbeiten, Bestellhistorie und
  Forderung; unerwartete Neuverpreisung wird vermieden. Testdaten aendern den
  Variantenpreis direkt, da die aktuelle Artikelpflege schon an A-050 scheitert.

## A-056 – Merch-Gruppierungswechsel schraenkt gleichzeitig den Statusfilter ein

- **Reproduzierbare Bedieninkonsistenz, P2, S–M, Risiko S–M.**
- `admin.merch`: Ohne Statusfilter zeigt `sort=member` alle Bestellungen;
  `sort=article` setzt dagegen automatisch BESTELLT (UI: Offen).
- Fall `grouping_changes_status_filter`: eine gelieferte Bestellung ist in der
  Mitgliedsansicht enthalten, beim Wechsel zur Artikelgruppierung entfaellt sie.
  Der gerenderte Kontext wechselt von keinem Statusfilter zu BESTELLT.
- Empfehlung: Gruppierung und Datenfilter unabhaengig halten oder den Wechsel
  klar als eigene Aufgabe «offene Sammelbestellung» benennen. Fachliche Absicht
  vor Vereinheitlichung klaeren.
- Abnahme: vergleichbare Gruppierungen zeigen denselben Bestand und dieselben
  Summen; bewusst unterschiedliche Bestaende sind eindeutig beschriftet.

## A-057 – Manuelle Buchung rundet eingegebene Rappen auf Fuenferschritte

- **Isoliert reproduzierter Betragsfehler / Dokumentationswiderspruch, P1, M, Risiko M.**
- `backend/forms/accounting.py:26` konvertiert zwar mit Decimal, rundet danach
  aber mit `round(rappen / RAPPEN_STEP)` auf fuenf Rappen. Der Formularpfad
  veraendert damit den eingegebenen Buchungsbetrag vor dem Speichern.
- ACCOUNTING_CHECKS.json, `manual_booking_precision`: POST des Originalformulars
  mit CHF 19.99 speichert 2000 Rappen. Der Service kann dagegen 1999 speichern.
  `docs/capabilities/accounting.md:150` verlangt Integer-Rappen und Rundung nur
  bei der Anzeige. Anders als A-053 liegt hier keine Float-Abschneidung vor.
- Empfehlung: Buchungswerte exakt in Rappen speichern; eine fachlich gewollte
  Zahlungsrundung separat und sichtbar behandeln. Rundungsregel fuer Formulare,
  Import, Forderungen und Darstellung gemeinsam festlegen.
- Abnahme: 19.99 bleibt 1999 Rappen, vergleichbare Eingangswege liefern dieselben
  Betraege; Nachkommastellen und ungueltige Werte erhalten klare Feldfehler.

## A-058 – Buchungsdatum darf ausserhalb des zugeordneten Geschaeftsjahres liegen

- **Isoliert reproduzierte Validierungsluecke, P1, M, Risiko M.**
- `backend/services/accounting.py:384` prueft bei Erstellung den Jahresstatus,
  aber nicht das Datum gegen das Jahr. Auch `update_booking` ab Zeile 420
  enthaelt diese Zuordnungspruefung nicht; das Formular verlangt nur ein Datum.
- Fall `manual_booking_outside_year`: Original-POST mit Datum 2025-06-01 im
  ausgewaehlten Jahr 2026 wird akzeptiert und gespeichert. Datums- und
  Jahresauswertungen koennen damit unterschiedliche Bestaende enthalten;
  konkrete Exportfolgen bleiben zu pruefen.
- Empfehlung: Jahreszuordnung zentral fuer Anlage, Bearbeiten und Import
  validieren. Falls abweichende Zuordnungen fachlich beabsichtigt sind, diese
  ausdruecklich modellieren statt stillschweigend zuzulassen.
- Abnahme: Daten direkt vor/nach Jahresgrenzen werden regelkonform behandelt;
  ungueltige Zuordnungen erzeugen einen verstaendlichen Formularfehler und keine
  Buchung. Bearbeitung und Import brauchen eigene Gegenpruefungen.

## A-059 – Beleg kann aus einem abgeschlossenen Jahr entfernt werden

- **Isoliert reproduzierte Luecke in der Abschlusssperre, P1, M, Risiko M–L.**
- `backend/services/accounting.py:954`, `attach_receipt_to_booking`, prueft nur
  den Status des Zieljahres. Die bestehende Zuordnung und deren Jahresstatus
  werden vor dem Ueberschreiben von `receipt.booking_id` nicht geschuetzt.
- Fall `move_receipt_out_of_closed_year`: Schatzmeister weist per Original-POST
  `/accounting/booking/2/receipt` einen Beleg aus der Buchung im geschlossenen
  Jahr 2026 einer Buchung im offenen Jahr 2027 zu. HTTP 302, neue Zuordnung
  dauerhaft in der Test-DB; altes Jahr bleibt CLOSED. Manueller CSRF-Check
  wurde mit gueltigem Token passiert. Kein externer Drive-Vorgang noetig.
- Empfehlung: Quelle und Ziel jeder Zuordnung gegen dieselben Sperrregeln
  pruefen. Belege und Metadaten in den Schutz von Revision und Abschluss
  einbeziehen; fachlich notwendige Korrekturen nachvollziehbar gestalten.
- Abnahme: Belege aus gesperrten Jahren koennen nicht still umgehaengt werden;
  abgelehnte Versuche lassen beide Buchungen unveraendert. Offenes Jahr und
  bisher ungebundener Beleg bleiben entsprechend der festgelegten Regel nutzbar.

## A-060 – Fehlgeschlagene Importverbuchung hinterlaesst Buchungen und verdoppelt sie beim Retry

- **Isoliert reproduzierter Transaktionsfehler, P1, M–L, Risiko L.**
- `backend/services/bank_import.py:545` ruft `create_booking` auf, das bereits
  committet. Erst danach werden Aufrundungskonto, weitere Buchung, Forderung
  und Importstatus verarbeitet. Der gesamte Vorgang ist nicht atomar.
- BANK_CHECKS.json, `missing_rounding_account_retry`: CHF 25 Zahlung gegen
  CHF 20 Merch-Forderung, Konto 3410 fehlt. Erster Original-POST hinterlaesst
  eine CHF-20-Buchung, Import bleibt pending, Forderung unbezahlt. Zweiter
  POST hinterlaesst zwei CHF-20-Buchungen bei weiterhin offenem Import.
  Das fehlende Konto ist ein synthetischer Konfigurationsfehler, kein Nachweis
  fuer den produktiven Kontenplan. Kein Fehler-Mocking notwendig.
- Empfehlung: Voraussetzungen vorab pruefen und Haupt-/Aufrundungsbuchung,
  Forderungsfortschreibung, Alias und Importstatus gemeinsam committen oder
  zurueckrollen. Wiederholungs- und Konkurrenzschutz auf Vorgangsebene vorsehen;
  `payment_ref` allein darf wegen legitimer Aufteilung nicht pauschal unique sein.
- Abnahme: Fehler an jedem Teilschritt hinterlassen keine halbe Verbuchung;
  Wiederholen erzeugt genau einen vollstaendigen Vorgang. Konkurrenz und
  PostgreSQL sind separat zu testen.

## A-061 – Zahlungszuordnung validiert Richtung und Mitglied nicht gemeinsam

- **Isoliert reproduzierte Zuordnungsluecke, P1, M, Risiko M–L.**
- `backend/services/bank_import.py:496` prueft den Forderungsstatus und den
  Vereinsglaeubiger, aber nicht die Eingangsrichtung. Zeile 578 schreibt jede
  zugeordnete Zahlung positiv fort. Ein explizites `member_id` kann ausserdem
  von `claim.member_id` abweichen.
- `outgoing_payment_settles_claim`: authentifizierter POST mit Ausgabetransaktion
  und claim_id markiert CHF 20 Forderung als beglichen. Die normale UI blendet
  die Forderungsauswahl bei Ausgaben aus; die serverseitige Grenze fehlt dennoch.
- `booking_member_differs_from_claim`: Buchung bei Mitglied 3, bezahlte Forderung
  bei Mitglied 2. Die Einnahmen-UI bietet beide Auswahlen unabhaengig an.
- Empfehlung: Zahlungseingang als Voraussetzung einer positiven Tilgung
  validieren. Zahler und Schuldner entweder konsistent zuordnen oder eine
  beabsichtigte Zahlung fuer Dritte ausdruecklich abbilden. Konto-/Event-Konsistenz
  in dieselbe Pruefung einbeziehen; diese Varianten noch separat verifizieren.
- Abnahme: Auszahlungen begleichen keine Einnahmeforderungen. Abweichende
  Zahler/Schuldner sind bewusst erfasst und in den Auswertungen nachvollziehbar.

## A-062 – Bearbeiten importierter Buchungen entkoppelt Journal und Zahlungsstand

- **Isoliert reproduzierte Integritaetsluecke, P1, M–L, Risiko L.**
- `backend/routes/accounting.py:363` / `backend/services/accounting.py:420`
  behandeln importierte Buchungen wie manuelle Buchungen, ohne zugeordnete
  Bankbewegung oder bereits fortgeschriebene Forderung abzugleichen.
- `edit_imported_booking_amount`: CHF 20 erfolgreich importiert und Forderung
  beglichen. Original-Edit-POST aendert Buchung auf CHF 5; Banktransaktion bleibt
  CHF 20/booked, Forderung CHF 20 bezahlt. Die Abweichung wird nicht als
  Korrektur oder nicht zugeordneter Restbetrag modelliert.
- Empfehlung: Bankbetrag als Quellbeleg erhalten und Korrekturen ueber einen
  expliziten Abgleich-/Stornoworkflow fuehren. Zahlungen und Forderungen dauerhaft
  miteinander verknuepfen, damit Korrekturen und Teilzuordnungen ableitbar bleiben.
- Abnahme: Betrag/Richtung/Mitglied einer importierten Buchung koennen nicht
  still den Bank-/Forderungsabgleich zerstoeren; Korrekturen sind nachvollziehbar
  und erhalten die Summe oder weisen eine bewusste Differenz aus.

## A-063 – Ersatzschluessel ohne Bankreferenz verschluckt unterschiedliche Zahlungen

- **Isoliert reproduzierter Dedup-Grenzfall, P1, M, Risiko M.**
- `backend/services/bank_import.py:329` bildet den Ersatzschluessel nur aus
  Datum, Betrag, Richtung und Buchungstext. Zahlungszweck/Details und mehrfache
  gleichartige Zahlungen werden nicht unterschieden.
- `different_purpose_without_reference`: zwei Zeilen gleichen Datums/Betrags/
  Buchungstexts ohne Referenz, aber mit «Invoice A» und «Invoice B», ergeben
  eine neue Transaktion und ein angebliches Duplikat. Nur Invoice A bleibt.
  Normale Wiederholung mit identischer ZKB-Referenz funktioniert im Kontrollfall.
- Empfehlung: fehlende Referenz als unsichere Identitaet behandeln. Moegliche
  Dubletten zur Pruefung anzeigen statt automatisch echte Bewegungen auszulassen;
  auch zweimal vollstaendig identische legitime Zahlungen beruecksichtigen.
- Abnahme: unterschiedliche Bewegungen bleiben erhalten; wiederholter Import
  erzeugt keine Doppelverbuchung. Verhalten bei fehlender Referenz transparent.

## A-064 – Unvollstaendige Sammelbuchung wird automatisch auf den Gesamtbetrag hochgerechnet

- **Isoliert reproduzierte Import-Validierungsluecke, P1, M, Risiko M–L.**
- `backend/services/bank_import.py:157,245` erkennt Sammelbuchungen, prueft aber
  weder die angekuendigte Detailanzahl noch CHF-Summendifferenzen vor Verteilung.
- `collective_missing_detail`: Parent «Gutschriften eBanking (2)» CHF 100,
  nur eine CHF-40-Detailzeile. Import setzt Parent auf ignored und macht aus
  dem einen Detail CHF 100 (Originalbetrag CHF 40 bleibt als Metadatum).
  Vollstaendige CHF-40/60-Details werden im Kontrollfall korrekt uebernommen.
- Empfehlung: Vollstaendigkeit, Waehrungen und Summen vor Aufteilung pruefen.
  Fehlende Details nicht wie Wechselkurs-/Rundungsdifferenzen behandeln;
  unaufgeklaerte Gruppen sperren oder zur bewussten Klaerung vorlegen.
- Abnahme: fehlende/ueberzaehlige Details und CHF-Differenzen koennen nicht
  unbemerkt falschen Empfaengern zugeordnet werden. Fremdwaehrungsaufteilung
  benoetigt gesonderte Kontrollen und Gegenpruefungen.

## A-065 – Ungueltiger CSV-Betrag verlaesst den vorgesehenen Import-Fehlerpfad

- **Isoliert reproduzierter Validierungsfehler, P2, S–M, Risiko M.**
- `backend/services/bank_import.py:97` kann ValueError werfen. Der Parser
  uebersetzt diesen nicht in BankImportError; die Upload-Route ab
  `backend/routes/accounting.py:978` faengt nur AccountingError ab.
- `invalid_amount_in_csv`: Original-Dateiupload mit einer gueltigen Zeile und
  Betrag «abc» in der zweiten wirft ValueError bis zum Testclient. Keine
  Transaktionen/Buchungen angelegt. In Testing propagiert die Exception;
  keine produktive Fehlerseite oder produktive HTTP-Antwort gemessen.
- Empfehlung: Zahlenformat, Vorzeichen, Nachkommastellen und Pflichtspalten
  strikt pruefen. Fehler mit Zeile/Feld als verstaendliche Importmeldung
  zurueckgeben; interne Exceptions nicht als Nutzermeldung durchreichen.
- Abnahme: fehlerhafte Dateien werden ohne Teilimport und mit konkreter
  Korrekturhilfe abgelehnt. Weitere Formate bleiben separat zu testen.

## A-066 – Budget bleibt waehrend laufender Revision veraenderbar

- **Reproduziertes Verhalten / widerspruechliche Sperrregel, P2, S–M, Risiko M.**
- `backend/services/accounting.py:284` und Budget-UI sperren erst CLOSED.
  Die Phasenbeschreibung in `docs/capabilities/accounting.md` beschreibt
  IN_REVIEW dagegen als gesperrtes Jahr, dessen Journal und Budget geprueft werden.
- REVISION_CHECKS.json, `budget_during_review`: Schatzmeister-POST aendert
  Budget von 2000 auf 9000 Rappen, Status bleibt in_review. Derselbe Versuch
  nach Abschluss wird korrekt abgelehnt (`budget_closed_blocked`).
- Empfehlung: fachlich entscheiden, ob Budget Teil der eingefrorenen
  Pruefgrundlage ist. Dann Aenderung erst nach Rueckzug erlauben; andernfalls
  Aenderungen waehrend Revision sichtbar versionieren und dem Revisor anzeigen.
- Abnahme: Revisor prueft einen eindeutig bestimmten Stand; UI, Dokumentation
  und Service setzen dieselbe Regel um. Keine stille Aenderung der Pruefgrundlage.

## A-067 – Deaktivierte Konten verschwinden aus historischen Detailauswertungen

- **Isoliert reproduzierter Auswertungsfehler, P1, M, Risiko M.**
- `backend/services/accounting.py:311` bildet Budget/Ist nur fuer aktuell
  aktive Konten. `get_budget_grouped` und die PDF-Gruppentabelle verwenden
  diese Daten; die Jahressumme beruecksichtigt dagegen alle Buchungen.
- `deactivated_account_closed_report`: abgeschlossenes Jahr mit CHF 20
  Ausgabe; Konto deaktivieren entfernt CHF 20 aus den Detaildaten, waehrend
  die Jahressumme weiterhin CHF 20 Ausgabe zeigt. Kein PDF gerendert;
  Wirkung auf neu erzeugte PDF-Daten aus dem Aufrufpfad belegt. Bereits
  gespeicherte Drive-PDFs werden dadurch nicht veraendert.
- Empfehlung: historische Berichte anhand der im Jahr bebuchten/budgetierten
  Konten bilden. Aktivstatus nur fuer neue Auswahl verwenden; Aenderungen von
  Name, Art und Gruppe ebenfalls auf historische Auswirkungen pruefen.
- Abnahme: Detail- und Gesamtsummen stimmen auch mit deaktivierten Konten
  ueberein; abgeschlossene Jahresdarstellungen bleiben nachvollziehbar.

## A-068 – Konto-Ist addiert Einnahmen und Ausgaben ohne Richtungsunterscheidung

- **Isoliert reproduzierter Rechenwiderspruch, P1, M, Risiko M.**
- `backend/services/accounting.py:311` summiert positive Betraege pro Konto
  ohne Richtung; Jahressumme ab Zeile 467 unterscheidet IN und OUT.
- `opposite_directions_same_account`: CHF 20 Ausgabe und CHF 5 Eingang auf
  demselben Ausgabenkonto ergeben Konto-Ist CHF 25, Jahresergebnis CHF -15.
  Die Service-Eingaben werden akzeptiert; keine echte Rueckerstattung gebucht.
- Empfehlung: festlegen, ob Gegenbuchungen auf demselben Konto erlaubt sind.
  Wenn ja, richtungsbezogen saldieren; andernfalls Richtung/Kontoart konsistent
  validieren und den Korrekturweg sichtbar anbieten.
- Abnahme: Rueckerstattung/Korrektur ergibt eine fachlich erklaerbare,
  zwischen Journal, Budgetvergleich, Gruppen und Jahresergebnis konsistente Zahl.

## A-069 – Anfangssaldo eines abgeschlossenen Jahres bleibt von offenen Vorjahren abhaengig

- **Isoliert reproduzierte Abschlussluecke, P1, M–L, Risiko L.**
- `approve_year` ab `backend/services/accounting.py:245` verlangt keinen
  abgeschlossenen Vorjahresstand. `get_opening_balance` ab Zeile 366 berechnet
  den Uebertrag jederzeit neu aus allen frueheren Buchungen.
- `closed_year_opening_changes`: Jahr 2026 abgeschlossen, 2025 noch offen.
  Aenderung einer 2025-Buchung von CHF 20 auf CHF 50 veraendert den Anfangssaldo
  des geschlossenen Jahres 2026 von CHF -20 auf CHF -50. Aktuelle Berichte
  koennen damit von zuvor gespeicherten Abschlussberichten abweichen.
- Empfehlung: Abschlussreihenfolge und verbindlichen Uebertrag definieren.
  Vorjahreskorrekturen nach Folgejahresabschluss brauchen einen geregelten
  Korrektur-/Neufreigabeprozess; nur einen Snapshot einzufuehren loest den
  fachlichen Abgleich mit geaenderten Vorjahren noch nicht.
- Abnahme: bestaetigter Anfangs-/Endsaldo aendert sich nicht still durch andere
  Jahre; erforderliche Folgekorrekturen bleiben sichtbar und nachvollziehbar.

## A-070 – Fehlgeschlagener Revisionsbericht hat keinen direkten Wiederholungsweg

- **Isoliert reproduzierter Wiederaufnahmefehler, P2, M, Risiko M.**
- `backend/routes/accounting.py:887` bestaetigt und committet das Jahr vor
  PDF-Erzeugung/Drive-Upload. Fehler zeigen eine Warnung, Abschluss bleibt bestehen.
- `report_failure_then_retry`: PDF-Service gezielt durch Fehler ersetzt.
  Erster POST schliesst das Jahr ohne report_drive_id. Zweiter POST scheitert
  bereits am Jahresstatus; PDF-Erzeugung wird insgesamt nur einmal versucht.
  Keine PDF-Datei und kein externer Aufruf erzeugt. Separater PDF-Export existiert,
  ruft aber ohne RevisionApproval auf und archiviert keinen Revisorenbericht.
- Empfehlung: fachliche Bestaetigung und Berichtserstellung als getrennte,
  sichtbare Zustaende behandeln. Bericht gezielt erneut erzeugen/archivieren
  koennen, ohne die Bestaetigung zuruecknehmen zu muessen; Doppeluploads vermeiden.
- Abnahme: nach Erzeugungs-/Uploadfehler kann der fehlende Bericht nachgeholt
  werden; Freigabeperson/-zeit bleiben erhalten. Fehler nach erfolgreichem Upload
  und vor DB-Verknuepfung sind noch separat zu pruefen.

## A-071 – Beleg-Auswahllisten umgehen die Rechte der angebotenen Objekte

- **Isoliert reproduzierte Offenlegung, P1, M, Risiko M–L.**
- `backend/routes/accounting.py:428` erzeugt fuer alle aktiven Mitglieder
  Buchungsoptionen mit Datum, Beschreibung und Betrag aus bis zu 50 offenen
  Buchungen. Die Event-Auswahl verwendet ebenfalls keine Audience-Filterung.
- RECEIPT_CHECKS.json, `member_upload_choices_disclosure`: normales Mitglied
  erhaelt Upload-GET 200 mit fremder Buchungsbeschreibung und Restaurantname
  eines Board-Events. Buchungsdetail liefert fuer dasselbe Mitglied 403;
  `event.is_visible_to` ist false. Zusaetzlicher Sichtbarkeitsweg zu A-042;
  hier entstehen die Datenlecks durch Auswahlfelder statt Statistiken.
- Empfehlung: Berechtigungen schon beim Aufbau der Optionen anwenden.
  Fuer Mitglieder einen bewusst begrenzten Zuordnungsweg definieren, falls
  direkte Belegverknuepfung weiterhin erlaubt sein soll. Vorschlaege duerfen
  nicht mehr offenlegen als der jeweilige Lesekontext erlaubt.
- Abnahme: unberechtigte Buchungs-/Eventdaten fehlen auch im HTML der
  Auswahlfelder. Berechtigte Rollen behalten die fuer ihre Arbeit noetige Auswahl.
- Dokument-Erweiterung, `docs_upload_event_choices_visibility`: Docs-Index
  rendert den Restaurantnamen eines fuer das Mitglied unsichtbaren Board-Events
  im Upload-Formular. `backend/routes/docs.py:112` laedt Events ohne Audience-
  Filter; gleicher Auswahlaufbau auch in Ordner-/Detailansicht (Codebeobachtung).

## A-072 – Erfolgreicher Mitglieder-Belegupload endet auf einer gesperrten Seite

- **Isoliert reproduzierter Workflow-Fehler, P2, S, Risiko S.**
- `backend/routes/accounting.py:467` erlaubt aktive Mitglieder und direkte
  Buchungszuordnung, leitet danach aber immer zum rollenbeschraenkten Detail um.
- `member_direct_receipt_upload_redirect`: Original-Upload-POST als normales
  Mitglied speichert einen verknuepften Beleg (Drive-Transport ersetzt), antwortet
  302 zu `/accounting/booking/1`; Folge-GET ergibt 403.
- Empfehlung: Erfolg auf einer fuer den Uploader erreichbaren Seite zeigen,
  z.B. eigener Belegliste/-ansicht. Buchungsdetail nur berechtigten Rollen anbieten.
- Abnahme: nach erfolgreichem Upload ist Erfolg/Zuordnung sichtbar; kein
  Berechtigungsfehler, der zu unnoetigem erneutem Hochladen verleitet.

## A-073 – Ruecknahme des Abschlusses entfernt die bisherige Bestaetigung aus der App

- **Reproduzierter Historienverlust, P2, M, Risiko M.**
- `backend/services/accounting.py:184` loescht RevisionApproval einschliesslich
  Reviewer/Zeitpunkt/report_drive_id. Es bleibt ein allgemeiner Logeintrag zur
  Ruecknahme, aber keine versionierte Bestaetigung im fachlichen Datenmodell.
- `revoke_correct_reapprove_history`: alte Bestaetigung mit synthetischem
  Berichtverweis angelegt; Ruecknahme reduziert Anzahl auf null. Danach sind
  Oeffnen, Korrigieren, Freigeben und erneutes Bestaetigen moeglich. Nur eine
  neue Bestaetigung bleibt; alter Berichtverweis ist nicht mehr vorhanden.
  Externe Dateien wurden nicht angelegt oder geloescht. Fehlender Bericht der
  neuen Bestaetigung ist hier erwartbar, da direkt der Service getestet wird.
- Empfehlung: zurueckgenommene Bestaetigungen als Historie erhalten, mit
  Ruecknahmeperson/-zeit/-grund und eindeutig zugehoeriger Berichtversion.
- Abnahme: alte und neue Pruefentscheide bleiben nachvollziehbar; veraltete
  Berichte sind als solche erkennbar und nicht mit der aktuellen Freigabe verwechselt.

## A-074 – Abschluss und Erledigung offener Revisionskommentare sind fachlich ungeklaert

- **Reproduziertes Verhalten, Produktentscheidung offen; P2, M, Risiko M.**
- `approve_year` prueft keine offenen Kommentare. `resolve_comment` ab
  `backend/services/accounting.py:1046` setzt nur ein Boolean, ohne Jahresstatus,
  Erledigungsperson oder -zeit zu speichern. Schatzmeister und Revisor duerfen
  dies ueber die Route ausfuehren.
- `unresolved_comment_approval_and_resolution`: Jahr mit offenem Revisorenkommentar
  wird geschlossen; Schatzmeister kann Kommentar danach als erledigt markieren.
  Normales Mitglied wird korrekt mit 403 abgewiesen.
- Empfehlung: Hinweis und abschlussblockierende Beanstandung unterscheiden,
  sofern fachlich gewuenscht. Klaeren, wer Beanstandungen bestaetigt und ob
  nach Abschluss noch erledigt werden darf; Erledigung nachvollziehbar speichern.
- Abnahme: explizite Regel fuer offene Hinweise/Beanstandungen beim Abschluss;
  nachtraegliche Aenderungen des Pruefstands bleiben sichtbar. Nicht pauschal
  jeden Kommentar als Abschlussblocker behandeln.

## A-075 – Freigabe fuer sensible Daten ueberlebt Logout und Kontowechsel

- **Isoliert reproduzierte Sicherheitsluecke, P1, M, Risiko L.**
- `backend/services/security.py:157` prueft nur die Ablaufzeit in der Session,
  nicht deren Bindung an das aktuelle Mitglied. `auth.logout` ab Zeile 165
  entfernt diese App-spezifische Freigabe nicht.
- AUTH_CHECKS.json, `step_up_cross_account_after_logout`: Mitglied A meldet
  sich an und bestaetigt sein Passwort per Original-Step-up-POST. Nach Logout
  und Login als B erreicht B `/member/profile?tab=sensitive` mit HTTP 200,
  ohne zusaetzliche Bestaetigung des Passworts von B. Session-Freigabe bleibt.
  Kein Zugriff auf A-Daten behauptet; die zusaetzliche Schutzschranke fuer B
  wird aufgrund der Freigabe von A uebersprungen.
- Empfehlung: Freigabe an Mitglied und Authentifizierungssitzung binden;
  bei Logout, Kontowechsel und sicherheitsrelevanten Resets entfernen. Weitere
  sensible Aktionen gegen dieselbe zentrale Regel pruefen.
- Abnahme: Konto B benoetigt seine eigene aktuelle Freigabe. Logout entfernt
  sensible Freigaben auch ohne anschliessenden Kontowechsel.
- MFA-Erweiterung, `enrollment_secret_survives_account_switch`: Einrichtung
  als A beginnen, Logout, Login als B, Einrichtung oeffnen: derselbe
  `session['2fa_secret']` wird verwendet. Auch diesen Zwischenzustand an das
  Mitglied binden und bei Kontowechsel entfernen. Nur synthetische Secrets getestet.

## A-076 – Geforderter erster Passwortwechsel ist nur eine Weiterleitung

- **Reproduzierte Durchsetzungsluecke, P1, M, Risiko M.**
- `Member.needs_password_change` basiert auf fehlendem password_changed_at.
  Der Login leitet dann normalerweise zum Passwortwechsel; eine gueltige
  next-Angabe hat jedoch Vorrang. Geschuetzte Fachseiten erzwingen den Wechsel
  nicht zentral.
- `first_password_change_bypass`: Login leitet zu `/auth/change-password`,
  danach ist direkter Profil-GET 200. Ein zweiter Login mit next=/member/profile
  ueberspringt sogar diese Weiterleitung, waehrend needs_password_change true bleibt.
- Empfehlung: falls der Wechsel von Initialpasswoertern verpflichtend ist,
  einen eingeschraenkten Anmeldestatus bis zum erfolgreichen Wechsel verwenden.
  Erlaubte Ziele (Wechsel, Logout und noetige Hilfeseiten) explizit bestimmen.
- Abnahme: direkte URLs und Rueckleitungen umgehen den Pflichtwechsel nicht;
  nach erfolgreicher Aenderung wird der urspruengliche erlaubte Einstieg erreichbar.

## A-077 – Passwort-Reset beendet bestehende Anmeldesitzungen nicht

- **Isoliert reproduziertes Sicherheitsrisiko, P1, M–L, Risiko L.**
- `backend/routes/auth.py:534` aendert Passwort und Tokenstatus, ohne andere
  Sessions zu widerrufen. `backend/extensions.py:66` laedt das Mitglied anhand
  der unveraenderten ID; keine pruefbare Session-Version wird verglichen.
- `reset_password_existing_session`: Client A ist angemeldet. Separater Client
  B setzt mit gueltigem synthetischem Reset-Token das Passwort erfolgreich
  zurueck. A erreicht danach das Profil weiterhin mit HTTP 200. Wiederverwendung
  desselben Tokens wird korrekt als used abgelehnt.
- Empfehlung: bestehende Sessions bei Wiederherstellung des Kontos widerrufen;
  auch Remember-me und gemerkte 2FA-Geraete in den Widerrufsvertrag einbeziehen.
  Fuer normalen Passwortwechsel die gewuenschte Behandlung der aktuellen Sitzung
  gesondert festlegen. Diese weiteren Wege noch verifizieren.
- Abnahme: vor dem Reset ausgestellte Sitzungen verlieren Zugriff; neue Anmeldung
  verlangt die aktuellen Anmeldedaten und gegebenenfalls den zweiten Faktor.

## A-078 – Login mit Zwei-Faktor-Pruefung verliert das urspruengliche Rueckkehrziel

- **Reproduzierte Ablaufinkonsistenz, P2, S–M, Risiko M.**
- `backend/routes/auth.py:139` speichert nur pending_2fa_user_id und leitet
  ohne next zu verify_2fa. Die Verifikationsroute liest spaeter next erneut aus
  der aktuellen Anfrage; der urspruengliche Zielwert wird nicht weitergereicht.
- `mfa_login_loses_return_target`: Passwort-Login eines synthetischen MFA-Kontos
  mit next=/member/profile fuehrt zu `/auth/2fa/verify`; das Ziel steht weder in
  der Weiterleitung noch in der Session. Kein TOTP-Abschluss in diesem Szenario;
  Verlust am Uebergang nachgewiesen, anschliessender Codepfad gelesen.
- Empfehlung: erlaubtes internes Rueckkehrziel fuer den begrenzten MFA-Vorgang
  erhalten und nach Abschluss/Abbruch entfernen. Gemeinsam mit A-035 absichern.
- Abnahme: Deep-Links erreichen nach Login mit und ohne MFA dasselbe erlaubte
  Ziel; abgebrochene Vorgaenge hinterlassen kein fremdes/spaeteres Rueckkehrziel.

## A-079 – Gueltige Backup-Codes scheitern am Vergleich neu gesalzener Hashes

- **Isoliert reproduzierter Wiederherstellungsfehler, P1, M, Risiko L.**
- `backend/routes/auth.py:237` sucht einen DB-Hash gleich einem frisch erzeugten
  `hash_backup_code(eingabe)`. Gesalzenes Passwort-Hashing erzeugt jedoch bei
  gleicher Eingabe unterschiedliche Hashes. `check_backup_code` bleibt ungenutzt.
- MFA_CHECKS.json, `valid_backup_code_rejected`: gespeicherter synthetischer
  Code besteht die originale Hash-Verifikation, aber der Login wird abgelehnt;
  Code bleibt unbenutzt, Client unangemeldet.
- Empfehlung: aktive Codes mit dem vorgesehenen Hash-Verifikator pruefen und
  Verbrauch gegen konkurrierende Nutzung absichern. Hash-Schutz beibehalten.
- Abnahme: gueltiger Code funktioniert einmal; falsche, widerrufene, verbrauchte
  und fremde Codes nie. Konkurrenz separat pruefen.

## A-080 – Erneute MFA-Einrichtung liefert keine nutzbaren Backup-Codes

- **Isoliert reproduzierter Lifecycle-Fehler, P1, M, Risiko M.**
- Deaktivierung ab `backend/routes/auth.py:327` widerruft Codes, laesst deren
  Zeilen bestehen. `backup_codes` ab Zeile 755 erzeugt neue Codes nur dann,
  wenn ueberhaupt keine Zeilen existieren.
- `reenrollment_cannot_get_fresh_backup_codes`: Deaktivieren und per echtem
  TOTP neu einrichten; Backup-Seite leitet weg. MFA aktiv, eine alte widerrufene
  Codezeile, null nutzbare Codes.
- Empfehlung: neue Codes an die neue MFA-Einrichtung binden; sichere einmalige
  Anzeige und expliziten Erneuerungsablauf vorsehen.
- Abnahme: Neueinrichtung liefert nutzbare neue Codes, alte bleiben ungueltig.

## A-081 – MFA-Schluessel und Anmeldecodes werden protokolliert

- **Bestaetigter Logging-Fehler, P1, S–M, Risiko L.**
- `backend/routes/auth.py:296,299` loggt das komplette Einrichtungsschluessel-
  Geheimnis mit Mailadresse. `backend/services/security.py:114` ff. loggt
  eingegebenen und aktuell errechneten TOTP-Code auf INFO-Niveau.
- `trust_created_before_mfa_enrollment` / `totp_repeat_and_logging`: abgefangene
  Logger-Aufrufe enthalten Testsecret bzw. Testcode. Nur Booleans gespeichert,
  keine Geheimnisse. Produktive Logs und deren Aufbewahrung nicht untersucht.
- Empfehlung: Geheimnisse aus Logmeldungen entfernen, nur Ergebnis und
  nicht geheime Vorgangsmerkmale protokollieren. Separat klaeren, ob produktive
  Logs betroffen sind. Keine pauschale Rotation des CRYPTO_KEY; diese bleibt tabu.
- Abnahme: weder Einrichtung noch Login/Fehlversuch loggen Secrets oder Codes.

## A-082 – Geraetevertrauen ueberlebt MFA-Reset und Neueinrichtung

- **Isoliert reproduzierte Widerrufsluecke, P1, M–L, Risiko L.**
- `remember_device` ab `backend/routes/auth.py:736` verlangt nur Login und
  erzeugt eine etwa 100 Jahre gueltige Session-Freigabe. Login prueft Mitglied
  und Ablaufzeit, keine aktuelle MFA-Version oder widerrufbare Geraeteregistrierung.
- `trust_created_before_mfa_enrollment`: Vertrauen vor Einrichtung per POST
  angelegt, spaeterer Passwort-Login nach Einrichtung ohne neuen TOTP moeglich.
- `reset_get_and_old_device_after_reenroll`: zuerst legitime TOTP-Anmeldung
  mit Geraetevertrauen, dann Logout; anderer Client setzt MFA zurueck und richtet
  es neu ein. Alter Client kann mit Passwort ohne neuen zweiten Faktor anmelden.
  Kein Passwort- oder Session-Signatur-Bypass behauptet.
- Empfehlung: Vertrauen erst nach frischer MFA-Pruefung ausstellen, an deren
  Generation binden, serverseitig widerrufbar machen und Laufzeit begrenzen.
- Abnahme: Reset/Neueinrichtung entwertet alte Freigaben. Passwort-/Admin-Reset
  ebenfalls gegenpruefen (A-077); diese Wege bleiben offen.

## A-083 – MFA-Reset-Link deaktiviert den zweiten Faktor bereits per GET

- **Isoliert reproduzierter Link-Lifecycle-Fehler, P2, M, Risiko M–L.**
- `backend/routes/auth.py:642` fuehrt die Mutation fuer GET und POST gleich aus.
- `reset_get_and_old_device_after_reenroll`: unangemeldeter GET mit gueltigem
  synthetischem Token deaktiviert MFA und verbraucht den Token. Kein tokenloser
  Reset; der geheime Link ist erforderlich.
- Empfehlung: GET zeigt nur eine Bestaetigungsseite, bewusster abgesicherter
  POST fuehrt den Reset aus. Linkvorschau/automatische Linkpruefung darf nichts
  deaktivieren; reales Mailscanner-Verhalten wurde nicht gemessen.
- Abnahme: GET veraendert weder MFA noch Tokenstatus; Bestaetigung einmalig,
  abgelaufene und bereits verwendete Links abgelehnt.

## A-084 – Doppelte Profil-Mailadresse endet in unbehandeltem Datenbankfehler

- Erweiterung Mitgliederanlage vom 2026-09-28: identischer Erstellen-POST
  nach Erfolg, strukturiertem Mailfehler oder erstem Auditfehler wirft jeweils
  IntegrityError. DB behaelt genau ein Konto, kein erneuter Mailaufruf. Die
  serverseitige Eindeutigkeit funktioniert; verstaendliche Formularbehandlung
  fehlt auch hier. Beleg: ONBOARDING_RETRY_CHECKS.json, drei Gruppen.

- **Isoliert reproduzierter Validierungsfehler, P2, M, Risiko M.**
- `backend/routes/member.py:218` ff. validiert das Mailformat, aber keine
  Eindeutigkeit; anschliessendes Commit behandelt den Unique-Konflikt nicht.
- PROFILE_CHECKS.json, `profile_duplicate_email`: eigenes Profil auf die
  bestehende Adresse eines anderen synthetischen Mitglieds speichern wirft
  IntegrityError. Nach Rollback ist die urspruengliche Adresse erhalten.
- Empfehlung: Eindeutigkeit als Feldfehler pruefen und zusaetzlich konkurrierende
  DB-Konflikte kontrolliert zurueckrollen. Eingaben im Formular erhalten.
- Abnahme: keine Serverexception bei belegter Adresse, keine Teilmutation;
  Verhalten von Gross-/Kleinschreibung und Normalisierung explizit vereinheitlichen.

## A-085 – Zahlenfelder in Profil und Administration haben unterschiedliche Validierungsluecken

- **Isoliert reproduzierte Eingabeprobleme, P2, M, Risiko M.**
- Profil nutzt numerische Felder ohne Wertebereich. Administration nutzt Strings
  und wandelt sie erst nach Formularvalidierung mit int/float um.
- `negative_physical_values`: Profil speichert Groesse -5, Gewicht -2 und
  Schuhgroesse -1. `admin_invalid_numeric_field`: Groesse «abc» im Original-
  Admin-POST wirft unbehandelten ValueError; nach Rollback keine Groessenaenderung.
- Empfehlung: gemeinsame typisierte Feldregeln fuer beide Wege, optionales
  Leerfeld erlauben, negative/ungueltige Werte als Feldfehler behandeln.
  Fachlich sinnvolle Ober-/Untergrenzen gemeinsam festlegen, nicht erraten.
- Abnahme: gleiche Eingabe hat in beiden Formularen dieselbe Bedeutung;
  Fehler erhalten Eingaben und erzeugen weder Exception noch ungueltige Speicherung.

## A-086 – Lesefehler loescht sensible Daten bereits beim GET

- **Isoliert reproduzierter Datenverlust, P1, M, Risiko L.**
- `backend/routes/member.py:181` ff. und `backend/routes/admin.py:578` ff.
  behandeln jede Entschluesselungs-Exception als beschaedigte Daten und loeschen
  den Datensatz samt Commit waehrend des Seitenaufrufs.
- `self_sensitive_get_deletes_on_error` / `admin_sensitive_get_deletes_on_error`:
  gueltige synthetische verschluesselte Daten, Entschluesselung gezielt durch
  voruebergehenden Fehler ersetzt. Danach null MemberSensitive-Zeilen. Eigene
  Ansicht liefert 200; Admin-Ansicht scheitert zusaetzlich an A-087, nachdem
  die Loeschung bereits committet wurde.
- Empfehlung: Daten bei Lesefehlern unveraendert bewahren, Fehler anzeigen
  und Ursache klaeren. Reparatur/Loeschung nur als ausdruecklicher, nachvollziehbarer
  Vorgang. CRYPTO_KEY nicht rotieren; im Test nur frischer Memory-Key verwendet.
- Abnahme: fehlender Key, unlesbarer Inhalt oder temporaere Exception mutieren
  beim GET keine Daten; nach Behebung koennen unveraenderte Daten gelesen werden.

## A-087 – Sensible Admin-Ansicht erwartet ein nicht uebergebenes Formular

- **Isoliert reproduzierter Renderfehler, P1, S, Risiko S–M.**
- `templates/admin/member_sensitive.html:27` ruft `form.hidden_tag()` auf.
  `admin.member_sensitive` uebergibt beim GET nur member/data, kein form.
- `admin_sensitive_valid_data_render`: berechtigter Admin mit gueltiger
  sensibler Freigabe und lesbaren Testdaten erhaelt UndefinedError («form»).
  Datensatz bleibt in diesem Kontrollfall erhalten; unabhaengig von A-086.
- Empfehlung: Route und Template auf gemeinsamen Formularvertrag bringen,
  einschliesslich CSRF, Feldvalidierung und Rueckgabe bei Eingabefehlern.
- Abnahme: berechtigter GET rendert mit leeren und vorhandenen Daten;
  unberechtigte Zugriffe bleiben gesperrt, Speichern und CSRF separat pruefen.

## A-088 – Google-Verifikationslink bestaetigt eine nachtraeglich geaenderte Adresse

- **Isoliert reproduzierte Verifikationsluecke, P1, M, Risiko L.**
- `backend/routes/member.py:623` verifiziert die aktuell gespeicherte Adresse;
  AuthToken enthaelt nur Mitglied und Zweck, keine Bindung an die Zieladresse.
  Der Adresswechsel ab Zeile 574 entwertet fruehere Verifikationslinks nicht.
- ACCESS_CHECKS.json, `old_email_token_verifies_new_address`: Original-Save fuer
  alte Adresse erzeugt Mail-Link (Versand ersetzt); danach neue Adresse speichern.
  Aufruf des alten Links setzt neue Adresse auf verified und uebergibt genau
  diese neue Adresse an den ersetzten Drive-Invite. Kein Zugriff auf ihr Postfach
  erforderlich. Kein echter Versand/Invite ausgefuehrt.
- Empfehlung: Token an Adresse bzw. Adressversion binden und alte Tokens bei
  Wechsel entwerten. Einladung erst fuer genau die nachgewiesene Adresse.
- Abnahme: alter Link bestaetigt niemals eine neue Adresse; Wechsel, erneutes
  Senden und parallel geoeffnete Links folgen derselben eindeutigen Regel.

## A-089 – Adresswechsel und Mitgliederdeaktivierung widerrufen Drive-Zugang nicht

- **Bestaetigte Integrationsluecke, P1, M–L, Risiko L.**
- `google_email_save` ersetzt die Adresse; `admin.edit_member` setzt is_active.
  Beide Wege rufen `DriveStorageService.remove_member_from_drive` nicht auf.
  Suche in backend/scripts findet fuer diesen Helfer nur dessen Definition.
- `google_address_change_no_revoke` / `member_deactivation_no_drive_revoke`:
  bei aktiviertem Drive-Feature werden Aenderungen gespeichert, aber null
  Widerrufsaufrufe. Externe Berechtigungen und manuelle Betriebsprozesse nicht
  untersucht; kein Nachweis ueber aktuell fortbestehende produktive Zugriffe.
- Empfehlung: alten Adress-/Permission-Bezug erhalten und Entfernung mit
  Wiederholungs-/Fehlerstatus an beide Lebenszyklusereignisse koppeln. Vereins-
  und direkte Drive-Berechtigungen muessen bewusst gemeinsam verwaltet werden.
- Abnahme: Austritt/Deaktivierung und Adresswechsel entfernen ungewollte alte
  Freigaben oder zeigen einen konkret nachholbaren Fehler. Keine echten
  Berechtigungen im Audit veraendert.

## A-090 – Letzter aktiver Admin kann sich selbst die Adminrolle entziehen

- **Isoliert reproduzierte Verwaltungsluecke, P2, M, Risiko M.**
- `backend/routes/admin.py:444` uebernimmt Rolle/Aktivstatus ohne Schutz des
  letzten aktiven Admins.
- `last_admin_self_demotion`: einziger Admin speichert eigenes Mitglied als
  MEMBER; null aktive Admins bleiben. Naechster Admin-Bearbeitungsaufruf 403.
- Empfehlung: Mindestbesetzung der Administration festlegen. Wenn mindestens
  ein Admin benoetigt wird, letzte Herabstufung/Deaktivierung abweisen und eine
  bewusste Uebergabe an einen anderen Admin ermoeglichen.
- Abnahme: erlaubte Rollenwechsel funktionieren, kein versehentlicher Verlust
  aller administrativen Zugaenge. Konkurrenz und letzter Admin deaktivieren
  noch separat pruefen; keine produktive Rollenmutation vorgenommen.

## A-091 – Drive-Fehlervertrag bricht zwischen Service und Dokument-Routes

- **Isoliert reproduzierter Fehlerbehandlungsbruch, P1, M, Risiko M.**
- Suchnachtrag vom 2026-09-21: Auch search_files reicht einen HTTP-403 auf
  der zweiten Ergebnisseite oder beim Laden des Trefferpfads als HttpError
  weiter. Die Docs-Suchroutes fangen nur DriveError. Servicepfad isoliert
  reproduziert, keine produktive HTTP-Antwort oder neue Route-Probe behauptet.
  Beleg: [Suchgrenzen](DOCS_SEARCH_BOUNDARY_CHECKS.json), Fehlergruppen.
- `backend/routes/docs.py:326` faengt DriveError, der Service ab
  `backend/services/drive_storage.py:1269` reicht API-HttpError aber unveraendert
  weiter. Detail ab Route-Zeile 177 versucht Auto-Sync abzusichern, ruft danach
  Metadaten erneut ausserhalb dieses Schutzes ab.
- DOCS_CHECKS.json: `remote_rename_http_error` erzeugt am ersetzten API-Transport
  einen echten googleapiclient HttpError mit Status 403. Er propagiert bis zum
  Testclient. `detail_metadata_error_after_sync` endet ebenfalls in HttpError
  nach dem Sync-Versuch. Dokumentzeile bleibt in beiden Faellen erhalten.
  Keine produktive HTTP-Antwort/Drive-Stoerung gemessen.
- Kontrollfall `move_failure_preserves_db_parent`: bereits als DriveError
  normalisierter Fehler wird behandelt (302), DB-Ordner bleibt unveraendert.
- Empfehlung: externe Fehler zentral in definierte Service-Fehler uebersetzen;
  relevante Metadatenabfragen und Nachladevorgaenge in denselben Fehlervertrag
  einbeziehen. Wiederholbare Fehler von fehlenden Rechten/Dateien unterscheiden.
- Abnahme: Rechtefehler, Nichterreichbarkeit und Quota ergeben kontrollierte
  Meldungen; keine unbehandelten API-Exceptions oder Erfolgsmeldungen nach
  Teilfehlern. Weitere Aktionen und Drive/DB-Teilerfolge separat testen.
- Erweiterung `resync_second_page_failure`: erste synthetische API-Seite wird
  committet, zweite wirft HttpError. Alte und neu importierte Zeile bleiben
  nach Rollback erhalten; die abschliessende Orphan-Bereinigung wird nicht
  erreicht. Keine unerwuenschte Loeschung im Test. Teilfortschritt muss beim
  Melden/Wiederaufnehmen klar sein; Rueckrollen des gesamten Laufs nicht behaupten.

## A-092 – Ungueltige Eventzuordnung wird erst nach externem Dokumentupload erkannt

- **Isoliert reproduzierte Validierungs-/Fehlerluecke, P2, M, Risiko M.**
- `backend/routes/docs.py:280` uebernimmt numerische event_id ohne Objektpruefung.
  `DriveStorageService.upload_document` ab Zeile 794 erstellt zuerst die Datei,
  dann die DB-Zeile. Unbekannte Event-ID scheitert erst am Fremdschluessel.
- DRIVE_BOUNDARY_CHECKS.json, `invalid_event_upload_compensation`: Original-
  Service mit erzwungenen SQLite-FKs und ungueltiger ID ruft einmal den ersetzten
  Upload auf, wirft IntegrityError und ruft den ersetzten Aufraeumhelfer einmal.
  Keine neue DB-Zeile bleibt. Keine echte Datei erzeugt; Erfolg des externen
  Aufraeumens nicht getestet. Die Route faengt IntegrityError nicht ab.
- Empfehlung: Existenz und erlaubte Sichtbarkeit der Eventzuordnung vor Upload
  pruefen; Fehler als Formularmeldung behandeln. Kompensation fuer echte
  nachgelagerte DB-Fehler trotzdem erhalten und deren Scheitern nachholbar machen.
- Abnahme: unbekannte/unerlaubte Referenz verursacht keinen Upload und keine
  Serverexception; Dateiauswahl und uebrige Eingaben bleiben nachvollziehbar.

## A-093 – Wiederhergestellte Drive-Datei verliert ihre App-Zuordnung zum Uploader

- **Reproduzierter Metadatenverlust, P2, M, Risiko M.**
- `auto_sync_document` ab `backend/services/drive_storage.py:1329` loescht
  bei trashed die Document-Zeile. `admin_full_resync` ab Zeile 1397 legt eine
  spaeter wieder sichtbare Datei ohne uploader_id und ohne event_id neu an.
- `trash_restore_loses_uploader`: synthetische Datei mit bekanntem Uploader,
  als trashed synchronisiert, danach als wiederhergestellt neu eingelesen.
  Zeilenzahl 1 → 0 → 1, uploader_id danach NULL. Eventverlust aus Neuanlage-
  Code abgeleitet, in diesem Fall nicht separat mit Eventdatensatz getestet.
  Datei-Inhalt bleibt ausserhalb des Tests; keine reale Datei geloescht.
- Empfehlung: entfernte Dateien als abgegangenen Bestand mit stabiler Drive-ID
  vormerken oder ihre App-Metadaten wiederherstellbar halten. Historie und
  Eventzuordnung beim Wiederauftauchen derselben Datei erhalten.
- Abnahme: Wiederherstellung derselben Drive-Datei stellt Herkunft/Zuordnung
  nachvollziehbar wieder her; tatsaechlich neue Dateien bleiben unterscheidbar.

## A-094 – Oeffentlicher Termin und Besuchshistorie wechseln schon am Eventtag

- **Reproduzierte Zeitgrenzen-Inkonsistenz, P2, M, Risiko M.**
- `get_landing_extras` in `backend/services/monatsessen_stats.py:75` vergleicht
  Datum mit voller aktueller Uhrzeit, Restauranttabelle ab Zeile 119 verwendet
  Datum <= heute. Dashboard behandelt Events dagegen bis Tagesende als kommend.
- PUBLIC_DASHBOARD_CHECKS.json, `today_event_public_date_boundary`: Eventdatum
  heute 00:00, Auswertung mittags; kein naechstes Essen mehr, aber bereits als
  besucht in der Tabelle. Datum-only-Erfassung ist in der App moeglich.
- Empfehlung: gemeinsame fachliche Regel fuer «kommend», «heute» und «besucht»
  festlegen, mit klarer Zeitzone. Fehlende Uhrzeit nicht als bereits beendetes
  Essen behandeln. Tageswechsel/Zeitzonen gesondert gegenpruefen.
- Abnahme: Landingpage, Dashboard und Hitlist widersprechen sich fuer denselben
  Eventtag nicht; Besuchsstatus folgt der beschlossenen fachlichen Grenze.

## A-095 – Oeffentliche Datenfehler werden als leere erfolgreiche Ergebnisse dargestellt

- **Isoliert reproduzierter Fehlerdarstellungsbruch, P2, M, Risiko M.**
- `backend/routes/public.py` faengt auf Landing-/Restaurantseite alle Exceptions
  ab und rendert Nullwerte ohne unterscheidbaren Fehlerzustand; die Suchseite
  verwirft dabei Query, Sortierung und Seite.
- `public_query_failure_becomes_empty_result`: Statistikaufruf gezielt durch
  RuntimeError ersetzt, Anfrage mit q=Audit/sort=name/page=2. Antwort 200 mit
  Gesamtzahl 0, leerer Query und Standardsortierung rating.
- Empfehlung: «keine Treffer» und «Daten derzeit nicht verfuegbar» unterscheiden,
  Suchzustand erhalten und Ursache serverseitig ohne sensible Inhalte loggen.
  Statuscode nach Art/Umfang des Ausfalls bewusst bestimmen.
- Abnahme: echte leere Suche bleibt normal bedienbar; Ausfall erweckt nicht den
  Eindruck, es gebe keine Restaurants/Mitglieder. Wiederholung behaelt Filter.

## A-096 – Restaurantidentitaet wird allein durch den Anzeigenamen bestimmt

- **Isoliert reproduzierte Aggregationsluecke, P2, M–L, Risiko M.**
- `get_landing_restaurant_table` gruppiert Events/Bewertungen nach Restaurantlabel;
  Ort und vorhandene place_id bleiben fuer die Identitaet unberuecksichtigt.
- `same_name_different_restaurants_merged`: zwei synthetische «Audit Bistro»
  mit unterschiedlichen Place-IDs und Orten ergeben eine Tabellenzeile; nur
  City B bleibt sichtbar. Ratings dieser beiden Orte wuerden nach Code ebenfalls
  in denselben Label-Topf gelangen; Rating-Mischung hier nicht separat getestet.
- Empfehlung: stabile Restaurantidentitaet definieren, z.B. Place-ID mit
  geregeltem Fallback fuer manuell erfasste Orte. Namen nur zur Anzeige verwenden;
  bestehende Zusammenlegungen vor spaeterer Datenmigration analysieren.
- Abnahme: gleiche Namen an verschiedenen Orten bleiben unterscheidbar;
  Namensaenderungen desselben Restaurants erzeugen keine unbeabsichtigten Dubletten.

## A-097 – Globale Controller ohne nachgewiesene Seitenverwendung

- **Bestaetigte Einbindungs-/Strukturbeobachtung, P2, M, Risiko M.**
- `base.html` bindet 13 lokale externe JS-Dateien auf jeder erbenden Seite ein.
  Die gerenderten Ladelisten fuer Startseite, Login, Restaurants und Ueber-uns
  bestaetigen dies (FRONTEND_ASSET_CHECKS.json).
- Darunter `v2/accordion.js` und `v2/search.js`: deren Auto-Initialisierung sucht
  `data-accordion` bzw. `data-search`. Keine solchen Hooks oder direkten externen
  Aufrufe von `Accordion`, `InstantSearch` oder ihren Initialisierungsfunktionen
  in Templates, Backend oder anderen JS-Dateien gefunden. Seiten implementieren
  verwandte Disclosure-/Filterfunktionen lokal, siehe A-005.
- Auswirkung: gemeinsame Bausteine werden ausgeliefert, ohne dass ihre Nutzung
  im untersuchten Code nachweisbar ist; Konsolidierung ist nur scheinbar erreicht.
  Kein gemessener Ladezeitverlust und noch keine Loeschfreigabe.
- Empfehlung: gewuenschten gemeinsamen Controller anhand realer Seitenmuster
  festlegen; Aufrufer migrieren oder verwaiste Implementierung entfernen.
  Anschliessend optionale Controller nur an ihren Nutzungsorten einbinden.
- Abnahme: deklarierte Komponenten haben belegte Consumer; keine parallelen
  Handler fuer denselben Zustand. Filter, Disclosures und dynamisch erzeugte
  Inhalte funktionieren in den vereinbarten Rollen-/Viewportzustaenden.
- Umfang und offene Messungen: [FRONTEND_REVIEW.md](FRONTEND_REVIEW.md).

## A-098 – Theme-Zustand und Schalter laufen nach Systemwechsel auseinander

- **Mit Original-JavaScript isoliert reproduzierter Zustandsfehler, P2, S–M, Risiko S.**
- `theme.js` wendet bei Systemwechsel ohne gespeicherte Auswahl das Systemtheme
  an. `getCurrentTheme()` und `toggle()` lesen dagegen ueber `getTheme()` den
  gespeicherten Wert oder pauschal `light`. `theme-toggle.js` verwendet diesen
  Rueckgabewert fuer Symbol, Beschriftung und `aria-checked`.
- Reproduktion: keine gespeicherte Wahl → Systemwechsel zu dunkel → DOM dunkel,
  Schalter und Manager melden hell. Naechstes `toggle()` setzt erneut dunkel.
  `resetToSystem()` bei dunklem System zeigt dieselbe Inkonsistenz; ein sichtbarer
  Aufrufer dieser Reset-Funktion ist damit nicht nachgewiesen.
- Beleg: [THEME_STATE_CHECKS.json](THEME_STATE_CHECKS.json), fuenf Zustandsproben
  mit Originalskripten in einer Node-VM und minimalem DOM-/Storage-Modell.
  Kein echter Browser-/Betriebssystemtest. Gespeicherte manuelle Wahl wird beim
  simulierten Systemwechsel korrekt beibehalten.
- Empfehlung: gespeicherte Praeferenz und tatsaechlich angewendetes Theme klar
  unterscheiden; Schalter und Toggle aus demselben wirksamen Zustand ableiten.
  Gewuenschten Standard (immer hell oder System) bewusst festlegen.
- Abnahme: Systemwechsel, manueller Wechsel und erneuter Seitenaufruf ergeben
  konsistente Darstellung, Symbol, Beschriftung und Schalterzustand.

## A-099 – Gemeinsame CSS-Regeln verwenden nicht definierte Designwerte

- **Code-bestaetigte Token-Luecke, P2, S–M, Risiko S–M; visuelle Auswirkung offen.**
- Die fuenf aktiven CSS-Quellen verwenden sechs nicht darin definierte Variablen
  ohne Fallback an sieben Stellen: `--leading-normal`, `--color-text-muted`,
  `--color-bg-tertiary`, `--space-11`, `--color-bg-primary`, `--font-size-sm`.
  Auch in Templates, Backend und JS wurde keine Definition fuer diese Namen gefunden.
- Konkreter aktiver Consumer: `.cleanup-step-nav__counter` verwendet
  `var(--font-size-sm)` in `components.css:5339`; Templates fuer Event-Bereinigung,
  Buchungserfassung und Belegupload nutzen diese Klasse. Das vorhandene
  Typografiesystem verwendet dagegen `--text-sm`.
- Weitere Treffer betreffen auch bislang nicht nachgewiesen genutzte Suchfeld-/
  Accordion-Klassen; nicht alle sieben Stellen sind sichtbare Seitenfehler.
- Ohne gueltigen Variablenwert/Fallback ist die betroffene Deklaration bei der
  Wertberechnung ungueltig. Nicht automatisch die vorherige Regel als wirksamen
  Ersatz annehmen; siehe [MDN var()](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/var).
- Beleg: [CSS_TOKEN_CHECKS.json](CSS_TOKEN_CHECKS.json), `survey_css_tokens.py`.
  Textabgleich, kein vollstaendiger CSS-Parser oder Computed-Style-Test.
  Dynamische Variablen wie `--rating-hue` und `--budget-meter-fill` sind separat
  beruecksichtigt und werden nicht als fehlende Designwerte gewertet.
- Empfehlung: aktive Komponenten auf kanonische Tokens umstellen; ungenutzte
  Komponenten vor einer Reparatur ihrer Tokens fachlich einordnen. Eine Pruefung
  fuer unbekannte Tokens mit ausdruecklicher Liste dynamischer Werte vorsehen.
- Abnahme: keine unerklaerten Variablen ohne Wert; Groessen/Farben der aktiven
  Consumer in beiden Themes und den vorgesehenen Viewports visuell pruefen.
- Browser-Gegenpruefung B-14/B-15: Buchungs- und Belegformular berechnen fuer die
  Schrittanzeige 16px; `--font-size-sm` ist leer, `--text-sm` vorhanden (0.875rem).
  Im Buchungsformular in Hell und Dunkel beobachtet. Siehe
  [Browsernachweis](browser/component-followup.json). Andere Token-Consumer offen.

## A-100 – Unsichtbares Navigationsmenue blockiert nach Wechsel auf Desktopbreite

- **Im Browser reproduzierter Fehler, P2, S–M, Risiko S–M.**
- Ausgeloggt auf `/ueber-uns` bei 390px das Navigationsmenue oeffnen, dann auf
  1024px verbreitern. `layout.css:294` blendet `.public-drawer` per `display:none`
  aus. `public-drawer.js` schliesst den modalen Dialog beim Breakpointwechsel nicht.
- Gemessener Zustand: Dialog `open=true`, `:modal=true`, `display=none`; auch der
  Menue-Trigger ist unsichtbar. Ein Klick auf den sichtbaren Desktop-Link Hitlist
  laesst die URL unveraendert. Escape schliesst den Dialog; derselbe Link navigiert
  danach korrekt nach `/restaurants`. Siehe B-23,
  [dialog-followup.json](browser/dialog-followup.json).
- Ursache: visuelles Ausblenden beendet den modalen Zustand nicht. Ein mit
  `showModal()` geoeffneter Dialog macht den uebrigen Dokumentinhalt inaktiv;
  siehe [MDN showModal()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal).
- Empfehlung: beim Wechsel zur Desktopnavigation den Dialog ueber seine
  Schliessfunktion schliessen, `aria-expanded` synchronisieren und Fokus an ein
  dann sichtbares, sinnvolles Ziel geben. Versteckten Trigger nicht fokussieren.
- Abnahme: geoeffnetes und geschlossenes Menue ueber 1023/1024px in beide
  Richtungen pruefen; Navigation bleibt per Maus, Tastatur und Touch bedienbar.
  Echte Tablet-Drehung und weitere Browser sind noch nicht geprueft.

## A-101 – Offline-API kann HTML mit Erfolgsstatus statt JSON liefern

- **Mit Original-Service-Worker isoliert reproduziert, P2, S–M, Risiko M.**
- `networkFirst` faellt bei Netzfehler und fehlendem Request-Cache auf die
  statische Offline-Webseite zurueck, auch fuer `/api/...`-Anfragen.
  SW-03 liefert `200 text/html`; `response.json()` scheitert.
- Beleg: [SW_STRATEGY_CHECKS.json](SW_STRATEGY_CHECKS.json). Cache/Netz sind
  synthetisch, kein Browser-Offline-Test. Der vorhandene Push-Status-Client
  faengt den Parsefehler ab; weitere Consumer muessen einzeln bewertet werden.
- Empfehlung: API-Fehler als definierten JSON-Fehler mit passendem Fehlerstatus
  oder bewusst als Netzfehler liefern. HTML-Ersatzseite auf Navigation begrenzen.
- Abnahme: Offline ohne API-Cache verletzt nicht den Antwortvertrag; UI zeigt
  «nicht verfuegbar» statt Erfolg oder irrefuehrendem Leerzustand.

## A-102 – Hintergrundaktualisierung ist nicht an Worker-Lebensdauer gebunden

- **Isoliert bestaetigte Zuverlaessigkeitsluecke, P2, S, Risiko S–M.**
- `staleWhileRevalidate` startet Fetch/Cache-Schreiben, gibt bei Cache-Treffer
  aber sofort die alte Antwort zurueck. Der Fetch-Handler registriert die
  Hintergrundarbeit nicht mit `event.waitUntil`. SW-06: Antwort bereits geliefert,
  Fetch noch offen, null waitUntil-Aufrufe.
- Moegliche Auswirkung: Browser beendet den Worker, bevor die neue Datei
  gespeichert ist. Ein tatsaechlicher Abbruch/veralteter Browserzustand wurde
  hier nicht reproduziert. [MDN waitUntil](https://developer.mozilla.org/en-US/docs/Web/API/ExtendableEvent/waitUntil)
  beschreibt die Verlaengerung der Event-Lebensdauer fuer solche Arbeit.
- Empfehlung: Hintergrund-Promise ueber den Fetch-Event absichern; Fehler
  weiterhin abfangen, Cache-Antwort nicht durch Netzlatenz verzoegern.
- Abnahme: Cache-Treffer bleibt schnell, Aktualisierung ist registriert und
  nach Abschluss fuer die naechste Anfrage nutzbar; Fehlerpfad bleibt bedienbar.

## A-103 – Automatische PWA-Updates laden laufende Formulare ungefragt neu

- **Bestaetigter Reload-Pfad, P2, M, Risiko M; Datenverlust im Browser noch offen.**
- SW aktiviert sofort via skipWaiting/clients.claim. Das aktuell eingebundene
  `pwa.df1b3f63.js` ruft bei controllerchange mit vorhandenem Controller direkt
  `window.location.reload()` auf. Keine Pruefung laufender Bearbeitung im Handler.
  SW-10 bestaetigt den Reload-Aufruf mit einem Zaehler statt echter Navigation.
- Potenzielle Auswirkung: ungespeicherte Formularwerte/Dateiauswahl gehen bei
  einem Update verloren. Betroffene Formulararten und Wiederherstellung sind
  noch nicht mit echtem Update im Browser gegengeprueft.
- Positiv: Erstaktivierung ohne vorherigen Controller fuehrt nicht zum Reload;
  Wiederholungsereignisse werden gegen Mehrfach-Reload abgesichert (SW-09/10).
- Empfehlung: Update-Uebernahme und Seitenreload mit Bearbeitungszustand
  abstimmen, z.B. nach Speichern oder ausdruecklicher Aktualisierung. Nicht
  pauschal alle Erstinstallationen oder Hintergrundpruefungen verzoegern.
- Abnahme: Update waehrend Buchung/Beleg/Event-Bearbeitung zerstoert keine
  ungespeicherten Eingaben; Erstinstallation, mehrere Tabs und Leerzustand testen.

## A-104 – GGL berechnet Ranglisten mehrfach mit Einzelabfragen pro Event/Mitglied

- **Lokal gemessene Abfrageskalierung, P2, M, Risiko M.**
- GGL-Tab Tabelle benoetigt bei 5 Events 46 SQL-Ausfuehrungen, bei 30 Events 171
  (je 5 Mitglieder). Je zwei Aufrufe mit frischer ORM-Session ergeben dieselben
  Zaehler. Keine Aussage ueber produktive Ladezeit.
- `ggl.index` berechnet fuer die aktuelle Saison Ranglisten in der Saisonschleife,
  fuer den Tab und ueber `get_member_performance_view_context` erneut.
  `get_season_ranking` fragt Teilnahmen je Event einzeln ab: bei 30 Events
  dieselbe Queryform 90-mal. Die restliche Skalierung enthaelt A-030; Zahlen
  nicht als voneinander unabhaengige Einsparpotenziale addieren.
- `_attach_member_to_ranking` laedt ausserdem einzelne Mitglieder; 5 → 30
  Mitglieder bei 5 Events erhoeht den Request von 46 auf 71 Abfragen.
- Historien-Gegenprobe: eine → sechs Saisons mit je fuenf Events erhoeht
  aktuelle Tabelle und Performance jeweils von 46 auf 141 Queries, bei
  unveraenderter aktueller Rangliste. Die Saisonschleife verarbeitet alte
  Saisons vorab; 50 der 95 zusaetzlichen Queries gehoeren zu A-030.
  Beleg: [24 Historien-Messungen](HISTORY_SCALING_CHECKS.json).
- Empfehlung: Rangliste je Request/Saison einmal aufbereiten, Tab-Bedarf
  beruecksichtigen und Teilnahmen/Mitglieder gebuendelt laden. Fachliche Regeln
  zu Ranggleichheit, Teilnahme und Saison separat erhalten und gegenpruefen.
- Abnahme: keine Einzelabfrage pro Event/Mitglied fuer die Ranglistenanzeige,
  keine wiederholte Berechnung desselben Saisonbestands; Ergebnisse bleiben gleich.
- Nachweise: [QUERY_SCALING_REVIEW.md](QUERY_SCALING_REVIEW.md) und
  [48 isolierte Render-Aufrufe](QUERY_SCALING_CHECKS.json).

## A-105 – Buchhaltung laedt alle Tabs und fragt Belege pro Buchung nach

- **Lokal gemessene Abfrageskalierung/Renderlast, P2, M–L, Risiko M.**
- `accounting.index` laedt Journal, Belege, Budget, Kommentare, Statistik, Import
  und Claims unabhaengig vom aktiven Tab. `accounting/index.html` rendert die
  Panels vollstaendig; CSS blendet inaktive Panels aus. Keine Begrenzung des
  Journals in `AccountingService.get_journal` (endet mit `.all()`).
- `booking.receipts` im Journal (`index.html:290`) erzeugt zusaetzlich eine
  Belegabfrage je Buchung. 5 → 40 Buchungen mit je einem Beleg: 32 → 67 SQL-
  Ausfuehrungen, auch in Uebersicht und Offene Posten. Uebersichts-HTML waechst
  von 92'691 auf 205'504 Bytes; reine lokale HTML-Groesse, keine Netzzeit.
- 5 → 40 Claims erhoeht bei konstanten 32 Queries dieselbe Uebersicht auf
  155'442 Bytes. Queryzaehler allein wuerde dieses Wachstum uebersehen.
- Empfehlung: Vertrag fuer sofortige Tabs vs. umfangreiche Listen festlegen,
  Listen begrenzen/bei Bedarf laden und Beleginformationen gesammelt bereitstellen.
  Nicht nur SQL optimieren und die unbegrenzte HTML-Ausgabe unveraendert lassen.
- Abnahme: Umfang nicht ausgewaehlter Listen belastet kleine Uebersichten nicht
  unbegrenzt; keine Einzelabfrage je Buchung fuer den Belegindikator. Tabwechsel,
  Filter, Rechte und Kennzahlen bleiben fachlich identisch.
- Beleg: [COMMERCE_SCALING_CHECKS.json](COMMERCE_SCALING_CHECKS.json), jeweils
  zwei frische ORM-Sessions; SQLite/synthetischer Admin, keine produktiven Zeiten.

## A-106 – Bestellverwaltung laedt Positionen fuer jeden Mengenzaehler einzeln

- **Lokal gemessenes N+1-Muster, P2, M, Risiko S–M.**
- `/admin/merch?tab=orders` mit Standardsortierung nach Mitglied laedt Bestellungen
  gesammelt. Das Template ruft fuer jede Order `get_item_count()` auf; dieses
  summiert die noch nicht geladenen `order_items`.
- 5 → 40 Bestellungen mit je einer Position: 15 → 50 SQL-Ausfuehrungen,
  Positions-SELECT 5 bzw. 40 Mal. HTML waechst von 43'297 auf 155'697 Bytes.
  Wiederholung mit frischer ORM-Session liefert dieselben SQL-/ORM-Zaehler.
- Empfehlung: Stueckzahlen je Order gesammelt aggregieren oder benoetigte
  Positionen gezielt vorladen; grosse Bestelllisten begrenzen. Mengen bedeuten
  Summe quantity, nicht einfach Zahl der Positionen.
- Abnahme: eine groessere Bestellliste verursacht keine einzelne Positionsquery
  pro Zeile; Mengenzaehler stimmen auch bei mehreren Positionen/Mengen >1.
- Gegenbeispiel: persoenlicher Bestelltab bleibt in dieser Fixture bei sieben
  Queries und laedt nur die Position der ausgewaehlten Bestellung.
- Beleg: [Skalierungsbericht](QUERY_SCALING_REVIEW.md), zweiter Durchlauf.

## A-107 – Offline-Seite leitet ohne App-Erreichbarkeitspruefung weiter

- **Isoliert reproduzierter Steuerungsfehler, P2, S–M, Risiko L.**
- Das aktive `static/offline.4ebb2a42.html` navigiert bei navigator.onLine
  nach 1.5s auf `/`, ohne Serverpruefung. Erneutes Offline storniert den Timer
  nicht. Der letzte Sync-Zeitpunkt ist nur die lokale Uhr.
- OFF-01 bis OFF-05 bestaetigen die Steuerung. Wiederholte Fallback-Auslieferung
  erzeugt weitere Navigationen im Modell; keine echte Browser-Schleife gemessen.
- Empfehlung/Abnahme: kontrollierter Wiederholungsweg, Erreichbarkeit pruefen,
  Timer koordinieren, Ziel erhalten und keinen nicht erfolgten Sync behaupten.
- Beleg: [Offline-Proben](OFFLINE_RETURN_CHECKS.json),
  [Teilbericht](INTEGRATION_OPERATIONS_REVIEW.md).

## A-108 – Places-Aufrufe haben keine eigenen Verbindungs-/Lesezeitlimits

- **Verifizierter Aufrufvertrag, P2, S–M, Risiko M.**
- `backend/services/places.py:55,113` ruft requests.get ohne timeout auf.
  INT-01/02 pruefen Originalargumente. Injizierter Timeout liefert leere
  Vorschlaege (INT-03), nicht unterscheidbar von fehlenden Treffern.
- Keine produktive Blockade gemessen. Fehlendes Transportlimit kann bei
  haengendem Dienst Request-Kapazitaet binden.
- Empfehlung/Abnahme: Verbindungs-/Lesezeiten und Interaktionsbudget festlegen;
  Fehler verstaendlich von leeren Treffern unterscheiden, manuelle Eingabe erhalten.
- Beleg: [Service-Proben](INTEGRATION_CONTRACT_CHECKS.json),
  [Teilbericht mit Requests-Referenz](INTEGRATION_OPERATIONS_REVIEW.md).

## A-109 – Mail-Service meldet ohne SMTP-Konfiguration Erfolg

- **Reproduzierbarer Service-Vertragsfehler, P2, S–M, Risiko M.**
- Ohne Resend-Key/SMTP-Host liefert MailService.send success=true mit
  error=smtp_host_missing. Bei Host ohne Credentials sogar success=true ohne
  Fehlertext. Kein Versand, keine message_id (INT-04/05).
- Kein expliziter Testmodus begrenzt diese Zweige. Positiv: Admin-Mailtest
  erkennt fehlende message_id und warnt. Andere Consumer noch einzeln pruefen.
- Empfehlung/Abnahme: uebersprungen, angenommen, versendet und fehlgeschlagen
  unterscheiden; fehlende Konfiguration darf nicht als Versand gelten.
- Beleg: [Service-Proben](INTEGRATION_CONTRACT_CHECKS.json).

## A-110 – Places-Autocomplete loggt den API-Schluessel auf INFO

- **Reproduzierbarer Logging-Fehler, P1, S, Risiko L.**
- `backend/services/places.py:52` loggt params einschliesslich key. INT-01
  erkennt einen erfundenen Marker im abgefangenen Original-Loggeraufruf;
  nur das Boolean-Ergebnis gespeichert. Keine echten Keys oder Logs gelesen.
- Produktive Exposition und Key-Beschraenkungen unbekannt. Gemeinsam mit
  A-081 systematischen Logging-Abgleich vorsehen; keine automatische Rotation.
- Empfehlung/Abnahme: nur sichere Parameter protokollieren; erfolgreiche und
  fehlgeschlagene Places-Aufrufe duerfen keine Keys loggen.
- Beleg: [Service-Proben](INTEGRATION_CONTRACT_CHECKS.json).

## A-111 – Wiederholter Cron-Lauf beauftragt dieselben Erinnerungen erneut

- **Isoliert reproduzierter Wiederholungsfehler, P2, M, Risiko M.**
- `check_and_send_3_week_reminders` waehlt nur nach Eventdatum/Typ/Publikation.
  NOT-01: Zwei unmittelbare Laeufe fuer dasselbe Event rufen Organisator- und
  Mitgliederversand jeweils zweimal auf. Kein dauerhafter Versandmarker.
- Keine echten Pushs oder parallelen Prozesse; sichtbare Doppelmeldungen nicht
  behaupten. Client-Tags ersetzen keinen serverseitigen Wiederholungsschutz.
- Empfehlung: Versandauftrag je Event/Art/Empfaenger nachvollziehbar reservieren,
  Ergebnis speichern und nur fehlgeschlagene Ziele gezielt wiederholen.
- Abnahme: erneute und parallele Ausfuehrung duplizieren abgeschlossene
  Auftraege nicht; Teilfehler bleiben wiederholbar. Schemaentscheidung spaeter.
- Beleg: [Neun Grenzproben](NOTIFICATION_BOUNDARY_CHECKS.json),
  [Teilbericht](INTEGRATION_OPERATIONS_REVIEW.md).

## A-112 – Reminder-Versandfehler werden als erfolgreicher Cron-Lauf gewertet

- **Reproduzierbarer Ergebnisfehler, P2, M, Risiko M.**
- NOT-02: Organisatorversand false und Mitgliederversand success=false;
  `check_and_send_3_week_reminders` liefert trotzdem success=true.
- NOT-09: Originaler `run_all_reminders` mit solchem eingesetzten Batch und
  ansonsten leeren erfolgreichen Laeufen endet mit Exitcode 0. Damit kann
  ein auf Prozessstatus basierender Monitor den Versandfehler uebersehen.
- Empfehlung: Durchlauf/Empfaenger/Versand getrennt zaehlen, Teilfehler bis
  HTTP-/Prozessstatus verfolgen; bewusst uebersprungene leere Laeufe erhalten.
- Abnahme: Totalausfall und Teilfehler erscheinen unterscheidbar im Ergebnis,
  Log und Monitoring-Vertrag; normale Null-Empfaenger-Laeufe bleiben erklaerbar.
- Beleg: [Neun Grenzproben](NOTIFICATION_BOUNDARY_CHECKS.json).

## A-113 – Cron-Testendpunkt ist mit ProductionConfig ohne Authentifizierung erreichbar

- **Isoliert reproduzierter Zugriffskontrollfehler, P1, S–M, Risiko M.**
- `/cron/test` ist CSRF-befreit, ohne Login/Cron-Token-Pruefung. Es sperrt nur
  bei config.ENV == production. Die originale ProductionConfig setzt ENV nicht.
- NOT-07: Isolierte Flask-App mit dieser Klasse, DEBUG=False und gesetztem
  synthetischem Cron-Token: anonymer POST auf regulaeren Cron 401, auf Test 200
  und Aufruf des ersetzten Reminder-Service. Explizites ENV=production sperrt
  korrekt (NOT-08). Aktuelle Railway-Konfiguration/Erreichbarkeit ungeprueft.
- Empfehlung: Testendpunkt explizit freischalten oder entfernen; jeden
  verbleibenden Versandpfad einheitlich authentifizieren, standardmaessig sperren.
- Abnahme: ProductionConfig allein ermoeglicht keinen anonymen Versandauftrag;
  fehlende Zusatzkonfiguration darf keine Schutzfunktion deaktivieren.
- Beleg: [Neun Grenzproben](NOTIFICATION_BOUNDARY_CHECKS.json).

## A-114 – Reminder-Auswahl holt am Folgetag verpasste Laeufe nicht nach

- **Reproduzierbarer Auswahlvertrag, Produkt-/Betriebsentscheidung, P2, M, Risiko M.**
- TIME-01 bis TIME-03 vergleichen passende UTC-Laufzeit und Folgetag:
  3-Wochen-, Wochen- und Bewertungsreminder verarbeiten jeweils zuerst ein
  Event, am Folgetag keines. Datumsauswahl enthaelt keinen Nachholmechanismus.
- Keine realen Scheduler-Ausfaelle oder verpassten Pushs nachgewiesen.
- Empfehlung: pro Reminder festlegen, ob/wie lange Nachholen sinnvoll ist;
  mit dauerhaftem Versandregister A-111 verbinden. Fenster nicht isoliert
  vergroessern, sonst werden bereits bearbeitete Empfaenger erneut beauftragt.
- Abnahme: verspaetete Laeufe folgen dokumentierter Regel, ueberfaellige
  Auftraege werden nachvollziehbar nachgeholt oder bewusst verworfen.
- Beleg: [Zeitfenster-Proben](REMINDER_WINDOW_CHECKS.json).

## A-115 – Aktueller Push-Versand reicht ein unbegrenztes Transportzeitlimit weiter

- **Verifizierter Aufrufvertrag, P2, S–M, Risiko M.**
- `PushNotificationService.send_push_notification` setzt kein timeout.
  TIME-04/05: lokal installierte pywebpush-Funktion reicht Default None an
  WebPusher.send; dessen Code reicht es an Requests weiter. Ein Ersatzwert
  bei fehlendem Keyword greift hier nicht, da das Keyword vorhanden ist.
- Keine produktive Wartezeit/Blockade gemessen. Versand erfolgt in Schleifen;
  ein haengender Versuch kann nachfolgende Empfaenger aufhalten.
- Empfehlung: begrenzte Transportzeiten und Laufbudget, Fehler pro Empfaenger
  erfassen, weitere Empfaenger verarbeiten; mit A-112-Ergebnisvertrag verbinden.
- Abnahme: simulierter Timeout beendet den Versuch kontrolliert, verschluckt
  den Fehler nicht und blockiert weitere Versandauftraege nicht unbegrenzt.
- Beleg: [Zeitfenster-/Transportproben](REMINDER_WINDOW_CHECKS.json),
  [Quellpfad und Grenzen](INTEGRATION_OPERATIONS_REVIEW.md).
- LEG-03 bestaetigt fehlendes timeout auch im alten NotifierService;
  gleicher Transportpfad, kein zusaetzlicher gleichartiger Befund.

## A-116 – Alter Notifier behandelt Subscription-Zustaende und temporaere Fehler falsch

- **Reproduzierbarer Zustands-/Datenverlustfehler, P1, M, Risiko M.**
- NotifierService fragt alle Abonnements eines Mitglieds ohne is_active ab.
  `_send_to_subscription` gibt bei jedem Fehler False, worauf der Aufrufer
  die Subscription loescht und committet.
- LEG-01/02: Timeout und HTTP 503 loeschen jeweils die synthetische Zeile.
  LEG-03: deaktivierte Subscription wird dennoch an den Transport uebergeben.
  Der aktuelle Push-Dienst erhaelt dagegen bei 503 die Zeile (NOT-04).
- Empfehlung: gemeinsamen Lifecycle verwenden, deaktivierte Geraete auslassen;
  nur bestaetigt ungueltige Endpoints deaktivieren, voruebergehende Fehler erhalten.
- Abnahme: Timeout/503 loeschen kein gueltiges Abonnement; deaktivierte Zeilen
  erhalten keine Versandauftraege. BillBro und Cron nutzen denselben Vertrag.
- Beleg: [Sechs Legacy-Proben](LEGACY_NOTIFIER_CHECKS.json).

## A-117 – BillBro meldet Versand, obwohl der Fallback nur einen Logeintrag schreibt

- **Reproduzierbare falsche Erfolgsmeldung, P2, M, Risiko M.**
- Ohne Subscription liefert `_send_fallback_notification` True nach reinem
  Logging. BillBro wertet dies als erfolgreichen Versand.
- LEG-04: Originaler Start-POST als Organisator mit einem Teilnehmer, ohne
  Subscription: Meldung ueber einen gesendeten Push bei null Push-/Mail-Aufrufen.
- Empfehlung: Ergebnis uebersprungen/fehlgeschlagen/versendet unterscheiden,
  echte Versandzahlen anzeigen. Ob Ersatz-Mail gewollt ist, separat entscheiden.
- Abnahme: kein Versand-Erfolg fuer reines Logging; Anzeige bleibt auch bei
  gemischten Empfaengerergebnissen korrekt. Siehe auch A-109/A-112 zum Vertrag.
- Beleg: [Sechs Legacy-Proben](LEGACY_NOTIFIER_CHECKS.json).

## A-118 – Alte Push-Registrierung entfernt andere Geraete desselben Mitglieds

- **Reproduzierbare Mehrgeraete-Abweichung, P2, M, Risiko M.**
- `NotifierService.subscribe_user_to_push` loescht zuerst alle Subscriptions
  des Mitglieds. LEG-05: zweites Geraet ersetzt das erste vollstaendig.
- Die Route `/notifications/subscribe` bleibt registriert. Aktuelle Browser-
  Nutzung des Altpfads nicht nachgewiesen; kein pauschal verwaister Code.
- Empfehlung: Registrierung pro Endpoint aktualisieren und andere Geraete
  erhalten; alte Clients bei API-Konsolidierung A-011 bewusst ueberfuehren.
- Abnahme: zwei Geraete bleiben parallel registriert, Wiederholung dupliziert
  den Endpoint nicht. LEG-06 zeigt bereits korrekten Rollback bei fehlenden keys.
- Beleg: [Sechs Legacy-Proben](LEGACY_NOTIFIER_CHECKS.json).

## A-119 – Technik-Status bleibt trotz gesetzter Meldung unsichtbar

- **Im Browser bestaetigter Darstellungsfehler, P2, S, Risiko S.**
- `templates/member/technical.html:313` setzt hidden; `showUpdateStatus` in
  `static/js/pwa.js:1181` setzt nur display:block. Die globale hidden-Regel
  mit !important gewinnt. B-26: Text gesetzt, Details offen, display:none,
  null sichtbare Rechtecke. Originaler Renderer isoliert aufgerufen; keine
  echte Diagnose-/Update-/Push-Aktion durchgefuehrt.
- Empfehlung: Sichtbarkeit einheitlich ueber hidden steuern, auch beim
  zeitgesteuerten Ausblenden; Statusstile im aktiven Designsystem bereitstellen.
- Abnahme: Info, Erfolg und Fehler sichtbar und zugaenglich angekuendigt;
  Ausblenden sowie erneute Anzeige funktionieren zuverlaessig.
- Beleg: [Browser-Gegenpruefung](browser/registry-followup.json), B-26.

## A-120 – Schliessen-Knopf an Flash-Meldungen bleibt wirkungslos

- **Im Browser bestaetigter Bedienfehler, P2, S, Risiko S.**
- Originaler Button in `templates/partials/_flash_messages.html` entfernt die
  Meldung nicht. B-27: direkt nach Reload und Klick weiterhin display:flex,
  opacity:1 und Meldung im DOM. `initializeFlashMessages` in app.js bietet
  automatisches Entfernen nach 5 Sekunden, aber keinen Schliessen-Handler.
- Empfehlung: gemeinsamen expliziten Schliessen-Handler verwenden und
  Anzeigedauer nach Meldungstyp festlegen; relevante Fehler lesbar erhalten.
- Abnahme: Maus und Tastatur schliessen die jeweilige Meldung sofort;
  automatisches Verschwinden nicht als erfolgreicher Klicktest werten.
- Beleg: [Browser-Gegenpruefung](browser/registry-followup.json), B-27.

## A-121 – Backup-Code-QR verspricht Export, zeichnet aber nur einen Platzhalter

- **Im Browser bestaetigte irrefuehrende Funktion, P2, S–M, Risiko M.**
- `templates/auth/backup_codes.html:124` bildet qrData, verwendet es aber nicht.
  showQRCode zeichnet lediglich Rahmen und Platzhaltertext. B-28 bestaetigt
  diesen sichtbaren Canvas mit synthetischen Codes, waehrend die UI zum Scannen
  auffordert und behauptet, alle Codes seien enthalten.
- Empfehlung: QR-Funktion entfernen, falls kein fachlicher Bedarf besteht;
  sonst definiertes, lokal erzeugtes Exportformat implementieren. QR-Encoding
  allein ist keine Verschluesselung und begruendet kein Sicherheitsversprechen.
- Abnahme: entweder keine QR-Aktion/Behauptung mehr oder unabhaengiger Decoder
  liest exakt die synthetischen Codes; keine Uebermittlung an externe QR-Dienste.
- Beleg: [Browser-Gegenpruefung](browser/registry-followup.json), B-28.

## A-122 – Event-Archiv verwendet nicht geladene Paginierungsstile

- **Im Browser bestaetigte Layoutabweichung, P3, S, Risiko S.**
- `templates/events/index.html:432` verwendet landing-pagination und deren
  Statusklasse. Definitionen stehen in `static/css/public.css:442`, aber das
  Archiv laedt nur main-v2. B-29: display:block und gap:normal an vier Breiten.
  Bei 320px steht Weiter direkt unter Zurueck ohne vertikalen Abstand;
  bei 390/820/1440px beginnt Weiter direkt am rechten Rand des Statustextes.
- Seitennavigation 1 → 2 → 3 → 2 funktioniert. Suche setzt auf Seite 1 zurueck
  und bleibt beim folgenden Seitenwechsel erhalten. Kein belegter Datenverlust.
- Empfehlung: gemeinsame Paginierungskomponente im aktiven V2-Bundle mit
  definiertem Umbruch, Abstaenden und Status; Public und intern gemeinsam nutzen.
- Abnahme: erste/mittlere/letzte Seite an 320px bis Desktop bedienbar und
  mit Abstaenden; Such-/Jahr-/Organisatorfilter bleiben bei Seitenwechsel erhalten.
- Beleg: [Archiv-/Warnhinweis-Gegenpruefung](browser/archive-warning-followup.json).

## A-123 – Fixierte Import-Dateispalte verdeckt auf schmalen Displays den Tabelleninhalt

- **Im Browser reproduzierter Layoutfehler, P2, S–M, Risiko S.**
- `templates/accounting/index.html:489` nutzt data-table--sticky-first fuer die
  Import-Historie. Die generische Regel setzt nowrap und sticky, ohne die
  Dateispaltenbreite auf einen Teil des verfuegbaren Bereichs zu begrenzen.
- B-39 bei 390px: Dateiname Audit-Kontoauszug-September-2026.csv ergibt
  304.36px erste Spalte bei 285px nutzbarer Tabellenbreite. Am maximalen
  Scrollstand 446 ueberdeckt diese Spalte weiterhin die anderen Daten und
  die Loeschaktion. DOM-Geometrie, Hit-Test und Screenshot stimmen ueberein.
  Kein Loeschversuch. Bei 820px stehen 675px Tabellenbreite zur Verfuegung;
  derselbe Dateiname nimmt dort nicht die gesamte Breite ein.
- Empfehlung: Dateispalte begrenzen und Dateinamen umbrechen/gezielt kuerzen,
  vollstaendigen Namen zugaenglich halten; alternativ sticky bei engem Raum
  aufheben. Tabellen mit anderen langen Identifikatoren mitpruefen.
- Abnahme: lange Dateinamen an 320/390px verdecken weder Zahlen noch Aktionen;
  alle Spalten am Scrollende sichtbar und mit Maus/Tastatur erreichbar.
  Bei 820px/Desktop bleibt die Orientierung erhalten.
- Beleg: [Buchhaltungstabellen](browser/accounting-tables-keyboard.json), B-39.

## A-124 – Kalender-ETag aendert sich auch ohne geaenderte Termine

- **Isoliert reproduzierter Cache-Vertragsfehler, P2, S–M, Risiko S.**
- CalendarFeedService setzt DTSTAMP bei jeder Generierung auf die aktuelle
  Uhrzeit und berechnet den ETag aus dem ganzen Feed. CAL-01 liefert bei
  gleicher Uhrzeit 304; CAL-02 liefert fuenf Minuten spaeter trotz unveraenderter
  Daten 200 mit neuem ETag. Einziger Unterschied der Termine ist DTSTAMP.
- Empfehlung: stabile Aenderungszeit-/Inhaltsbasis fuer Feed und ETag nutzen.
  Abnahme: unveraenderte Termine liefern auch bei spaeterem bedingtem Abruf
  304; echte Inhaltsaenderung liefert neuen ETag und aktuellen Body.
- Kein gemessener produktiver Lastschaden; private max-age=300 bleibt wirksam.
- Beleg: [Kalenderproben](CALENDAR_CACHE_CHECKS.json), CAL-01/02.

## A-125 – Kalender-Aenderungsvergleich deckt ausgegebene Felder nicht vollstaendig ab

- **Isoliert reproduzierte Vertragsabweichung, P2, M, Risiko M.**
- calendar_relevant_state laesst Notizen aus, obwohl diese in DESCRIPTION
  erscheinen. audience steht in RELEVANT_FIELDS, fehlt aber ebenfalls im
  Snapshot. CAL-03/05 bestaetigen unveraenderte SEQUENCE nach diesen Aenderungen;
  CAL-04 bestaetigt korrektes Hochzaehlen beim Restaurantwechsel.
- Empfehlung: ausgegebene Inhalte, Sichtbarkeit und Aenderungsquellen gemeinsam
  inventarisieren und konsistent versionieren. Abnahme: definierte relevante
  Aenderungen erhoehen die Version genau einmal; irrelevante tun dies nicht.
- Kein nachgewiesener Rechtebruch oder beobachteter Updateverlust in realen
  Kalender-Apps; deren Synchronisierungsverhalten separat pruefen.
- Beleg: [Kalenderproben](CALENDAR_CACHE_CHECKS.json), CAL-03 bis CAL-05.
- Erweiterung CAL-10: geaenderter Organisator-Rufname aendert ORGANIZER-CN
  und DESCRIPTION, ohne SEQUENCE oder LAST-MODIFIED des Events zu aendern.
  Dieser abhaengige Profilpfad gehoert in denselben Aenderungsvertrag.
  [Inhalts-/Grenzproben](CALENDAR_CONTENT_CHECKS.json) bestaetigen daneben
  stabile UID und korrektes Hochzaehlen fuer sechs direkte Feldaenderungen.
- CAL-15 bestaetigt die Notizluecke ueber den originalen Event-Edit-POST;
  CAL-13/14/16 pruefen unveraendertes Speichern, Datum und mehrere Aenderungen
  als Positivkontrollen. Siehe [Routenproben](CALENDAR_ROUTE_CHECKS.json).

## A-126 – Ordnerauswahl meldet Aufklapp- und Auswahlzustand nicht semantisch

- **Im gerenderten Browser-DOM bestaetigte Zugaenglichkeitsluecke, P2, M, Risiko S.**
- `static/js/v2/docs-folder-picker.js` erzeugt Root-Toggle mit reinem +/-Text;
  alle weiteren Toggle-Namen lauten gleich „Unterordner laden“. aria-expanded
  fehlt. Auswahl wird nur durch row--selected markiert, ohne ausgewiesenen
  Auswahlzustand am bedienten Element. B-42 bestaetigt dies mit zwei Ebenen.
- Empfehlung: ein konsistentes Auswahlmuster mit ordnerbezogenen Namen,
  eindeutigem Aufklappzustand und programmatisch erkennbarem Auswahlzustand.
  Nicht lediglich role=tree setzen, ohne dessen Tastaturmodell umzusetzen.
- Abnahme: Tastatur und Screenreader erkennen Ordner, offen/geschlossen und
  ausgewaehltes Ziel; nach Laden und Auswahl bleibt die Orientierung erhalten.
- Enter-Auswahl, Dialogrueckkehr und Escape funktionieren in den geprueften
  Faellen. Keine pauschale Unbedienbarkeit und kein Screenreader-Test behauptet.
- Beleg: [Dokumentdialoge](browser/docs-dialog-followup.json), B-41 bis B-44.
- Ergaenzung B-50 bis B-52: Zweige bleiben im geprueften Erfolgs-/Fehlerpaar
  unabhaengig; erneutes Laden ist durch Zu-/Aufklappen moeglich. Ein leerer
  Unterordner zeigt jedoch nur ein Minus, ohne Leerzustandsmeldung, bei weiterhin
  generischem zugänglichem Namen. Beim gemeinsamen Zustandsmodell auch
  Laden, leer und Fehler mit erkennbarem Wiederholungsweg beruecksichtigen.
  Beleg: [Zweigproben](browser/docs-branches-followup.json).

## A-127 – Upload ohne Datei verwirft bereits eingegebene Formulardaten

- **Im Browser reproduzierter Eingabeverlust, P2, S–M, Risiko S.**
- `_upload_modal.html` setzt novalidate, obwohl Datei und Titel required sind;
  docs-upload-modal.js ersetzt dies nicht durch Submit-Validierung.
  Die Route lehnt fehlende Dateien korrekt ab, leitet aber auf den Einstieg
  zurueck. B-45: eingegebener Dateiname ist beim erneuten Oeffnen leer.
- Empfehlung: fehlende Datei vor Navigation am Feld anzeigen und fokussieren;
  bei Serverfehlern Titel/Ziel/Event erhalten und Dialog mit Fehler wieder
  anzeigen. Servervalidierung bleibt erforderlich.
- Abnahme: fehlende Datei fuehrt zu verstaendlichem Fehler ohne Entwurfsverlust;
  normale Abbruch-/Wiederaufnahme- und Serverfehlerpfade bleiben konsistent.
- Beleg: [Upload-Fehlerproben](browser/docs-errors-followup.json), B-45.
- Erweiterung vom 2026-09-21: Rename/Move/Restore leiten bei behandeltem Fehler
  ebenfalls ohne Entwurf zurueck. DOCS_ACTION_CHECKS.json bestaetigt Redirects
  ohne gespeicherte Eingaben; docs-quick-actions.js setzt beim Oeffnen Rename
  auf den bisherigen Namen und Move/Restore auf leere Ziele. Quellcode-/
  Routenbeleg, noch kein neuer Browser-Nachweis des Eingabeverlusts. Empfehlung
  fuer Entwurfserhalt und feldnahe Wiederholung auf diese Aktionen ausdehnen.

## A-128 – Fehler beim Laden des Picker-Wurzelordners bleiben ohne sichtbare Rueckmeldung

- **Mit simuliertem HTTP-Fehler im Browser reproduziert, P2, S, Risiko S.**
- openPicker in docs-folder-picker.js behandelt Fehler des initialen
  `/docs/api/root`-Aufrufs nicht. Der Dialog oeffnet erst nach erfolgreichem
  Laden. B-46: synthetischer 503 fuehrt nur zu Konsolenfehler; Fokus bleibt
  auf Ordner waehlen, kein Picker und keine sichtbare Meldung.
- Empfehlung: Lade-/Fehlerzustand am Ausloeser oder im bereits geoeffneten
  Dialog anzeigen, erneuten Versuch und Abbrechen anbieten; Eingaben erhalten.
- Abnahme: Root-HTTP-Fehler/Netzwerkausfall liefert sichtbare, zugaengliche
  Rueckmeldung; Wiederholen nach Erholung funktioniert ohne verlorenen Entwurf.
- Fehler beim Laden von Unterordnern hat bereits eine sichtbare Meldung (B-44);
  nicht alle Picker-Fehlerwege pauschal als unbehandelt bezeichnen.
- Beleg: [Upload-Fehlerproben](browser/docs-errors-followup.json), B-46.
- B-47 ergaenzt die Positivkontrolle: Nach einmaligem Root-503 oeffnet ein
  erneuter Klick den Picker erfolgreich; der eingegebene Titel bleibt erhalten.

## A-129 – Unterordner erscheinen hinter Nachbarordnern ihres Elternordners

- **Im Browser reproduzierter Hierarchiefehler, P2, M, Risiko S.**
- `renderChildren` in `static/js/v2/docs-folder-picker.js` haengt den neuen
  Kindercontainer an das Ende des bestehenden Zweigcontainers. B-48 zeigt:
  Unterlagen, Ladefehler, Protokolle; Protokolle gehoert jedoch zu Unterlagen.
  Die Einrueckung allein macht diese Reihenfolge nicht eindeutig.
- Empfehlung: Kinder direkt unter ihrem Elternordner darstellen und beim
  Auf-/Zuklappen benachbarte Zweige unabhaengig erhalten. Zusammen mit A-126
  ein einheitliches, auch per Tastatur verstaendliches Auswahlmuster festlegen.
- Ergaenzende Orientierungsluecke B-49: Nach Auswahl von Protokolle und
  Zuklappen von Unterlagen bleibt Uebernehmen aktiv, ohne sichtbare Auswahl
  oder Zusammenfassung. Die Uebernahme zeigt danach korrekt Protokolle an.
  Empfehlung: aktuelles Ziel auch bei zugeklapptem Zweig sichtbar benennen.
- Abnahme: mehrere Nachbarzweige und tiefere Ebenen bleiben ihrem Elternordner
  eindeutig zugeordnet; das aktuell uebernommene Ziel ist jederzeit erkennbar.
- Kein nachgewiesener falscher Upload; nur sichtbare Hierarchie und Zielanzeige
  geprueft. Beleg: [Baum-/Wiederholungsproben](browser/docs-tree-retry.json), B-47 bis B-49.

## A-130 – Parallele Picker-Oeffnungsanfragen werden nach Abschluss nicht entwertet

- **Isoliert im Originalcontroller reproduziert, P2, S–M, Risiko S.**
- **Browser-Nachweis ergaenzt:** B-53/B-54 bestaetigen mit verzoegerten lokalen
  Root-Antworten zwei Dokumente-Zeilen und erneutes Oeffnen nach Schliessen.
  Fokus zuerst zurueck auf Ordner waehlen, danach auf Schliessen im Picker.
  Beleg: [Root-Rennen im Browser](browser/docs-root-race.json). Die folgenden
  Grenzen zum DOM-Ersatz beziehen sich auf die vorherigen PICK-Proben.
- `openPicker` in `static/js/v2/docs-folder-picker.js` leert den Baum vor dem
  Root-Request. Jeder spaetere Erfolg fuegt aber bedingungslos eine Root-Zeile
  hinzu und ruft showModal auf. Mehrere Klicks vor Abschluss sind ungesperrt;
  Schliessen entwertet ausstehende Anfragen nicht.
- PICK-03: zwei ausstehende Root-Anfragen, Antworten in umgekehrter Reihenfolge,
  ergeben zwei Root-Zeilen. PICK-04: zweite Antwort nach Schliessen fordert
  erneut showModal an. Kein echter Browser-/Fokusnachweis fuer diesen Ablauf.
- Empfehlung: genau eine aktive Oeffnungsabsicht verwalten, Ladezustand zeigen,
  Mehrfachausloesung abfangen und Antworten nach Abbruch/Neustart ignorieren.
  Requests bei Bedarf abbrechen; allein Abort ohne Zustandspruefung reicht nicht.
- Abnahme: langsame Root-Antworten, Mehrfachklick, Schliessen und Wiederaufnahme
  erzeugen genau eine aktuelle Ansicht; Abbrechen bleibt wirksam.
- PICK-01/02 als Positivkontrollen: zwei befuellte Zweige bleiben unabhaengig;
  alte Unterordnerantwort schreibt nur in bereits entfernten Container und
  ueberschreibt die neue Ansicht nicht. A-129 zur Reihenfolge bleibt bestehen.
- Beleg: [Asynchrone Controllerproben](PICKER_ASYNC_CHECKS.json), reproduzierbar
  mit `node docs/initiatives/app-audit/check_picker_async.cjs`. Minimaler DOM-Ersatz,
  keine echte Netzverbindung, keine Layout-/Dialogsemantik- oder Performanceaussage.

## A-131 – Ordnersuche begrenzt globale Treffer vor dem Filtern des Zielbaums

- **Isoliert im Originalservice reproduziert, P2, M, Risiko S.**
- `DriveStorageService.search_files` beendet die globale Drive-Suche nach
  mindestens 50 Roh-Treffern und filtert erst danach `hits_raw[:50]` auf den
  angefragten Ordnerbaum. Weitere API-Seiten mit passenden Dateien fehlen.
- Probe: 50 Treffer ausserhalb des Zielbaums auf Seite 1, passender Treffer
  auf Seite 2 ergeben leere Ordnersuche und nur einen API-Aufruf. Kontrolle
  mit 49 Treffern auf Seite 1 liest Seite 2 und findet die passende Datei.
- Empfehlung: Begrenzung auf passende Ergebnisse anwenden und Fortsetzung
  explizit anbieten. Bei notwendigem Suchbudget unvollstaendige Suche anzeigen;
  nicht als vollstaendiges Ergebnis ohne Treffer ausgeben. API-Aufwand begrenzen
  und messen, statt ungeprueft alle Drive-Dateien unbegrenzt zu laden.
- Abnahme: passende Datei bleibt auch hinter 50 sachfremden Treffern auffindbar;
  Trefferlimit, Fortsetzung und unvollstaendige Suche sind nachvollziehbar.
- Beleg: [Suchproben](DOCS_SEARCH_CHECKS.json), letzte zwei Gruppen. Synthetische
  API-Seiten, keine Aussage ueber aktuellen Vereinsbestand oder reale Latenzen.

## A-132 – Dokumentensuche vermischt Fehler, ungueltige Eingabe und Leerzustaende

- **Ueber Originalroutes und gerenderte Templates reproduziert, P2, S–M, Risiko S.**
- Root- und Ordnersuche zeigen bei behandeltem DriveError zwar eine Warnung,
  gleichzeitig aber auch Keine Treffer. Das Ergebnis wurde nicht ermittelt.
- Direkter Aufruf `/docs/?q=A` fuehrt weder Suche noch Ordnerabfrage aus, zeigt
  dennoch Keine Ordner unter der Drive-Wurzel. Das HTML-minlength schuetzt
  normale Formulareingaben, nicht direkte URLs; kein Browser-Submit behauptet.
- Empfehlung: explizite Zustaende fuer Ausgangsansicht, zu kurzen Suchbegriff,
  laufende/fehlgeschlagene Suche und erfolgreich leeres Ergebnis. Mindestlaenge
  auch serverseitig verstaendlich rueckmelden; nach Fehler erneute Suche anbieten.
- Abnahme: Fehler zeigt keine scheinbar gesicherte Leermeldung; zu kurzer Begriff
  behauptet keinen leeren Bestand. Suchbegriff bleibt fuer Korrektur erhalten.
- Positiv: echte leere Suche zeigt Keine Treffer ohne Warnung; Suchbegriff Audit
  bleibt bei Fehler in beiden Suchformularen erhalten. Kein pauschales Schweigen
  bei Fehlern; Abgrenzung zu A-095 fuer oeffentliche Suchseiten.
- Beleg: [Suchproben](DOCS_SEARCH_CHECKS.json), erste fuenf Gruppen. HTML-Ausgabe
  geprueft, keine neue Browser-/Screenreader-Abnahme.

## A-133 – Dokumentensuche fragt identische Ordnerpfade fuer jeden Treffer erneut ab

- **Isoliert gezaehlte externe Aufrufe, P2, M, Risiko S.**
- search_files ruft get_folder_breadcrumb pro Treffer auf. Die Methode laedt
  jede Pfadstufe erneut, auch bei identischem Elternordner. Synthetischer Fall:
  50 Dateien im gleichen zweistufigen Pfad verursachen eine Suchabfrage plus
  100 Metadatenabfragen. Keine gemessene Produktionsladezeit.
- Empfehlung: Ordner-Metadaten bzw. vollstaendige Pfade innerhalb einer Suche
  wiederverwenden; gleiche Elternordner zusammenfassen. Ein request-lokaler
  Cache vermeidet langfristig veraltete Pfade und spart redundante Aufrufe.
  Weiterhin Zugangsfehler und externe Aenderungen kontrolliert behandeln.
- Abnahme: 50 Treffer mit identischem zweistufigem Elternpfad brauchen im
  erfolgreichen Referenzfall nur zwei Pfadabfragen. Gemischte Pfade bleiben
  korrekt; reale Latenz und Quota anschliessend separat messen.
- Beleg: [Suchgrenzen](DOCS_SEARCH_BOUNDARY_CHECKS.json),
  fifty_hits_same_two_level_parent. Originalsuch-/Pfadmethoden, nur Transport
  ersetzt. Keine neuen Bibliotheken oder App-Aenderungen im Audit.

## A-134 – Dateiaktionen zeigen im Dialog nicht eindeutig die betroffene Datei

- **Bestaetigte Template-/Controller-Beobachtung, P2, S, Risiko S.**
- B-55 bis B-58 bestaetigen den fehlenden Quelldateinamen bei Move/Archive/
  Restore auch im Listen-Browser (regulaeres Mitglied, 1280x720). Abbrechen/
  Escape und der Wechsel von Alpha zu Beta funktionieren in den geprueften
  Faellen; richtige Beta-Formularziele. Kein Submit. Beleg:
  [Aktionsdialoge](browser/docs-actions-followup.json).
- `_drive_quick_modals.html` nennt bei Move/Archive/Restore nur die Aktion und
  ggf. das Ziel, keinen Quelldateinamen. docs-quick-actions.js uebertraegt fuer
  diese Dialoge nur die Dokument-ID in die Formular-URL. Liste und Detailansicht
  verwenden dieselbe Implementierung. Nach Oeffnen fehlt eine direkte Kontrolle,
  welche Datei gerade bearbeitet wird; keine falsche Dateiaenderung nachgewiesen.
- Rename zeigt den bisherigen Namensstamm im Eingabefeld, aber keine dauerhafte
  Ausgangsbezeichnung mit Endung, sobald der Name bearbeitet wird.
- Empfehlung: in allen vier Dialogen Dateiname und bei Bedarf Quellordner als
  festen Kontext anzeigen; Zielordner/Archivziel konkret benennen. Technische
  Begriffe wie konfigurierter Archiv-Ordner im Shared Drive im Nutzertext ersetzen.
- Abnahme: Aktion, betroffene Datei und Ziel sind vor Bestaetigung erkennbar,
  auch bei aehnlichen Dateinamen und nach Bearbeiten des Eingabefelds.
- Positiv: gemeinsame Dialogvorlage und gemeinsamer Controller fuer Liste/Detail;
  diese bestehende Wiederverwendung erhalten. Browser-Nachtrag oben deckt
  gezielte Listenfaelle ab, keine vollstaendige Fokus-/Geraete-/Submitabnahme.
  Siehe DOCS_REVIEW.md, Aktionsvergleich.

## A-135 – Wiederherstellen erlaubt ein Ziel innerhalb des Archivs

- **Isoliert im Originalservice reproduziert, P2, S–M, Risiko S.**
- restore_document prueft gueltigen Drive-Ordner und archivierte Quelldatei,
  aber nicht, ob das Ziel ausserhalb des Archivbaums liegt. Das widerspricht
  dem Text des Wiederherstellen-Dialogs. Ziel Archiv selbst fuehrt ohne Move
  zu DOCUMENT_RESTORED; ein Archiv-Unterordner wird tatsaechlich zum Ziel und
  ebenfalls als Wiederherstellung protokolliert. Datei bleibt in beiden Faellen
  nach der originalen Archivpruefung archiviert.
- Empfehlung: Archiv und dessen Nachfahren serverseitig als Restore-Ziel
  ausschliessen; im Picker nachvollziehbar kennzeichnen. Erfolg/Protokolleintrag
  erst nach tatsaechlichem Wechsel aus dem Archivzustand erzeugen.
- Abnahme: Archiv und verschachtelte Archivziele werden ohne Move/Restore-Log
  abgewiesen; Ziel ausserhalb funktioniert weiterhin mit genau einem Eintrag.
- Beleg: [Lifecycle-Proben](DOCS_LIFECYCLE_CHECKS.json), restore_into_archive,
  restore_into_archive-child und restore_success. Kein echter Drive-Schreibzugriff.

## A-136 – Verschieben ins bereits erreichte Drive-Ziel laesst veralteten App-Ordner stehen

- **Isoliert im Originalservice reproduziert, P2, S–M, Risiko S.**
- Teilfehler-Nachtrag: Nach simuliertem externen Erfolg und scheiterndem
  DB-Commit behaelt auch der erneute Move/Archive/Restore-Versuch nach Rollback
  den alten DB-Ordner. Archive/Restore erzeugen dabei ein Aktionslog, ohne die
  Abweichung zu korrigieren. DOCS_PARTIAL_FAILURE_CHECKS.json bestaetigt den
  Zusammenhang zwischen diesem No-op-Pfad und fehlender Wiederaufnahme.
- move_document beendet den Ablauf sofort, wenn der extern gelesene Elternordner
  bereits dem Ziel entspricht. Weicht document.drive_parent_id davon ab, wird
  dieser lokale Cache nicht korrigiert. Probe: App source, Drive target, Auftrag
  target ergibt weiterhin App source nach frischem DB-Lesen, ohne externen Move.
- Empfehlung: auch beim entfallenden externen Move den App-Zustand mit den
  bereits gelesenen Metadaten abgleichen. Synchronisierung von einem wirklichen
  Verschieben im Aktivitaetsprotokoll unterscheiden; keinen falschen Move loggen.
- Abnahme: bereits erreichtes Ziel plus veraltete DB-Zuordnung korrigiert die
  App ohne weiteren Drive-Move; bereits konsistenter Zustand bleibt unveraendert.
- Beleg: [Lifecycle-Proben](DOCS_LIFECYCLE_CHECKS.json),
  same_remote_target_stale_db und same_parent_noop. Andere Auto-Sync-Pfade
  koennen spaeter korrigieren; kein dauerhafter Verlust oder falscher Dateitransfer
  behauptet. Keine Produktionsdaten betroffen.

## A-137 – Abgefangener Audit-Schreibfehler laesst die Datenbanksitzung unbrauchbar

- **Isoliert mit echtem ORM-Flush reproduziert, P2, M, Risiko M.**
- Aktivierungsnachtrag: Nach Passwort-/Token-Commit scheitert bei Auditfehler
  die anschliessende Anmeldung mit PendingRollbackError. Neues Passwort und
  verbrauchter Link bleiben gespeichert; keine Login-Session, kein Audit.
  Wiederholung wird als verbrauchter Link zur Anmeldung umgeleitet. Beleg:
  ACTIVATION_BOUNDARY_CHECKS.json. Abschluss-/Fehlermeldung muss diesen
  teilweise erfolgreichen Zustand korrekt vermitteln; keine Kontosperre behauptet.
- Mitgliederanlage am 2026-09-28: Fehler am ersten oder zweiten Audit-Insert
  endet ebenfalls mit PendingRollbackError. Konto bleibt gespeichert; beim
  ersten fehlen Token und beide Logs, beim zweiten bleibt Token/erstes Log
  erhalten. ONBOARDING_FAILURE_CHECKS.json. A-139 behandelt separat die
  Versandreihenfolge gegenueber dauerhafter Speicherung des Aktivierungslinks.
- Querschnitts-Nachtrag: Originalrouten fuer Login ohne next, RSVP und Event-
  Loeschen werfen beim simulierten Auditfehler PendingRollbackError. Login mit
  lokalem next und Kalenderaktivierung liefern dagegen 302/201 ohne Audit.
  Beleg: [Routenreichweite](AUDIT_FAILURE_REVIEW.md). Auswirkungen unterscheiden
  sich nach Folgezugriffen; kein pauschaler Ausfall aller Aufrufer.
- SecurityService.log_audit_event faengt Schreibfehler, setzt die fehlgeschlagene
  SQLAlchemy-Transaktion aber nicht zurueck. Probe: normaler Move ist bereits
  committed; injizierter Fehler beim Audit-Insert wird geloggt und verschluckt.
  Eine nachfolgende Dokumentabfrage wirft PendingRollbackError. Nach explizitem
  Rollback bleibt der Move gespeichert, der Aktivitaetseintrag fehlt.
- Empfehlung: Audit-Fehler mit klarer Transaktionsgrenze behandeln; Session
  wieder verwendbar machen und fehlgeschlagene Protokollierung nachvollziehbar
  erfassen. Kein blindes Rollback fremder, noch offener Fachtransaktionen: fuer
  gemeinsame Helfer Savepoint/separate Session oder verbindliche Aufrufgrenze
  pruefen. Aktions-/Audit-Wiederaufnahme zusammen definieren.
- Abnahme: injizierter Audit-Insertfehler laesst folgende Abfragen im selben
  Request zu; bereits gespeicherte Fachaenderung bleibt erhalten. Fehlendes
  Protokoll wird nicht als vollstaendig geschrieben behauptet.
- Beleg: [Teilfehlerproben](DOCS_PARTIAL_FAILURE_CHECKS.json), move/audit_insert.
  Keine pauschale Aussage zu allen Audit-Aufrufern oder produktivem HTTP-Status;
  globale Nutzung des Helfers und PostgreSQL-Verhalten separat gegenpruefen.
- Transaktionsnachtrag: 64 direkte Aufrufstellen inventarisiert; drei
  Originalhelfer-Proben zeigen, dass sein Commit auch andere offene Aenderungen
  speichert. Ein spaeteres Rollback macht diese dann nicht rueckgaengig. Kein
  eigenstaendiger Produktfehler behauptet, sondern Grenze fuer die Korrektur:
  Audit-/Fachtransaktion ausdruecklich je Ablauf festlegen. Belege:
  AUDIT_TRANSACTION_CHECKS.json und AUDIT_FAILURE_REVIEW.md. Alle 64 Aufrufer
  bleiben damit nicht automatisch verhaltensgeprueft.

## A-138 – Wiederholung einer fehlgeschlagen wirkenden RSVP-Aktion kehrt Teilnahme um

- **Ueber Originalroute isoliert reproduziert, P2, M, Risiko S.**
- `/events/<id>/rsvp` invertiert teilnahme bei jedem POST. Nach erfolgreichem
  Commit, aber fehlgeschlagenem Audit, scheitert die Antwort an A-137. Ein
  erneuter identischer POST invertiert den bereits gespeicherten Zustand erneut.
- Probe: initial false, erster POST endet mit PendingRollbackError bei dauerhaft
  true; Wiederholung ohne Fehler endet mit 302 und dauerhaft false.
- Empfehlung: expliziten gewuenschten Teilnahmezustand senden und wiederholtes
  Setzen desselben Zustands ohne Umkehr behandeln. Mehrfachausloesung im UI
  abfangen; serverseitigen Vertrag nicht allein von Button-Sperren abhaengig machen.
- Abnahme: identische Wiederholung nach verlorener/fehlerhafter Antwort belaesst
  gewuenschte Teilnahme; bewusstes anschliessendes Absagen funktioniert weiterhin.
- Beleg: [Audit-Routenproben](AUDIT_FAILURE_ROUTE_CHECKS.json),
  rsvp_failure_then_retry. Kein Browser-Retry oder echtes Netzwerkproblem
  simuliert; nachgewiesen sind zwei Original-POSTs mit injiziertem Auditfehler.

## A-139 – Onboarding-Mail wird vor dauerhafter Speicherung des Aktivierungslinks beauftragt

- **Ueber Originalroute mit abgefangenem Versand reproduziert, P2, M, Risiko M.**
- Wiederaufnahme-Nachtrag: erneuter identischer Erstellen-POST nach erstem
  Auditfehler erzeugt IntegrityError, keine Mail und keinen Token. Das bestehende
  Konto wird dadurch nicht repariert. Nach normalem Mailfehler bleibt der Token
  zwar vorhanden, aber derselbe POST sendet ebenfalls nicht erneut. Gemeinsame
  Duplikat-Fehlerbehandlung unter A-084, Wiederaufnahmevertrag hier.
- create_member speichert zuerst das Mitglied, legt den Aktivierungstoken in
  der laufenden Transaktion an und ruft MailService.send vor deren Commit auf.
  Erst der erste Audit-Aufruf committet den Token mit. Schlaegt dieser fehl,
  rollt die Tokenanlage zurueck, waehrend das Konto bestehen bleibt.
- Probe first_audit_failure: Mail-Mock meldet Erfolg, danach Audit-Fehler;
  frische DB-Abfrage findet Mitglied, aber keinen Token. Eine tatsaechlich
  zugestellte Mail koennte deshalb einen nicht nutzbaren Link enthalten.
  Keine reale Mail gesendet oder Zustellwahrscheinlichkeit gemessen.
- Empfehlung: Aktivierungszustand vor Versand dauerhaft speichern; Versand
  getrennt verfolgen und fuer bestehende Konten kontrolliert wiederholen.
  Audit-Fehler duerfen gueltige, bereits versandte Links nicht zuruecknehmen.
- Abnahme: simulierte Fehler vor/nach Versand und beiden Audit-Aufrufen lassen
  Konto, Aktivierungslink und sichtbaren Versandstatus nachvollziehbar; erneutes
  Senden erzeugt keine doppelte Mitgliederanlage.
- Positiv: normales Erfolgsergebnis und strukturierter Versandfehler enden mit
  302, gespeichertem Token und zwei Logs; Versandfehler zeigt warning statt success.
- Beleg: [Onboarding-Fehlerproben](ONBOARDING_FAILURE_CHECKS.json), fuenf Gruppen.
  Unerwartete Versandexception nur als injizierte Vertragsgrenze geprueft.

## A-140 – Aktivierungsweg meldet bestehendes 2FA-Konto ohne zweiten Faktor an

- **Bedingter Originalrouten-Nachweis, P1, M, Risiko M.**
- **Erreichbarkeit am 2026-10-10 bestaetigt:** Originale Admin-Anlage mit
  abgefangenem Versand, Login mit Anfangspasswort, originales MFA-Setup mit
  lokalem TOTP, danach Aktivierung mit noch unbenutztem Link. Der normale Login
  fordert MFA; Aktivierung erzeugt volle Session und Dashboard 200 ohne Faktor.
  Keine direkt gesetzte MFA-Zeile in dieser Folgeprobe. Beleg:
  [Onboarding-/MFA-Ablauf](ONBOARDING_MFA_SEQUENCE_CHECKS.json).
- auth.activate ruft nach Passwort-/Token-Commit direkt login_user auf, ohne
  den MFA-Zustand zu pruefen. Voraussetzung der Probe: gueltiger unbenutzter
  Onboarding-Token und is_totp_enabled=True fuer dasselbe aktive Mitglied.
- Normaler Login setzt im Kontrollfall nur pending_2fa_user_id. Aktivierung
  erzeugt dagegen vollstaendige Session ohne MFA-Zwischenschritt; Dashboard
  liefert 200. Kein zweiter Faktor angegeben oder verifiziert.
- Empfehlung: auch nach Aktivierung vorhandene MFA-Regeln anwenden; unbenutzte
  Onboarding-Links beim Abschluss/Wechsel relevanter Zugangszustaende gezielt
  entwerten. Anmeldelogik fuer alternative Zugangswege zentral vereinheitlichen.
- Abnahme: Konto mit aktivem 2FA erhaelt ueber Aktivierung vor Faktorpruefung
  keinen vollstaendigen Zugriff; normale Erstaktivierung bleibt nutzbar.
- Beleg: [Aktivierungs-Sessions](ACTIVATION_SESSION_CHECKS.json),
  mfa_enabled_valid_onboarding. Kombination direkt in isolierter Fixture gesetzt;
  regulaere Erreichbarkeit inzwischen durch obige Folgeprobe nachgewiesen.
  Produktionsbestand und tatsaechlich vorhandene alte Links weiterhin unbekannt.
  Kein pauschaler Bypass ohne gueltigen Token behauptet.

## A-141 – Alte Zugangslinks bleiben nach Passwortwechsel und 2FA-Neueinrichtung wirksam

- **In vier Originalrouten-Folgen bestaetigt, P1, M, Risiko M.**
- **MFA-Erweiterung:** Zwei weitere Originalablauffolgen belegen dieselbe
  Widerrufsluecke fuer MFA_RESET: vor einem Mail-/Admin-Reset ausgestellte Links
  deaktivieren auch die anschliessend neu eingerichtete 2FA und loeschen deren
  neue Backup-Codes. Kontrolllogin verlangt davor MFA; danach genuegt das
  bekannte Passwort. Kein Login allein durch den MFA-Link behauptet.
  Bereits verwendeter Link bleibt nach dritter Einrichtung korrekt gesperrt.
  Beleg: [MFA-Link-Lebenszyklus](MFA_RESET_LINK_LIFECYCLE_CHECKS.json).
- **Zwei Folgeproben bestaetigt:** zweimalige normale Passwort-vergessen-Anfrage
  erzeugt zwei nutzbare Links. Nutzung des neueren entwertet den aelteren nicht.
  Auch nach Admin-Login, originaler Step-Up-Bestaetigung und Admin-Passwortreset
  ueberschreibt ein zuvor normal angeforderter Reset-Link das neue Passwort.
  Nur Versand abgefangen; keine direkte Tokenerzeugung in diesen Folgeproben.
  Beleg: [Reset-Anfragefolgen](RESET_REQUEST_SEQUENCE_CHECKS.json).
- Ein vor der Passwortaenderung ausgestellter, unbenutzter und nicht abgelaufener
  ONBOARDING- oder PASSWORD_RESET-Token kann danach erneut ein Passwort setzen.
  Nachgewiesen nach regulaerem Passwortwechsel und nach Reset mit einem anderen
  Token. Besitz des alten geheimen Links ist Voraussetzung; kein tokenloser Zugriff.
- auth.change_password entwertet keinen Token; auth.reset_password verbraucht
  ausschliesslich den benutzten Token. _resolve_auth_token prueft Zweck, Verwendung
  und Ablauf, aber keinen Widerruf aufgrund zwischenzeitlicher Passwortaenderung.
- Auswirkung: ein Passwortwechsel allein beseitigt die Zugriffsmöglichkeit ueber
  einen zuvor abgeflossenen Link nicht. Aktivierungslink erzeugt zusaetzlich eine
  angemeldete Session; Reset-Link leitet korrekt zur Anmeldung. MFA-Auswirkung
  separat A-140; bestehende Sessions separat A-077, keine Doppelzaehlung dort.
- Positiv: nach Verwendung des jeweiligen alten Links wird dessen erneute Nutzung
  in allen vier Gruppen abgelehnt; das zuletzt gesetzte Passwort bleibt erhalten.
- Empfehlung: bei erfolgreichem Passwortwechsel/Reset alle noch offenen
  Passwort-Reset- und ueberholten Aktivierungslinks desselben Kontos atomar
  entwerten. Zentralen Vertrag fuer Ausgabe, Verbrauch und Widerruf festlegen.
  Den administrativen Passwortreset in denselben Widerrufsvertrag aufnehmen.
  MFA-Reset und erneute Einrichtung muessen alte MFA-Reset-Links entwerten;
  Geraetevertrauen bleibt der separate Widerrufsgegenstand unter A-082.
  Andere Zwecke wie E-Mail-Verifikation gesondert bewerten, nicht blind loeschen.
- Abnahme: zuvor ausgestellte Links aendern nach Passwortwechsel/Reset weder
  Passwort noch Session; ein danach neu angeforderter Reset bleibt nutzbar.
  Normale Erstaktivierung und Schutz vor Wiederverwendung bleiben erhalten.
- Beleg: [Token-Lebenszyklusproben](CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json),
  vier Gruppen, Originalhelfer/-routen mit synthetischen Konten in SQLite.
  Ausgabe ueber den Helfer, kein Mailversand oder vollstaendiger Versandablauf.
  Parallelitaet, Postgres, MFA und produktiver Bestand in diesen Proben offen.
- Referenz: [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html),
  Abschnitt Account Recovery After Suspected Compromise: offene Recovery-Links
  nach erfolgreicher Wiederherstellung entwerten. Die Anwendung auf jeden
  erfolgreichen Passwortwechsel ist unsere projektspezifische Empfehlung.

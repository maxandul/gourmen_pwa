# Browser-Pruefprotokoll – Teilumfang

Durchgefuehrt 2026-09-06/07, im Codex-In-App-Browser mit explizitem Viewport.
App-Baseline unveraendert `bf4d84a`. Server `serve_ui_fixture.py` ausschliesslich
auf 127.0.0.1:5087; vier synthetische Mitglieder, vier Events, Beispieljahr/Konten,
ein Merch-Artikel. Drive-Auflistung/Suche liefern leere Testdaten.
Keine Produktionsdaten, kein echter Upload oder Buchungsabschluss.

Der Server nutzt die bestehenden Original-Templates, CSS und JS. Testing
schaltet CSRF und Rate-Limit aus; Backend-Netzwerk ist gesperrt. Browser-
Unterstuetzung von Kamera, Push, externen APIs und Drittassets wird damit nicht
als produktiv verifiziert betrachtet. Screenshots sind Viewport-Simulation,
keine echten iPhone-/Android-/Tablet-Tests.

## Reproduzierte Interaktionen

| ID | Schritte | Beobachtung | Ergebnis |
|---|---|---|---|
| B-01 | Event `/events/3` ohne Query → BillBro → Browser-Zurueck | URL ohne tab; BillBro bleibt ausgewaehlt und sichtbar | A-003 bestaetigt |
| B-02 | Event ohne Query → BillBro → Weiter | Pfeilziel bleibt `tab=info`; Folgeevent zeigt Infos | A-015 bestaetigt |
| B-03 | `/accounting/?year=1&tab=uebersicht` → Journal → Geschaeftsjahr → Filtern | Rueckkehr zu Uebersicht; Reset-Link ebenfalls alter Tab | A-015 bestaetigt |
| B-04 | Buchhaltung und Dokumente als Admin anzeigen | kein aktiver Hauptbereich | A-002 bestaetigt |
| B-05 | Drive → Suchen & Hochladen → Hochladen → Escape | initialer Fokus Schliessen; Dialog schliesst; Fokus zurueck auf Hochladen | positiv fuer diesen Dialog |
| B-06 | Events → Statistiken → Teilnahmequote Vollbild → Tab | Fokus bleibt auf Trigger, dann naechster Chart-Button ausserhalb des Dialogs | A-016 bestaetigt |
| B-07 | Merch → Audit-Shirt aufklappen | Farbe/Groesse/Anzahl ohne verknuepfte Namen im DOM/Accessibility-Baum | A-017 bestaetigt |
| B-08 | Event erstellen anzeigen | Event-Typ/Sichtbarkeit unbenannt; Organisator korrekt benannt | A-017 bestaetigt |
| B-09 | Event-Detail an 8 Breiten | bei 1024/1280 Inhalt rechts ausserhalb Viewport und abgeschnitten | A-014 bestaetigt |
| B-10 | Buchhaltung an 5 Breiten | gleicher Shell-Fehler bei 1024/1280 | A-014 Gegenpruefung |
| B-11 | Public Ueber-uns bei 1024 | Main x=0..1009, Dokument 1009 breit; kein gemessener horizontaler Ueberlauf | Public-Shell getrennt |
| B-12 | ausgeloggter Login bei 1024 | keine Sidebar vorhanden, Main trotzdem x=200..1224 | A-014 betrifft auch Auth-Shell |
| B-13 | Buchhaltung 390px, Theme umschalten | Dark-Theme sichtbar, DOM-Inhalte unveraendert | Darstellung gesichtet, Kontraste nicht gemessen |

## Gespeicherte Belege

- `browser/event-viewports.json`: 360, 390, 768, 820, 1023, 1024, 1280, 1440 px.
- `browser/accounting-viewports.json`: 390, 820, 1024, 1280, 1440 px.
- `browser/event-info-390.jpg`, `event-info-820.jpg`, `event-info-1024.jpg`, `event-info-1440.jpg`.
- `browser/accounting-390.jpg`, `accounting-820.jpg`, `accounting-1024.jpg`, `accounting-dark-390.jpg`.
- `browser/docs-upload-390.jpg`, `events-chart-modal-390.jpg`, `merch-form-390.jpg`, `login-1024.jpg`.

Viewport-Zahlen enthalten je nach Inhalt 15px Scrollbar-Differenz zwischen
innerWidth und clientWidth. Die zugrunde liegende Geometrie ist deshalb
explizit in JSON festgehalten. Keine Ladezeitmessungen aus diesen Aufrufen ableiten.
Screenshot-Dateinamen nennen die angeforderte CSS-Viewport-Breite. Die gespeicherten
JPEGs zeigen den vom Browser gelieferten Inhaltsausschnitt; dessen Pixelmasse
koennen durch Scrollbars und Ausschnitt abweichen. Fuer Breitenvergleiche gelten
die DOM-Messwerte in den JSON-Dateien, nicht die Bildabmessungen.

## Fortsetzung

### Komponenten-Gegenpruefung vom 2026-09-20

Gleiche lokale Fixture, synthetischer Admin; Original-App unveraendert.
Keine Buchung gespeichert, keine Datei gewaehlt oder hochgeladen.
Belege: [component-followup.json](browser/component-followup.json).
Die DOM-Messwerte wurden aus den Browser-Toolausgaben uebertragen.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-14 | Buchung erfassen, Schrittanzeige in Hell und Dunkel | Computed font-size 16px, `--font-size-sm` leer, vorhandenes `--text-sm` 0.875rem (=14px bei Root 16px). A-099 im aktiven Formular bestaetigt. |
| B-15 | Beleg einreichen bei 320px | Gleiche fehlende Variable, Schrittanzeige 16px. Zweiter Consumer von A-099 bestaetigt. |
| B-16 | Buchung: Weiter mit leeren Betrag-/Beschreibungsfeldern | Bleibt Schritt 1; Fokus auf Betrag, native Validierung aktiv. Positiv fuer diesen Fehlerpfad. |
| B-17 | Betrag 100 und synthetische Beschreibung → Weiter → Zurueck | Schritt 2 zeigt Zuordnung, Zurueck erhaelt beide Eingaben. Fokus bleibt beim Vorwaertswechsel auf Weiter; Screenreader-Ansage nicht geprueft. |
| B-18 | Manueller Hell-/Dunkel-Schalter | Dunkles DOM, Schalterzustand und aria-checked stimmen ueberein. Anschliessend wieder auf Hell gestellt. Systemwechsel-Bug A-098 damit weder widerlegt noch im Browser bestaetigt. |
| B-19 | Buchung Schritt 2 dunkel an 320/390/640/768/820/1024px | Bis 820px keine sichtbaren input/select/button-Rechtecke ausserhalb der Dokumentbreite. Bei 1024px Main x=200 bis 1224, vier Controls ragen rechts hinaus. A-014 erweitert um Buchungsformular. |
| B-20 | Formular-Cards und aktive Stylesheet-Regel lesen | Drei einfache Cards ohne eigene Rolle/Tabindex; zwei enthalten Eingaben. Globale `.card:active`-Transform-Regel geladen. Effekt waehrend gedruecktem Pointer nicht gemessen, daher weiter Beobachtung. |

Bei 320px wurde Schritt 2 zusaetzlich als Screenshot gesichtet: Titel und
Schrittnavigation umbrechen, Felder stehen untereinander. Screenshot nur in der
Sitzung angesehen, keine neue Bilddatei gespeichert. Lange Select-Optionen sind
im geschlossenen Feld abgeschnitten; vollstaendige Lesbarkeit bei Auswahl offen.

Die verfuegbare Browsersteuerung bietet Viewport-Aenderung, aber keine
Systemfarbschema-Emulation oder gehaltenen Pointer fuer diese Gegenpruefung.
Keine Betriebssystemeinstellung geaendert und keine kuenstliche DOM-Manipulation
als echter Systemwechsel ausgegeben. A-098 behaelt seinen isolierten JS-Beleg.
Die sieben neuen Browser-Protokolle sind keine zusaetzlichen Backend-Workflowtests.

### Weitere Formular-/Dialogzustaende vom 2026-09-20

Belege: [dialog-followup.json](browser/dialog-followup.json). Original-App,
synthetische Rollen, keine Datei gewaehlt, keine Buchung oder Kalenderaktion.

| ID | Schritte | Beobachtung / Einordnung |
|---|---|---|
| B-21 | Regulaeres Mitglied, Beleg einreichen bei 390px, Weiter ohne Datei | Schritt 1 bleibt sichtbar, Fokus am File-Input. Native sichtbare Meldung «Wähle eine Datei aus.»; kein zusaetzlicher Inline-Fehler. Positiv fuer das Verhindern des leeren Weitergehens. Screenreader nicht getestet. |
| B-22 | Ausgeloggt, Ueber-uns bei 390px, Navigation oeffnen → Escape | Initialer Fokus Schliessen, echter modaler Dialog; Escape schliesst und gibt Fokus an Menue-Trigger zurueck, aria-expanded=false. |
| B-23 | Menue erneut oeffnen → 1024px → Hitlist klicken | Dialog unsichtbar, aber weiterhin open und modal; Link navigiert nicht. Nach Escape funktioniert derselbe Link. Neuer Befund A-100. |
| B-24 | Admin, Buchhaltung bei 820px, Statistik → Saldo-Vollbild → Tab → Escape | Fokus bleibt ausserhalb und geht zum Jahresvergleich-Trigger; Escape schliesst. A-016 fuer Buchhaltung bestaetigt. |
| B-25 | Admin, GGL → Spielverlauf | Verstaendlicher Leerzustand sichtbar. Kein Diagramm vorhanden; GGL-Dialogpruefung braucht eine Fixture mit Verlaufsdaten und bleibt offen. |

Die Bildschirmbreite wurde simuliert. Keine echte Tablet-Drehung, kein
browseruebergreifender Test. Native Kalenderdialoge und verschachtelte Drive-
Dialoge sind trotz Quellsichtung noch nicht durch diesen Durchlauf abgedeckt.

Diese Stichproben verifizieren konkrete gemeinsame Ursachen. Sie ersetzen nicht
die vollstaendige Seite × Rolle × Datenzustand × Viewport-Matrix. Unter anderem
Formularfehler, Tablet-Touch, 320px-Reflow, 200%-Zoom, reduzierte Bewegung und
echte Browser-/Geraeteunterschiede sind weiterhin offen.

### Registry-Restfaelle vom 2026-09-20

Lokale Fixture serve_registry_probes.py mit synthetischem Admin und erfundenen
Backup-Codes. Original-Templates und ausgelieferte JS-Dateien. Nur der
Status-Testknopf ist Fixture-Zusatz; er ruft ausschliesslich den originalen
Renderer auf. Kein Push-Versand, SW-Reset oder echte MFA-Aenderung.
Beleg: [registry-followup.json](browser/registry-followup.json).

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-26 | Status rendern, Technik-Details offen | hidden=true, inline display:block, berechnet none, Text gesetzt, keine Rechtecke. A-119. |
| B-27 | Flash-Seite neu laden, sofort Schliessen klicken | Meldung weiterhin im DOM, display:flex, opacity:1. A-120. |
| B-28 | QR-Code anzeigen | Sichtbarer Rahmen mit Platzhaltertext statt QR-Muster. Screenshot in Sitzung gesichtet, nicht gespeichert. A-121. |

Ein zuerst unterhalb der Navigation eingefuegter Testknopf veraenderte den
Status nicht. Erst nach Platzierung im Hauptinhalt wurde der Renderer
nachweislich ausgefuehrt; nur dieser erfolgreiche Aufruf ist B-26.
Die Sichtbarkeitspruefung ersetzt keine End-to-End-PWA-/Push-Pruefung.

### Archivnavigation und Warnhinweis vom 2026-09-20

Beleg: [archive-warning-followup.json](browser/archive-warning-followup.json).
Erweiterte lokale Fixture mit 27 vergangenen Events; originale Archivroute.
Warnzustand aus Original-Template mit synthetischem MFA-Viewmodel, kein
End-to-End-Test der Security-Route oder ihrer Zugangspruefungen.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-29 | Archiv mittlere Seite an 320/390/820/1440px, vor/zurueck, Suche und Weiter | Fehlende Paginierungsstile (A-122); Navigation und Erhalt des Suchtexts positiv. Suche ist zeitverzoegert, finale DOM-Aktualisierung abgewartet. |
| B-30 | Keine Backup-Codes bei als aktiv dargestellter MFA | Warntext lesbar, normaler Absatzstil statt besonderer Warnkennzeichnung. Konsistenzbeobachtung, kein belegter Sicherheitsdefekt. |

Temporare Browserbreite zurueckgesetzt, Tab geschlossen. Keine echten
Geraete, keine vollstaendige Filterkombinations-/Screenreader-Pruefung.

### Tastatur: Merch-Karten und breite Tabellen vom 2026-09-20

Beleg: [keyboard-followup.json](browser/keyboard-followup.json). Lokale
Fixture um einen zweiten synthetischen Artikel erweitert. Originale
Shop-/Archiv-/Mitglieder-Routen; keine Bestellung oder andere Mutation gesendet.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-31 | Regulaeres Mitglied, Shop, zwei Karten an 390px | Tab erreicht Toggle; Enter oeffnet, Space schliesst. aria-expanded stimmt mit Sichtbarkeit ueberein. Tab ueberspringt verborgene Felder und erreicht zweite Karte. Navy/M/2 und 60 CHF bleiben nach Schliessen/Oeffnen erhalten. Beide Toggle-Namen sind identisch und nennen den Artikel nicht. |
| B-32 | Regulaeres Mitglied, Archiv an 390px | Tab vom Suchfeld erreicht ersten Event-Link. Rechts verschiebt Scrollposition von 0 auf 40, weitere Tastendruecke bis zum Maximum 248. Erste Spalte bleibt bei x=45, rechter Fade am Ende entfernt. Positiver Nachweis fuer diesen Einstieg. |
| B-33 | Admin, Mitglieder an 390/820px | Tab ab Neues Mitglied erreicht Bearbeiten ganz rechts und scrollt stark nach rechts. Links reduziert scrollLeft um 40px (1749→1709 bzw. 1564→1524). Bedienbar, aber Einstieg mit Orientierungssprung. |

Die Variantenauswahl nutzte select/fill, keine vollstaendige Tastaturbestellung.
Tab-/Enter-/Space-/Pfeilproben waren echte Browser-Tastaturereignisse; Scroll
wurde nicht durch DOM-Manipulation erzwungen. Kein Screenreader-Nachweis und
keine browseruebergreifende Freigabe. GGL und Buchhaltung separat offen.
Empfehlung: Toggle-Namen artikelbezogen machen; fuer Tabellen einen bewusst
benannten Tastatureinstieg pruefen, ohne alle Zellen einzeln fokussierbar zu machen.
Keine neue Befundnummer allein fuer diese Orientierungsempfehlung.

### GGL und Budget: Tastatur-Gegenpruefung vom 2026-09-20

Beleg: [ggl-budget-keyboard.json](browser/ggl-budget-keyboard.json).
Bestehende lokale Testdaten, Original-Routen. Keine Buchung gespeichert und
keine Budgetwerte geaendert. Pfeiltaste im bearbeitbaren Budget bewusst erst
nach Tab auf den Speichern-Button, um keine Zahleneingabe zu veraendern.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-34 | Mitglied, GGL-Tabelle an 390px | Tab nach Spielverlauf erreicht Scroll-Huelle ohne explizites tabindex. Rechts scrollt 0→40→241 (Maximum). Rang/Name bleiben bei x=45/77 fixiert; rechter Fade am Ende entfernt. |
| B-35 | Admin, Budget an 390px | Tab nach Kontenplan erreicht erstes Betragsfeld und scrollt auf 139. Tab zum Speichern-Button, Links scrollt auf 99. Kontozelle position:static und x=-54; Konto scrollt aus dem sichtbaren Bereich. Beide Werte bleiben 0.00. |
| B-36 | Revisor, Budget an 320px | Keine Bearbeitungsfelder sichtbar. Tab nach Statistik erreicht benannte Scroll-Region; Rechts scrollt 0→40. Kontozelle wandert auf x=5. |

Kein nachgewiesener Tastaturblocker in diesen drei Faellen. Automatische
Fokussierbarkeit der Scroll-Huelle ist ein beobachtetes Browserverhalten,
keine zugesicherte Mehrbrowser-Eigenschaft. GGL-Probe hat vier Nullpunkte-
Zeilen, keine langen Namen oder breiten Rangzahlen; Spielverlauf nicht geprueft.

Budget verwendet nur data-table/accounting-budget-table, nicht den vorhandenen
Modifier data-table--sticky-first. UI.md nennt Budget dagegen als Beispiel
fuer diesen Modifier. A-012 wird damit konkretisiert. Empfehlung: festlegen,
ob die Kontospalte zur Orientierung sticky sein soll; dann Gruppenzeilen,
Zeilenumbrueche und Platzverbrauch an schmalen Breiten mitpruefen.
Keine neue Nummer fuer denselben Dokumentations-/Konsistenzkomplex.

Offen bleiben Tastaturproben fuer befuelltes Journal, Belege, offene Posten
und Import-Historie sowie echte Geraete, Screenreader und weitere Browser.

### Befuellte Buchhaltungstabellen vom 2026-09-20

Beleg: [accounting-tables-keyboard.json](browser/accounting-tables-keyboard.json).
Fixture ergaenzt um eine Ausgabe, Metadaten eines ungebuchten Belegs und eines
Imports sowie einen teilweise bezahlten Mitgliederbeitrag. Kein echter
Drive-Beleg, CSV-Upload, Loeschvorgang oder Begleichen. Original-Routen als Admin.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-37 | Journal, 390px | Tab nach Buchung erfassen erreicht Datumslink. Rechts scrollt 0→40; Datum bleibt bei x=45. |
| B-38 | Belege, 390px | Tab nach Beleg einreichen erreicht Beleglink. Rechts bis Maximum 477; erste Spalte fixiert, Randverlauf am Ende entfernt. Datei-Metadaten nicht geoeffnet. |
| B-39 | Import-Historie, 390px; Geometrievergleich 820px | 304px breite sticky Dateispalte bei 285px Scrollbreite verdeckt alle weiteren Spalten einschliesslich Aktion auch am rechten Ende. Screenshot gesichtet und Hit-Test bestaetigt, neuer Befund A-123. Bei 820px passt die erste Spalte in den 675px Bereich. |
| B-40 | Offene Posten, 390px | Tab nach Kontenplan erreicht Beglichen, scrollt auf 260. Links scrollt auf 220; erste Postenzelle ist static und liegt bei x=-175 ausserhalb. Keine Begleichung ausgeloest. |

Journal/Belege haben hier funktionierende fixierte Identifikationsspalten;
offene Posten verlieren beim Scrollen die sichtbare Postenbezeichnung.
Letzteres ist eine Orientierungsempfehlung, kein nachgewiesener Datenfehler.
Gezielte lokale Tastaturproben fuer diese vier befuellten Tabellen sind damit
abgeschlossen. Keine Freigabe der gesamten Buchhaltung oder aller Datenlaengen,
Rollen, Browser und Geraete. Formaktionen/Downloads waren nicht Teil dieses Tests.

### Verschachtelte Dokumentdialoge vom 2026-09-20

Beleg: [docs-dialog-followup.json](browser/docs-dialog-followup.json). Lokaler
Admin an 390px. Original-Controller; nur Ordnerlisten sind synthetisch, ein
Zweig erzeugt gezielt einen Serverfehler. Keine echte Datei gewaehlt.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-41 | Upload → Ordner waehlen | Beide native Dialoge modal; Fokus auf Schliessen im oberen Picker. |
| B-42 | Root/Unterlagen aufklappen, Protokolle mit Enter waehlen/uebernehmen | Zielname im Upload aktualisiert, Fokus zurueck auf Ordner waehlen. Fehlende Aufklapp-/Auswahlsemantik bestaetigt A-126. |
| B-43 | Picker Escape, Upload Escape, erneut oeffnen | Jeweils korrekte Fokus-Rueckkehr; Dateiname Audit-Entwurf und sichtbarer Zielname bleiben erhalten. |
| B-44 | Synthetischer Ladefehler im Unterordner | Verstaendliche sichtbare Meldung, ohne role/live-Region; Escape funktioniert. Ansage durch Screenreader nicht geprueft. |

Hidden-Ziel-ID wird mit dieser Browserprobe nicht als korrekt eingereicht
verifiziert; nur sichtbarer Zielname geprueft. Kein Upload-Submit, keine
Dateiauswahl, keine echte Drive-Mutation. Vollstaendiger Fokusumlauf und
Root-API-Fehlerpfad offen. Persistenter Entwurf nach Abbruch ist Beobachtung,
kein automatisch unerwuenschtes Verhalten.

### Upload-Fehler und Root-Ausfall vom 2026-09-20

Beleg: [docs-errors-followup.json](browser/docs-errors-followup.json).
B-45: Original-Upload ohne Datei, aber mit synthetischem Titel, fuehrt zum
Redirect mit Fehlermeldung. Nach erneutem Oeffnen ist der Titel leer (A-127).
B-46: Fixture liefert fuer Root-API gezielt 503; originaler Picker bleibt
geschlossen, Konsolenfehler und keine sichtbare Rueckmeldung (A-128).
Gesamter sichtbarer Dialogtext geprueft; Titel bleibt in diesem zweiten Fall
erhalten. Keine Datei gewaehlt, keine externe Aktion. Browserbreite zurueckgesetzt.

### Picker-Wiederaufnahme und Hierarchie vom 2026-09-20

Beleg: [docs-tree-retry.json](browser/docs-tree-retry.json). Lokaler Admin,
390x850, synthetische Ordner und einmaliger Root-503; Originalcontroller.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-47 | Erneuter Klick nach einmaligem Root-Fehler | Picker oeffnet beim zweiten Versuch; Titel Audit-Wiederaufnahme bleibt erhalten. Positive Ergaenzung zu A-128. |
| B-48 | Ersten von zwei Nachbarordnern aufklappen | Dessen Kind erscheint hinter dem zweiten Nachbarordner, mit tieferer Einrueckung. Neuer Hierarchiebefund A-129. |
| B-49 | Kind auswaehlen, Elternzweig zuklappen, Uebernehmen | Auswahl unsichtbar, Uebernehmen bleibt aktiv. Danach korrekter sichtbarer Zielname Protokolle, Titel erhalten und Fokus auf Ordner waehlen. |

Kein Upload oder Nachweis der eingereichten Ziel-ID. Keine reale Drive-Aktion.
Mehrere gleichzeitig expandierte Nachbarzweige, tiefe/grosse Baeume und
weitere Rollen/Browser bleiben offen. Viewport zurueckgesetzt, Tab geschlossen,
lokaler Server beendet.

### Unabhaengige Zweige, Fehlerwiederholung und Blattordner vom 2026-09-20

Beleg: [docs-branches-followup.json](browser/docs-branches-followup.json).
Originalcontroller, lokale Fixture als Admin, Browsergroesse 938x856.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-50 | Zwei Zweige offen, einer mit synthetischem Fehler | Erfolgreicher Zweig bleibt erhalten. Zuklappen dieses Zweigs entfernt dessen Kind, laesst aber den Fehler im Nachbarzweig stehen. |
| B-51 | Fehlerzweig zu- und erneut aufklappen | Erster Klick entfernt Fehlermeldung, zweiter fordert erneut an (zweiter 500 im lokalen Serverlog); Nachbarzweig bleibt offen. Keine direkte Wiederholen-Aktion. |
| B-52 | Ordner ohne Kinder aufklappen | Erfolgreicher 200; sichtbares Minus, keine Kinder und keine Leerzustandsmeldung. Zugangsname bleibt Unterordner laden. |

B-50 ist eine positive Kontrolle der Zweig-Unabhaengigkeit, keine Freigabe
beliebiger Baumstrukturen. B-51 prueft erneuten Versuch bei fortbestehendem
Fehler, nicht Erholung des Unterordnerdienstes. B-52 erweitert die Empfehlung
zu A-126 um klar erkennbare Lade-/Leerzustaende. Kein neuer separater Befund.
Zwei erfolgreich befuellte Nachbarzweige, langsame/ueberholte Antworten,
tiefe/grosse Baeume und weitere Rollen bleiben offen. Keine echte Drive-Aktion,
kein Upload. Tab geschlossen und lokaler Server beendet.

### Parallele Root-Anfragen im Browser vom 2026-09-20

Beleg: [docs-root-race.json](browser/docs-root-race.json). Admin, 1280x720,
Originalcontroller und nativer Dialog. Audit-Fixture verzoegert Root-Antworten
abwechselnd um 2 und 12 Sekunden; keine echten Drive-Anfragen.

- B-53: zwei Klicks vor Abschluss der ersten Antwort fuehren zu zwei sichtbaren
  Dokumente-Zeilen im Baum (DOM-Zaehler 2).
- B-54: nach erster Antwort Schliessen betaetigt. Snapshot bestaetigt nur noch
  Upload-Dialog und Fokus auf Ordner waehlen. Nach spaeter Antwort erscheint
  der Picker erneut, Fokus auf dessen Schliessen-Schaltflaeche.

A-130 damit auch im Browser bestaetigt. Ein erster zeitlich uneindeutiger
Versuch wurde nicht als Beleg gewertet; die Wiederholung koppelte Schliessen
direkt an das Sichtbarwerden. Ein kurzer Tool-Warteversuch endete vor der
zweiten Antwort, die abschliessende Beobachtung erfolgte nach deren Eintreffen.
Keine Dateien gewaehlt/hochgeladen; Tab geschlossen, Server beendet. Weitere
Browser und reale Latenzen bleiben ungeprueft.

### Dateiaktionen im Browser vom 2026-09-21

Beleg: [docs-actions-followup.json](browser/docs-actions-followup.json).
Original-Ordner-/Dialogtemplates und Controller, synthetische Anzeige-Route mit
zwei Dateizeilen, regulaeres Mitglied, 1280x720. Keine Dateiaktion abgeschickt.

| ID | Pruefung | Ergebnis |
|---|---|---|
| B-55 | Alpha umbenennen, Eingabe aendern, Abbrechen, wieder oeffnen | Fokus zurueck auf Umbenennen; kein offener Dialog. Wieder geoeffnet ist der urspruengliche Namensstamm voreingetragen. |
| B-56 | Alpha verschieben, Escape | Dialog ohne Quelldateiname, Ziel leer. Escape schliesst, Fokus zurueck auf Verschieben. |
| B-57 | Alpha archivieren, Abbrechen | Allgemeiner Text ohne Dateiname; Abbruch schliesst den Dialog. |
| B-58 | Beta umbenennen, Escape, wiederherstellen, Abbrechen | Richtiger Beta-Namensstamm und Formularziele /902/rename bzw. /902/restore. Restore ohne Quelldateiname; Abbruch schliesst und fokussiert Wiederherstellen. |

A-134 damit fuer Move/Archive/Restore im Listen-Browser bestaetigt. Der
Dateiwechsel zeigt keine versehentlich uebernommene Alpha-Zuordnung bei Beta.
Namensreset nach bewusstem Abbrechen ist positive Kontrolle, kein neuer
Entwurfsverlustbefund; A-127 betrifft insbesondere unerwartete Fehler.
Detailansicht, mobile Breiten, voller Fokusumlauf, verschachtelte Zielauswahl
und Submit-/Fehlerwiederaufnahme weiterhin offen. Tab/Server beendet.

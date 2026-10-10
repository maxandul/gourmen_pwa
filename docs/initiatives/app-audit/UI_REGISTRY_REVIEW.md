# UI-Registry: Zeilenabgleich D-05

Stand 2026-09-20, unveraenderte Baseline bf4d84a. Keine UI-Aenderung.

## Erfassung und Grenzen

Alle **150 Tabellen-Datenzeilen** aus Sektion 5 von docs/UI.md erfasst:
UI_REGISTRY_REVIEW.csv und UI_REGISTRY_LOCATIONS.json, reproduzierbar mit
check_ui_registry.py. 121 versionierte HTML/CSS/JS-Quelldateien durchsucht;
gehashte Kopien und main-v2.css ausgeschlossen, um Fundstellen nicht zu vervielfachen.
Zeilennummern beziehen sich auf diese Baseline. Keine Produktionsaussage.

Das ist eine Suchstellenkarte, keine automatische Freigabe. Treffer koennen
Kommentare, Selektoren, Markup oder JavaScript sein. CSS-Kaskade, geladene Assets,
zusammengesetzte Klassen und Feature-Schalter brauchen weitere Gegenpruefung.
Auch Token ohne Treffer ist kein Loeschauftrag. BEM-Kurzformen sind nur bei
eindeutigem Basisklassenbezug expandiert; Prosa kann abweichende Bezuege meinen.
Nicht-Klassen-Zeilen (Body, ID, Makros, Topbar-Dateien), das Tool-Strip-Beispiel
und die Deprecated-Liste sind nicht durch Klassentreffer abgeschlossen.
Die generierte CSV bleibt Suchinventar; manuelle Urteile stehen hier getrennt.

## Manuell nachverfolgte Abweichungen

| Registry-Zeilen | Codeabgleich | Urteil / Empfehlung |
|---|---|---|
| UIR-059 bis 062, 077 bis 087, 112 bis 114 (18 Zeilen) | Dokumentierte Merch-Runden-/Lookup-/Pillenklassen fehlen in den erfassten Quellen. Auch MerchRoundItem, round_shop und templates/admin/merch_v2 fehlen im Backend-/Template-Abgleich. Vorhanden sind merch_article/order/order_item/variant und templates/admin/merch sowie member/merch. | Registry beschreibt hier keinen implementierten Ist-Stand dieser Baseline. Herkunft/Zielversion klaeren; geplante Komponenten getrennt vom verbindlichen Ist-Verzeichnis fuehren. Kein Auftrag, das Rundenmodell nachzubauen. |
| UIR-071, UI.md:221 | backend/routes/admin.py:74-128 berechnet Kennzahlen und rendert admin/index.html. Template ab Zeile 26 enthaelt admin-hub, hero, metrics, cta. | Aussage, GET /admin leite nur zum Verein-Hub um und es gebe keine Uebersicht mehr, widerspricht der lokalen Route. Admin-Route ist unter /admin/ definiert; Slash-Normalisierung ist kein Hub-Redirect. |
| UIR-128, UI.md:367 | templates/admin/index.html:115-139 zeigt Re-Sync-Karte fuer Admin mit DRIVE_FEATURE_ENABLED; components.css:6544 ff. enthaelt Styles. | Als entfernt bezeichnete Karte ist weiterhin eingebunden. Bedingte Anzeige explizit dokumentieren; keine Loeschfreigabe. Re-Sync im Audit nicht ausgeloest. |
| UIR-002/003, UI.md:128-129 | base.css:130/143/148 definiert icon und sm/lg; icon--md und chip--small ohne exakten Treffer in der Quellenkarte. | Dokumentierte Modifier nicht als verfuegbare Varianten empfehlen, bevor Definition/Ladeweg belegt ist. Standardgroesse der Basisklasse ist keine Definition eines --md-Modifiers. |
| UIR-125, UI.md:364 | docs/detail.html:48-87 nutzt meta-card, meta, history-card/list/item/action/meta. components.css:6471-6517 definiert unter anderem meta/actions/history-list/item/action/meta. | __meta-grid und exaktes __history stimmen nicht mit den vorhandenen Namen ueberein. Registry konkretisieren; gemeinsame Wortpraefixe beweisen keine identischen Klassen. |

Diese Punkte erweitern **A-012**, weiterhin insgesamt 118 Befunde. Dokumentation
nicht stillschweigend auf einen vermuteten zukuenftigen Merch-Stand umschreiben.

## Positiver dynamischer Gegenbeleg

UIR-123: docs-folder-picker.js:49-73 erzeugt children/row/toggle/choose per
createElement/className. Selektionsmodifier wird in Zeilen 35-39 umgeschaltet.
components.css:6405-6450 definiert die betreffenden Zeilen-/Button-Styles;
docs/index.html:130, folder.html:169 und detail.html:131 laden den Controller.
Damit ist der dynamische Verwendungspfad statisch belegt. Die Klassen duerfen
nicht wegen fehlender statischer Template-Tokens aussortiert werden.
Laden echter Ordner, Dialogfokus und verschachtelte Bedienung bleiben Teil des
offenen Browser-Audits; dieser Codebeleg ersetzt keine Interaktionspruefung.

## Naechster Abschlussumfang

D-05 bleibt offen. Die restlichen Zeilen einzeln auf CSS-Definition und
tatsaechlichen Einbindungspfad pruefen; insbesondere Prosa-/BEM-Kurzformen,
Makros/Body/ID und Deprecated-Eintraege nachverfolgen. Danach aktive,
unregistrierte Komponenten gegenpruefen. Bestehende Browserbefunde verknuepfen,
statt aus Suchtreffern responsive oder barrierefreie Funktion abzuleiten.

## Zweiter Registry-Durchlauf: Sonderfaelle und Legacy

Statischer Vertragsabgleich am selben Commit; keine neue Browsermessung.
Nachfolgende Urteile ergaenzen die Suchkarte, ohne deren Rohstatus zu ersetzen.

| Zeile / Vertrag | Nachverfolgter Beleg | Ergebnis und Grenze |
|---|---|---|
| UIR-012 Body / Public-Shell | base.html:50-65 setzt data-layout bei public.* und laesst Sidebar/Bottom-Nav aus; layout.css:550-559 zentriert Public-Inhalt und reduziert unteres Padding | Dokumentierter Einbindungspfad stimmt. Nicht gleichbedeutend mit vollstaendiger Layoutfreigabe; A-100 bleibt bestehen. |
| UIR-037 top-notifications | base.html:53 vor Flash/Content; layout.css:380 position:static; pwa.js:86-87 holt Host und nutzt ihn ab :478/:524/:575/:625 | ID ist keine fehlende CSS-Klasse. Hinweiscontainer im normalen Dokumentfluss belegt. Installations-/Push-Anzeige bleibt vom Zustand abhaengig; kein echter OS-Push-Test. |
| UIR-039 Install-Banner | pwa.js:533-536,584-587,636-639 erzeugt __body/__actions; layout.css:426 definiert __steps | Kurzformen meinen app-shell-install-banner__body/__actions, nicht steps__body. Die Body-Klasse wird mit stack-vertical kombiniert; eigene CSS-Regel ist nicht Voraussetzung fuer einen Strukturanker. |
| UIR-052 Card-Section | components.css:827/834/850; admin/temp_password.html:38-50 sowie events/detail.html:741 | __header/__title/__body sind Geschwister am Block card-section. Markup und CSS vorhanden. |
| UIR-088 Formular-Makros | partials/_form_macros.html:2-12; Imports in admin/create_member.html, admin/edit_member_enhanced.html und member/profile.html; components.css:2197/2228 | required_mark prueft flags.required, field_errors zeigt den ersten Fehler. Beschriebener Makrovertrag stimmt. Barrierefreie Fehlerzuordnung wird dadurch nicht automatisch hergestellt; A-018 bleibt relevant. |
| UIR-098 Grid --full | components.css:4840; events/index.html:211 und events/detail.html:197 | Volle Breite sitzt auf dashboard-info-tile--full innerhalb des Grids. Kein Beleg fuer dashboard-info-grid--full; die Prosa ist mehrdeutig. Vollstaendigen Selektor dokumentieren. |
| UIR-137 Budget | accounting/_tab_statistik.html:43 und stats.html:102; components.css:6755 | --over wird als budget-meter__fill--over bei pct > 100 gesetzt. --budget-meter-fill ist eine CSS-Variable, keine Klasse. Keine fehlenden Modifier aus solchen Kurzformen ableiten. |
| UIR-148 Tabellenlink | accounting/index.html:282-283,395-396,506-507; components.css:637-642 | data-table__link-label und data-table__chev sind Geschwister, keine Kinderklasse link__*. Definition/Verwendung belegt. |

### UIR-092 bis 094: Kopfleiste und Dialogpausen

base.html:78 laedt topbar-scroll.js. Controller und layout.css:568-583 verwenden
dieselbe Grenze 1023px; Desktop entfernt den Scroll-Listener und zeigt die Leiste.
Reduced Motion schaltet die CSS-Transition aus. TOP_RESERVE ist 80; Schwellen
sind streng delta > 16 / delta < -4, nicht bereits bei exakt 16 bzw. -4.
Das Delta sammelt sich gegen lastY bis zum naechsten Zustands-/Baselinewechsel.

Die Dialogpause ist enger als die generische Beschreibung vermuten laesst:
isModalOpen erkennt explizite role=dialog/aria-modal=true ohne hidden,
dialog.public-drawer[open], details.user-menu[open] und data-sidebar-open=true.
Native Docs-/Kalender-Dialoge tragen diese expliziten Attribute nicht:
docs/_folder_picker_modal.html:2, _upload_modal.html:2, _drive_quick_modals.html
und member/technical.html:128/138. Die Docs-Controller verwenden showModal
(docs-folder-picker.js:147, docs-upload-modal.js:32, docs-quick-actions.js:9),
setzen aber keinen passenden role-/aria-modal-Selektor nachtraeglich.
Implizite Dialogsemantik ist kein passender CSS-Attributselektor.

Bei erkanntem Modal friert update den Zustand ein; eine bereits versteckte
Kopfleiste wird dort nicht explizit wieder gezeigt. Kommentar und Dokumentation
sollten zwischen Zustand erhalten und sichtbar halten unterscheiden.
**Codegrenze bestaetigt; sichtbare Auswirkung bei realem Scrollen/nativem Modal
noch offen.** Gezielt in der bestehenden Drive-/Kalender-Browserrestpruefung
testen. Kein pauschaler Barrierefreiheitsfehler allein aus diesem Codeabgleich.

### Tool-Strip ausserhalb der Registry-Tabelle

Events index:769-828 und Accounting index:899-968 enthalten eigene Funktionen
fuer Wiederherstellen aus sessionStorage, Toggle-Speichern und Einklappen nach
GET-Submit. Ohne gespeicherten Zustand starten die geprueften Filter geschlossen;
bei gespeichertem '1' werden sie wieder geoeffnet. 'Standardmaessig eingeklappt'
beschreibt deshalb nur den Ausgangszustand, nicht jeden Seitenaufruf.
accordion.js bedient dagegen data-accordion / accordion-item und ist nicht
der Controller dieses nativen details-Musters. Bestaetigt A-005/A-097.
Registry sollte Markup, zustaendigen Controller und Persistenzvertrag verbinden.

### Deprecated-Liste: sechs Klassenfamilien

In components.css weiterhin definiert: context-actions (:4597-4630),
dashboard-next-event (:5080-5151), dashboard-card-link (:5156-5185),
card--dash-tile (:5193-5231), dashboard-hygiene-rows (:5242) und
dashboard-row-link einschliesslich --block-start (:5236-5292).
Keine Treffer fuer diese Familien in Templates und static/js/v2.
Damit sind es konkrete Bereinigungskandidaten im CSS, keine aktiven Muster,
die fuer neue Oberflaechen vorgeschlagen werden sollten. Der globale V2-Build
nimmt components.css weiterhin auf; Hash-Kopien sind davon getrennte Artefakte.
Vor spaeterer Entfernung bleiben dynamisch zusammengesetzte Namen und weitere
Erzeuger/Assets zu pruefen. Der Audit loescht nichts und erteilt keine automatische
Loeschfreigabe. Allgemeine Suchanweisung in UI.md entsprechend einschraenken.

Ergebnis: A-012/A-005/A-097 praezisiert, weiterhin **118 Befunde**. D-05 bleibt
offen fuer die uebrigen Einzelzeilen, Wildcard-Familien und den Rueckabgleich
aktiver Komponenten, die im Verzeichnis fehlen.

## Dritter Registry-Durchlauf: Cards, Formulare und Rueckabgleich

### Weitere Familien: Definition und Verwendung getrennt

| Registry | Nachverfolgung | Ergebnis |
|---|---|---|
| UIR-042 bis 050 Cards | components.css:656-735; member/merch/index.html:51-68 und admin/merch/index.html:343-363; beide laden collapsible-card.js (:353/:435) | Toggle/Content werden ueber is-collapsed und aria-expanded umgeschaltet. Definition, Markup und Controller belegt. Header hat zwar cursor:pointer, der Controller bindet nur den Toggle-Button; nicht den gesamten Header als Klickflaeche dokumentieren. Interaktions-/Fokusfreigabe folgt daraus nicht. |
| UIR-047/048 Varianten | components.css:718-735 | card__actions--split-toggle und card__actions-chips sind definiert, aber ohne Treffer in Templates/V2-JS. Verfuegbare Definition ist keine nachgewiesene aktuelle Verwendung. |
| UIR-051 Sektion | components.css:801-812; admin/member_security_overview.html:45 ff. | card-section verwendet; --accent definiert, ohne Treffer in Templates/V2-JS. |
| UIR-053 Infozeilen | components.css:2124-2164; accounting/booking_detail.html:33 ff. | Label/Value-Muster belegt. Die Klasse form besitzt hier eine kontextbezogene Margin-Regel; nicht mit dem HTML-Element form gleichsetzen. |
| UIR-054 bis 056 Tabellen | components.css:1106-1212; accounting/index.html:266/378/590/673 | Wrapper, Tabelle, Sticky-Modifier und Gruppenzeile definiert und verwendet. Vorhandene CSS-Regeln sind kein Nachweis korrekter Breite an allen Viewports; A-014 bleibt offen. |
| UIR-069 Insight | components.css:1041-1099; events/index.html:497-513 | Panel/section/heading/value verwendet; list/item nur als CSS gefunden. Nicht die gesamte Familie als verwaist einstufen. |
| UIR-070/072 Hub | components.css:1-60; member/index.html:17 ff. | hub-grid/hub-card/--featured definiert, keine Treffer in Templates/V2-JS. Verein nutzt settings-nav. Dokumentiertes Hub-Beispiel entspricht nicht dieser Seite. Admin-Abweichung bereits im ersten Durchlauf. |
| UIR-073 bis 076 Forms | components.css:2162-2270; admin/create_member.html:24 ff., accounting/booking_new.html:32 ff.; Makrobeleg im zweiten Durchlauf | form/form-field/required/form-actions verwendet; eigene universelle .form-Layoutregel nicht aus Tag-Treffern ableiten. Feldstyling und Fehlerzuordnung sind verschiedene Pruefaufgaben. |
| UIR-089 bis 091 Tabs/Disclosure | components.css:2726 ff.,2859 ff.,3942 ff.; accounting/index.html:103 ff.; base.html laedt tabs.js | Definition und Einbindung belegt. Tab-Controller sowie seitenbezogene Disclosure-Logik getrennt. Bereits dokumentierte A-003/A-004/A-005 bleiben bestehen. |

### Rueckwaertssuche: verwendete Namen gegen das Verzeichnis

`check_registry_reverse.py` erzeugt UI_REGISTRY_REVERSE.csv/.json. Erfasst
literale class-Attribute versionierter Templates nach Maskieren von Jinja;
kein Renderlauf. **117 Kandidatenfamilien**, ausdruecklich keine 117 Fehler.
Makroargumente, dynamische Namen, Kommentare und Erreichbarkeit brauchen
manuelle Einordnung. Auch ein dokumentierter Modifier kann bei der Suche nach
einem eigenstaendigen Blocknamen als Kandidat erscheinen.

Manuell eingeordnet:

- **chip-select / chip-select-wrap**: echte Registry-Luecke. components.css:3653-3742
  definiert Status-/Teilnahmevarianten; events/index.html:178/287,
  events/detail.html:144 und admin/merch/index.html:130 verwenden sie.
  Gemeinsames Auswahlmuster mit fachlich verschiedenen Werten dokumentieren.
- **rating-chip**: echte Registry-Luecke. events/index.html:412 nutzt
  chip rating-chip--dynamic mit --rating-hue; components.css:3597-3647 definiert
  die Farbregeln. Alte feste Varianten 1-5 separat von der dynamischen Variante
  erfassen; aus deren CSS-Existenz keine aktuelle Verwendung ableiten.
- **quantity-input / price-value / variant-row**: Merch-Verhaltensanker, nicht
  automatisch fehlendes Styling. member/merch/index.html:71/103/111 kombiniert
  sie mit form-row/form-field__input/info-row__value. merch-order.js:27/48/84/
  129/137/166-167 selektiert bzw. erzeugt diese Klassen. Der Controller wird
  dort in Zeile 352 geladen. Beim Refactoring als JS-Vertrag behandeln.
- **form-row**: Rueckwaertssuche meldet 23 Templates, aber UI.md nennt bereits
  form-row--inline-submit und --inline-remove. Teilabdeckung statt komplett
  fehlender Familie; Grundlayout und stacked/align-end in components.css:2242-2263
  im Verzeichnis ergaenzen, falls dieses vollstaendig sein soll.
- **tool-strip**, **accounting-chart-modal**, **app-shell-install-banner**:
  bereits im Beispiel oder ueber Element-/Modifiernamen dokumentiert. Keine
  neuen Befunde aus dem fehlenden exakten Blocknamen erzeugen.

Empfehlung fuer die spaetere Bereinigung: Registry unterscheidet aktiv verwendet,
definiert ohne belegte Verwendung, Verhalten-/Strukturanker und historisch/geplant.
Je Familie Quelle, Einbindung und Zustand nennen. Reine Trefferzahlen sollen
weder Loeschentscheidungen noch neue Komponenten begruenden.

Weiterhin 118 Befunde; Erweiterung der Struktur-/Dokumentationsbefunde A-007/A-012.
D-05 bleibt fuer restliche bereichsspezifische Zeilen und Kandidaten offen.
Keine Aussage, alle 150 Zeilen seien durch diese drei Durchlaeufe abgeschlossen.

## Vierter Registry-Durchlauf: bereichsspezifische Verwendungspfade

Statische Gegenpruefung der beschriebenen Einbindung; keine neue Browser- oder
Produktionsmessung. Die folgenden Familien sind damit nicht in allen Zustaenden
freigegeben. Einzelne Child-/Wildcard-Varianten bleiben getrennt nachzuverfolgen.

| Registry | Definition / Einbindung | Einordnung |
|---|---|---|
| UIR-095 bis 100 Dashboard | components.css:4807 ff.,4834 ff.,4868 ff.,5702 ff.; dashboard/index.html:9,58,81,122; dashboard.py:120 | Intent-/Info-Kacheln und Reise-Hero eingebunden. Hero serverseitig durch hamburg2026_visible begrenzt (:57), nicht nur versteckt. Vorhandene Datums-Grenzproben in DOCUMENT_CLAIM_CHECKS.json gelten weiter. Historischen Reisebaustein nicht mit staendig aktiver Dashboard-Funktion verwechseln. |
| UIR-101 bis 104 Event-Detail | components.css:1664 ff.,4244 ff.,4299 ff.; events/detail.html:267,540,1092,1124 | Teilnehmer-, Bewertungs- und Toolbar-Familien im Detailtemplate vorhanden. Sichtbarkeit der Daten bleibt eine eigene Rechtepruefung (bestehende Event-Befunde); Klassentreffer bestaetigen diese nicht. |
| UIR-105 bis 108 Event-Statistik | components.css:1740 ff.,1771 ff.,1783 ff.,1834 ff.; events/index.html:631-662; events-monatsessen-stats.js:511 ff. | Tabellen-Sortierbuttons besitzen Datenattribute und JS-Verwendung, nicht nur dekorative CSS-Klassen. Aktive Sortierung ist dynamisch; Registry sollte den Controller nennen. |
| UIR-109/115/116 Bereinigung | components.css:5306-5324 ff.; events/cleanup.html:43-77 | Hinweis, Schrittnavigation und Undo-Form vorhanden. Undo ist ein POST; die CSS-Bezeichnung macht daraus keinen rein lokalen Rueckgaengig-Schritt. Fachliche Ruecknahmefehler bleiben A-029. |
| UIR-110 GGL | components.css:1459/1524; restaurants-table-scroll.js:13-24 | --ggl-rank-col-outer ist eine gemessene CSS-Variable. Breite aus Rangzellen, auf volle Pixel aufgerundet; CSS-Fallback 3ch. Kein fehlender Klassenmodifier. Vollstaendige Scroll-/Zoom-Matrix weiterhin offen. |
| UIR-111 BillBro | components.css:4178 ff.; events/detail.html:325-329; accounting/index.html:734-739 | Dasselbe Schritt-Muster zeigt auch den Jahresabschluss. Dokumentation unter nur BillBro ist zu eng. done/current und Index vorhanden; fachliche Phasen sind je Workflow verschieden. |
| UIR-119 bis 122 Docs-Browser | components.css:6089/6163/6181/6229 ff.; docs/folder.html:12,30,94,109 ff. | Shell, Ordnerkopf, Kacheln und Dateizeilen vorhanden. Datei-Aktionsmenue wird bei document_id eingebunden; Drive-Link zusaetzlich abhaengig von web_view_link. Registry ist keine Aussage, jede Datei biete immer jede Aktion. |
| UIR-124/126/127 Docs-Dialoge | components.css:5967-5983,6461 ff.; docs/_upload_modal.html:2-41; docs-upload-modal.js:30-36,69 ff. | Gemeinsames zentriertes dialog-Styling bestaetigt. Upload-Dropzone schaltet --active beim Drag; Ordnerlabel wird auch in Quick-Modals verwendet. Native Dialoge von Chart-Overlay unterscheiden; offene Fokus-/Verschachtelungspruefung bleibt. |
| UIR-129 Google-Profil | components.css:6576-6598; member/profile.html:298-331 | Eigenes Formular mit POST member.google_email_save und verified/pending-Anzeige. Statusstyling bestaetigt keine Token-/Berechtigungssicherheit; A-088 bleibt relevant. |
| UIR-130 bis 136 Kalender | member/technical.html:45-140 und :515/519; components.css:6622-6685 ff. | URL/Kopieren, Plattformhinweise, Aktionen und native Bestaetigungsdialoge vorhanden. calendar-subscribe-card hat keine eigene Regel im Quellenabgleich, nutzt aber card. Kein fehlendes Styling allein aus dem Blocknamen ableiten. |
| UIR-138 bis 140 Belege/Tabellen | components.css:1217,1238-1270; accounting/receipt_upload.html:47-80 und Inline-Script ab :150 | Hauptklasse accounting-receipt-capture ist Strukturwrapper; actions/preview/preview-img besitzen Styles. Zwei Buttons setzen capture/accept verschieden; Vorschau nur fuer Bild-MIME. Kamera-Verhalten realer Mobilgeraete damit nicht bewiesen. |
| UIR-141/142 Jahresaktionen | accounting/index.html:74-86 und :949-958; components.css:1231 | Jahresanlage/Aktionen in der Filterstruktur; Einklappen beim Navigieren separat im Template implementiert. Bereits erfasste Disclosure-Dopplung, kein neues Problem pro Button. |
| UIR-143 bis 146 Charts | components.css:1991-2046 ff.; accounting/_tab_statistik.html:9-98,177-192; accounting/index.html:1048-1097 | Vollbild verschiebt den vorhandenen Chart-Knoten in den Modal-Body, setzt --fullscreen und legt einen Rueckkehr-Platzhalter an. Kein zweites unabhaengiges Diagramm. Bestehender Fokusbefund A-016 bleibt trotz korrekter Klassenverwendung bestehen. |
| UIR-147/149/150 Tabellenaktionen | components.css:593/613/649; accounting/booking_detail.html:95/112, accounting/index.html:398 | Inline-Submit, Tab-Aktionen und sekundaere Tabellenzeile definiert/verwendet; --text-xs im Beschreibungstext ist ein Token, kein data-table__sub-Modifier. |

### Gemeinsame Workflow-Bausteine unter fachlichen Namen

cleanup-step-nav wird auch in accounting/booking_new.html:24-26 fuer drei Schritte
und receipt_upload.html:28-30 fuer zwei Schritte verwendet. billbro-workflow
wird im Jahresabschluss benutzt. Das ist bereits vorhandene Wiederverwendung,
keine zu beseitigende Dopplung. Empfehlung fuer ein spaeteres Zielbild: generische
Schrittanzeige/-navigation mit dokumentierten Zustands- und Bedienvertraegen;
fachliche Phasen weiterhin in den jeweiligen Modulen. Umbenennung erst mit
allen CSS-/Template-/JS-Verweisen planen, nicht isoliert einzelne Klassen ersetzen.

Weiterhin 118 Befunde. Dieser Durchlauf praezisiert A-012 und den bestehenden
Komponentenvergleich. Noch offen: Public-/Navigationsvarianten, einzelne bislang
nur kartierte Child-Klassen, Error-/Offline-Ladewege sowie weitere Kandidaten
der Rueckwaertssuche. D-05 bleibt in_progress.

## Fuenfter Registry-Durchlauf: Public-Navigation und Fehler-/Offline-Ladewege

### Public und Navigation

| Registry | Gegenpruefung | Ergebnis |
|---|---|---|
| UIR-013 bis 016,018 | partials/_user_bar.html:1-76; layout.css:119-303; public-drawer.js vollstaendig gelesen | Public-Markup kombiniert user-bar/public-topnav. Desktop-Navigation ab 1024px, Hamburger darunter. Alle dokumentierten Drawer-Unterelemente im Markup; Controller oeffnet showModal und behandelt Schliessen/Links/Backdrop/cancel. Kein Resize-Schliessen: bestehender A-100 bleibt relevant. Pills sind Seitenlinks, keine inhaltsumschaltenden ARIA-Tabs. |
| UIR-017/028/029 | restaurants.html:214-246; restaurants-table-scroll.js:135-138 | AJAX-Austausch ruft Teardown und anschliessend Init ueber Restaurants-Aliase auf. Generische und alte Funktionsnamen verweisen auf denselben Scroll-Controller. Nicht zwei unabhaengige Implementierungen entfernen. |
| UIR-019 bis 027 | public/restaurants.html:34-76; public.css:285 ff.,618-625 | Suche/Sortierung/Meta-Zeile und Feldvarianten eingebunden. Suche auf submit, Sortierung auf change, nicht bei jedem Tastendruck; Code :250 ff. Toolbar wird bei max-width:768px gestapelt, Kuechen-Spalte dort ausgeblendet. 'Unter 768px' ist als Kurzbeschreibung um den Grenzwert ungenau. |
| UIR-032 bis 036 | public/landing.html, about.html, restaurants.html; public.css:24-61,571-578; partials/_landing_instagram.html | CTA-/Seitentitel-/KPI-/About-Familien in den jeweiligen Templates; drei KPI-Spalten ab 769px. Landing bindet Instagram-Partial (:96) mit zwei Blockquotes und Fallback-Links sowie embed.js (:182) ein. Externe Erreichbarkeit/Datenschutz/Ladeleistung hier nicht neu geprueft. |
| UIR-040 User-Menue | _user_bar.html:104-143; components.css:5522-5538 | Profil/Sicherheit/Einstellungen und bei Public zuerst Zur App wie dokumentiert; ausgeloggt Anmelden, Logout nur eingeloggt. badge/sep bedingt im Markup vorhanden, keine Altlast allein wegen seltener Anzeige. |
| UIR-041 Settings-Unterelement | components.css:4752-4769; gesamte Quellenkarte | settings-nav__badge definiert, aber ohne Template-/JS-Treffer in den erfassten Quellen. Abgrenzung zur tatsaechlich verwendeten user-menu__badge. Kein Loeschauftrag fuer die ganze settings-nav-Familie. |

Alle drei Public-Templates laden public.604da1b3.css zusaetzlich zum V2-Bundle
(landing/about:10, restaurants:21). Die Public-Regeln duerfen deshalb nicht
allein gegen components.css bewertet werden. Diese Codepruefung ersetzt keine
neue Viewport-Messung und schliesst bisherige Public-Befunde nicht.

### UIR-117: Fehlerseiten

backend/app.py:183-194 registriert die 403-/404-/500-Handler. Sie rendern
errors/403.html, 404.html, 500.html mit passendem HTTP-Status; 500 rollt die
DB-Session zurueck. Alle drei Templates erweitern base.html und verwenden
error-page, __code, __actions, definiert in components.css:5561-5623.
Startseitenlink stets, Dashboardlink nur eingeloggt. Statuscode-Anzeige ist
aria-hidden, die Fehlerbeschreibung steht im sichtbaren h1.

Damit sind Definition und Server-Einbindung belegt. Ein Fehler bei bestehendem
DB-/Context-Processor-Ausfall kann trotzdem den Renderweg betreffen; Robustheit
unter solchen Ausfaellen wurde hier nicht simuliert. Fehlende Route ist zudem
nicht automatisch ein public.*-Endpoint; Public-Shell-Annahmen nicht pauschal
auf alle Fehlerseiten uebertragen.

### UIR-118: Offline ist ein statischer Auslieferungsweg

static/sw.js:35 nimmt /static/offline.4ebb2a42.html in STATIC_ASSETS auf.
Bei fehlgeschlagenem HTML-Netzabruf wird diese Datei via caches.match gesucht
(:274); fehlt sie, folgt ein Textfallback mit Status 503. Ein weiterer
Fallback-Verweis steht bei :385. Kein normaler Flask-Render von templates/offline.html
ist fuer diesen Service-Worker-Pfad erforderlich.

templates/offline.html, static/offline.html und static/offline.4ebb2a42.html
sind zum Pruefzeitpunkt bytegleich (SHA-256
3258ca3f13a45c10096ba95d20f56bfc81689b165d64a1730ba491b3116c5d13).
Sie laden main-v2.fa47ba3e.css direkt und verwenden offline-shell samt __inner
und __lead, definiert in components.css:5632 ff. Kein base.html-Include.
Keine Divergenz der drei Kopien festgestellt, aber weiterhin mehrere zu
pflegende Orte. Die Rolle Quelle/Kopie/Auslieferungsartefakt dokumentieren.

Die vorhandenen A-098/A-101/A-107 und Offline-Proben bleiben bestehen:
Klassenverwendung und identische Kopien beweisen weder nutzbare gecachte
App-Seiten noch eine verlaessliche automatische Online-Rueckkehr. Kein echter
Offline-/Update-Zyklus in diesem Durchlauf.

Weiterhin 118 Befunde. Public-/Fehler-/Offline-Einbindung als begrenztes
Codepaket abgeglichen; nicht als vollstaendiger Verhaltensnachweis abgeschlossen.
Rest fuer D-05: bislang nur kartierte einzelne Child-/Modifier-Varianten
(einschliesslich Events-Index), Basis-/Layoutdetails und ungepruefte Kandidaten
der Rueckwaertssuche. Abschliessende Zeilen-Abdeckungsmatrix noch erstellen.

## Sechster Registry-Durchlauf: Restvarianten und Abdeckungsmatrix

UI_REGISTRY_COVERAGE.csv erfasst jetzt jede der 150 Ausgangszeilen genau einmal,
mit Pruefumfang, Berichtsdurchlauf und Restaufgabe. build_registry_coverage.py
verwendet explizite manuelle Zuordnungen; keine automatische Freigabe aus
Suchtreffern. Die Rohkarte UI_REGISTRY_REVIEW.csv bleibt unveraendert.

| Status | Zeilen | Bedeutung |
|---|---:|---|
| code_path_partially_reviewed | 118 | Einbindung/Vertrag teilweise gelesen; nicht alle Varianten/Zustaende abgeschlossen |
| document_discrepancy_confirmed | 5 | Konkreter Dokumentationswiderspruch belegt; kein pauschaler Zeilenabschluss |
| documented_component_absent | 18 | Beschriebene Merch-Komponenten im geprueften Bestand nicht vorhanden |
| css_only_candidate | 5 | Definition vorhanden, keine Template-/V2-JS-Treffer; dynamische Restpruefung vor Entfernung |
| lexical_map_only | 4 | Bisher nur Suchkarte: UIR-038,057,058,068 |

Diese Zahlen sind **Zeilenstatus**, keine neuen Befundzahlen und keine
Bestandenquote. Keine Zeile wird durch den Generator als vollstaendig erledigt
markiert. Teilweise ungenutzte Varianten in sonst aktiven Familien bleiben im
Bericht, statt die gesamte Familie als CSS-Altlast einzustufen.

Ergaenzende Nachverfolgung:

- UIR-001/004: dokumentierte Button-Modifier in components.css:337-471,
  Alert-Varianten :2477-2511 vorhanden. Beispiele btn--success in
  auth/backup_codes.html:63, btn--billbro in events/index.html:222.
  Alle Aktions-/Fehler-/Hover-Zustaende dadurch nicht neu getestet.
- UIR-005: _flash_messages.html normalisiert danger zu error und message zu
  info; Klassen entstehen als flash-{{ flash_mod }}. Kein fehlender statischer
  flash-danger-Treffer als Funktionsverlust zu werten. Unbekannte Kategorien
  werden nicht durch diesen Abgleich auf passende Styles geprueft.
- UIR-006: empty-state mit __icon/__message und --filtered in components.css:2517 ff.;
  --filtered in events/index.html:306 sowie docs/index.html:92/folder.html:81.
  Filtrierte Leerzustaende sind damit vorhandene Varianten, keine Altlast.
- UIR-007 bis 011: Container/Zurueck/Seitentitel in base.css:206 ff.; Bottom-Nav
  in layout.css:312 ff., auf Desktop ausgeblendet (:538). Vier Ziele im Partial;
  deren aktive Zuordnung bleibt vom bereits erfassten A-002 betroffen.
- UIR-030/031/063-065: Event-Link-Unterelemente und Restaurant-/Status-/
  Organisatorspalten in components.css:1302-1395 und events/index.html:248 ff.
  Restaurant-Link nur bei place_website; Event-Datum/Icon/Chevron gemeinsame
  Linkflaeche. Today-Hero :163 ff. setzt --stacked erst ab zweitem Schleifendurchlauf;
  events.py:244-263 waehlt heute als Standard bei vorhandenen heutigen Events.
  Mehrfach-Events/Leerwerte/Linkziele nicht durch den Klassenabgleich vollstaendig getestet.
- UIR-066/067: stat-tiles/stat-tile und --metrics-follow in components.css:865-904/1001
  definiert, ohne Treffer in Templates/V2-JS. Von der aktiven metrics-spotlight-
  Familie getrennt halten; weitere Bereinigungskandidaten.

Korrektur der Berichtszuordnung: Im fuenften Durchlauf gehoeren Scroll-Huellen
zu UIR-028/029, Kuechen-Spalte zu UIR-027 und Public-CTA bis About zu UIR-032-036.
UIR-031 ist der heute-Hero. Die entsprechenden Tabellenzeilen wurden korrigiert.

Naechster begrenzter Abschluss: vier nur kartierte Zeilen detailliert abgleichen;
anschliessend offene Modifier/Unterelemente anhand der Matrix bearbeiten und
Rueckwaertskandidaten klassifizieren. D-05 bleibt offen, weiterhin 118 Befunde.

## Siebter Registry-Durchlauf: vier bisher nur kartierte Eintraege

### UIR-038: Einstellungshinweise in PWA-Bannern

pwa.js:96-102 erzeugt app-shell-banner__settings-hint und gegebenenfalls
__settings-link. Ziel stammt aus data-member-settings-href, das base.html fuer
angemeldete Mitglieder mit member.technical setzt. Ohne geeignetes Attribut
bleibt der Hinweis reiner Text. Aufrufe :492/535/586/638 binden ihn in verschiedene
Installations-/Push-Banner ein. layout.css:393-411 definiert Hinweis, Link und
Hover. Quelle pwa.js und geladene pwa.df1b3f63.js sind aktuell SHA-256-gleich.

Definition, Erzeugung und Auslieferungsbezug sind damit belegt. Kein Nachweis,
dass jeder Browser/Installationszustand den Banner korrekt anzeigt. Kein echter
Pushversand oder Installationstest. Keine fehlende Template-Klasse und keine Altlast.

### UIR-057/058: Mitgliedertabelle und Breitenbegrenzung

admin/members.html:39-42 hat genau die Verschachtelung, auf die die direkten
Kindselektoren in components.css:1565-1581 zielen: page-content-Modifier,
Scroll-Aussenhuelle, Scroll-Innenhuelle, Tabelle. min-width:0 und width/max-width
begrenzen die Huellen; die Tabelle selbst verwendet width:max-content und
min-width:100%. Erste Spalte sticky; inaktive Zeilen opacity:0.72.

Alle neun dokumentierten Unterelemente/Modifier in UIR-057 nachverfolgt:
row--inactive, col-email, col-adresse, col-kleider, col-fuehrerschein,
col-status, status-chips, actions, actions-inner. Sie stehen in
admin/members.html:70-128 und components.css:1614-1662. Aktionen sind im Template
auf current_user.is_admin() begrenzt. Die Route admin.py:299-303 rendert die
Liste unter verein_member_required; der Dateiname Admin bedeutet deshalb
nicht, dass die gesamte Liste ausschliesslich Admins sehen.

Die dokumentierte Struktur ist vorhanden. 'Alle Mitgliedsfelder' in der Registry
ist als technische Zusage zu weit: Das Template ist eine ausgewaehlte Uebersicht,
keine vollstaendige Model-/Berechtigungsmatrix; sensible Daten werden verlinkt.
CSS-Abgleich ersetzt weder Datenschutzentscheidung noch Langdaten-/Zoom-/
Touch-Pruefung. Bereits offene Rollen-/Layoutpruefungen bleiben bestehen.

### UIR-068: metrics-spotlight statt unbestimmtem Wildcard-Vertrag

components.css:911-999 definiert context, hero, metric, metric-label,
metric-value, metric-hint und metric-value--accent. Die Verwendung ist in
accounting/index.html:160-195, events/index.html:476-492 und ggl/index.html:89 ff.
belegt. Public-Landing nutzt die Kennzahlen-Unterelemente ebenfalls (:64-76),
mit zusaetzlichen Regeln fuer metric--next-essen und metric-value--landing-text
in public.css:36-43/571 ff. Voller Wrapper und Unterelement-Wiederverwendung
sind verschiedene gueltige Verwendungen.

Besonderheit: metric-value--accent hat eine eigene Farbe; innerhalb von hero
wird sie wieder auf color-text-primary gesetzt (components.css:986-993).
Der Kommentar bezeichnet diese Kombination dort als deprecated. '--accent'
bedeutet also nicht in jedem Kontext eine sichtbare Akzentfarbe.
Die benachbarte stat-tiles--metrics-follow-Regel ist bereits separat als
Kandidat erfasst und kein Beleg einer aktiven Kennzahlen-Untersektion.

Empfehlung: Statt __metric* die konkreten Unterelemente und Kontextvarianten
auffuehren. Beim Redesign gemeinsame Zahlen-/Label-/Hinweisstruktur erhalten;
responsive Anordnung pro Verwendung explizit pruefen. Berechnung und Inhalt
der Kennzahlen bleiben Gegenstand der jeweiligen Modul-/Performanceberichte.

### Aktualisierter Abdeckungsstand

Alle 150 Zeilen besitzen jetzt mindestens einen manuellen Pruefverweis.
UI_REGISTRY_COVERAGE.csv: **122 teilweise nachverfolgte Codepfade, 5 konkrete
Dokumentationsabweichungen, 18 nicht vorhandene Merch-Komponentenzeilen,
5 CSS-Kandidaten, 0 rein kartierte Zeilen.** Die Tabelle des sechsten Durchlaufs
bleibt als damaliger Stand erhalten. Keine Vollstaendigkeits-/Browserfreigabe.

Naechster Schritt: verbleibende Modifier-/Child-Grenzen gezielt erfassen und
117 Rueckwaertskandidaten auf tatsaechliche Registry-Luecken, bereits teilweise
beschriebene Familien, Hilfsklassen und Verhaltensanker einordnen. D-05 bleibt
offen; weiterhin 118 Befunde, keine App-Aenderung.

## Achter Registry-Durchlauf: Rueckwaertskandidaten eingeordnet

UI_REGISTRY_REVERSE_TRIAGE.csv ordnet alle 117 Rohkandidaten genau einmal ein;
reproduzierbar durch classify_registry_reverse.py mit expliziten Zuordnungen.
Rohkarte und ihre Anzahl bleiben erhalten, damit Suchfehler nachvollziehbar sind.

| Einordnung | Anzahl | Konsequenz |
|---|---:|---|
| Bereits teilweise dokumentiert | 10 | Element-/Modifier-/Beispielnennung, kein komplett fehlender Block |
| Verhaltens-/Zustandsanker | 8 | Umbenennen/Entfernen muss JS-Verwendung beruecksichtigen |
| Hilfs-/Kontextstil | 7 | Nicht jeder Klassenname benoetigt eine eigene grosse Komponente |
| Registry-Luecke bestaetigt | 6 | Konkrete bestehende Bausteine im Verzeichnis ergaenzen |
| Scannerartefakt | 2 | Kein realer eigenstaendiger Klassenname |
| Historische Hamburg-Seite | 20 | Eigener zeitlich begrenzter Seitenumfang, keine automatische Loeschfreigabe |
| Detailpruefung offen | 64 | Fundstelle bekannt; Definition, Erzeugung und Ladeweg noch gemeinsam pruefen |

Die sechs bestaetigten Luecken sind chip-select, chip-select-wrap, rating-chip,
billbro-guess-ranking-table, docs-file-list und theme-switch. Ihre Definitions-
und Templatebelege stehen im Register. Teilweise sind sie Unterbausteine bereits
bekannter Familien. Empfehlung: bestehende Bausteine dokumentieren und den
Bezug zu Chip/Dateizeile/Theme-Steuerung nennen, keine neuen Parallelkomponenten.
Erweiterung A-012, keine sechs neuen funktionalen Fehler.

Wichtige Fehlalarme: cls stammt aus JavaScript-Verkettung in
events/hamburg2026.html:1257-1258, nicht aus einer tatsaechlichen Klasse cls.
flash- entsteht beim Maskieren von flash-{{ flash_mod }} in
partials/_flash_messages.html:23. Auch chip-select-- ist ein unvollstaendiger
Maskierungsrest; die Familie chip-select selbst ist dagegen real.
Der Rohscanner ist somit keine vollstaendige HTML-/Jinja-/JS-Analyse.

Die 20 hamburg-*-Familien haben ihre erfassten Fundstellen ausschliesslich in
der historischen Reiseseite. events.py:453-460 prueft den Sichtbarkeits-Cutoff.
Das ordnet ihre Reichweite ein, schliesst jedoch weder die historische
Dokumentationspruefung noch jeden dynamischen Erzeugungspfad ab.
Hamburg ist vom ausgeschlossenen Game-Sideprojekt getrennt; Game bleibt unberuehrt.

64 Kandidaten bleiben bewusst detail_review_open, jeweils mit konkretem
Datei-/Zeilen-Einstieg. Darunter alte Merch-Formnamen, Places-Dialogbausteine,
Chart-/Navigationsvarianten sowie einzelne Public-/Security-Komponenten.
Beispiel: btn-success in admin/create_event.html:190 wird in JS-generiertem
Markup mit btn kombiniert; im geprueften V2-CSS kein btn-success-Selektor.
Das ist noch keine pauschale Aussage ueber den gesamten Ladeweg oder sichtbaren
Fehler. Solche Faelle als Naechstes gruppenweise nachverfolgen.

Weiterhin 118 Befunde; keine App-Aenderung. D-05 bleibt offen fuer diese
Detailpruefungen und die noch nicht abgeschlossenen Registry-Varianten.

## Neunter Registry-Durchlauf: erreichbare alte Merch-Oberflaechen

Zehn bisher offene Rueckwaertskandidaten anhand Route, Template, lokalem CSS
und JS-Erzeugung eingeordnet. Kein Netzwerkzugriff, keine Bestellung erzeugt.

### Eigene Routen statt verwaister Vorlagen

member.py:343-435 bedient GET/POST /merch/order und rendert
member/merch/order.html. /merch/orders (:437-445) rendert die eigenstaendige
orders.html mit Bestellungen des aktuellen Mitglieds. Nur der Detailpfad
/merch/order/<id> leitet nach Ownership-Abfrage in den heutigen Merch-Tab um.
Die zwei alten Uebersichts-/Bestellvorlagen deshalb nicht mit dieser
Detailweiterleitung verwechseln. orders.html:22 verlinkt zudem Neue Bestellung
auf den alten Bestellpfad; der Pfad ist nicht bloss eine unerreichbare Datei.

### Sieben Kandidaten mit lokalem Styling

btn-remove, form-control, form-group, price-display, remove-group,
variant-row-content und variants-container werden direkt in order.html:400-521
gestylt. Das CSS steht im Content-Block der Vorlage und kommt zusaetzlich zum
globalen V2-Bundle. Es beschreibt eigenes Grid, Felder, Entfernen-Schaltflaeche
und Breakpoints bei 1024/768px. Eine Suche nur in static/css/v2 waere hier falsch.

Das Inline-Script (:180-249) erzeugt weitere Variantenzeilen mit denselben
Klassen; removeVariantRow sucht den umgebenden variant-row und erhaelt mindestens
eine Zeile. Es ist eine zweite Steuerung neben dem bereits untersuchten
merch-order.js des heutigen Shop-Tabs. Funktions-/Datenfehler nicht erneut aus
diesem Strukturabgleich ableiten; bisherige Merch-Szenarien gelten weiter.

### Drei Strukturwrapper

price-group steht mit form-group zusammen (order.html:79 und dynamisch :229).
order-info und order-items in orders.html:45/70 umschliessen Infozeilen und
Cards. Keine eigene CSS-Regel fuer jeden Wrapper ist noetig, damit dessen
Unterelemente gestylt werden. Das Fehlen solcher Regeln beweist keinen Defekt.

### Empfehlung und verbleibende Grenzen

Erreichbare alte Bestellwege mit eigener Optik/Steuerung sind ein konkreter
Konsolidierungskandidat zu A-006/A-007/A-012. Spaeter einen verbindlichen
Bestell-/Bestelllistenpfad festlegen; bestehende Links, direkte URLs, POST-
Verarbeitung und Variantenbedienung beim Zusammenfuehren mit abnehmen.
Keine isolierte Loeschung von Templates oder Klassen und keine automatische
Weiterleitung bestehender POST-Anfragen ohne fachlichen Abgleich.

Kein neuer Render-/Browserlauf, keine Aussage ueber alle CSS-Variablen oder
visuelle Gleichwertigkeit. Klassifikation jetzt 7 reachable_local_style und
3 reachable_structure_wrapper; **54 statt 64 offene Detailfamilien** im
Rueckwaertsregister. Alle 117 Rohkandidaten bleiben nachvollziehbar.
Weiterhin 118 Befunde, keine App-Aenderung.

## Zehnter Registry-Durchlauf: Merch-Entscheidung und Places-Bausteine

### Nutzerentscheidung: alte Merch-Seiten entfallen spaeter

Der Nutzer benoetigt die alten Merch-Seiten nicht mehr. Damit ist ihr Erhalt
kein fachliches Ziel; die konkrete Entfernung gehoert zur spaeteren Umsetzung.
Gemeint sind hier die zuletzt untersuchten separaten Bestell-/Bestelllistenseiten,
nicht der aktuelle Shop, Bestellungen, Datenmodelle oder die gesamte Merch-Funktion.

Wichtige Abhaengigkeiten fuer das Umsetzungspaket:
- Aktueller Shop in member/merch/index.html:46 sendet POST an member.merch_order.
  Die alte GET-Seite und die benoetigte POST-Verarbeitung teilen dieselbe Route.
- member.py:419 leitet nach erfolgreicher Bestellung auf member.merch_orders;
  diese Rueckleitung muss in den aktuellen Bestelltab fuehren, wenn die alte Liste entfaellt.
- member/merch/index.html:335 verlinkt ebenfalls auf den alten Bestellpfad.
- Bestehende direkte URLs und der bereits weiterleitende Detailpfad beruecksichtigen.

Abnahme spaeter: aktueller Shop kann weiterhin bestellen, Bestellbestaetigung
landet im vorgesehenen Tab, keine UI-Links fuehren auf entfernte Vorlagen und
alte GET-URLs haben einen bewusst festgelegten Nachfolger. Daten und aktuelle
Bearbeitung nicht allein wegen des Alters benachbarter Dateien entfernen.
Keine App-Aenderung im fortgesetzten Audit.

### Zehn weitere Rueckwaertskandidaten

Sieben Familien sind im aktiven V2-CSS gestylt: places-details-header,
places-details-body, places-error, places-no-results, places-result-main,
places-result-secondary und close-btn (letzteres unter .places-details).
Definitionen in components.css:3013-3119; beide Templates admin/create_event.html
und events/edit.html erzeugen das Markup im eingebetteten Controller (:139-228).
Routes rendern diese Templates (admin.py:702, events.py:905/912), base.html
laedt das V2-Bundle. Keine verwaisten Klassen, keine separate Bibliothek noetig.
Der Places-Detailbereich ist hier ein eingefuegter Bereich, kein natives dialog.

save-details-btn ist der Klickanker fuer Uebernehmen (beide Templates :190/196 ff.).
Der Button besitzt btn, aber als zweite Stilklasse btn-success statt des aktiven
btn--success. btn-success findet sich im alten CSS; diese Templates laden es
nicht separat. Das ist eine konkrete Stilnamen-Abweichung, kein Beleg fuer einen
funktionslosen Button. Beim Zusammenfuehren der duplizierten Controller A-020
mit korrigieren und visuell abnehmen; keine neue Browsermessung hier.

form-help in admin/create_event.html:420 ist mit text-muted auf small kombiniert.
Keine eigene V2-Regel, aber vorhandenes Element-/Hilfsklassen-Styling. Nicht jeden
Struktur-/Hilfsnamen als fehlende Grosskomponente in die Registry aufnehmen.

Rueckwaertsregister jetzt **44 statt 54 offene Detailfamilien**; alle 117
Kandidaten erhalten. Weiterhin 118 Befunde, Erweiterung bestehender Konsistenz-/
Dokumentationsbefunde. Places-Netzwerk-/Validierungsprobleme bleiben gesondert
in den bereits vorhandenen Modul- und Integrationsberichten.

## Elfter Registry-Durchlauf: Diagramme, Navigation und Status

14 weitere Kandidaten nachverfolgt; 30 bleiben detail_review_open. Zwei der
zugeordneten Statusfamilien besitzen ausdruecklich eine offene Verhaltensfrage,
sind also nicht abgeschlossen. Keine neuen Browsermessungen.

- **Fuenf Chart-Familien:** ggl-chart, ggl-chart-expand-btn, ggl-chart-modal,
  events-stats-chart-expand-btn, events-stats-chart-modal. GGL-Template:174-261
  bindet Buttons/Modal/ggl-season.js ein; Controller:382-437 verschiebt den
  Chart-Knoten, erzeugt Platzhalter und stellt den Knoten beim Schliessen zurueck.
  Events-Template:554/738 und events-monatsessen-stats.js:548 ff. haben denselben
  Ablauf. components.css:1898-2112 enthaelt Styles/Fullscreen-/Viewportregeln.
  Aktive Bausteine, nicht alte Duplikat-Diagramme; bestehender Fokusbefund A-016
  bleibt. Gemeinsamen Modal-Vertrag spaeter konsolidieren.
- **Sechs Navigations-/Planungsfamilien:** dashboard-explore-nav kombiniert
  settings-nav (dashboard/index.html:231, components.css:5076). event-detail-nav
  (events/detail.html:32-45, base.css:293-301) zeigt Vorher/Weiter nur bei vorhandenen
  Nachbarn und uebergibt tab_param. events-planning-strip (:50) ist auf Admin/
  Organisator begrenzt und nutzt card/filter/disclosure. nav-icon/item/text stehen
  im Bottom-Nav-Partial und layout.css:328-372. Vorhandene aktive Anzeige beweist
  nicht korrekte Bereichszuordnung; A-002 bleibt.
- **Teilnahmestatus:** events/detail.html:283-288 setzt confirmed/declined/pending,
  components.css:2554-2581 definiert alle drei. Die Einordnung fehlender Antwort
  versus vorhandener Participation-Zeile bleibt die fachliche Frage aus A-044.

### Gezielte Restpruefung: PWA-Statusmeldungen bleiben moeglicherweise verborgen

technical.html:313-314 enthaelt #sw-status.update-status mit hidden und
status-text. pwa.js:1181 ff. setzt Text, Statusklasse und style.display='block',
entfernt hidden jedoch nicht. base.css:21-23 setzt [hidden] auf display:none
!important. Das ist ein konkreter statischer Sichtbarkeitskonflikt. Controller-
Aufrufe fuer Diagnose/Update/Push greifen auf diesen Bereich zu (:863 ff.).
Die Status-Styles stehen in static/css/pwa.css:135 ff.; im untersuchten
technical/base/Head-Partial-Ladeweg keine separate Einbindung dieser Datei.

Restaufgabe: gerenderte Technikseite mit isoliertem Statusaufruf pruefen,
computed display und Text erfassen; ohne echte Notification, SW-Neuregistrierung
oder Cache-Loeschung. Erst damit sichtbaren Ablauf und weitere Controller-
Einfluesse bestaetigen. Die beiden Klassen sind aktive Anzeigeanker mit
Nachpruefbedarf, keine Loeschkandidaten. Rueckwaertsregister status_display_followup.
Dieser Pruefpunkt ist noch kein zusaetzlicher nummerierter Befund; Katalog
weiterhin 118, keine Entwarnung durch die niedrigere Kandidaten-Restzahl.

## Zwoelfter Registry-Durchlauf: restliche 30 Rueckwaertsfamilien

Alle 117 Kandidaten haben jetzt eine begruendete Einordnung; keine Familie
bleibt ohne Detailansatz als detail_review_open. **Das ist ein Abschluss der
Ersteinordnung, keine Funktionsfreigabe.** Gezielte Nachpruefungen unten bleiben.

| Gruppe | Beleg und Einordnung |
|---|---|
| Acht Public-Familien | landing-footer/hero/hitlist-block/lead-quote/logo/next-essen sowie social-link/socials: public.css:16-56,70-196,253,487-529 und Public-Templates mit geladenem public.604da1b3.css. Aktive Unterbausteine der Landing/Hitlist, keine Altlasten. |
| Vier Shell-Familien | logo-link, user-actions, user-bar-logo, user-section in _user_bar.html:12-83 und layout.css:45-110. Gemeinsam mit User-Bar dokumentieren, nicht vier weitere Komponenten erfinden. |
| Sieben Event-/Workflow-Familien | billbro-workflow-block, events-archive-filter/panel/toolbar, events-cleanup-intro, events-stats-summary-insights, events-year-planning-list. Styles in components.css:4170/5071/5300/1870/2305; Archiv-Filter/Panel werden im Inline-Controller events/index.html:844-933 selektiert. Nicht jede Steuerklasse benoetigt einen eigenen CSS-Selektor. |
| Vier vorhandene Stilfamilien | flash-messages: layout.css:443/app.js:82; page-info: components.css:2353; page-subtitle: base.css:265; table: components.css:2362-2406, verwendet in admin/merch/article_detail.html:103. table bedeutet hier keine zusaetzliche Bootstrap-Abhaengigkeit. |
| Zwei Inline-Stile/Anker | backup-code in auth/backup_codes.html:30 inline gestylt, :73/124 fuer Kopieren/QR selektiert; member-name in admin/temp_password.html:42 inline gestylt. Keine echten Mitglieds-/Backup-Daten gelesen. |
| Zwei semantische Wrapper | card-description (edit_member_enhanced.html:143) und security-tips (member/security.html:148) sind Absatz bzw. Liste ohne gefundene eigene V2-Regel. Element-/Elternstyling bleibt vorhanden. Kein belegter Layoutdefekt allein daraus. |
| Drei gezielte Restfaelle | landing-pagination, flash-close, text-warning: siehe unten. |

### Konkrete Nachpruefliste statt weiterer unspezifischer Kandidaten

1. **PWA-Status:** zwei Familien update-status/status-text aus Durchlauf 11;
   hidden/display-Konflikt isoliert im Browser verifizieren, ohne SW-/Push-Aktion.
2. **Event-Paginierung:** landing-pagination in events/index.html:432 nutzt
   Styles aus public.css:442-459; kein Public-CSS-Link im untersuchten Event-
   Template/Head-Ladeweg gefunden. Gemeinsame btn/mt-6-Stile wirken weiterhin.
   Event-Archiv mit mehreren Seiten im Browser auf Anordnung/Umbruch pruefen.
3. **Flash-Schliessen:** Button flash-close im Partial, Styles layout.css:508 ff.;
   Quellensuche in JS ohne passenden Klassen-Handler. app.js initialisiert
   automatisches Ausblenden von flash-message. Klickverhalten im gerenderten
   DOM gezielt pruefen; automatisches Verschwinden ist kein Klicknachweis.
4. **Warnhinweis:** text-warning in admin/member_security_overview.html:68,
   keine eigene V2-Regel gefunden. Warntext steht trotzdem im DOM. Erwartete
   visuelle Kennzeichnung gegen verwendete Hilfsklassen konsolidieren.
5. **Backup-Code-QR:** showQRCode in auth/backup_codes.html baut einen Canvas
   mit Text '(In Produktion: Echter QR-Code)' statt QR-Encoding. Variable qrData
   wird aus Code-Text gebildet, aber nicht kodiert. Aktiven Trigger/Verhalten
   mit synthetischen Codes nachpruefen; keine realen Codes verwenden oder ausgeben.

Die ersten vier Punkte betreffen fuenf explizit als targeted_followup bzw.
status_display_followup markierte Familien. Der QR-Pruefpunkt steht zusaetzlich
bei inline_style_and_hook; Statuszahlen allein bilden Restarbeit nicht voll ab.
Diese Beobachtungen noch nicht als neue nummerierte Befunde konsolidiert.
Weiterhin 118 im Katalog, keine App-Aenderung. Auch noch offene Child-/Modifier-
Grenzen der 150 Registry-Zeilen bleiben bestehen.

## Durchlauf 13 – Drei konkrete Browser-Restfaelle geklaert

B-26 bis B-28 bestaetigen die offenen Punkte PWA-Status, Flash-Schliessen
und Backup-Code-QR. Neue Befunde A-119 bis A-121; insgesamt 121.
Original-App bleibt unveraendert. Belege und Testgrenzen in BROWSER_REVIEW.md
und browser/registry-followup.json. Die bisherige CSV-Triage bezeichnet die
Ersteinstufung; fuer diese drei Restfaelle gilt nun dieser Folgestand.

Noch offen: Event-Archiv-Paginierung mit mehreren Seiten, Warnstil
text-warning sowie weitere Child-/Modifier-Grenzen der 150 Registry-Zeilen.
Keine pauschale Komponenten- oder Modulfreigabe.

## Durchlauf 14 – Archivnavigation, Warnstil und Basisvarianten

B-29 prueft 27 synthetische vergangene Events (drei Seiten). Navigation
1 → 2 → 3 → 2 funktioniert; Suche Audit-Archiv setzt Seite 1 und bleibt
beim Weiterklicken erhalten. Paginierungsstil fehlt im geladenen Bundle:
display:block statt flex, gap:normal. Bei 320px kein Zeilenabstand zwischen
Zurueck/Weiter; bei 390/820/1440px kein Abstand zwischen Status und Weiter.
Neuer Befund A-122. Keine pauschale Fehlfunktion der Navigation behaupten.

B-30 rendert das originale Security-Template mit synthetischem MFA-Viewmodel
(keine echten Codes, kein MFA-Reset). text-warning hat keine V2-Definition;
computed color rgb(79,100,119), Gewicht 400 entsprechen dem normalen Absatz
(base.css:75). Text bleibt sichtbar und benennt den Zustand klar. Daher
Struktur-/Konsistenzbeobachtung zu A-007, kein neuer Sicherheitsfehler und
kein allein aus fehlender Farbe abgeleiteter Barrierefreiheitsverstoss.
Empfehlung: vorhandenes alert--warning mit explizitem Text verwenden, falls
Handlungsbedarf hervorgehoben werden soll; nicht nur eine neue Farbe erfinden.

### Varianten von btn, alert und empty-state

Reproduzierbarer lexikalischer Abgleich: check_atom_variants.py und
ATOM_VARIANTS.json. Ungehashte V2-CSS-Quellen gegen Templates und V2-JS;
auch Kommentare/Inline-Skripte werden erfasst, keine vollstaendige CSS-Analyse.

- btn--ghost: keine CSS-Regel gefunden; echter Consumer im Profil bei noch
  unbestaetigter Google-Adresse (profile.html:353) und dynamisch in toast.js:109.
  theme-toggle.js:7 ist dagegen nur ein Kommentar. Nicht gleich gewichten.
- btn--secondary: keine CSS-Regel; admin/index.html:133 im bedingten Drive-
  Re-Sync-Formular. Basisklasse btn bleibt wirksam. Kein Versand/Resync ausgeloest.
- btn--sm/lg/icon-only sind in V2 definiert, in der Basis-Registry nicht genannt.
  lg/icon-only ohne Consumer in diesem Scan; keine Loeschfreigabe daraus.
- alert: alle hier gefundenen konkreten Varianten/Unterelemente definiert;
  error/actions ohne lexikalischen Consumer. Keine pauschale Verhaltensfreigabe.
- empty-state: filtered/icon/message definiert und in Templates nachgewiesen;
  Variantenvertrag statisch abgeglichen, Viewport-/Screenreader-Zustaende offen.

Empfehlung: Ghost/Secondary-Verwendung fachlich einer vorhandenen Variante
zuordnen oder einen begruendeten gemeinsamen Stil definieren; Registry und
Aufrufer synchronisieren (A-007/A-012). Keine neuen Nummern fuer jede Variante.
Die fuenf konkreten Restpunkte aus Durchlauf 12 sind damit eingeordnet.
Weitere Child-/Modifier-Grenzen und die Gesamtmatrix bleiben offen.

## Durchlauf 15 – Karten-, Formular- und Tabellenvarianten

Sechs Familien mit 47 definierten und 36 verwendeten Unterelement-/Modifier-
Namen statisch abgeschlossen abgeglichen. Zwei fehlende Definitionen
(form-field__hint/checkbox), 13 Definitionen ohne Consumer-Treffer.
Manuelle Einordnung und konkrete Grenzen in
[STRUCTURAL_VARIANTS_REVIEW.md](STRUCTURAL_VARIANTS_REVIEW.md), Rohbelege in
STRUCTURAL_VARIANTS.json. Keine automatische Loeschfreigabe.

Sinnvolle Unterschiede: responsive Card-Footer sowie eine/zwei sticky
Tabellenspalten. Konsistenzluecken: hint/help, generische Merch-Toggle-Namen,
Card-Registry und unvollstaendig beschriebener Tabellen-Scroll-Wrapper.
A-005/A-007/A-012/A-018/A-019 praezisiert; weiterhin 122 Befunde.
Keine neuen Browserproben; konkreter Folgetest fuer Merch-Toggles und
Tastatur-Scroll in Tabellen festgehalten.

## Durchlauf 16 – Tastatur-Gegenpruefung

B-31 bestaetigt Enter/Space, aria-expanded, Ueberspringen verborgener
Merch-Felder und erhaltene Auswahl mit zwei Artikeln. Generische Namen
bleiben als Empfehlung bestehen. B-32/B-33 bestaetigen horizontales
Pfeiltasten-Scrollen in Archiv/Mitgliederliste. Fehlendes tabindex allein
war hier keine Bedienblockade. Mitgliederliste springt beim ersten
Tabelleneinstieg zu den Aktionen rechts: Orientierung gezielt verbessern.
Details und Grenzen: BROWSER_REVIEW.md, browser/keyboard-followup.json.
Weiterhin 122 Befunde; keine pauschale Freigabe anderer Tabellen/Browser.

## Durchlauf 17 – GGL- und Budgettabellen

B-34: GGL-Scroll-Huelle ohne tabindex in diesem Browser per Tab erreichbar,
Pfeilscroll und zwei sticky Spalten funktionieren. B-35/B-36: Budget
bearbeitbar sowie lesend ebenfalls per Tastatur scrollbar. Kontospalte
ist position:static und verlaesst beim Scrollen den sichtbaren Ausschnitt.
UI.md nennt Budget als sticky-first-Beispiel, aber index.html:661 nutzt
nur data-table/accounting-budget-table. Erweiterung A-012; Entscheidung
zur fixierten Kontospalte samt schmalen Viewports empfehlen. Keine neue
Befundnummer. Belege: BROWSER_REVIEW.md und browser/ggl-budget-keyboard.json.

## Durchlauf 18 – Befuellte Buchhaltungstabellen

B-37 bis B-40: echte Tastatur-Scrollproben als Admin an 390px. Journal/Belege
halten Identifikationsspalten fixiert, offene Posten scrollen die Bezeichnung
weg. Import-Historie hat reproduzierbare Ueberdeckung durch zu breite sticky
Dateispalte (A-123); 820px als Geometrievergleich. Die pauschale Empfehlung
„erste Spalte sticky“ reicht nicht: maximaler Platzverbrauch und Langdaten
muessen im Komponentenvertrag stehen. BROWSER_REVIEW.md und
browser/accounting-tables-keyboard.json dokumentieren Messwerte und Grenzen.
Gezielte lokale Probe der vier Tabellen abgeschlossen, insgesamt 123 Befunde.

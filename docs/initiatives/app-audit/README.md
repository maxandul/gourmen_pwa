# App-Audit und Zielbild fuer Refactoring / Redesign

## Begrenzte Umsetzung (11.10.2026)

Der Nutzer hat U1a, U1b und anschliessend die Fortsetzung mit U1c beauftragt. Die folgenden älteren Planungsstände
bleiben als Verlauf erhalten; daraus folgt keine Freigabe weiterer Pakete.

| Paket | Status | Branch und Nachweis |
|---|---|---|
| U1a / A-086: Daten bei Lesefehlern bewahren | Lokal umgesetzt und geprüft, 11.10.2026 | `codex/u1a-preserve-sensitive-data`; [Umsetzung und Tests](U1A_DATENERHALT.md) |
| U1b / A-081, A-110: Geheimnisse aus Logs entfernen | Lokal umgesetzt und geprüft, 11.10.2026 | `codex/u1b-secret-safe-logging`; [Umsetzung und Tests](U1B_LOGGING.md) |
| U1c / A-075: sensible Freigaben an die Anmeldung binden | Lokal umgesetzt und geprüft, 11.10.2026 | `codex/u1c-step-up-session`; [Umsetzung und Tests](U1C_STEP_UP.md) |


Stand: 2026-10-10. Status: **in_progress**. Auftrag: vollstaendiges, mehrstufiges Audit;
danach User-Feedback zu den Empfehlungen, erst anschliessend Umsetzung.

**Übergabe vorbereitet (11.10.2026):** Bestätigte Planung samt 19 Vorschaufragmenten unter `mockups/` gesichert. Aktuelle Startanweisung in [AGENT_HANDOFF.md](AGENT_HANDOFF.md); U1a lokal implementieren erst nach Absenden des Startauftrags im neuen Chat. Keine App-Änderung, kein Push oder Deploy in dieser Vorbereitung.

**Aktueller Einstieg:** [Konsolidierte Gesamtvorlage und Restabdeckung](RESTABDECKUNG_GESAMTVORLAGE.md).
**B01 läuft:** [Buchhaltungspraxis](BUCHHALTUNG_PRAXISABGLEICH.md) konkretisiert
Budget und Buchungen mit denselben 18 Posten, unverändert bestätigt, sowie
ein Vereinskonto ohne Kasse, Reise-Rechnungen/Kartenzahlungen, Kontoabgleich und
Budget/Ist/GV. Private Essen nur Betragserinnerung; frühere Zahlungskontrolle
im Mockup entsprechend vereinfachen. Keine fachliche Gesamtabnahme.
Reise-Mehrkosten bleiben privat ausserhalb der App. Belege sind grundsätzlich
optional; Buchungen und Zuordnungen ohne Rechnungsbeleg müssen möglich sein.
Jahreswechsel: Zahlungsprinzip als delegierte Standardwahl; Bankbuchungsdatum
bestimmt Jahres-Ist, offene Rechnungen/Forderungen separat ausweisen.
Weitere Zahlungsregeln bestätigt: Vereinsauslagen bei Erstattung im Ist,
Sammelzahlungen auf mehrere Forderungen/Mitglieder verteilen, Merch-Zuschuss
nicht als zusätzliche Ausgabe zählen. Budgetvorschlag/GV-Beschluss mit
Versionshistorie ohne zusätzliche App-Freigaberunde bestätigt. Mitgliederbeiträge
ebenfalls bestätigt; zusammengeführter Arbeitsablauf in B01 dokumentiert.
Neue Buchhaltungsübersicht `buchhaltung-praxis-entwurf.html` mit «sieht gut aus» gestalterisch bestätigt; Prüfumfang/Grenzen in B01. Merch-Darstellung bestätigt, Aufteilung auf 6650/6660 in B01 ausgearbeitet. Ergänzende
Prozessentwürfe: private Betragserinnerung, Buchung ohne Belegdatei und Revision
mit direkter Wiederöffnung/Admin-Stellvertretung jetzt nachgeführt und lokal
geprüft. Merch-Lieferausnahmen in `merch-lieferausnahmen.html` mit «ok» gestalterisch
bestätigt: Teilübergabe, Einzelstorno, Ersatz-Zustimmung und Lieferantenausfall.
Nächstes: gezielte Restabdeckung und Zusammenführung zur Gesamtvorlage.
Ältere Entwürfe inzwischen nachgeführt: Merch-Bestätigungen bei Wiederöffnung
erhalten, Abschluss bei Zahlung UND Übergabe, aktuelle Sitzung nach normaler
Passwortänderung erhalten, Getränke/Service optional und gleichgewichtet.
Merch-Preisregel je Ausführung bestätigt: Einkaufspreis minus Zuschuss, keine Marge; Ersatz mit geändertem Preis/Mitgliederanteil vor Zustimmung. Ausführungspreise und Ersatz mit Nachzahlung sind jetzt dargestellt und lokal geprüft. Öffentliche Aggregate sind ebenfalls dargestellt und mit fehlenden Kategorien sowie ohne Bewertungen lokal geprüft. Geldflussregeln G1–G3 bestätigt. K1-Rückzahlungsposten und ergänzende Nettoübersicht bestätigt. Beitragsausnahmen/Budgethistorie konkretisiert; B02 zum persönlichen Ausblenden privater Erinnerungen bestätigt. Gesamtvorlage mit Entwurfsverzeichnis, Fachstand, U1–U6-Abhängigkeiten und Abnahmekriterien zusammengeführt. Gemeinsame Merch-Beispielrunde, Ausführungspreise im Shop, Beitragsausnahmen, Budgethistorie und B02 jetzt lokal ergänzt und geprüft; Ergänzungen mit «passt» gestalterisch bestätigt. R13 zu sensiblen Angaben/Dokumenten/laufender Revision bestätigt. Erstes begrenztes Umsetzungspaket U1a (Daten bei Lesefehlern bewahren) samt Abnahmekriterien vorbereitet, nicht beauftragt; technische Verträge und Inhaltsfreigaben bleiben.
**F8-Teilentscheid:** Bewertungen nach dem Anlass ohne Frist abgeben/ändern;
Getränke und Service optional. Essen bleibt bestehendes Pflichtfeld.
Ausgefüllte Kategorien sind im Einzelgesamtwert gleich gewichtet.
Restaurantgesamtwert als gleichgewichtetes Mittel der Einzelbewertungen über
alle Besuche bestätigt; nur tatsächlich Anwesende dürfen bewerten.
GGL-Regeln ebenfalls bestätigt. Öffentliche Restaurantaggregate erlaubt,
Einzelbewertungen/Namen/Kommentare intern; künftige Events geschützt,
Instagram nur verlinkt. Siehe [Bewertung/GGL](BEWERTUNG_GGL_ENTSCHEIDUNGEN.md)
und PUBLIC_HOMEPAGE_ENTWURF.md. Nächster Fachblock: Buchhaltungspraxis B01.
**F7-Teilentscheide:** verbindliche Bestellung trotz vorläufigem Preis, keine
zweite Bestätigung des definitiven Preises; Bestätigungen bei Wiederöffnung
erhalten, unveränderte Bestellungen nicht erneut einreichen. Abschluss erst bei
Zahlung UND Übergabe und erledigten Liefer-/Erstattungsfällen. Lieferausnahmen
einschliesslich Ersatz mit Zustimmung und Rückzahlung bestätigt. Zuschuss je
Mitglied/Runde, gedeckelt auf Warenwert und nach Storno neu berechnet, bestätigt.
Änderungs-/Stornowege ebenfalls bestätigt: offen durch Mitglied, geschlossen
über Verwaltung/Admin, nach Lieferantenauftrag erst Möglichkeit klären;
bezahlte Änderungen mit Folgenvorschau. Massgeblich: Merch-Entwurfsdokumente.
**F1-Teilentscheid:** Mitglieder-Wiederherstellung und Sitzungsverhalten sind
in KONTO_ZUGANG_ENTWURF.md bestätigt; eigener Systemadmin-Notfallzugang ebenfalls:
separate Wiederherstellungscodes, technischer Hosting-Wiederherstellungsweg,
kein zusätzlicher Ersatzadmin. Auch das ergänzende F1-Regelpaket ist bestätigt:
erneute Bestätigung sensibler Änderungen, einmalige ersetzbare Links,
externe Zugangsentzüge und erneute Anmeldung anderer Geräte inklusive 2FA.
**F2-Entscheid:** Systemadmin mit bereichsübergreifendem Bearbeitungsrecht,
einschliesslich Finanzen; differenzierte Vorstand-/Funktionsrechte und gezielte
Zusatzrechte sind bestätigt, siehe [Rollenentscheidungen](ROLLEN_ENTSCHEIDUNGEN.md).
Revisionsbestätigung regulär durch Revisor, bei Bedarf stellvertretend durch
Systemadmin mit sichtbarem Vermerk; keine Selbstbestätigung des Schatzmeisters.
F6 geändert:
Systemadmin und Schatzmeister dürfen abgeschlossene Jahre jeweils allein mit
Grund wiederöffnen, ohne Revisorzustimmung. Erneute Revision/Berichtshistorie bleiben.
Die [Gestaltungsabdeckung](ABDECKUNG_GESTALTUNG.md) bleibt die Musterübersicht.
**Abstimmungsgrenze:** Zustimmung zu Mockups gilt fuer Gestaltung und gezeigte
Benutzerfuehrung. Der fachliche Gesamtabgleich der Buchhaltung mit der
Vereinspraxis bleibt ausdruecklich offen. F3–F6 sind separat besprochene Einzelregeln.
[Revision und Korrektur](REVISION_KORREKTUR_ENTWURF.md) sind am 11. Oktober 2026
hinsichtlich Darstellung und gezeigter Benutzerfuehrung bestaetigt.
[Direktes Bearbeiten und Warteschlangen](INLINE_WARTESCHLANGE_ENTWURF.md) sind
am 11. Oktober hinsichtlich Darstellung und gezeigter Benutzerfuehrung bestaetigt.
[Merch-Mitgliedersicht](MERCH_MITGLIEDER_ENTWURF.md) gestalterisch bestaetigt.
[Verwaltung der Bestellrunde](MERCH_VERWALTUNG_ENTWURF.md) ebenfalls gestalterisch
bestaetigt. [Dokumente und Uploads](DOKUMENTE_UPLOAD_ENTWURF.md), Block 4,
gestalterisch bestaetigt. [Konto und Zugang](KONTO_ZUGANG_ENTWURF.md), Block 5,
ebenfalls gestalterisch bestaetigt. [Oeffentliche Homepage/Restaurantliste](PUBLIC_HOMEPAGE_ENTWURF.md)
mit eigenstaendigem Design ebenfalls bestaetigt. [Systemzustaende/E-Mails](SYSTEM_EMAIL_ENTWURF.md)
sind jetzt ebenfalls gestalterisch bestaetigt. Restabdeckung R01–R12 ist konsolidiert;
[Chart-/Sonderseitenzuordnung](CHARTS_SONDERSEITEN_ZUORDNUNG.md) liegt vor:
zehn aktive Chartpositionen zugeordnet; GGL-Mehrpersonenvergleich und Ausgabenbalken
mit «ok» bestaetigt. [Finanzergänzung R07/R08](FINANZ_ERGAENZUNG_ENTWURF.md)
ist gestalterisch bestaetigt. [Verwaltungszugänge R10](VERWALTUNGSZUGAENGE_ENTWURF.md)
sind gestalterisch bestaetigt. [Seitengeltung R01–R05](SEITENGELTUNG_GESAMTVORLAGE.md)
ist konkretisiert, CSV mit 83 Baseline-Einträgen aktualisiert. Als Naechstes
Fachrunde F1/F2, F7, F8 und eigener Buchhaltungs-Praxisabgleich B01.
Prozessrestvarianten und Fachregeln bleiben offen; F1/F2 konkret vorbereitet.
Die vom Nutzer gewuenschte juengere
Ueberarbeitung wurde auf `phase/10-merch-wip` (`c90082e`) identifiziert.
[Zielversion und Altbestand](MERCH_ZIELVERSION.md): altes System spaeter operativ
stilllegen, Daten fuer moegliche Uebernahme erhalten. Jetzt keine App-Aenderung.
Alle 83 Inventar-Templates sind in [GESTALTUNGSZUORDNUNG.csv](GESTALTUNGSZUORDNUNG.csv)
16 primaeren Musterfamilien zugeordnet. Drei bestaetigte Beispielansichten decken
noch nicht alle Muster ab. Das gemeinsame Formularmuster ist bestaetigt; als Naechstes folgen
Tabellen/Charts und weitere Prozesse gemaess Abdeckungsuebersicht.
Keine neue umfassende Befundsuche; keine App-Umsetzung.
[Formulare und Bearbeitung](FORMULARE_ENTWURF.md) liegen jetzt als interaktiver
Event-/Profilentwurf vor und sind als gemeinsames Muster bestaetigt.
[Listen, Tabellen und Charts](LISTEN_CHARTS_ENTWURF.md) sind als Grundmuster
bestaetigt. Zuordnung aller bestehenden Charttypen und Mobile-Pruefung mit elf
Mitgliedern bleiben offen. [Buchhaltungsprozesse](BUCHHALTUNG_PROZESSE_ENTWURF.md)
zeigen Buchung, Belegeinreichung und Zahlungszuordnung; diese drei Entwuerfe
sind bestaetigt. Als Naechstes folgen Revision und finanzielle Korrekturen.

**Bisheriger Verlauf:** [Gesamtbeurteilung und vorlaeufiges Zielbild](GESAMTBEURTEILUNG.md).
**App-Wechsel:** [Uebergabe fuer ChatGPT Work](AGENT_HANDOFF.md). Fortsetzung in der
neuen ChatGPT-App ausdruecklich in **Work**, nicht in Codex; Sicherung auf eigenem Branch.
Die erste Entscheidungsvorlage buendelt alle 141 Befunde in sechs vorgeschlagene
Umsetzungspakete; die Einzelzuordnung steht im [Paketregister](PAKETREGISTER.csv).
Der Nutzer hat die Zusammenfuehrung und fruehe Zielbildarbeit beauftragt, keine
App-Umsetzung. [Oberflaechenentwuerfe und Fachentscheidungen](OBERFLAECHENENTWUERFE.md)
konkretisieren jetzt Dashboard, Eventdetail und Buchhaltung fuer Mobile/Desktop
mit Tablet-Regeln; interaktive Vorschau in der Work-Unterhaltung. Rueckmeldung zu
Gestaltung der Fachseiten und F1 bis F8 steht aus. Dashboard-Inhaltsreihenfolge,
Kopfzeile, Navigation und Abstaende inklusive Logo, Lucide-Icons, Theme-Schalter
und Kontomenue sind vom Nutzer bestaetigt. Das Eventdetail ist in diesem Rahmen
mit Teilnahme, BillBro und Bewertungen als interaktiver Entwurf ausgearbeitet.
Auch das Eventdetail-Layout wurde bestaetigt. Der Buchhaltungsentwurf liegt jetzt
im selben Rahmen vor und wurde ebenfalls bestaetigt. Jetzt liegt der Vorschlag
[BillBro-Schritte und Bedienverhalten](BILLBRO_INTERAKTION.md) mit durchspielbarer
Work-Vorschau vor. Interaktionsdetails (Schritte, Scroll/Fokus, Bearbeiten/Loeschen,
mobile Klickzustaende, Fehler/Ruecknahme) und Fachentscheidungen werden vor
einer Umsetzung abgestimmt; die Layoutzustimmung ersetzt diese nicht.
BillBro wurde anschliessend grundsaetzlich bestaetigt, mit Korrekturen zur
Anwesenheit, automatischem Abwesend-Label bei fehlender Antwort nach Rundenschluss,
Rueckkehr von Rechnung zu Angaben und Trinkgeld in Prozent statt Anteil pro Person
im Pruefschritt. Details in BILLBRO_INTERAKTION.md; weiterhin keine App-Umsetzung.
F3 wurde danach bestaetigt: bezahlte Betraege erhalten, Differenzen als offene
Betraege bzw. Rueckzahlungsbedarf, Schatzmeisterbestaetigung bei betroffenen
Vereinszahlungen und Bestaetigung privater Eingaenge/Rueckzahlungen durch den
Auslegenden. F4 Zahlwegwechsel wurde ebenfalls bestaetigt: vor Abschluss durch
Organisation aenderbar, danach ohne Zahlungen mit Vorschau und nachvollziehbarem
Forderungsersatz; mit Zahlungen nur ueber Korrekturablauf mit Schatzmeister und
privater Eingangsbestaetigung durch den Auslegenden. F5 Teil-/Ueberzahlungen wurde
bestaetigt: Restbetrag bei Teilzahlung, ausdrueckliche Zuordnung der Ueberzahlung
durch den Schatzmeister (Aufrundung, andere offene Forderung oder Rueckzahlung),
doppelte Zahlung zur Klaerung statt automatischer Einnahme. F6 wurde ebenfalls
bestaetigt: Buchungssperre ab Revisionsfreigabe, Hinweise vs. blockierende
Beanstandungen, begruendete Rueckgabe durch Revisor und erneute Pruefung.
Wiederoeffnung abgeschlossener Jahre nach spaeterer Nutzerkorrektur durch
Systemadmin oder Schatzmeister allein, ohne Revisorzustimmung, mit Grund;
bisherigen Bericht erhalten, neue Version nach Revision.
F1/F2 Zugang/Rollen, F7 Merch und F8 Bewertungen/GGL bleiben offen.
Restpruefungen bleiben im
[Pruefstand und Abschlussplan](COMPLETION_PLAN.md); K1 bis K5 sind keine Voraussetzung
mehr fuer eine erste Gesamtbeurteilung. Aeltere Fortsetzungsnotizen sind Verlauf.

## Auftrag und Entscheidungsrahmen

**Nutzerentscheidung im Audit:** Die alten Merch-Bestell-/Bestelllistenseiten
werden nicht mehr benoetigt und sind fuer die spaetere Entfernung vorgesehen.
Aktueller Shop postet noch auf member.merch_order; gemeinsame Bestellverarbeitung
erhalten oder umziehen, Links/Rueckleitungen anpassen. Audit wird fortgesetzt,
in diesem Schritt keine App-Loeschung. Details: UI_REGISTRY_REVIEW.md, Durchlauf 10.

Die gesamte App wird untersucht: oeffentlicher und geschlossener Bereich,
alle Module, Tabs, Navigation, Filter-/Bearbeitungsbereiche, Formulare, Cards,
Tabellen, Diagramme sowie Bereinigung, BillBro, Merch und Buchhaltung als Workflows.
Auch CSS-Wachstum, Altlasten, Backend, Performance, PWA, Sicherheit, Betrieb,
Tests und veraltete Dokumentation gehoeren dazu. Ein umfassendes Refactoring
und ein Frontend-Redesign sind moegliche Ergebnisse, noch keine beschlossene Umsetzung.

**Ausgeschlossen auf ausdruecklichen Nutzerwunsch:** das pausierte Sideprojekt
Essens-Pokemon/Game einschliesslich `docs/GDD_FOOD_POKEMON.md`,
`docs/GDD_FOOD_POKEMON_REVIEW.md` und `docs/capabilities/game.md`.
Diese Dateien bleiben unangetastet. Das Rohinventar behaelt seine 47 Dokumente;
der aktuelle Dokumentations-Pruefumfang umfasst **44 Dokumente**.

Bewertung nach Nutzen, fachlicher Korrektheit, Konsistenz und Wartbarkeit fuer
einen kleinen Verein. Bestehende Regeln duerfen begruendet infrage gestellt werden.
Unterschiede werden in fachlich notwendige Varianten und historisch entstandene
Abweichungen eingeordnet. Gemeinsame Ursachen erhalten einen Befund mit mehreren
betroffenen Stellen, statt einer Vielzahl redundanter Einzelprobleme.

## Verbindliche Pruefmethode

- **Inventar ist kein Review.** Eine Datei, Route oder Seite gilt durch Auflisten,
  Suchtreffer, Syntaxpruefung oder einen erfolgreichen GET nicht als durchgeprueft.
- Status je Pruefobjekt: inventarisiert, Code gelesen, Verhalten verifiziert,
  Befund dokumentiert, abgeschlossen; alternativ offen mit konkretem Grund.
- Befunde trennen: bestaetigter Fehler, bestaetigte Strukturbeobachtung mit
  Empfehlung, Verdacht, Produkt-/Designentscheidung. Beleg und Unsicherheit angeben.
- Keine Loeschfreigabe allein durch fehlende Textreferenzen: dynamische Verwendung,
  registrierte Routes, Redirects, alte Links, Cron und externe Clients beruecksichtigen.
- Performance getrennt als Code-Hypothese, lokale Messung oder Produktionsmessung
  ausweisen. Dateigroessen sind keine gemessenen Ladezeiten.
- Kein pauschales Versprechen absoluter Fehlerfreiheit: Ziel ist nachvollziehbare
  Vollstaendigkeit des Pruefumfangs mit offen ausgewiesenen Grenzen.
- Keine App-Aenderungen, Migrationen, Deploys oder produktiven Schreibaktionen im Audit.
  Bestehende lokale, nicht versionierte Dateien bleiben erhalten.
- User-Feedback folgt auf den konsolidierten Befundkatalog; Zwischenberichte sind
  Fortschrittsstaende und keine neue Freigabeanforderung fuer jeden Durchlauf.

## Durchlaeufe und Status

| Nr. | Durchlauf | Status | Abschlussbeleg / naechste Arbeit |
|---|---|---|---|
| 00 | Pruefkonzept, Repository-Inventar, Baseline | done | 442 Dateien, 83 Templates, 172 Deklarationen; 168 registrierte Regeln in Testing; 69 bestehende Tests bestanden. Grenzen unten. |
| 01 | Querschnitt: Shell, Navigation, Tabs, Komponenten, Assets | in_progress | Alle 83 Templates strukturell erfasst; 7 Standard-Tab-Systeme und 13 Filter-Fundstellen eingeordnet. COMPONENT_REVIEW.md. Vollstaendige Interaktionsmatrix offen. |
| 02 | Alle Module und fachlichen Workflows | in_progress | 44 Event-/Workflow-, 18 Merch-, 31 Buchhaltungs-, 29 Auth/MFA/Profil/Zugangs-, 51 Dokument- und 7 Public/Dashboard-Szenarien plus dokumentierte Folgeproben, 141 Befunde insgesamt. Restfaelle in den Modul-Teilberichten. Kein Modul vollstaendig abgeschlossen. |
| 03 | CSS-/JS-Abhaengigkeiten und Altlasten | in_progress | 77 CSS-/JS-Dateien, 4 gerenderte Ladelisten, CSS-Build textlich konsistent. FRONTEND_REVIEW.md trennt Quellen, aktive Einbindungen und Bereinigungskandidaten. Komponentenvergleich, Token-Abgleich und 5 isolierte Theme-Proben ergaenzt. Vollstaendige Kaskade und Browser-Coverage offen. |
| 04 | Responsive UX und Barrierefreiheit | in_progress | Erste lokale Browser-Reproduktionen, Event an 8 und Buchhaltung an 5 Viewports; Desktop-Clipping, Tab-/Dialog-/Labelprobleme bestaetigt. BROWSER_REVIEW.md; B-14 bis B-58 ergaenzen Formulare, 320px, sechs Buchungs-Viewports sowie Public-/Chartdialoge. Echte Geraete und Restmatrix offen. |
| 05 | Backend, Datenintegritaet und Sicherheit | in_progress | Isolierte Rechte-/Integritaetspruefungen in Modulberichten und AUTH_REVIEW.md; A-141 ueber normale Reset-Anfragen, administrativen Passwortreset und alte MFA-Reset-Links nach Neueinrichtung bestaetigt. Keine vollstaendige Sicherheitsabdeckung; CSRF, Rate-Limits, reale Konfiguration und weitere Grenzen offen. |
| 06 | Performance, PWA, Integrationen und Betrieb | in_progress | 10 SW-/Update-, 5 Offline-, 6 Service-Vertrags- und 9 Versand-/Cron-Grenzproben, 5 Zeitfenster-/Transport- und 6 Legacy-Notifier-Proben sowie 120 Render-Messungen zur SQL-Skalierung in 3 Durchlaeufen, einschliesslich historischer Saisons/Geschaeftsjahre. PWA_PERFORMANCE_REVIEW.md / QUERY_SCALING_REVIEW.md; echte Ladezeiten, weitere Grenzen und Betrieb offen. |
| 07 | Dokumentationsabgleich | in_progress | 47 Inventareintraege, davon 3 Game-Dokumente ausgeschlossen; 44 im Pruefumfang: 30 teilweise abgeglichen, 14 nur am Einstieg eingeordnet; 5 lokale Dokumentationsproben. DOCUMENTATION_REVIEW.md; Betriebsnachweise separat erfasst. |
| 08 | Gegenpruefung, Lueckenschluss und Zielbild | in_progress | K0 konsolidiert; Gesamtbeurteilung und Zuordnung aller 141 Befunde vorhanden. Am 2026-10-10 grafische Entwuerfe fuer drei Ansichten, Mobile/Desktop und Tablet-Regeln ergaenzt. Abstimmung, Einzelobjektabschluss und gezielter Lueckenschluss offen. |
| 09 | User-Feedback und Umsetzungspakete | in_progress | B01: ein Bankkonto, Reise/Bankabgleich/Budget/GV, private Essen nur Erinnerung, Reise-Mehrkosten ausserhalb App, Belege optional; alle 18 Posten fuer Buchungen/Budget bestaetigt. Zahlungsprinzip als delegierte Standardwahl dokumentiert. Erstattungen/Sammelzahlungen/Merch ohne Doppelzaehlung bestaetigt. Budgetvorschlag/GV-Beschluss mit Historie und Beitragsablauf bestaetigt; Gesamtprozess zusammengefuehrt. Neue Buchhaltungsuebersicht gestalterisch bestaetigt; Merch-Darstellung bestaetigt, Postenaufteilung ausgearbeitet; private Erinnerung/Belegoptionalitaet/Revision nachgefuehrt. Vier Merch-Lieferausnahmen gestalterisch bestaetigt; Merch-Hauptregeln/Sitzungserhalt/optionale Bewertung nachgefuehrt; Merch-Preisregel je Ausfuehrung ohne Marge bestaetigt und visuell nachgefuehrt; oeffentliche Aggregate inklusive fehlender Angaben nachgefuehrt und lokal geprueft; Geldflussregeln G1-G3 bestaetigt; K1-Rueckzahlungsposten/Nettoansicht bestaetigt; Beitragsausnahmen/Budgethistorie konkretisiert, B02 privates Ausblenden bestaetigt; Gesamtvorlage zusammengefuehrt, gezielte Merch-/B01-Entwurfsharmonisierung lokal ergaenzt und geprueft; Ergaenzungen gestalterisch bestaetigt; R13-Rechtepaket bestaetigt; U1a als begrenzter Umsetzungseinstieg vorbereitet, nicht beauftragt; technische Vertraege/Inhaltsfreigaben bleiben. Planung samt 19 Mockups und Startanweisung fuer neuen Umsetzungschat gesichert. Keine Umsetzungsfreigabe in diesem Chat. |

## Abdeckungsmatrix fuer vertiefte Durchlaeufe

Alle folgenden Bereiche sind **noch nicht vollstaendig geprueft**:

| Bereich | Zusaetzlich zum normalen Anzeigen/Bedienen zu pruefen |
|---|---|
| Public / Login | Einstieg, Rueckkehr zur App, Suche/Sortierung/Pagination, SEO, Drittinhalte, Session-Zustaende |
| Dashboard | Relevanz, Priorisierung, zeitliche Hinweise, Links, offene Posten, rollenabhaengiger Inhalt |
| Events | Kommend/Archiv/Statistik, Erstellung/Bearbeitung, Planung, Sichtbarkeit, Vorher/Weiter, Teilnahme, Ratings, Hamburg-Sonderseite |
| BillBro / GGL | Phasen, Teilnehmerrollen, Schaetzung, Rundung, Finalisierung, Ruecknahme, Zahlweg, Ranggleichheit, Saison, Diagramme |
| Verein / Mitglieder | Profil, sensible Felder, Administration, Onboarding, Rollen/Funktionen, Deaktivierung |
| Technik / Sicherheit | Installation, Push, Kalender, 2FA, Reset, Backup-Codes, Step-Up, Logout und Accountwechsel |
| Dokumente | Ordnernavigation, Suche, Upload, Rename/Move, Archiv/Restore, Hard-Delete, Synchronisierung, externe Fehler |
| Merch | Sortiment, Varianten, Bestellung/Bearbeitung, Admin-Verarbeitung, Zahlung/Lieferung; dokumentierte vs. implementierte Workflows |
| Buchhaltung | Journal, Belege, Konten, Budget, Import/Dedup, Teilzahlung, Jahresabschluss, Revision, Exporte, Korrekturen |
| Bereinigung | Schrittfolge, Vorschlaege, Ueberspringen, Zurueck/Undo, Abbruch und Wiederaufnahme |
| Hintergrund/Betrieb | Reminder, Mail, Push, ICS, Health, Deployment, Migrationen, Backups, Konfiguration, verwaiste Helfer |

Fuer jede Seite: Rollen und Berechtigungen; leer/ein/viele/lange Inhalte;
Erfolg/Validierungsfehler/Serverfehler; Links und Browser-Zurueck; Speichern,
Doppelklick, Abbruch und Wiederaufnahme soweit anwendbar.

Visuelle Zielmatrix: 360/390 px Mobile, 768/820 px Tablet hochkant,
1024 px Tablet quer bzw. Uebergang, 1280/1440 px Desktop; ausserdem direkt
unter/auf/ueber tatsaechlichen CSS-Breakpoints. Reflow bei 320 CSS-px,
200%-Zoom, Hell/Dunkel, reduzierte Bewegung, Tastatur und Touch.
Simulation und echte Geraete strikt unterscheiden; Safari/iOS/PWA-Pruefungen
bleiben offen, solange kein entsprechender Testnachweis vorliegt.

## Baseline und Grenzen

- Code: `bf4d84aad2725070cf77f6d9fc5bc818a5e0a43f`, Branch `master`.
- 436 versionierte + 6 vorhandene nicht ignorierte lokale Dateien. Audit-Ausgaben
  selbst sind aus dem Inventar ausgeschlossen. Ignorierte Laufzeitdaten, venv,
  Datenbanken und private Schluessel gehoeren nicht zum Quellcodeinventar.
- Vorhandene lokale Dateien: build_logs.txt, drei Game-Konzeptdokumente,
  zwei pwa-Hashkopien. Sie sind nicht als produktiv eingesetzte Features gewertet.
- 172 AST-Route-Deklarationen sind **nicht** 172 produktive Endpunkte.
  Testing registriert 168 Regeln inkl. Static; Fallback-App und nicht registrierte
  Demo-/Stats-Blueprints erklaeren unterschiedliche Erfassungsmengen mit.
- Lokaler venv-Launcher funktioniert in dieser Sitzung nicht (referenzierter
  Python-Pfad nicht verfuegbar). Bestehende venv-Pakete laufen mit gebuendeltem
  Python 3.12.14. Kein Nachinstallieren von Dependencies.
- Testumgebung: `.env`-Laden unterbunden, Anwendungs-ENV entfernt, SQLite nur
  im Arbeitsspeicher, ausgehende Sockets gesperrt. Bestehende Tests unveraendert.
- **69 passed, 287 warnings**, 37.76 Sekunden. Kein Coverage-Prozent gemessen;
  kein Beleg fuer vollstaendige Fach-/Sicherheitsabdeckung. SQLite ersetzt keine
  PostgreSQL-Migrations-/Constraint-Pruefung. CSRF/Rate-Limit sind in Testing aus.
- 18 zusaetzliche GET-Aufrufe mit einem synthetischen Mitglied/Organisator:
  Routing/Rendering-Baseline, keine vollstaendigen Workflow- oder Browser-Tests.
- Erste lokale Browser-JavaScript-/Viewport-Pruefungen sind dokumentiert.
  Production-Commit, produktive Konfiguration, echte Geraete, reale Ladezeiten
  und externe Integrationen bleiben ungeprueft.

## Dateien / Fortsetzung

- [Dokumentationsabgleich](DOCUMENTATION_REVIEW.md), [47 Dokument-Pruefstaende](DOCUMENT_REVIEW_REGISTER.csv) und [offene Betriebsnachweise](OPERATIONS_EVIDENCE_REGISTER.md).

- [Wiederverbindung, Integrationen und Betrieb](INTEGRATION_OPERATIONS_REVIEW.md):
  [5 Offline-Proben](OFFLINE_RETURN_CHECKS.json) und
  [6 Service-Vertragsproben](INTEGRATION_CONTRACT_CHECKS.json) sowie [9 Versand-/Cron-Grenzproben](NOTIFICATION_BOUNDARY_CHECKS.json) und [5 Zeitfenster-/Transportproben](REMINDER_WINDOW_CHECKS.json) sowie [6 Legacy-Notifier-Proben](LEGACY_NOTIFIER_CHECKS.json); A-107 bis A-118.

- [Erste Befunde](FINDINGS.md): vorlaeufig, kein abschliessender Auditbericht.
- [PWA und Performance](PWA_PERFORMANCE_REVIEW.md): Cache-/Offline-/Update-Vertrag,
  [10 isolierte Algorithmus-Szenarien](SW_STRATEGY_CHECKS.json), `check_sw_strategies.cjs`.
- [Datenbank-Skalierung](QUERY_SCALING_REVIEW.md): vier Datenbestaende, sechs Seiten,
  je zwei frische Sessions; [48 Messungen](QUERY_SCALING_CHECKS.json), `check_query_scaling.py`.
  Zweiter Durchlauf: [48 weitere Messungen](COMMERCE_SCALING_CHECKS.json) fuer
  Bestellungen, Claims und Buchung-/Belegpaare, `check_commerce_scaling.py`.
  Dritter Durchlauf: [24 Historien-Messungen](HISTORY_SCALING_CHECKS.json) fuer
  mehrere Saisons/Geschaeftsjahre, `check_history_scaling.py`.
- [Frontend-Quellen und Altlasten](FRONTEND_REVIEW.md): Ladewege, Build-Gegenpruefung,
  Controller und Bereinigungskandidaten; [Asset-Nachweise](FRONTEND_ASSET_CHECKS.json).
- [Public und Dashboard](PUBLIC_DASHBOARD_REVIEW.md): Sichtbarkeit, Suche,
  Datumsgrenzen; [7 Szenarien](PUBLIC_DASHBOARD_CHECKS.json), `check_public_dashboard.py`.
- [Dokumentverwaltung](DOCS_REVIEW.md): erste Rechte-/Fehlerpfade,
  [7 isolierte Szenarien](DOCS_CHECKS.json), `check_docs_workflows.py`.
  [7 Upload-/Sync-Grenzfaelle](DRIVE_BOUNDARY_CHECKS.json), `check_drive_boundaries.py`.
- [Anmeldung und Profil](AUTH_REVIEW.md): erste Sitzungs-/Resetpruefungen,
  [7 isolierte Szenarien](AUTH_CHECKS.json), `check_auth_workflows.py`.
  [7 weitere MFA-Szenarien](MFA_CHECKS.json), `check_mfa_workflows.py`.
  [8 Profil-/Admin-Szenarien](PROFILE_CHECKS.json), `check_profile_workflows.py`.
  [7 Zugangs-/Verwaltungsszenarien](ACCESS_CHECKS.json), `check_access_lifecycle.py`.
- [Komponentenvergleich](COMPONENT_REVIEW.md): Tab-/Filter-/Formular-/Dialog-/Workflow-Muster.
- [Merch-Teilbericht](MERCH_REVIEW.md): Bestellung, Varianten, Status und Claims;
  [18 isolierte Szenarien](MERCH_CHECKS.json), `check_merch_workflows.py`.
- [Buchhaltungs-Teilbericht](ACCOUNTING_REVIEW.md): Betraege, Jahreszuordnung,
  Sperren, Belegzuordnung und erste Rechtepruefung;
  [7 isolierte Szenarien](ACCOUNTING_CHECKS.json), `check_accounting_workflows.py`.
  Dazu [12 Import-/Zuordnungsszenarien](BANK_CHECKS.json), `check_bank_workflows.py`.
  [7 Revisions-/Berichtsszenarien](REVISION_CHECKS.json), `check_revision_workflows.py`;
  darin eine Matrix mit 16 Rollen-/Aktionskombinationen.
  [5 Beleg-/Korrekturszenarien](RECEIPT_CHECKS.json), `check_receipt_workflows.py`.
- [Browserprotokoll](BROWSER_REVIEW.md): Reproduktionen, Viewport-Messungen und Screenshots.
- [Events und Workflows](EVENT_WORKFLOW_REVIEW.md): vertiefter Teilbericht,
  mit [18 isolierten Szenarien](EVENT_WORKFLOW_CHECKS.json); reproduzierbar via
  `check_event_workflows.py`. Fehlerbelege sind keine bestandenen Regressionstests.
  [Weitere 17 Szenarien](EVENT_FOLLOWUP_CHECKS.json) via `check_event_followup.py`
  erfassen Bewertungen, Event-Erstellung/Planung und GGL-Vergleiche.
  [9 Grenzfallpruefungen](EVENT_BOUNDARY_CHECKS.json) via `check_event_boundaries.py`
  erfassen Public-/Statistik-Datenfluss, Reminder und Loesch-/Ownership-Regeln.
- [Praezisierte Template-Erfassung](UI_PATTERN_SURVEY.csv): exakte Klassentokens;
  Details in UI_PATTERN_LOCATIONS.json, Zusammenfassung in UI_SURVEY_SUMMARY.json.
- [Dateiinventar](FILE_INVENTORY.csv): gesamter erfasster Repository-Bestand.
- [Route-Inventar](ROUTE_INVENTORY.csv): Deklarationen mit Decorators und Code-Ort.
- [Template-Matrix](TEMPLATE_MATRIX.csv): Suchmuster fuer vergleichbare Oberflaechen.
- [CSS-Inventar](CSS_INVENTORY.csv), [Dokumente](DOC_INVENTORY.csv), [Asset-Pruefungen](ASSET_CHECKS.csv).
- [Zusammenfassung](INVENTORY_SUMMARY.json), [Runtime-Pruefungen](RUNTIME_CHECKS.json), [Testergebnis](TEST_RESULTS.txt).
- `collect_inventory.py` erzeugt Rohinventare neu; dabei gesetzte Review-Status sind
  Startwerte. Manuelle Review-Fortschritte hier und im Befundkatalog pflegen,
  bis ein eigenes, beim Regenerieren erhaltenes Pruefregister eingefuehrt ist.
- `run_existing_tests.py` und `check_runtime.py` dokumentieren die isolierten Pruefungen.

Historische Fortsetzungsnotiz (aktuelle Reihenfolge: COMPLETION_PLAN.md): Paket D-05,
[UI-Registry-Abgleich](UI_REGISTRY_REVIEW.md)
erfasst alle 150 Tabellenzeilen als Suchstellenkarte und dokumentiert erste
manuelle Gegenpruefungen. Zweiter Durchlauf verfolgt Body/ID/Makros,
BEM-Kurzformen, Topbar/Dialogpause, Tool-Strip und sechs Legacy-CSS-Familien nach.
Dritter Durchlauf: Cards/Formulare/Tabellen/Hub weiter nachverfolgt;
Rueckwaertssuche mit 117 Kandidatenfamilien und ersten manuellen Einordnungen
(keine Fehlerzahl). Vierter Durchlauf: Bereichskomponenten und gemeinsame
Workflow-Bausteine nachverfolgt. Fuenfter Durchlauf: Public-Navigation und
Fehler-/Offline-Ladewege statisch abgeglichen. Einzelne Child-/Modifier-/
Basisdetails und Rueckwaertskandidaten bleiben offen. Sechster Durchlauf:
[Abdeckungsmatrix](UI_REGISTRY_COVERAGE.csv) fuer alle 150 Zeilen erstellt;
Siebter Durchlauf: auch 038/057/058/068 nachverfolgt, keine rein kartierte Zeile
mehr. 122 Codepfade teilweise geprueft, 5 Dokuabweichungen, 18 fehlende Merch-
Eintraege, 5 CSS-Kandidaten. Achter Durchlauf: alle 117 Rueckwaertskandidaten
in UI_REGISTRY_REVERSE_TRIAGE.csv eingeordnet; 64 Detailpruefungen explizit offen,
Rest auf Teil-Dokumentation, Hooks, Hilfsstile, 6 Registry-Luecken, 2 Suchartefakte
und 20 historische Hamburg-Familien verteilt. Weitere Registry-Varianten offen.
Neunter Durchlauf: zehn alte Merch-Kandidaten mit erreichbaren Routen und
lokalem CSS/Struktur nachverfolgt; aktuell noch 54 offene Detailfamilien im
Rueckwaertsregister. Alte Seiten sind keine verwaisten Dateien.
Zehnter Durchlauf: Places-/Formhilfen-Gruppe nachverfolgt, aktuell 44 offene
Detailfamilien. Nutzerentscheidung zum Entfall alter Merch-Seiten oben erfasst.
Elfter Durchlauf: Chart-/Navigations-/Statusgruppe nachverfolgt, 30 noch nicht
eingeordnete Detailfamilien; zusaetzlich zwei Statusanker mit gezielter offener
Browserfrage (hidden gegen display:block), siehe UI_REGISTRY_REVIEW.md.
Zwoelfter Durchlauf: alle 117 Rueckwaertsfamilien erstmals eingeordnet;
gezielte Restliste statt unspezifischer Kandidaten: PWA-Status, Event-Paginierung,
Flash-Schliessen, Warnstil, Backup-Code-QR. Keine Funktionsfreigabe; weitere
Registry-Varianten offen. Details im zwoelften Registry-Durchlauf.
D-01/D-02 als Namensabgleich und D-03 als statischer Feld-/Seed-Vertragsabgleich abgeschlossen, siehe DOCUMENT_CLOSURE_MATRIX.md; echte PWA-Update-/Offline-Gegenpruefung im Rahmen
der verfuegbaren Browserfunktionen bleibt offen.
B-21 bis B-25 ergaenzen Datei-Pflichtfeld,
Public-Drawer und Accounting-Chart; GGL mit Verlaufsdaten sowie verschachtelte
Drive-/Kalenderdialoge bleiben fuer spaetere Browserdurchlaeufe offen.
Systemtheme-Wechsel im Browser weiter offen. Offene fachliche Grenzen
aus allen Modul-Teilberichten bleiben fuer gezielte Gegenpruefung erfasst;
kein Modul ist durch die bisherigen Szenarien pauschal abgeschlossen.
Pro Modul Rollen, Fehler-/Leer-/Langdatenzustaende,
Formularschritte und Rueckleitungen pruefen. Die Browser-Testbasis hat vier Rollen;
bisherige Browser-Interaktionen erfolgten hauptsaechlich als Admin sowie ausgeloggt.
Die neuen Workflow-Reproduktionen nutzen Organisator und regulaeres Mitglied.
Alle Befunde einschliesslich Layoutproblem A-014 bleiben unveraendert im App-Code.

Dreizehnter Registry-Durchlauf: B-26 bis B-28 bestaetigen PWA-Status,
Flash-Schliessen und QR-Platzhalter (A-119 bis A-121). Belege in
BROWSER_REVIEW.md und browser/registry-followup.json. Event-Paginierung,
Warnstil und weitere Child-/Modifier-Pruefungen bleiben offen.

Vierzehnter Registry-Durchlauf: Archivnavigation und Warnzustand mit B-29/B-30
geprueft. A-122 zur fehlenden Paginierungsgestaltung; Seitennavigation und
Suchfiltererhalt positiv. Basisvarianten btn/alert/empty-state statisch
vertieft (ATOM_VARIANTS.json); Ghost/Secondary ohne CSS-Definition, Warntext
bleibt lesbar. Die gezielten Restpunkte aus Durchlauf 12 sind eingeordnet;
weitere Komponentenvarianten und die umfassende Interaktionsmatrix bleiben offen.

Fuenfzehnter Registry-Durchlauf: Namens-/Definitionsabgleich von sechs
Karten-/Formular-/Tabellenfamilien abgeschlossen (47 Definitionen,
36 verwendete Varianten). STRUCTURAL_VARIANTS_REVIEW.md trennt sinnvolle
Varianten, Inkonsistenzen und 13 Kandidaten ohne Consumer-Nachweis.
Weiterhin 122 Befunde; Interaktionsabdeckung bleibt separat offen.

Sechzehnter Registry-Durchlauf: B-31 bis B-33 pruefen Merch-Karten als
regulaeres Mitglied und Tabellen als Mitglied/Admin. Tastaturbedienung und
Erhalt lokaler Artikelauswahl positiv; generische Toggle-Namen und horizontaler
Fokussprung in der Mitgliederliste als Orientierungsthemen dokumentiert.
Weiterhin 122 Befunde. GGL-/Buchhaltungstabellen, andere Browser und
Screenreader bleiben offen. Beleg: browser/keyboard-followup.json.

Siebzehnter Registry-Durchlauf: B-34 bis B-36 bestaetigen Tastatur-Scroll
in GGL (Mitglied) und Budget (Admin/Revisor). GGL haelt Rang/Name sticky;
Budget-Konto scrollt entgegen dem Registry-Beispiel mit (Erweiterung A-012).
Weiterhin 122 Befunde. Journal/Belege/offene Posten/Import-Historie sowie
Langdaten und weitere Browser bleiben explizit offen.

Achtzehnter Registry-Durchlauf: B-37 bis B-40 schliessen die gezielte lokale
Tastaturprobe fuer befuelltes Journal, Belege, offene Posten und Import-Historie
als Admin ab. Neuer A-123: lange sticky Import-Dateispalte verdeckt weitere
Spalten/Aktion auf schmalem Display. Insgesamt 123 Befunde. Rollen-/Browser-/
Langdatenmatrix bleibt offen; Belege in browser/accounting-tables-keyboard.json.

Kalender-Vertragsdurchlauf: fuenf isolierte Proben zu Cache und SEQUENCE;
A-124/A-125, insgesamt 125 Befunde. CALENDAR_CONTRACT_REVIEW.md trennt
bestaetigte Service-Abweichungen von ungeprueftem Client-/Produktivverhalten.
Dokumentations-Abschlussmatrix auf aktuellen UI-Pruefstand nachgezogen.

Zweiter Kalenderdurchlauf: CAL-06 bis CAL-12 (sieben Gruppen) pruefen
Datumsgrenze, Board-Sichtbarkeit, Entpublizieren, sieben einzelne Felder,
Organisator-Rufname, vier Zeitumstellungsdaten und ungueltigen/inaktiven Zugang.
Positive Inhalts-/Zugangsproben; A-125 um abhaengigen Profilnamen erweitert.
Weiterhin 125 Befunde; echte Kalender-Clients und komplette Mutationsrouten offen.

Dritter Kalenderdurchlauf: CAL-13 bis CAL-20 pruefen originale Event-Edit-/
Delete-POSTs. A-125 (Notiz-Version) und A-026 (ignorierte Sichtbarkeit) bestaetigt;
stabile UID, einmaliges Hochzaehlen bei Mehrfachaenderung und ein Rechtefall
positiv. 20 Kalender-Pruefgruppen insgesamt, weiterhin 125 Befunde.

Dokumentdialog-Durchlauf: B-41 bis B-44 pruefen Upload/verschachtelten
Ordnerpicker an 390px, Rueckkehr/Abbruch und simulierten Ladefehler. A-126
zu fehlenden semantischen Aufklapp-/Auswahlzustaenden; insgesamt 126 Befunde.
Kein Upload; sichtbarer Zielname und Entwurfserhalt positiv.

Upload-Fehlerdurchlauf: B-45/B-46 bestaetigen Entwurfsverlust ohne Datei
(A-127) und fehlende Root-Picker-Fehlermeldung (A-128). Insgesamt 128 Befunde.
Originalcontroller mit lokal simuliertem 503, kein echter Upload.

Picker-Wiederaufnahme: B-47 bis B-49 bestaetigen erfolgreichen erneuten
Versuch nach Root-Fehler, fehlerhafte Hierarchiereihenfolge (A-129) und
unsichtbare Auswahl nach Zuklappen. Insgesamt 129 Befunde. Kein Upload;
weitere Zweig-/Daten-/Rollenvarianten bleiben offen.

Zweig-Durchlauf: B-50 bis B-52 pruefen unabhaengiges Zuklappen, erneuten
Ladeversuch bei anhaltendem Unterordnerfehler und fehlende Leerzustandsmeldung.
A-126 ergaenzt, weiterhin 129 Befunde. Zwei befuellte Nachbarzweige und
verzoegerte Antworten bleiben offen; keine App-Aenderung und kein Upload.

Asynchroner Picker-Durchlauf: PICK-01 bis PICK-04 am Originalcontroller mit
synthetischem DOM und kontrollierter Antwortreihenfolge. Zwei befuellte Zweige
und veraltete Unterordnerantwort positiv; parallele Root-Anfragen duplizieren
Zeilen und fordern nach Schliessen erneut Oeffnen an (A-130). Insgesamt 130
Befunde. Echte Browser-Bestaetigung dieser Rennen bleibt offen. Belege:
PICKER_ASYNC_CHECKS.json und DOCS_REVIEW.md.

Root-Rennen im Browser: B-53/B-54 bestaetigen A-130 mit nativen Dialogen,
zwei Root-Zeilen und Wiederoeffnen nach Schliessen samt Fokuswechsel. Lokale
synthetische Verzoegerung, kein Upload. Weiterhin 130 Befunde. Browserbeleg
fuer PICK-03/04 ergaenzt; andere Ablaufvarianten und Browser bleiben offen.

Dokumentensuche: acht isolierte Gruppen zu leeren/fehlgeschlagenen Suchen,
Mindestlaenge, Ordnerlinks und Suchpaginierung. A-131 (globale Begrenzung vor
Ordnerfilter) und A-132 (widerspruechliche Leerzustaende), insgesamt 132 Befunde.
Originalservice mit synthetischen API-Seiten; Suchbegriff bei Fehler erhalten.
DOCS_SEARCH_CHECKS.json und DOCS_REVIEW.md; reale Google-Suche/Browser offen.

Zweiter Suchdurchlauf: sechs Gruppen zu verschachtelten Suchbereichen,
Sonderzeichen, leerer API-Seite mit Fortsetzung, Folgefehlern und Pfadaufwand.
A-091 um Suchfehler erweitert; A-133 zu 100 redundanten Pfadabfragen bei 50
Treffern im gleichen zweistufigen Pfad. Insgesamt 133 Befunde. API-Aufrufe
isoliert gezaehlt, keine gemessene Produktionslatenz. DOCS_SEARCH_BOUNDARY_CHECKS.json.

Dateiaktionen: gemeinsame Dialoge von Liste/Detail quellenbasiert verglichen;
zehn Routenproben zu Erfolg, behandeltem Fehler und fehlendem Ziel. A-134 zum
fehlenden Dateikontext; A-127 um Entwurfserhalt erweitert. Insgesamt 134 Befunde.
DOCS_ACTION_CHECKS.json und DOCS_REVIEW.md. Mutationsservices ersetzt; keine
echte Dateiaenderung, Browser-/Service-Erfolgsabnahme weiterhin offen.

Aktionsdialoge im Browser: B-55 bis B-58 als regulaeres Mitglied mit zwei
synthetischen Dateien. A-134 bestaetigt; Abbruch/Escape und Dateizuordnung beim
Wechsel positiv. Weiterhin 134 Befunde. Kein Submit, Detail-/Mobil-/Fehlerpfade
weiter offen. browser/docs-actions-followup.json und BROWSER_REVIEW.md.

Dokument-Lifecycle: acht Originalservice-Proben mit zustandsbehaftetem Fake-Drive
und In-Memory-DB. Vier normale Erfolgswege mit passendem Audit-Eintrag positiv.
A-135 (Restore innerhalb Archiv) und A-136 (veralteter DB-Ordner bei bereits
erreichtem Ziel), insgesamt 136 Befunde. DOCS_LIFECYCLE_CHECKS.json; externe
Teil-/DB-Fehler und Parallelitaet weiterhin offen.

Dokument-Teilfehler: fuenf Gruppen nach externem Erfolg, bei DB-Commit-/Audit-
Insertfehlern. Wiederholung erweitert A-136; neuer A-137 zur fehlgeschlagenen
Session nach unterdruecktem Audit-Fehler. Insgesamt 137 Befunde. Original-
Services, Fake-Drive und In-Memory-DB; globale Audit-Aufrufer/Produktion offen.
DOCS_PARTIAL_FAILURE_CHECKS.json und DOCS_REVIEW.md.

Audit-Querschnitt: fuenf weitere Originalrouten-Gruppen ausserhalb Dokumente.
Login-/Event-Fehler erweitern A-137; Kalender und Login mit next bleiben
funktionsfaehig ohne Protokoll. Neuer A-138 zur RSVP-Umkehr bei Wiederholung
nach bereits gespeichertem Zustand. Insgesamt 138 Befunde. AUDIT_FAILURE_REVIEW.md
und AUDIT_FAILURE_ROUTE_CHECKS.json; weitere Audit-Aufrufer/Produktion offen.

Audit-Transaktionen: 64 direkte Aufrufstellen in sieben Dateien inventarisiert,
drei Originalhelfer-Proben zu offenen Fachaenderungen/Commit/Rollback. A-137
um die Transaktionsgrenze praezisiert, weiterhin 138 Befunde. Keine pauschale
Verhaltensfreigabe aller Aufrufer. AUDIT_CALL_INVENTORY.json,
AUDIT_TRANSACTION_CHECKS.json und AUDIT_FAILURE_REVIEW.md.

Mitgliederanlage: fuenf Originalrouten-Proben mit abgefangenem Versand.
A-139 zur Mailbeauftragung vor dauerhaftem Aktivierungstoken; A-137 um beide
Audit-Fehlerstellen erweitert. Normaler Versandfehler zeigt korrekt Warnung.
Insgesamt 139 Befunde. ONBOARDING_FAILURE_CHECKS.json / AUTH_REVIEW.md; kein
echter Versand. Projektbasis weiterhin bf4d84a, App-Code unveraendert.

Onboarding-Wiederaufnahme: drei Gruppen mit je zwei Original-POSTs. Duplikat-
schutz verhindert zweites Konto, aber erneute Anlage scheitert unbehandelt und
sendet keine Einladung neu. A-084/A-139 erweitert, weiterhin 139 Befunde.
ONBOARDING_RETRY_CHECKS.json / AUTH_REVIEW.md. Kein eigener Neusendepfad im
untersuchten Code; keine echte Mail und keine produktive Aenderung.

Aktivierungslink: sechs Originalrouten-Gruppen zu Erfolg/Wiederverwendung, Ablauf,
Zweck, deaktiviertem Mitglied, Passwortvalidierung und Auditfehler. Schutzfaelle
positiv; A-137 um bereits gespeichertes Passwort bei gescheitertem Abschluss
erweitert. Weiterhin 139 Befunde. ACTIVATION_BOUNDARY_CHECKS.json / AUTH_REVIEW.md.
Keine echten Accounts/Mails, Parallelitaet/MFA-/Browservarianten offen.

Aktivierungs-Sessions: drei Gruppen mit normalem Login nach Teilfehler, bereits
angemeldetem anderem Konto und MFA/Onboarding-Kombination. A-140: Aktivierung
umgeht vorhandene MFA-Pruefung bei gueltigem Link; normale Erreichbarkeit der
kombinierten Zustaende noch offen. Insgesamt 140 Befunde. ACTIVATION_SESSION_CHECKS.json
und AUTH_REVIEW.md. Keine echten Accounts oder MFA-Daten veraendert.

Onboarding/MFA-Folgeprobe, Abschluss 2026-10-10: Admin-Anlage, Anfangspasswort-
Login und originales MFA-Setup lassen den Aktivierungslink unbenutzt. Dieser
meldet anschliessend ohne MFA an; normaler Kontrolllogin verlangt MFA. A-140
ueber regulaere Routen erreichbar, weiterhin 140 Befunde. ONBOARDING_MFA_SEQUENCE_CHECKS.json
und AUTH_REVIEW.md. Keine echten Konten/Mails oder Produktionsschluessel beruehrt.

Token-Lebenszyklus, 2026-10-10: vier Originalrouten-Folgen zu alten Aktivierungs-
und Reset-Links nach normalem Passwortwechsel oder Reset mit anderem Link.
A-141: alle vier alten Links koennen das Passwort erneut setzen; anschliessende
Wiederverwendung wird korrekt abgelehnt. Insgesamt 141 Befunde.
CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json / AUTH_REVIEW.md. Ausgabehelfer direkt,
keine Mail-/Produktionspruefung; weitere Ausgabe-/Admin-/Tokenzweck-Grenzen offen.

Reset-Anfragefolgen, 2026-10-10: zwei Gruppen mit originaler Linkausstellung
ueber Passwort vergessen und abgefangenem Versand. Aelterer Link wirkt nach
Reset mit neuerem Link sowie nach administrativem Passwortreset weiter.
Admin-Login und Step-Up original durchlaufen. A-141 erweitert, weiterhin 141
Befunde. RESET_REQUEST_SEQUENCE_CHECKS.json / AUTH_REVIEW.md. Weitere
Tokenzwecke, Parallelitaet und Produktionsbestand offen; App unveraendert.

MFA-Link-Lebenszyklus, 2026-10-10: zwei Originalablauffolgen ueber Mail- und
Admin-Reset mit anschliessender echter lokaler MFA-Neueinrichtung. Alter Link
deaktiviert neue 2FA und entfernt deren Backup-Codes; verbrauchter Link bleibt
nach dritter Einrichtung gesperrt. A-141 erweitert, weiterhin 141 Befunde.
MFA_RESET_LINK_LIFECYCLE_CHECKS.json / AUTH_REVIEW.md. Keine echten Mails,
Konten oder Produktionsschluessel beruehrt; Parallelitaet/Produktion offen.

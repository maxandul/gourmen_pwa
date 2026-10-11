# Konsolidierte Gesamtvorlage und Restabdeckung

Stand der Zusammenführung: 11. Oktober 2026, nach Bestätigung von B02.
Dies ist der aktuelle Einstieg für Gestaltung, Fachregeln und Umsetzungsreihenfolge.
Die nachstehenden Detailregister bleiben erhalten. Ältere «offen»-Angaben sind
anhand der hier verlinkten neuesten Entscheidungen einzuordnen. Keine pauschale
Abnahme aller Screens und keine Freigabe zur Änderung der laufenden App.

## Gesamtbild und Geltung

Neueste gezielte Nachführung: `merch-gemeinsame-runde.html` verbindet Mitglied,
Organisation und Schatzmeister mit denselben lokalen Bestell-/Zahlungsdaten für
Ersatz, Nachzahlung und Teilübergabe. Mitgliedershop zeigt Preise je Ausführung.
Beitragsausnahmen, Budgethistorie und B02 sind inzwischen interaktiv ergänzt und
lokal geprüft. Die übrigen Prototypdateien bleiben eigenständige Beispielszenarien;
keine vollständige Lieferanten-/Bankkette oder neue Gesamtabnahme behaupten.
Die vorgeführten Ergänzungen wurden anschliessend mit «passt» gestalterisch
bestätigt. R13 zu sensiblen Angaben, Dokumenten und laufender Revision ist
anschliessend mit «ja» bestätigt; Details in ROLLEN_ENTSCHEIDUNGEN.md.

Die bestehende App wird schrittweise überarbeitet; kein vollständiger Neubau.
Dashboard, Events, GGL und Verein bilden die Hauptnavigation. Profil, Sicherheit
und persönliche Einstellungen liegen im Kontomenü. Mobile Bottom-Navigation,
Desktop-Seitenleiste und Hell-/Dunkelschalter gehören zur gemeinsamen Vorlage.
Öffentliche Homepage mit eigenständiger Gestaltung; Merch-Ziel ist das jüngere
Bestellrundensystem. Alte Merch-Daten bleiben als mögliche Migrationsquelle erhalten.

Bestätigt sind die vorgeführten Gestaltungsgrundlagen und die ausdrücklich
besprochenen Fachregeln. Detailausarbeitungen des Agenten und lokale Simulationen
sind davon getrennt. Die aktuelle Buchhaltungsübersicht ist
`buchhaltung-praxis-entwurf.html`; `buchhaltung-entwurf.html` und
`gourmen-entwuerfe.html` sind historische Übersichten und keine aktuelle Gesamtvorgabe.

## Verzeichnis der geltenden Entwürfe

Vorschauen liegen im bestehenden lokalen Visualisierungsordner der Unterhaltung:
`C:/Users/ulric/.codex/visualizations/2026/10/10/01a1273d-8534-7ff2-9f24-0554ea8d3aa9/`.
Für die chatunabhängige Übergabe sind die aktuellen 19 Vorschaufragmente zusätzlich
unter `mockups/` in dieser Initiative gesichert, mit Hash-/Grössenverzeichnis
`mockups/manifest.csv`. Die gesicherten Fragmente ändern keine App-Templates.
Dateinamen unten identifizieren die geprüften vorhandenen Vorschauen. Die
Dokumentlinks beschreiben Geltung und Grenzen; keine eigenständige App oder
durchgängig verbundene Datenbasis zwischen den Vorschauen voraussetzen.

| Bereich | Aktuelle Vorschauen | Verbindliche Einordnung |
|---|---|---|
| App-Rahmen und Dashboard | `dashboard-rahmen.html` | Navigation, Theme und Aufgabenhierarchie; [Seitenzuordnung](SEITENGELTUNG_GESAMTVORLAGE.md) |
| Event und BillBro | `eventdetail-entwurf.html`, `billbro-ablauf.html` | Anwesenheit, Rückweg Rechnung → Angaben, Trinkgeld CHF/%, kein Anteil pro Person unter Prüfen; [Bewertung/GGL](BEWERTUNG_GGL_ENTSCHEIDUNGEN.md) |
| Formulare und Bearbeitung | `formulare-entwurf.html`, `bearbeiten-warteschlange.html` | [Formulare](FORMULARE_ENTWURF.md), [Inline/Warteschlange](INLINE_WARTESCHLANGE_ENTWURF.md) |
| Listen, Tabellen und Charts | `listen-charts-entwurf.html` | [Listen/Charts](LISTEN_CHARTS_ENTWURF.md), [zehn Chartpositionen und elf Mitglieder](CHARTS_SONDERSEITEN_ZUORDNUNG.md) |
| Buchhaltung als Gesamtprozess | `buchhaltung-praxis-entwurf.html` | [B01 einschliesslich G1–G3, K1 und B02](BUCHHALTUNG_PRAXISABGLEICH.md); fünf Arbeitsbereiche, ein Vereinskonto |
| Buchung, Beleg, Import und Zahlweg | `buchhaltung-prozesse.html`, `finanz-ergaenzung.html` | [Prozessentwurf](BUCHHALTUNG_PROZESSE_ENTWURF.md), [Finanzergänzung](FINANZ_ERGAENZUNG_ENTWURF.md); neuere B01-Regeln haben Vorrang |
| Revision und Korrektur | `revision-korrektur-entwurf.html` | [Revision/Korrektur](REVISION_KORREKTUR_ENTWURF.md), [Rollen](ROLLEN_ENTSCHEIDUNGEN.md) |
| Merch-Mitglieder | `merch-mitglieder-entwurf.html` | [Mitgliederentwurf](MERCH_MITGLIEDER_ENTWURF.md); Preise/Varianten noch mit neuestem Verwaltungsstand harmonisieren |
| Merch-Verwaltung und Ausnahmen | `merch-verwaltung-entwurf.html`, `merch-lieferausnahmen.html` | [Verwaltungsentwurf](MERCH_VERWALTUNG_ENTWURF.md), [Zielversion](MERCH_ZIELVERSION.md); Ausnahmefälle noch zu einer durchgängigen Beispielrunde verbinden |
| Gemeinsame Merch-Beispielrunde | `merch-gemeinsame-runde.html` | Drei Rollen auf einem lokalen Datenstand: Ersatz mit Zustimmung, erhaltene Zahlungen, Nachzahlung, Teilübergabe und Abschluss. Ergänzt die breiteren Einzelentwürfe. |
| Dokumente und Upload | `dokumente-upload-entwurf.html` | [Dokumente/Upload](DOKUMENTE_UPLOAD_ENTWURF.md), Drive als Dateiablage |
| Konto und Verwaltung | `konto-zugang-entwurf.html`, `verwaltungszugaenge-entwurf.html` | [Konto/Zugang](KONTO_ZUGANG_ENTWURF.md), [Verwaltungszugänge](VERWALTUNGSZUGAENGE_ENTWURF.md), differenzierte Bereichsrechte |
| Öffentliche Homepage | `oeffentliche-homepage-entwurf.html` | [Homepage](PUBLIC_HOMEPAGE_ENTWURF.md); öffentliche Aggregate, Einzelbewertungen intern; Inhaltsfreigaben offen |
| Systemzustände und E-Mail | `system-email-entwurf.html` | [System/E-Mail](SYSTEM_EMAIL_ENTWURF.md); reale Zustellung/Installation nicht durch Simulation belegt |

## Fachlicher Stand in einem Blick

| Thema | Bestätigter Stand |
|---|---|
| Rollen | Systemadmin darf alle Bereiche bearbeiten; Vorstand ist nicht automatisch Admin. Fachrollen und gezielte Zusatzrechte. Schatzmeister/Admin öffnen ein Jahr allein mit Grund wieder; Revision regulär Revisor, Admin-Stellvertretung gekennzeichnet. |
| BillBro | Tatsächliche Anwesenheit massgeblich, Organisation kann Zusagende als abwesend markieren. Nichtantwortende bei Rundenschluss abwesend, sofern nicht als anwesend erfasst. Private Essen nur Betragserinnerung. |
| Bewertung/GGL | Bewertung nach Anlass ohne Frist; Essen Pflicht, Getränke/Service optional, ausgefüllte Kategorien gleich gewichtet. Elf Mitglieder im Chart erreichbar; genaue GGL-Regeln im Fachentscheid. |
| Merch | Einkaufspreis je Ausführung minus gedeckeltem Rundenzuschuss, keine Marge. Bindende Bestellung trotz vorläufigem Preis; Ersatz mit Zustimmung zu Preisfolgen. Wiederöffnung erhält Bestätigungen. Abschluss bei Zahlung, Übergabe und erledigten Ausnahmefällen. |
| Buchhaltung | Ein Konto, keine Kasse; Bankabgleich zentral. Belegdateien optional, 18 Posten bleiben. Reise-Mehrkosten privat ausserhalb der App. Jahres-Ist nach tatsächlichem Bankbuchungsdatum; offene Beträge separat. |
| Korrekturen | G1–G3 und K1 bestätigt: Ausgleich vor neuen Zahlungsaufforderungen klären; Lieferanten-/Mitgliederrückflüsse getrennt. Rückflüsse auf 3620/6710, Sachauslagen auf Sachposten. Nettoübersicht erklärt verbleibende Kosten/Zuschüsse. |
| Beiträge und Budget | Beitragsvorschau mit begründeten Ausnahmen; keine doppelte Jahresforderung. Vorschlag, GV-Beschluss und spätere Änderungen historisiert. Bedienungsdetails in B01 konkretisiert. |
| Private Erinnerung B02 | Persönlich ausblendbar, im Event wieder erreichbar, kein Zahlungsnachweis. Bei geändertem Betrag/Empfänger erneut sichtbar. Mit «ja» bestätigt. |

## Gemeinsame Bedienung und Geräteabnahme

- Mobile: eine Hauptaufgabe pro Schritt, wichtige Werte ohne seitliches
  Abschneiden. Bearbeiten beim Inhalt, Löschen mit Gegenstand und Folgen;
  bezahlte/abgeschlossene Vorgänge über Korrekturweg. Kein generisches Löschrecht
  aus der Darstellung ableiten. Keine blaue Touch-Markierung, sichtbarer Tastaturfokus.
- Rückwärts erhält Eingaben, Listenfilter und Position. Nach Schrittwechsel zum
  neuen Abschnitt; bei Validierungsfehlern zum ersten betroffenen Feld mit lesbarer
  Meldung. Dialoge führen den Fokus hinein und zurück. Lange Formulare und mobile
  Tastatur in der Umsetzung separat testen.
- Tablet: nach verfügbarer Inhaltsbreite umschalten, nicht pauschal verkleinerten
  Desktop verwenden. Liste/Detail nur nebeneinander, wenn beide lesbar bleiben.
  Bereits gezeigte Breakpoints sind Entwurfswerte, keine globale neue Tokenvorgabe.
- Desktop: breite Vergleiche und Liste/Detail nutzen, Hauptaktion eindeutig.
  Vergleichstabellen dürfen einen eigenen Scrollbereich besitzen; keine horizontale
  Seitenüberbreite. Für alle Geräte Hell/Dunkel, lange Texte, grosse Schrift,
  leere/fehlerhafte Zustände sowie elf Mitglieder prüfen.

## Umsetzungspakete, Abhängigkeiten und Abnahme

Planung der späteren Umsetzung, jetzt kein Ausführungsauftrag. Vorhandene
141 Befunde und Paketregister bleiben die technische Basis; kein neuer Gesamtaudit.

| Paket | Abhängigkeit und begrenzter Auftrag | Erforderlicher Abnahmenachweis |
|---|---|---|
| U1 Zugang und Datenschutz | Fachrollen/F1/F2 in vollständige Aktions- und Feldmatrix übersetzen; konkrete Link-/Sitzungsfristen festlegen. Vorrang vor breiter Freigabe weiterer Funktionen. | Serverrechte auf allen Einstiegen, Widerruf/Recovery/MFA, keine Datenlöschung bei Lesefehlern, keine Geheimnisse in Logs, Nutzertrennung im Cache. |
| U2 Datenintegrität und Geldflüsse | B01/F3–F7/G1–G3/K1 umsetzen; Rechte U1 berücksichtigen. Vor produktiven finanziellen Abläufen Speichergrenzen und Migrationsbedarf klären. | Wiederholung/Teilfehler ohne doppelte Buchung, PostgreSQL-Tests, Summenerhalt, getrennte Forderung/Zahlung, Teilstorno und Jahreswechsel, unveränderte Zahlungshistorie. |
| U3 Fachabläufe und Wiederaufnahme | U1/U2-Verträge verwenden; Event, Beiträge, Merch, Drive und Revision jeweils als zusammenhängenden Ablauf bearbeiten. | Pro Ablauf Erfolg, Rückweg, Abbruch, Fehler, Wiederholung und parallele Änderung; richtige Folgeaufgabe/Rolle. B02 rein persönliche Anzeigeentscheidung. |
| U4 Gemeinsame Oberfläche | Bestätigte Muster und Seitenzuordnung verwenden. Bausteine können parallel vorbereitet werden, fachliche Anzeigen müssen U1–U3 entsprechen. | Repräsentative Seiten plus ihre Varianten auf Mobile/Tablet/Desktop, Hell/Dunkel, Fokus, Scroll, Eingabeerhalt; keine abgeschnittenen Aktionen oder falschen Status. |
| U5 Performance und Betrieb | Ergebnisse/Rechte aus U1–U3 bewahren; bekannte kritische Cache-/Updatefehler nicht bis zum Ende aufschieben. | Messbarer Vorher/Nachher-Vergleich, echte Geräte/PWA, Updates mit offenen Eingaben, tatsächliche Mail-/Drive-Fehler und Wiederaufnahme. |
| U6 Altlasten und Pflege | Erst nach tragfähigen Zielwegen aus U3/U4. Merch-Altdaten erhalten, Migration separat planen; Game ausgeschlossen. | Aufrufer/Weiterleitungen und Altclients prüfen, reproduzierbare Assets, aktualisierte Anchor-Docs; keine Löschung allein wegen ausgelassener Mockup-Inhalte. |

Empfohlene Reihenfolge: zuerst U1/U2-Grundlagen und akut blockierende Einzelbefunde,
dann pro Fachablauf U3 mit zugehörigem U4-Baustein. U5 an den betroffenen Abläufen
mitführen; U6 nach Ablösung. Kein grosser gleichzeitiger Umbau aller Bereiche.

## Noch erforderlich vor dem Einstieg in die Umsetzung

1. **Harmonisierte Entwürfe einordnen:** Merch-Mitgliederpreise sind angeglichen;
   Ersatz/Nachzahlung/Teilübergabe laufen in einer gemeinsamen Beispielrunde.
   B02, Beitragsausnahmen und Budgethistorie sind interaktiv vorgeführt und lokal
   geprüft. Diese Ergänzungen sind mit «passt» bestätigt. Lieferanten-/Bankbewegungen
   bleiben in den Fachregeln und ergänzenden Fällen beschrieben; keine vollständige
   Integration aller unabhängigen Prototypdateien behaupten.
2. **Technische Sicherheitsverträge:** fachliche Grenzen für sensible Angaben,
   Dokument-Lösch-/Archivregeln und laufende Revision sind durch R13 bestätigt.
   Vollständige Zuordnung vorhandener Felder/Aktionen, direkte Drive-Freigaben,
   konkrete Zugangsfristen und Nebenläufigkeit vor der jeweiligen Umsetzung
   präzisieren. Die Fachregel allein belegt keine wirksame Zugriffskontrolle.
3. **Öffentliche Inhalte:** echte Fotos bzw. bewusst illustrative Auswahl,
   vollständige Vereins-/Kontakt-/Rechtstexte freigeben. Blockiert die
   Veröffentlichung dieser Inhalte, nicht automatisch interne Umsetzungspakete.
4. **Umsetzung separat beauftragen:** erstes begrenztes Paket, Testumfang und
   gegebenenfalls Migrationsplan benennen. Aktuell bleiben App, Daten und Betrieb
   unverändert. Die lokale Mockup-Prüfung ersetzt keine echte Geräte-/Produktionsabnahme.

## Erstes begrenztes Umsetzungspaket: U1a Daten bei Lesefehlern bewahren

**Nachtrag 11.10.2026: separat beauftragt, lokal umgesetzt und geprüft.**
[Umsetzung und Testnachweis](U1A_DATENERHALT.md); keine Freigabe weiterer Pakete
oder eines Deployments. Der nachstehende Umfang bleibt die Abnahmegrundlage.
Die Gestaltungs-/Fachplanung ist für diesen
kleinen Einstieg keine Blockade mehr. Ausgangspunkt ist der vorhandene Befund
A-086: Ein Lesefehler darf sensible Bestandsdaten nicht löschen. Kein neuer
umfassender Audit und kein gleichzeitiger Umbau des gesamten Rollenmodells.

- Bestehenden Fehler anhand der vorhandenen Nachweise lokal nachstellen.
- Betroffenen Lesepfad so korrigieren, dass fehlerhafte Entschlüsselung weder
  Datensatz noch verschlüsselten Inhalt löscht/überschreibt oder als leere Werte
  zum anschliessenden Speichern anbietet. Benutzbare Fehlermeldung ohne vertrauliche
  Inhalte; gezielte Wiederholung bzw. Klärung möglich.
- Regression mit synthetischen Daten: gültiger Inhalt weiterhin lesbar; ungültiger
  Inhalt vor/nach Leseversuch identisch vorhanden; kein versehentliches Speichern
  leerer Ersatzwerte; keine Geheimnisse in Fehlermeldung/Log. Datenbankzustand
  unabhängig von einer blossen HTTP-Erfolgsmeldung prüfen.
- Nur notwendige Code-/Test-/Dokumentänderungen; CRYPTO_KEY unverändert, keine
  produktive Datenreparatur, keine Migration oder Änderung bestehender Freigaben.
  Sollte die Prüfung einen zusätzlichen Daten-/Migrationsbedarf zeigen, diesen
  getrennt konkret vorlegen, nicht stillschweigend mit erledigen.
- Ergebnis als überprüfbarer Diff mit tatsächlichen Testnachweisen bereitstellen.
  Deployment ist ein weiterer Schritt. Keine Behauptung, U1 sei mit U1a komplett.

Danach U1-Rechte-/Zugangsverträge und U2-Geldflüsse in kleinen Paketen bearbeiten;
U3/U4 verbinden die fachlichen Verbesserungen mit den bestätigten Oberflächen.
Die öffentliche Inhaltsfreigabe kann davon unabhängig erfolgen.

## Detailregister und bisheriger Arbeitsstand

Stand: 11. Oktober 2026. Massgeblicher aktueller Arbeitsplan nach Bestätigung
aller bislang vorgelegten Grundentwürfe. Keine Umsetzungsfreigabe und kein
neuer umfassender Audit. Diese Zusammenführung ersetzt ältere «als Nächstes»-
Angaben in den einzelnen Entwurfsdokumenten, nicht deren offene Anforderungen.

**Fortschritt R06/R12:** [Charts und Sonderseiten](CHARTS_SONDERSEITEN_ZUORDNUNG.md)
ordnet die zehn aktiven Chartpositionen und Altseiten gezielt zu. R12 ist auf
Konzeptebene geklärt; R06-Bestandszuordnung ist abgeschlossen. GGL-Vergleich mit
elf Personen und Betragsbalken statt Ausgabenring sind mit dem anschliessenden
«ok» gestalterisch bestätigt. [Finanzergänzung R07/R08](FINANZ_ERGAENZUNG_ENTWURF.md)
ist mit «ok. weiter» ebenfalls gestalterisch bestätigt. Zahlwegwechsel und
Ausgleichsregeln sind inzwischen in B01/G1–G3 bestätigt.
[Verwaltungszugänge R10](VERWALTUNGSZUGAENGE_ENTWURF.md) sind gestalterisch
bestätigt; F1/F2-Grundregeln sind inzwischen separat entschieden. [Seitengeltung R01–R05](SEITENGELTUNG_GESAMTVORLAGE.md)
und das aktualisierte CSV ordnen die Baseline-Seiten den vorhandenen Mustern zu.
Die Grundentscheidungen zu Zugang/Rollen, Merch, Bewertungen/GGL und den
Buchhaltungskernabläufen liegen vor. Buchhaltungspraxis-Übersicht und jetzt auch
vier Merch-Lieferausnahmeansichten sind gestalterisch bestätigt. Private
Betragserinnerung, optionale Belege und Revisionsrechte wurden in den älteren
Detailentwürfen nachgeführt. Nächster Block ist die gezielte Zusammenführung
mit den unten begrenzten Restpunkten, keine neue lose Entwurfs- oder Auditserie.

## Was feststeht

Gestaltung und gezeigte Benutzerführung sind bestätigt: App-Rahmen, Dashboard,
Eventdetail, Buchhaltungsübersicht, BillBro, Formulare, Listen-/Chartgrundmuster,
Buchung/Beleg/Zahlungszuordnung, Revision/Korrektur, Inline/Warteschlange,
Merch-Mitglieder-/Verwaltungssicht, Dokumente/Uploads, Konto/Zugang, öffentliche
Homepage sowie zuletzt Systemzustände/E-Mails («ok. passt.»).

Einzelregeln F3–F6 und die BillBro-Anwesenheitskorrekturen sind gesondert fachlich
bestätigt. Merch v2 mit Bestellrunden ist das gewählte System. Alte Daten bleiben
als mögliche Migrationsquelle erhalten. Öffentliche Homepage darf eigenständig
gestaltet sein. Der fachliche Gesamtabgleich der Buchhaltung bleibt ausdrücklich offen.

Die 83 Templates sind eine Zuordnung der alten Auditbaseline, keine vollständige
Inventur des separaten Merch-v2-Branches. Keine prozentuale Gesamtfertigstellung
aus dieser Zahl oder aus der Zahl genehmigter Mockups ableiten.

## Gemeinsames Muster genügt – gezielt zuordnen

Hier ist zunächst kein neues Grundlayout nötig. Die konkrete Seitenzuordnung
und Abnahmekriterien müssen dennoch vor der Gesamtvorlage festgehalten werden.

| ID | Bereich | Übernahme und noch zu dokumentierender Unterschied |
|---|---|---|
| R01 | Weitere Bereichseinstiege und Detailseiten | App-Rahmen, priorisierte Aufgaben, Detailaktionen aus Dashboard/Event/Dokument/Merch verwenden; je Seite sichtbare Hauptaktion und Rolle benennen. Keine pauschale Freigabe unbekannter Datenfelder. |
| R02 | Standardformulare und Kontenbearbeitung | Bestätigtes Formular-/Inline-Muster übernehmen; Pflichtfelder und Rechte fachlich abgleichen. Sensible/finanzielle Änderungen erhalten den jeweiligen Freigabe- oder Korrekturweg. |
| R03 | Dokument-/Belegvarianten | Ordnerwahl, Entwurfserhalt, Fortschritt und unklarer Speicherstand übernehmen. Kamera, echte Vorschau, Dateigrenzen, Eventzuordnung, grosse Bäume und Namenskonflikte als konkrete Abnahmekriterien ergänzen. |
| R04 | Listen und Meldungen | Suche, Sortierung, Rückkehrkontext, Leer-/Fehlerzustände und Teilfehler verwenden. Serverpagination, Browserhistorie und grosse Bestände gezielt abnehmen. |
| R05 | E-Mail-/Systemvarianten | Gemeinsame bestätigte Vorlage verwenden. Tatsächliche Tokenfristen, Versandstatus, Gerätetexte und Clienttests separat festlegen; kein neuer Gestaltungstyp nötig. |

Quellen: FORMULARE_ENTWURF.md, LISTEN_CHARTS_ENTWURF.md,
DOKUMENTE_UPLOAD_ENTWURF.md, INLINE_WARTESCHLANGE_ENTWURF.md,
SYSTEM_EMAIL_ENTWURF.md und ABDECKUNG_GESTALTUNG.md.

## Gezielte Ergänzungen vor der Gesamtvorlage

| ID | Lücke | Konkretes Ergebnis, das noch fehlt |
|---|---|---|
| R06 | Bestehende Diagramme und elf Mitglieder | Jeden tatsächlich relevanten GGL-, Event- und Buchhaltungschart einer Darstellung zuordnen. Rang/Punkte, Mehrfachreihen, Datenlücken und Touch-Legende unterscheiden. Mobile-Vergleich für elf Mitglieder zeigen, falls Grundmuster dafür nicht genügt. Quellen: vorhandene Komponenten-/Registry-Berichte; bei fehlenden Chartdetails nur diese gezielt lesen. |
| R07 | Importvorstufe und Sammelaktionen | Datei → Prüfung gültiger/fehlerhafter/doppelter Zeilen → ausgewählte Übernahme → Teilergebnis/Wiederaufnahme darstellen. Anschliessend an bestätigten Zuordnungsarbeitsplatz anschliessen. Fachlich keine automatische Buchung aus unklarer Zahlung ableiten. |
| R08 | Private Auslagen und Zahlwegwechsel | Private Essen nach B01 nur Betragserinnerung; Zahlungsbestätigung aus der Vorschau entfernt. Wechsel ohne/mit Vereinszahlung dargestellt; Gegenrichtung und konkrete Vereins-Ausgleichsschritte noch spezifizieren. |
| R09 | Merch-Ausnahmen | Unterschiedliche Lieferanten-/Mitgliederpreise und Preise je Ausführung zuordnen; Wiederöffnung, Teillieferung, Ersatz/Fehlmengen und Storno nach Zahlung benötigen zuerst F7. Rückschritte dürfen keine bezahlten Forderungen unbemerkt ersetzen. |
| R10 | Google-/Kalender- und Admin-Zugänge | Auf bestehende Einstellungs-/Bestätigungsmuster abbilden: Adressverifikation, noch ausstehende Einladung, Kalenderlink erneuern/deaktivieren, Mitgliederanlage/Einladungsfehler und Schutz des letzten Admins. Abweichende Folgen müssen sichtbar werden. F1/F2 nicht vorwegnehmen. |
| R11 | Öffentliche Inhalte | Bewertung nach F8, öffentliche Eventdaten nach Sichtbarkeitsentscheidung, Instagram-Link/Embed sowie vollständige About-Inhalte zuordnen. Foto-/Text-/Kontaktfreigabe offen. Kein Löschauftrag aus Auslassungen im Entwurf. |
| R12 | Sonder-/Altseiten | Hamburg als historische Reiseansicht einordnen; ältere Buchhaltungs-Volltemplates gegen bereits dokumentierte aktuelle Tabvarianten abgleichen. Alte Merch-Oberflächen operativ stilllegen erst in Umsetzung; Daten/Migrationsquelle erhalten. Game bleibt ausgeschlossen. |

Quellen für R06/R12: COMPONENT_REVIEW.md nennt Canvas-Diagramme in vier
Template-Kontexten inklusive historischem Volltemplate; UI_REGISTRY_REVIEW.md
belegt aktive GGL-/Event-/Buchhaltungs-Chartbausteine und die historische Hamburg-
Seite. Diese Berichte liefern keine hier schon abgeschlossene Chartzuordnung.
Accounts-GET ist laut Komponentenbericht bereits auf den Tab umgeleitet; weitere
Verwendung der alten Volltemplates bleibt gezielt zu klären. Keine neue Entfernung
oder definitive Inaktivität aus dieser Zusammenfassung behaupten.

## Fachentscheidungen separat bearbeiten

**Aktualisierte F6-Regel:** Systemadmin und Schatzmeister dürfen jeweils allein
mit dokumentiertem Grund ein abgeschlossenes Jahr wiederöffnen. Keine Zustimmung
des Revisors mehr erforderlich. Erneute Revision und Berichtshistorie bleiben.
Die Revisionsvorschau ist entsprechend nachgeführt, einschliesslich markierter
stellvertretender Bestätigung durch den Systemadmin.

| ID | Thema | Nächste konkrete Entscheidungsgrundlage |
|---|---|---|
| F1 | Zugang, Widerruf, Wiederherstellung | Mitgliederablauf, Admin-Notfallmodell und ergänzendes Regelpaket bestätigt: erneute Bestätigung, Linkersetzung, externe Entzüge, Gerätevertrauen. Technische Ausgestaltung und konkrete Fristen bleiben offen. Siehe KONTO_ZUGANG_ENTWURF.md. |
| F2 | Rollen und Sichtbarkeit | Admin-Vollzugriff, Bereichsrechte und Zusatzfreigaben bestätigt. Revision regulär durch Revisor, stellvertretend durch Systemadmin mit sichtbarem Vermerk; keine Selbstbestätigung Schatzmeister. Einzelne Sichtbarkeitsdetails offen. F3/F4 erhalten; F6-Wiederöffnung separat geändert. Siehe ROLLEN_ENTSCHEIDUNGEN.md. |
| F7 | Merch v2 | Preisverbindlichkeit, Wiederöffnung, Abschluss, Lieferausnahmen, Zuschuss und Änderungs-/Stornowege bestätigt. Nach Lieferantenauftrag erst Möglichkeit klären, nach Zahlung Folgenvorschau bei Erhalt der Zahlungen. Vier Ausnahmeansichten gestalterisch bestätigt. Einkaufspreis je Ausführung minus Zuschuss ohne Marge sowie Ersatz mit Preisfolgen bestätigt. Darstellung, Integration in Hauptablauf und Buchhaltungsanbindung noch ausarbeiten. Siehe Merch-Entwurfsdokumente. |
| F8 | Bewertung und GGL | Bewertungs-/GGL-Regeln bestätigt. Auch öffentliche Restaurantaggregate (Gesamtwert, Kategorien, Anzahl) bestätigt; Einzelbewertungen/Namen/Kommentare intern. Siehe BEWERTUNG_GGL_ENTSCHEIDUNGEN.md. |
| B01 | Buchhaltung als Gesamtprozess | Ein Vereinskonto/keine Kasse, Bankabgleich, Reiseablauf, Budget/Ist/GV. Reise-Mehrkosten ausserhalb App; Belege optional; private Essen nur Erinnerung. Alle 18 Posten unverändert für Buchungen/Budget bestätigt. Zahlungsprinzip als delegierte Standardwahl: Bankbuchungsjahr zählt, offene Beträge separat sichtbar. Erstattungen, Sammelzahlungen und Merch ohne doppelte Zuschussausgabe bestätigt. Budgetvorschlag/GV-Beschluss mit Historie bestätigt. Beitragsablauf bestätigt, Gesamtprozess zusammengeführt. Neue Buchhaltungsübersicht gestalterisch bestätigt; Merch-Darstellung bestätigt, Postenaufteilung ausgearbeitet; ergänzende Detailentwürfe offen; siehe BUCHHALTUNG_PRAXISABGLEICH.md. |

**Korrektur zur frühen F7-Empfehlung:** Die ursprüngliche Empfehlung «Preis bei
Bestätigung binden» in OBERFLAECHENENTWUERFE.md entstand vor der Versionsklärung.
Sie ist kein beschlossener Ausgangspunkt für v2. Verbindliche Bestellung trotz
vorläufiger Preise und definitive Preise ohne zweite Bestätigung sind inzwischen
bestätigt; Produktwechsel erfordert weiterhin Zustimmung.

## Begrenzte Restliste für die konsolidierte Gesamtvorlage

Diese Liste ersetzt die alte Reihenfolge als nächste Arbeitsanweisung. Bereits
bestätigte Regeln nicht nochmals pauschal zur Zustimmung vorlegen.

| Rest | Konkretes Ergebnis | Betroffene Umsetzungspakete |
|---|---|---|
| Widersprüche in älteren Ansichten | Merch-Wiederöffnung/Abschluss, Sitzungserhalt nach normaler Passwortänderung, optionale Bewertungsfelder und öffentliche Aggregate sind nachgeführt. Merch-Ausnahmen mit Hauptablauf vollständig verknüpfen. | U1, U3, U4 |
| Noch offene Geldflussvarianten | G1–G3 zu Zahlwegwechsel, getrennten Rückflüssen und Jahreswechsel bestätigt. K1-Rückzahlungsposten und Brutto-/Nettoübersicht bestätigt; Teilzahlungsbeispiele ausgearbeitet. In Gesamtvorlage und Ablaufabnahme übernehmen. Keine Zahlung oder historische Änderung aus einem Mockup ableiten. | U2/U3: bestätigte Regeln, technische Ablaufabnahme ausstehend |
| Preis-/Variantenfälle Merch | Einkaufspreis je Ausführung minus Zuschuss ohne Marge bestätigt. Ersatzanfrage enthält geänderten Preis und Mitgliederanteil. Regel im Haupt-/Ersatzentwurf dargestellt und lokal geprüft; Mitgliedershoppreise angeglichen; gemeinsame Ersatz-/Zahlungs-/Übergabekette lokal gezeigt. Lieferantenbewegungen bleiben gesonderte Anschlussfälle. | U2/U3/U4: bestätigte Regel ausarbeiten |
| Begrenzte Bedien-/Inhaltsdetails | Beitragsausnahmen und Budgethistorie in B01 konkretisiert. B02, Beitragsausnahmen und Budgethistorie interaktiv ergänzt und lokal geprüft; öffentliche Texte/Fotos/Kontaktdaten noch freizugeben. Vorhandene Formular-/Listenmuster nutzen, nur echte Unterschiede visualisieren. | Betroffene Teile U3/U4 |
| Gesamtvorlage und Abnahmeplan | Gültige Ansichten und Seitengeltung sowie U1–U6 mit Abhängigkeiten, offenen Entscheidungen und Abnahmekriterien sind oben zusammengeführt. Gezielte Harmonisierung und Einzelverträge bleiben. Technische Tests für Rechte, Datenkonsistenz, echte Geräte/Dienste explizit als Umsetzungstests kennzeichnen. | U1–U6, weiterhin keine Umsetzungsfreigabe |

Die bereits vorhandenen Auditbefunde bleiben Grundlage der Umsetzungspakete.
Diese gestalterisch-fachliche Konsolidierung ersetzt keine Produktionsabnahme.

## Bisherige Arbeitsschritte als Einordnung

1. R06 sowie R12 begrenzt zuordnen; nur echte Darstellungsabweichungen ergänzen.
2. R07/R08 als zusammenhängende Ergänzung der Finanzabläufe und R10 als
   Ergänzung der Verwaltung konkretisieren. R01–R05 schriftlich auf Seiten abbilden.
3. Fachentscheidungen im passenden Kontext bündeln: Zugang/Rollen, Merch,
   Bewertungen/GGL; Buchhaltung ausdrücklich als eigener Praxisabgleich.
   Davon abhängige R09/R11 anschliessend abschliessen.
4. Gesamtvorlage mit bestätigten Mustern, bewusst offenen Entscheidungen,
   Seitengeltung und Umsetzungspaketen U1–U6 zusammenführen. Für offene
   Entscheidungen betroffene Pakete als blockiert kennzeichnen, nicht stillschweigend
   freigeben. Technische Sicherheits-/Datenprobleme behalten ihre Priorität.

Reine technische Implementierungsprüfungen dürfen als spätere Abnahmekriterien
geführt werden; wesentliche Bedien- oder Fachentscheidungen nicht. Insbesondere
«Chart auf Mobile technisch testen» ist später, «wie elf Reihen dargestellt werden»
gehört jetzt in die Vorlage. Der aktuelle Stand ist **Grundgestaltung bestätigt,
Restabdeckung und Fachabgleich offen**, nicht «fertig zur Umsetzung».

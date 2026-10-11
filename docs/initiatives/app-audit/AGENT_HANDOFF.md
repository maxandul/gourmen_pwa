# Übergabe: Planungsstand gesichert, Einstieg in die Umsetzung

**U1f-Nachtrag 11.10.2026:** Nächste lokale Fortsetzung A-079:
MFA-Backup-Code mit vorhandenem Hash-Prüfer verifizieren und vor Anmeldung
einmalig verbrauchen. Branch `codex/u1f-backup-code-login` über `627e697`;
[Nachweis und Grenzen](U1F_BACKUP_CODES.md). A-076 wurde nur eingeordnet,
Pflichtwechsel-/Zwischenzielablauf bleibt ein späteres Paket.

**U1e-Nachtrag 11.10.2026:** Nächste beauftragte lokale Fortsetzung A-043:
beide RSVP-Erinnerungseinstiege prüfen Organisator/Admin identisch vor Versand.
Branch `codex/u1e-reminder-permissions` über `f8a40f9`;
[Nachweis und Grenzen](U1E_REMINDER_RECHTE.md). Kein echter Versand oder Deploy.

**U1d-Nachtrag 11.10.2026:** Nächste beauftragte lokale Fortsetzung: A-113,
Cron-Testendpunkt standardmässig sperren und bei Freischaltung authentifizieren.
Branch `codex/u1d-cron-test-access` über `f31c688`;
[Nachweis und Grenzen](U1D_CRON_TEST.md). Kein Versand, Deploy oder Merge auf master.

**U1c-Nachtrag 11.10.2026:** Nach U1b setzt der beauftragte nächste Schritt
A-075 um: sensible Freigaben und Auth-Zwischenzustände bei Kontowechsel/
Neuanmeldung verwerfen. Branch `codex/u1c-step-up-session` über `d7317a0`;
[Nachweis und Grenzen](U1C_STEP_UP.md). Kein globaler Sitzungswiderruf bei Reset,
kein Deploy oder Merge auf master.

**U1b-Nachtrag 11.10.2026:** Der Nutzer hat anschliessend «Geheimnisse aus Logs
entfernen» (A-081/A-110) beauftragt. Umsetzung auf `codex/u1b-secret-safe-logging`
über U1a-Commit `9cf5126`; [Nachweis und Grenzen](U1B_LOGGING.md).
Weitere Zugangskorrekturen sind dadurch noch nicht umgesetzt oder veröffentlicht.

**Nachtrag 11.10.2026:** U1a wurde im anschliessenden Umsetzungschat ausdrücklich
beauftragt und lokal auf `codex/u1a-preserve-sensitive-data` umgesetzt.
[Nachweis und Grenzen](U1A_DATENERHALT.md). Kein Deploy, kein Merge auf master.
Die Startanweisung unten ist für U1a damit erledigt; weitere Pakete benötigen
einen eigenen Auftrag. Der historische Planungsstand bleibt erhalten.

Stand: 11. Oktober 2026. Dieser Einstieg hat Vorrang vor dem historischen Verlauf
weiter unten. Der Nutzer hat die Sicherung der Planung und Vorbereitung des
neuen Umsetzungschats beauftragt. In diesem Vorbereitungschat keine App-Änderung.

## Aktueller Stand und Quellenreihenfolge

- Repository `maxandul/gourmen_pwa`, lokal `C:/gourmen_pwa`.
- Planungsbranch `codex/app-audit-handoff-2026-10-10`.
- Zuerst `AGENTS.md`, dann `README.md` und `RESTABDECKUNG_GESAMTVORLAGE.md` in
  dieser Initiative lesen. Letzteres ist die konsolidierte aktuelle Gesamtvorlage.
- Fachquellen: `ROLLEN_ENTSCHEIDUNGEN.md` (einschliesslich bestätigtem R13),
  `BUCHHALTUNG_PRAXISABGLEICH.md` (G1–G3, K1, B02 bestätigt), Merch-Entwürfe und
  `BEWERTUNG_GGL_ENTSCHEIDUNGEN.md`. Bestätigte Regeln nicht erneut abfragen.
- `GESAMTBEURTEILUNG.md`, `FINDINGS.md`, `PAKETREGISTER.csv` und
  `COMPLETION_PLAN.md` enthalten Auditbasis und Nachweise. Keine neue umfassende
  Befundsuche. Historische Aussagen «offen» nicht über neuere Entscheide stellen.
- Aktuelle Vorschauquellen sind unter `mockups/` in dieser Initiative gesichert;
  `mockups/manifest.csv` nennt Dateien, Grösse und SHA-256. Es sind HTML-Fragmente
  mit synthetischen Daten, keine Produktivtemplates. Bei späterer Vorschau im
  jeweiligen Host darstellen; für eigenständige HTML-Exporte den passenden
  Visualisierungs-Renderer verwenden. Nicht in App-Assets kopieren.

## Erster begrenzter Implementierungsauftrag nach ausdrücklichem Start

U1a «Daten bei Lesefehlern bewahren», vorhandener Befund A-086. Konkreter Umfang
und Abnahmekriterien stehen in der Gesamtvorlage. Für diesen Auftrag zusätzlich
`docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/DOMAIN.md` und den betreffenden
Abschnitt von `AUTH_REVIEW.md` lesen. Kein neues Rollenmodell, kein Oberflächenumbau
und kein Merch-Branch-Merge in diesem Paket.

Lokalen Fehler mit synthetischen Daten nachstellen, kleinsten sinnvollen Fix
implementieren und prüfen: Entschlüsselungsfehler erhalten Datensatz und Payload,
erzeugen keine leeren Ersatzwerte zum Überschreiben und verraten keine Secrets.
Gültige Daten bleiben lesbar. Relevante Regressionstests und Dokumentation ergänzen,
Ergebnis als prüfbaren Diff berichten. Keine Produktion, kein Deploy, kein Merge
auf master, keine Schlüsseldrehung oder produktive Datenreparatur.

Branchbasis bewusst prüfen: Der Planungsbranch ist kein Nachweis des aktuellen
Produktionsstands. Für U1a vor Codeänderung Unterschiede zum beabsichtigten Ziel-
branch gezielt prüfen und Feature-Branch verwenden; dokumentierten Planungsstand
erhalten. Nicht blind master auschecken oder vorhandene lokale Dateien verwerfen.
Merch v2 liegt separat auf `phase/10-merch-wip` und ist für U1a nicht einzumischen.
Die technische Integration dieses Zielsystems gehört in ein späteres eigenes Paket.

Fremde unversionierte Dateien im bisherigen Arbeitsordner unangetastet lassen:
`build_logs.txt`, Game-Dokumente und die zwei vorhandenen gehashten PWA-JS-Dateien.
Ein sauberer Arbeitsbaum darf nicht durch deren Löschung erzwungen werden.

## Kopierfertiger Starttext für einen neuen lokalen Codex-Chat

Öffne `C:/gourmen_pwa` (Repository `maxandul/gourmen_pwa`). Die gesicherte Planung
liegt auf `codex/app-audit-handoff-2026-10-10`. Lies `AGENTS.md` sowie den aktuellen
Einstieg in `docs/initiatives/app-audit/AGENT_HANDOFF.md` und die dort genannte
Gesamtvorlage. Setze jetzt ausschliesslich U1a «Daten bei Lesefehlern bewahren»
(A-086) lokal auf einem geeigneten Feature-Branch um, einschliesslich gezielter
Regressionstests und Dokumentation. Prüfe vorher die richtige Codebasis; erhalte
die Planungsunterlagen und fremde lokale Dateien. Keine neue Gesamtaudit- oder
Mockup-Runde, keine erneute Abstimmung bestätigter Fachregeln. Kein Deploy, kein
Merge auf master, keine Produktionsdatenänderung und keine Schlüsselrotation.
Berichte verständlich, was geändert wurde und welche Prüfungen bestanden haben.

Der Text ist eine vorbereitete Startanweisung. Erst das Absenden durch den Nutzer
im neuen Chat beauftragt die Implementierung; diese Datei allein ist kein Auftrag
zur sofortigen Ausführung durch den aktuellen Planungsagenten.

## Historischer Verlauf der Planung (überholte nächste Schritte möglich)

### Ursprüngliche Übergabe für ChatGPT Work

Stand: 10. Oktober 2026. Der Nutzer wechselt von der bisherigen App in die neue ChatGPT-App und arbeitet dort ausdrücklich in **Work**, nicht in Codex, weiter. Technische Aufgaben können im zugänglichen Projekt erledigt werden; die Kommunikation bleibt verständlich und auf Ergebnisse ausgerichtet.

## Einstieg und Auftrag

Repository: `maxandul/gourmen_pwa`. Lokaler Projektordner auf dem bisherigen Computer: `C:\gourmen_pwa`.

Zuerst `AGENTS.md` im Repository lesen, danach in diesem Ordner:

1. `GESAMTBEURTEILUNG.md` – erste Gesamtbeurteilung und vorläufiges Zielbild.
2. `README.md` – Auftrag, Entscheidungen und Prüfstand.
3. `COMPLETION_PLAN.md` – offene Prüfbereiche und Abschlusskriterien.
4. `PAKETREGISTER.csv` und bei Bedarf `FINDINGS.md` – Zuordnung aller 141 Befunde zu sechs vorgeschlagenen Umsetzungspaketen und Detailbelege.

Die Analyse soll eine verständliche Entscheidungsgrundlage für die Weiterentwicklung der gesamten App liefern. Sie ist in wiederholte Detailprüfungen abgedriftet. Der Nutzer hat deshalb die Zusammenführung und frühe Zielbildarbeit bestätigt. Die erste Gesamtbeurteilung liegt vor; sie ist keine vollständige Abnahme der App.

## Nächste konkrete Arbeit

Aktueller Abschlussstand: R13 wurde mit «ja» bestätigt; sensible Angaben,
Dokumentrechte und laufende Revision nicht erneut zur Grundsatzentscheidung stellen.
Die Gesamtvorlage enthält jetzt das konkret abgegrenzte Einstiegspaket U1a
«Daten bei Lesefehlern bewahren» (A-086), einschliesslich Abnahmekriterien.
Es ist vorbereitet, aber noch nicht zur Implementierung beauftragt. Die bisherige
Grenze «keine App-Änderungen» gilt weiter. Öffentliche Inhaltsfreigaben sowie
technische Rechte-/Zugangsverträge bleiben separat benannt.

Letzte Rückmeldung «passt» bestätigt die gemeinsame Merch-Runde, angeglichene
Shoppreise, Beitragsausnahmen/Budgethistorie und B02-Darstellung. Nächster
Entscheid ist das gebündelte R13-Paket in ROLLEN_ENTSCHEIDUNGEN.md: sensible
Felder, Dokumentpflege/Archiv/Löschen und Bearbeitung während laufender Revision.
R13 noch nicht bestätigt; keine Rechte oder App-Dateien geändert.

Neueste Nachführung: gemeinsame Merch-Beispielrunde verbindet drei Rollen für
Ersatz/Nachzahlung/Teilübergabe/Abschluss; Mitgliedershop hat Ausführungspreise.
Buchhaltung v4 zeigt Beitragsausnahmen und Budgetversionsvergleich; Finanzergänzung
v3 zeigt B02 Ausblenden/Wiederanzeigen. 84 ergänzende Layoutkombinationen plus
Ablaufprüfungen und bestehende 60 Buchhaltungskombinationen bestanden.
Grenzen in Fachdocs: keine gesamte Lieferanten-/Bankkette, keine dateiübergreifende
Persistenz. Als Nächstes verbleibende Einzelverträge aus der Gesamtvorlage bündeln,
nicht nochmals diese Grundregeln zur Entscheidung vorlegen. Keine App-Änderung.

Die konsolidierte Gesamtvorlage steht am Anfang von
RESTABDECKUNG_GESAMTVORLAGE.md: aktuelles Entwurfsverzeichnis, Fachstand,
Geräteregeln, U1–U6 mit Abhängigkeiten und Abnahmen. Nächster begrenzter Schritt
ist die dort benannte Entwurfsharmonisierung (Merch-Datenkette und neueste
B01-Bedienung), danach verbleibende Einzelverträge. Keine neue Grundentwurfsserie,
keine umfassende Befundsuche und weiterhin keine Umsetzungsfreigabe.

Aktuelle Entscheidungsvorlage: B01 enthält G1–G3 zu Zahlwegwechseln mit bereits
geflossenem Geld, getrennten Lieferanten-/Mitgliederrückzahlungen und Teilzahlungen
über Jahresgrenzen. G1–G3 sind mit «ja, passt» bestätigt. K1-Rückzahlungsposten
und Nettoübersicht sind ebenfalls mit «ja» bestätigt. Beitragsausnahmen und
Budgethistorie sind konkretisiert. B02 (eigene private Erinnerung ausblenden,
bei Betrags-/Empfängeränderung wieder anzeigen) ist mit «ja» bestätigt; siehe B01.

Neueste Nachführung: Öffentliche Restaurantliste und Detaildialog zeigen jetzt
Gesamtbewertung, Kategorien und jeweilige Anzahl. Fehlende optionale Angaben
werden nicht als null angezeigt. Drei fiktive Fälle bei vier Breiten geprüft,
zusätzlich bestehende Homepage-Prüfung bei sechs Breiten bestanden. Öffentliche
Einzelbewertungen, Namen und Kommentare bleiben ausgeschlossen. Ältere Angaben
zur ausstehenden Aggregatdarstellung sind damit überholt. Aktueller Restplan:
RESTABDECKUNG_GESAMTVORLAGE.md; weiterhin keine App-Implementierung.

Neuester Fachentscheid: Merch-Preis je Ausführung ist tatsächlicher Einkaufspreis
minus Zuschuss, ohne Vereinsmarge. Grössen/Varianten dürfen verschiedene Preise
haben; Ersatzanfrage muss geänderten Preis und neuen Mitgliederanteil zeigen.
Mit «ja» bestätigt; Rechenbeispiel im Merch-Verwaltungsentwurf. Visuelle
Nachführung der Ausführungspreise und Ersatz-Nachzahlung jetzt erfolgt und lokal geprüft; keine erneute Grundsatzbestätigung.

Neueste Nachführung: Merch-Hauptentwurf erhält Bestellbestätigungen bei Wiederöffnung
und wartet nach vollständiger Übergabe auf die noch offene Zahlung. Kontoentwurf
erhält die aktuelle Sitzung bei normaler Passwortänderung; Eventdetail zeigt
Getränke/Service optional und mittelt nur ausgefüllte Kategorien. 36 lokale
Layoutkombinationen plus gezielte Interaktionen geprüft. Öffentliche Aggregate,
Geldfluss-/Preisvarianten und vollständige Verknüpfung der Merch-Ausnahmeansichten
bleiben offen; keine neue App-Implementierung.

Aktuelle Nachführung vom 11. Oktober: finanz-ergaenzung.html zeigt private Essen
nur als Betragserinnerung; buchhaltung-prozesse.html erlaubt die Beispielbuchung
ohne Belegdatei; revision-korrektur-entwurf.html zeigt direkte Wiederöffnung
mit Grund durch Schatzmeister/Admin sowie markierte Admin-Stellvertretung bei
Revision. 36 Breiten-/Themenkombinationen und gezielte Ablaufprüfungen lokal
geprüft; nur Beispieldaten, keine App-Änderung. Ältere Absätze über ausstehende
Nachführung dieser drei Punkte sind dadurch überholt. Merch-Lieferausnahmen sind
jetzt in merch-lieferausnahmen.html ergänzt und mit «ok» gestalterisch bestätigt:
Teilübergabe, Einzelstorno mit gedeckeltem Zuschuss/Rückzahlung, Ersatz mit
Mitgliederzustimmung sowie Lieferantenausfall mit Folgenvorschau je Mitglied.
48 Layoutkombinationen und lokale Hauptinteraktionen geprüft. Grenzen in
MERCH_VERWALTUNG_ENTWURF.md; kein vollständiger Lieferanten-/Buchhaltungsabgleich.
Nächstes: gezielte Restabdeckung und Zusammenführung zur Gesamtvorlage,
keine neue umfassende Befundsuche.


**Massgeblicher Arbeitsplan:** [Restabdeckung vor Gesamtvorlage](RESTABDECKUNG_GESAMTVORLAGE.md).
Systemzustände/E-Mails sind gestalterisch bestätigt. R01–R05 übernehmen vorhandene
Muster mit konkreter Seitenzuordnung; R06–R12 benennen gezielte Ergänzungen.
Chart-/Altseitenzuordnung liegt in CHARTS_SONDERSEITEN_ZUORDNUNG.md vor:
zehn aktive Chartpositionen; GGL-Mehrpersonenvergleich und Ausgabenbalken als
Vorschläge jetzt mit «ok» bestätigt. R12 konzeptionell geklärt, nichts entfernt.
FINANZ_ERGAENZUNG_ENTWURF.md und finanz-ergaenzung.html sind mit «ok. weiter»
gestalterisch bestätigt; Gegenrichtungen/Ausgleichswege verbleiben unter B01.
VERWALTUNGSZUGAENGE_ENTWURF.md und verwaltungszugaenge-entwurf.html zeigen
R10 gestalterisch bestätigt: Google, Kalender, Einladung, Rollen; keine Fachfreigabe.
SEITENGELTUNG_GESAMTVORLAGE.md konkretisiert R01–R05; das CSV mit 83 eindeutigen
Baseline-Einträgen ist aktualisiert. Keine vollständige v2-/Routen-/Feldabnahme.
F2-Grundsatz jetzt entschieden: einziger Systemadmin muss im Bedarfsfall alle
Bereiche bearbeiten können, auch Finanzen. Frühere gegenteilige Empfehlung
verworfen. Getrennte Vorstand-/Funktions-/Bereichsrechte und gezielte
Zusatzfreigaben durch den Admin sind mit «passt» bestätigt, siehe
ROLLEN_ENTSCHEIDUNGEN.md: Marketingchef Merch/Öffentliches, Reisekommissar Reisen,
Organisation eigenes Event, Schatzmeister Buchhaltung, Revisor Prüfung.
F6 anschliessend ausdrücklich geändert: Systemadmin und
Schatzmeister dürfen abgeschlossene Jahre jeweils allein mit Grund wiederöffnen,
ohne Revisorzustimmung. Berichtshistorie/erneute Revision bleiben. Alte interaktive
Revisionsvorschau zeigt noch den überholten Zustimmungsweg; vor Gesamtvorlage
anpassen. Revisionsbestätigung jetzt beschlossen: regulär Revisor, bei Bedarf
stellvertretend Systemadmin mit sichtbarem Vermerk; Schatzmeister darf eigene
Buchhaltung nicht als geprüft bestätigen. F1-Mitgliederablauf jetzt bestätigt:
Passwortlink erhält MFA; Faktorverlust über Systemadmin nach persönlicher oder
telefonischer Identitätsprüfung; Sicherheitsreset/Deaktivierung widerrufen
Sitzungen und Gerätevertrauen; normale Passwortänderung erhält aktuelle Sitzung,
beendet andere. Eigener Admin-Notfallzugang jetzt ebenfalls bestätigt:
Codes getrennt vom Handy, dokumentierter technischer Weg über Hostingzugang,
kein zusätzlicher Ersatzadmin. Noch kein technischer Notfallweg umgesetzt/geprüft.
Ergänzendes F1-Bündel in KONTO_ZUGANG_ENTWURF.md jetzt mit «ja, passt» bestätigt
(erneute Bestätigung, Linkersetzung, externe Entzüge, Gerätevertrauen).
F7-Teilentscheide jetzt bestätigt: Bestellung verbindlich trotz vorläufigem Preis,
definitiver Preis ohne zweite Bestätigung. Bei Wiederöffnung Bestätigungen
erhalten, Bearbeitung möglich, unveränderte Bestellungen nicht neu einreichen.
Altverhalten im v2-Code/Mockup setzt auf Entwurf; vor Gesamtvorlage anpassen,
keine App-Änderung jetzt. Keine pauschale Freigabe später Rückschritte nach Zahlung.
Abschluss bei Zahlung UND Übergabe jetzt bestätigt; gesamte Runde automatisch
erst bei allen erledigten Bestellungen ohne offene Liefer-/Erstattungsfälle.
Auch Lieferausnahmen bestätigt: Teilmengen/Teilübergabe, positionsweises Storno
nicht verfügbarer Ware, Rückzahlungsbedarf bei bezahlten Ausfällen, ausdrückliche
Zustimmung zu Ersatz/anderer Ausführung, Lieferantenausfall gesammelt mit
Folgenvorschau je Mitglied. Noch im Mockup vor Gesamtvorlage ergänzen.
Vereinszuschuss jetzt bestätigt: fester Betrag je Mitglied/Runde, maximal
definitiver Warenwert, ungenutzten Zuschuss nicht auszahlen. Nach Storno anhand
verbleibender Artikel neu berechnen, überzahlten Eigenanteil zurückerstatten.
CHF 20 nur Beispiel, kein Standardbetrag. Änderungs-/Stornowege jetzt bestätigt:
offen durch Mitglied, nach Schliessung durch Merch-Verantwortliche/Admin, nach
Lieferantenauftrag erst Möglichkeit klären; nach Zahlung Vorher/Nachher mit
Zuschuss/Nach-/Rückzahlung, bestehende Zahlungen erhalten.
F8-Teilentscheidung: Bewertungen nach Anlass immer abgebbar/änderbar, keine
14-Tage-Frist; Getränke und Service optional, keine Nullwerte für fehlende
Angaben. Essen bleibt bestehendes Pflichtfeld. Siehe BEWERTUNG_GGL_ENTSCHEIDUNGEN.md.
Ausgefüllte Kategorien jetzt ausdrücklich gleich gewichtet; Einzelgesamtwert
als Mittel vorhandener Angaben. Restaurantaggregation jetzt bestätigt: jede
Einzelbewertung gleichgewichtet, auch über mehrere Besuche, unabhängig von der
Anzahl ausgefüllter Kategorien. Tatsächliche Anwesenheit als Berechtigung bestätigt.
GGL-Grundregeln aus DOMAIN.md jetzt bestätigt: Kalenderjahrsaison, absolute
Abweichung, N-bis-1-Punkte, geteilte Punkte bei Gleichstand, exakter Tipp gültig.
Ergänzende GGL-Regeln ebenfalls bestätigt: fehlender Tipp ohne Punkte und nicht
in N, kein Zusatzbonus bei exaktem Treffer, Ergebnisse bei Deaktivierung erhalten,
keine automatische historische Neuberechnung; Erfassungsfehler nachvollziehbar
durch Admin korrigierbar. Öffentliche Aufteilung jetzt mit «passt alles» bestätigt:
Restaurantgesamtwert/Kategorien/Anzahl öffentlich, Einzelbewertungen/Namen/
Kommentare intern, künftige Events mit Ort/Uhrzeit/Teilnehmenden geschützt,
Instagram nur verlinkt. Foto-/Text-/Kontakt-/About-Freigabe bleibt offen.
B01 gestartet, siehe BUCHHALTUNG_PRAXISABGLEICH.md: ein Vereinskonto, keine Kasse;
Schwerpunkt regelmässiger Kontoauszug mit vollständiger Ein-/Ausgangszuordnung.
Jahresausflug: beschlossenes Budget, Reisekommissar reicht Rechnung/Drive-Beleg
ein, Ausgabe erfassen, Schatzmeister bezahlt bei Bank, später Bankabgang verknüpfen.
Kartenausgaben auf Reisen aus Kontoauszug zuweisen. Private Essen: nur Betrag als
Erinnerung, selbstständige private Überweisungen, keine Vereinsbuchung; frühere
private Zahlungskontrolle nicht mehr notwendiger Zielablauf. Budgetbericht:
beschlossenes Budget vs. Ist, nächstes Budget vorschlagen und GV-Änderungen aufnehmen.
Ausflug weiter geklärt: Verein spricht Budget, zusätzliche Kosten privat und
nicht über die App abbilden; keine automatische Eigenbeitragsforderung erzeugen.
Belege grundsätzlich optional, Buchungen/Zuordnung ohne Rechnungsbeleg möglich;
fehlende Datei allein kein Fehler/Abschlussblocker. Mockups/Checklisten anpassen.
Budgetgliederung und alle 18 Posten aus scripts/seed_accounting_chart.py mit
«passt so» unverändert bestätigt; Nummern/Bezeichnungen in B01 dokumentiert.
Kein Live-DB-Abgleich, Script nicht ausgeführt. Jahreszuordnung: Nutzer delegiert
Standardwahl («so wie üblich»); Zahlungsprinzip gewählt, Bankbuchungsdatum zählt
für Jahres-Ist. Dezemberrechnung mit Januarzahlung zählt im neuen Jahr; offene
Rechnungen/Forderungen zum Jahresende separat sichtbar, keine Doppelzählung.
Begründung und Quelle in B01. Mit «ja» zusätzlich bestätigt: private Vereinsauslagen
erst bei Erstattung im bezahlten Ist; eine Überweisung auf mehrere Forderungen/
Mitglieder aufteilen; Merch-Lieferantenausgabe und Mitgliedereinnahmen ohne
zusätzlichen Zuschussabgang. Postendarstellung 6650/6660 noch ausarbeiten.
Budgetablauf mit «ja» bestätigt: Vorschlag aus bisherigem Budget möglich,
GV-Vergleich Budget/Ist/neuer Vorschlag, Beschlussbeträge und -datum erfassen,
Vorschlag und frühere Stände erhalten; spätere Änderungen mit Datum/Grund.
Schatzmeister und Admin bearbeiten ohne zusätzliche App-Freigaberunde.
Mitgliederbeiträge mit «ja» bestätigt: Jahresbetrag/Frist nach Vereinsbeschluss,
Mitgliedervorschau mit begründeten Ausnahmen, einmal je Mitglied/Jahr erzeugen,
offen/teilbezahlt/bezahlt durch Kontoabgleich, eigener Betrag für Mitglieder,
Erinnerung durch Schatzmeister nach Bedarf, keine automatischen Mahngebühren.
Zusammengeführter Arbeitsablauf in B01 dokumentiert. Neue interaktive Übersicht
buchhaltung-praxis-entwurf.html mit «sieht gut aus» gestalterisch bestätigt: Kontoabgleich, offene Ein-/Ausgänge, Beiträge, Budget/GV, Jahresabschluss.
60 Layoutkombinationen sowie ausgewählte lokale Interaktionen geprüft; genauer
Umfang und Grenzen in B01. Ältere Gesamtübersicht historisch, ergänzende Detail-
entwürfe weiter relevant. Merch-Darstellung (Kosten/geschuldete Anteile/Eingänge/Zuschuss) mit «ja» bestätigt; Agent hat Aufteilung derselben Ausgabe auf 6650/6660 in B01 konkretisiert. Sonderfälle und Nachführung dieser
Details bleiben offen; keine weitere pauschale Bestätigung beschlossener Kernabläufe.
Keine Buchhaltungs-Gesamtabnahme aus Mockups ableiten; gezielte Anpassung nötig.
Merch-Ausnahmeansichten, Preis-/Variantenfälle und Buchhaltungsanbindung bleiben
vor Gesamtvorlage auszuarbeiten, keine pauschale F7-Vollständigkeit behaupten.
Passwortänderungs-Vorschau vor Gesamtvorlage anpassen. Weitere F1-Details,
einzelne Aktions-/Sichtbarkeitsdetails, F7/F8 und
Buchhaltungspraxis separat offen. Frühe F7-Preisempfehlung gilt nicht ungeprüft
für Merch v2. Keine neue umfassende Befundsuche, keine App-Umsetzung.
Die folgenden Standabsätze sind historische Zwischenstände.

**Aktueller Einstieg:** Öffentliche Homepage gestalterisch bestätigt.
[Systemzustände und E-Mail](SYSTEM_EMAIL_ENTWURF.md) liegen zur Rückmeldung vor.
Danach konsolidierte Restabdeckung vor Block 7: bisherige Restvarianten,
Chartzuordnung mit elf Mitgliedern, Sonder-/Altseiten und F1/F2/F7/F8 bündeln.
Für jeden Restpunkt vorhandenes Muster, nötige Ergänzung oder Fachentscheidung
benennen. Keine pauschale Vollständigkeit, kein neuer Audit und keine App-Umsetzung.
Alle folgenden Standabsätze dokumentieren den bisherigen Verlauf.

**Aktuell:** Konto/Zugang gestalterisch bestätigt. Nutzer erlaubt ausdrücklich
eigenständiges modernes Design für die öffentliche Homepage. [Öffentlicher
Auftritt](PUBLIC_HOMEPAGE_ENTWURF.md) liegt jetzt zur Rückmeldung vor, mit
KI-Tischmotiv, Homepage und lokaler Restaurantliste. Keine echten Bewertungsdaten.
Nächster Teil von Block 6: System-/Offline-/Updatezustände und E-Mail-Vorlage.
F1/F2/F7/F8, öffentliche Event-Sichtbarkeit und dokumentierte Restvarianten offen.
Nachfolgende Standabsätze sind Verlauf; keine App-Umsetzung.

**Neuster massgeblicher Stand:** Dokumente/Uploads gestalterisch bestätigt.
[Konto, Einstellungen und Zugang](KONTO_ZUGANG_ENTWURF.md), Block 5, liegt zur
Rückmeldung vor. F1/F2 mit konkreten Optionen vorbereitet, ausdrücklich noch offen.
Danach Block 6 (öffentlicher Bereich, Systemzustände, E-Mail-Grundvorlage).
Restvarianten von Block 3–5 und Chartzuordnung bleiben vor Gesamtvorlage erforderlich.
Die nachstehenden Standabsätze sind historischer Verlauf.

**Aktuellster Stand:** Merch-Verwaltung gestalterisch bestätigt.
[Dokumente/Uploads](DOKUMENTE_UPLOAD_ENTWURF.md), Block 4, liegt zur Rückmeldung vor.
Danach Einstellungen/Zugang (Block 5). Restvarianten von Block 3 sind explizit
im Dokumentenentwurf und den Prozessdokumenten festgehalten; kein pauschaler
Blockabschluss, keine Fachfreigabe und keine App-Umsetzung. Ältere Standabsätze
unterhalb beschreiben den bisherigen Verlauf.

**Massgeblicher Stand:** Merch-Mitgliedersicht gestalterisch bestätigt.
[Merch-Verwaltung](MERCH_VERWALTUNG_ENTWURF.md) mit acht Schritten liegt jetzt
zur Rückmeldung vor. Wiederöffnung gezielt im Code geklärt: bestätigte Bestellungen
werden auf Entwurf zurückgesetzt; gewünschte Fachregel noch offen. Anschliessend
Restvarianten von Block 3 bündeln und Dokumente/Uploads (Block 4) bearbeiten.
Keine App-Änderung, keine pauschale Fachfreigabe.

**Aktuellster Entwurf 11.10.2026:** [Merch-Mitgliedersicht](MERCH_MITGLIEDER_ENTWURF.md)
mit Bestellrunde, Auswahl, Prüfung und Bestellstatus liegt zur Rückmeldung vor.
Noch nicht bestätigt; F7 und die genaue Abschlussregel bleiben offen. Nächster
Entwurf ist die Verwaltung der v2-Bestellrunde. Die älteren Standabsätze unten
sind Verlauf, insbesondere ist die Frage nach der Zielgeneration beantwortet.

**Merch-Ziel geklärt am 11.10.2026:** Nutzer wählt seine jüngere Überarbeitung.
Gezielter Git-Abgleich identifiziert Merch v2 mit Bestellrunden auf
`phase/10-merch-wip`, Commit `c90082e`, nicht im Auditbranch enthalten.
Weiter mit Mitglieder-/Verwaltungsentwurf dieser Version; Quellen und Grenzen
in [MERCH_ZIELVERSION.md](MERCH_ZIELVERSION.md). Altes System soll später operativ
stillgelegt werden, alte Daten als mögliche Migrationsquelle erhalten. Jetzt
kein Branchwechsel, Merge, Deploy, Deaktivieren oder Migrieren. Die frühere
Frage Einzelbestellungen/Bestellrunden ist damit beantwortet.

**Aktueller Stand:** Inline-Bearbeitung und Warteschlange sind gestalterisch
bestätigt. Für Merch ist die bereits dokumentierte Zielabweichung als Frage
vorgelegt: laufende Einzelbestellungen oder gemeinsame Bestellrunden, alternativ
Zielvariante offen und zunächst gemeinsame Darstellung. Antwort steht aus.
Keine Variante ohne Antwort als beschlossen behandeln. Grundlage MERCH_REVIEW.md,
Abschnitt «Tatsaechlicher Ablauf und Dokumentationsabweichung».

**Neuster Vorschlag 11. Oktober:** [Inline-Bearbeitung/Warteschlange](INLINE_WARTESCHLANGE_ENTWURF.md)
als zwei interaktive Bedienmuster erstellt und geprüft, noch nicht bestätigt.
Budget und Teilnahme sind lediglich Beispielkontexte; keine neuen Fachrechte.
Gestaltungszustimmung strikt von fachlichem Gesamtabgleich unterscheiden.
Merch, Import-Sammelaktionen und weitere Muster bleiben in der Gesamtübersicht offen.

**Aktueller Stand 11. Oktober 2026:** Revision und Abrechnungskorrektur sind
hinsichtlich Darstellung und gezeigter Benutzerführung bestätigt. Fachlicher
Gesamtabgleich der Buchhaltung bleibt offen; keine Umsetzungsfreigabe.
Als Nächstes verbleibende Muster für Inline-Bearbeitung und Warteschlangen
konkretisieren. Weitere Restvarianten in REVISION_KORREKTUR_ENTWURF.md erhalten.
Die nachfolgenden älteren Standabsätze sind Verlauf.

**Massgebliche Nutzerklarstellung:** Mockup-Zustimmung betrifft Gestaltung und
gezeigte Benutzerführung, nicht fachliche Vollständigkeit der Buchhaltung.
F3–F6 bleiben separat bestätigte Einzelregeln. Vor Umsetzung ist die tatsächliche
Vereinspraxis fachlich abzustimmen. [Revision/Korrektur](REVISION_KORREKTUR_ENTWURF.md)
liegt jetzt zur gestalterischen Rückmeldung vor; noch nicht bestätigt.
Restvarianten stehen dort und in der Gestaltungsabdeckung. Keine App-Umsetzung.

**Aktuell bestätigt:** Die drei Buchhaltungsprozessentwürfe (Buchung erfassen,
Beleg einreichen, Bankzahlungen zuordnen) wurden vom Nutzer bestätigt. Als
Nächstes Revision und finanzielle Korrekturen nach F3–F6 gestalten. Die Restliste
in BUCHHALTUNG_PROZESSE_ENTWURF.md bleibt offen. Keine Umsetzungsfreigabe.

**Neuster Stand Block 3:** Listen-/Tabellen-/Chartgrundmuster sind bestätigt.
Nutzerhinweis elf Mitglieder: alle bestehenden Charttypen vor Gesamtabschluss
zuordnen; kein pauschaler Abschluss durch den Einzelverlauf. Die
[Buchhaltungsprozesse](BUCHHALTUNG_PROZESSE_ENTWURF.md) zeigen Buchung, Belegeinreichung
und Zahlungszuordnung zur Rückmeldung. Als Nächstes weitere Fachprozesse gemäss
deren Restliste, insbesondere Revision/Korrektur. Noch keine Bestätigung dieser
neuen Prozessentwürfe und keine App-Umsetzung. Ältere Standabsätze sind Verlauf.

**Aktueller Stand Block 2:** [Listen, Tabellen und Charts](LISTEN_CHARTS_ENTWURF.md)
mit Mitgliederliste, Journal, Budgetvergleich und GGL-Verlauf erstellt. Zur
Rückmeldung, noch nicht bestätigt. Danach Fachprozesse (Block 3), dort auch
Inline-Bearbeitung/Sammelaktionen konkretisieren. Weitere Chartvarianten bleiben
explizit offen. Kein neuer Auditdurchlauf und keine App-Änderung.

**Neuster Entwurfsstand:** [Formulare/Bearbeitung](FORMULARE_ENTWURF.md) als
interaktive Event-/Profilbeispiele erstellt, lokal geprüft und bestätigt. Die
nächste Arbeit ist der Tabellen-/Chartblock; sensible
Formulare, Inline-Bearbeitung und Upload bleiben explizite Sondervarianten.

**Aktualisierung nach Nutzerfeedback:** Massgeblich ist jetzt die
[Gestaltungsabdeckung](ABDECKUNG_GESTALTUNG.md). App-Rahmen, Dashboard, Eventdetail
und Buchhaltungsübersicht sind als Beispiele bestätigt, BillBro mit Korrekturen
abgestimmt, F3 bis F6 fachlich bestätigt. F1/F2/F7/F8 bleiben offen.
Alle 83 Inventar-Templates sind in GESTALTUNGSZUORDNUNG.csv zugeordnet.
Als Nächstes Tabellen/Charts gestalten, danach die weiteren Blöcke
der Abdeckungsübersicht. Keine isolierte Fachfragenserie; alle unterschiedlichen
Muster gehören vor die abschliessende Gesamtvorlage. Die folgenden Absätze
beschreiben den ursprünglichen Einstieg. Weiterhin keine App-Umsetzung.

Das vorläufige Zielbild anhand der vorhandenen App konkretisieren: grafische Entwürfe für **Dashboard, Eventdetail und Buchhaltung**, jeweils Mobile und Desktop, ergänzt um Tablet-Regeln. Vorhandene Gestaltung und Seitenfamilien berücksichtigen. Dazu die entscheidungsrelevanten Fachfragen für Zugang und Geldflüsse vorbereiten.

Die Entwürfe sollen als Vorschläge beurteilbar sein. Keine neue umfassende Befundsuche beginnen. Zusätzliche Prüfungen brauchen eine konkrete offene Frage und eine Konsequenz für Zielbild, Entscheidung oder Abnahme. Die verbliebenen Abdeckungslücken bleiben im Abschlussplan sichtbar.

### Fortsetzung am 10. Oktober 2026

Die [Oberflächenentwürfe und Fachentscheidungen](OBERFLAECHENENTWUERFE.md) liegen
jetzt vor: drei interaktive Seiten in der Work-Unterhaltung mit Mobile-/Desktop-
und Tablet-Auswahl, ergänzende Layoutregeln und acht offene Fachentscheidungen.
Als Nächstes Rückmeldung zu den Entwürfen sowie F1 bis F8 einarbeiten. Die Vorschau
nutzt ausschliesslich Beispieldaten. Keine App-Umsetzung oder neue Befundsuche erfolgt.
Die Entwurfsspezifikation liegt lokal im Repository; ein Push dieses Nachtrags
ist damit nicht behauptet. Die interaktive Vorschau gehört zur Work-Unterhaltung.

## Entscheidungen und Grenzen

- Die vier Hauptbereiche und die Überarbeitung der bestehenden Technik sind vorgeschlagen, noch nicht als endgültiges Design beschlossen.
- Die sechs Umsetzungspakete sind Vorschläge; App-Änderungen, Auth-Änderungen, Migrationen und Deployment sind noch nicht freigegeben.
- Game/Essens-Pokemon bleibt ausgeschlossen. Seine vorhandenen lokalen Dokumente nicht verändern oder löschen.
- Alte Merch-Bestellseiten sollen später entfallen. Die noch vom aktuellen Shop genutzte Bestellverarbeitung muss erhalten oder gezielt umgezogen werden.
- Die Auditbelege beziehen sich auf Codebasis `bf4d84a`. Lokale Reproduktionen sind keine Produktions- oder Geräteabnahme. Neue Codeänderungen erfordern einen erneuten Abgleich der betroffenen Befunde.
- Vorhandene lokale Dateien bewahren. Keine produktiven Daten, Schlüssel oder externen Dienste durch die Entwurfsarbeit verändern.

## GitHub-Sicherung

Für die Übergabe wird ein eigener Branch `codex/app-audit-handoff-2026-10-10` verwendet. Der Name ist nur ein Git-Branchname und legt den Arbeitsmodus nicht fest: Fortsetzung ausdrücklich in **Work**.

Die Sicherung umfasst diesen Auditordner mit Berichten, Prüfskripten, Ergebnisdateien und Browserbelegen sowie den Eintrag in `docs/initiatives/README.md`. Andere bereits vorhandene lokale Dateien, insbesondere `build_logs.txt`, Game-Dokumente und die beiden unversionierten PWA-Hashkopien, gehören nicht zur Sicherung.

Für eine neue Projektkopie den Sicherungsbranch auswählen; die Unterlagen sind nicht durch diese Sicherung automatisch auf `master`. Keine Zusammenführung auf `master` nur für den App-Wechsel, da dies einen Railway-Deploy auslösen kann. Der tatsächliche Upload-Erfolg und der Link zur Sicherung werden nach dem Push in der bisherigen Aufgabe bestätigt.

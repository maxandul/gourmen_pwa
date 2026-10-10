# Gourmen PWA Gesamtbeurteilung und vorläufiges Zielbild

Stand 10. Oktober 2026. Erste Entscheidungsvorlage auf Basis des lokalen Codes `bf4d84a` und der vorhandenen Auditbelege. Das Gesamtaudit bleibt offen; die Gestaltung und Umsetzungspakete sind Vorschläge zur Rückmeldung.

Die Gourmen PWA deckt die wesentlichen Aufgaben des Vereins bereits ab. Meine Empfehlung ist, diese Grundlage schrittweise zu überarbeiten: zuerst Zugang und Datenverarbeitung verlässlich machen, danach die Fachabläufe und gemeinsame Bedienung vereinheitlichen und gezielt die Geschwindigkeit verbessern. Die bisherigen Befunde begründen keinen vollständigen Neubau oder Wechsel des technischen Systems.

Das grösste gemeinsame Problem sind Regeln, die je nach Einstiegsweg unterschiedlich gelten: bei Anmeldung und Rechten, bei Zahlungen und Statuswechseln sowie bei Navigation und Formularen. Eine Überarbeitung nach gemeinsamen Ursachen verspricht deshalb mehr Nutzen als 141 voneinander unabhängige Korrekturen.

## Was die bisherige Analyse trägt

Der [Prüfstand](COMPLETION_PLAN.md) umfasst 83 strukturell erfasste Templates, zahlreiche lokale Fach- und Fehlerproben, Browserbelege B-01 bis B-58 und 120 Messungen zur Anzahl der Datenbankabfragen. Der [Befundkatalog](FINDINGS.md) enthält 141 Einträge. Darunter sind reproduzierte Fehler, Strukturbeobachtungen und offene fachliche Entscheidungen; die Zahl ist weder eine Fehlerquote noch ein Fortschrittsmass.

Der vorhandene Testbestand bestand im früheren isolierten Lauf mit 69 Tests. Das belegt die dort geprüften Fälle, nicht die Fehlerfreiheit der App. Für diese Zusammenführung wurden keine Tests erneut ausgeführt. Produktiver Commit, tatsächliche Betroffenheit von Mitgliedern, reale Ladezeiten und Geräteverhalten sind nicht durch die lokale Baseline belegt.

Die Untersuchung hat einen hohen Detailgrad erreicht, während das Gesamtbild zurückblieb. Künftig steht diese Entscheidungsvorlage vor weiteren Vertiefungen. Offene lokale Prüfungen bleiben im Abschlussplan erhalten und werden danach geordnet, welche Entscheidung oder spätere Abnahme sie absichern.

## Was erhalten bleiben sollte

- **Die bestehende technische Grundlage:** Flask, serverseitige Templates, PostgreSQL und eine installierbare PWA sind kein durch das Audit belegtes Hindernis. Ein Wechsel würde zusätzliche Migration und neue Fehlerquellen schaffen, ohne die Fachregeln automatisch zu klären.
- **Die Vereinsfunktionen:** Events, BillBro, GGL, Dokumente, Merch und Buchhaltung bilden zusammenhängende Aufgaben ab. Diese Beziehungen sollten verständlicher und zuverlässiger werden.
- **Das vorhandene Designsystem:** Farben, semantische Designwerte, Hell-/Dunkelmodus und wiederverwendbare Elemente bieten einen Ausgangspunkt. Der Bedarf liegt vor allem in ihrer konsequenten Anwendung und ihrem Verhalten.
- **Die Trennung zwischen öffentlichem Auftritt und Mitgliederbereich:** Beide haben andere Aufgaben. Sie dürfen unterschiedlich aufgebaut sein, sollten aber erkennbare Gestaltung und klare Übergänge teilen.
- **Vorhandene positive Muster:** Das Event-Archiv hat eine Seitenteilung; das aktuelle CSS-Bundle entspricht beim textlichen Vergleich seinen Quellen; einzelne Dialoge bestehen bereits Fokus- und Escape-Proben. Diese Teile können gezielt weiterverwendet werden. Sie sind keine pauschale Abnahme ihrer gesamten Umgebung.

Quellen: [Architektur](../../ARCHITECTURE.md), [Komponenten](COMPONENT_REVIEW.md), [Frontend](FRONTEND_REVIEW.md), [Abfrageskalierung](QUERY_SCALING_REVIEW.md).

## Beurteilung der Bereiche

| Bereich | Grundlage und belegter Handlungsbedarf | Empfohlene Richtung |
|---|---|---|
| Öffentlicher Auftritt | Eigene öffentliche Ansichten sind vorhanden. Zeitgrenzen, Restaurantzuordnung und die Darstellung von Datenfehlern sind inkonsistent. Vertrauliche Events können in Auswertungen einfliessen. | Bestehenden Auftritt erhalten; Sichtbarkeit und Datengrundlage klären, Suche und Fehlerzustände verlässlich machen. Quellen: A-042, A-094 bis A-096. |
| Dashboard | Persönlicher Einstieg und offene Aufgaben sind angelegt. Die Bereinigungsberechnung belastet auch andere Seiten. Vollständige Prüfung der Summen und Aufgabenpriorität fehlt. | Den nächsten Anlass und konkrete offene Aufgaben priorisieren; Kennzahlen nachordnen. Bereinigung nur dort berechnen, wo sie gebraucht wird. A-030; PUBLIC_DASHBOARD_REVIEW.md. |
| Events und BillBro | Der gemeinsame Eventkontext ist sinnvoll. Änderungen nach Finalisierung, Zahlwegwechsel und einzelne Rücknahmen können widersprüchliche oder verlorene Daten erzeugen. | Eine Eventdetailseite mit klarer Teilnahme, Abrechnung und zulässigen Korrekturen. Statuswechsel gemeinsam mit ihren finanziellen Folgen behandeln. A-001, A-023 bis A-029, A-031, A-033, A-046, A-138. |
| GGL und Statistiken | Die Rangliste gehört zum Vereinsnutzen. Exakte Tipps, Gleichstände und berücksichtigte Mitglieder/Teilnahmen werden nicht überall gleich behandelt; Ergebnisse werden mehrfach berechnet. | Eine verbindliche Berechnungsgrundlage für Rangliste, Punkte und Diagramme. A-021, A-022, A-032, A-040, A-104. |
| Mitglieder und Zugang | Login, 2FA und zusätzliche Passwortbestätigung existieren. Alternative Zugangswege, alte Freigaben und Wiederherstellung halten die Schutzregeln teilweise nicht ein. Lesefehler können sensible Datensätze löschen. | Einen durchgängigen Lebenszyklus für Konto, Sitzung, 2FA und Zugangslinks festlegen; Lesefehler bewahren Daten. A-075 bis A-090, A-139 bis A-141. |
| Dokumente | Der Drive-Browser folgt dem zentralen Vereinsspeicher. Fehler zwischen Drive und App, Wiederherstellung, Suchzustände und Ordnerauswahl sind nicht durchgehend verlässlich. | Drive als führende Dateiablage beibehalten; klare Rückmeldungen und Wiederaufnahme bei Teilfehlern. A-091 bis A-093, A-126 bis A-136. |
| Merch | Der aktuelle Shop ist die geeignete Basis. Varianten, Preise, Bestellstatus und Forderungen können auseinanderlaufen. Alte Seiten werden laut Nutzerentscheidung nicht mehr benötigt. | Einen Shop und einen Verwaltungsablauf behalten; Bestellhistorie und finanzielle Folgen sichern. Alte Einstiege erst mit geklärter Bestellverarbeitung entfernen. A-048 bis A-056; UI_REGISTRY_REVIEW.md. |
| Buchhaltung und Revision | Import, offene Posten, Belege und Abschluss sind vorhanden. Belegt sind unter anderem doppelte Buchungen nach Teilfehlern, falsche Beträge/Zuordnungen und Lücken bei Abschluss und Historie. | Erst die fachliche Verlässlichkeit herstellen, danach die Oberfläche nach Aufgaben gliedern. A-057 bis A-074. |
| PWA und Betrieb | Installation, Offline-Ersatz, Kalender und Versand sind angelegt. Cachegrenzen, Updateverhalten, Fehlerstatus und wiederholter Versand benötigen Korrekturen oder zusätzliche Belege. | Private Daten bewusst behandeln; Updates erhalten laufende Eingaben; Versand und Betrieb zeigen tatsächliche Ergebnisse. A-010, A-101 bis A-118, A-124/A-125. |
| Wartbarkeit und Dokumentation | Gemeinsame Bausteine und Tests existieren. Kopien, Altpfade, manuelle Asset-Schritte und widersprüchliche Anleitungen erhöhen den Pflegeaufwand. | Eine gepflegte Quelle pro gemeinsamem Verhalten und Build-Schritt; Altlasten mit ihren Aufrufern entfernen. A-005 bis A-013, A-020, A-097 bis A-099. |

Die Detailbelege stehen im [Befundkatalog](FINDINGS.md) und seinen verlinkten Teilberichten. Die rechte Spalte ist die daraus abgeleitete Empfehlung.

## Probleme mit Vorrang

**Zugang und vertrauliche Daten:** Lokal bestätigt sind unter anderem nicht zuverlässig widerrufene Freigaben und Links, unbrauchbare Backup-Codes, protokollierte MFA-Geheimnisse und eine Aktivierung ohne zweiten Faktor bei gleichzeitig gültigem Aktivierungslink und eingerichteter 2FA. Diese Befunde rechtfertigen ein frühes Korrekturpaket. Sie belegen keinen tatsächlichen Missbrauch in Produktion. Der mögliche Zugriff auf fremde Cacheinhalte benötigt noch einen echten Browsernachweis; die fehlende Nutzerbegrenzung im Code ist bereits belegt. Quellen: [Zugang](AUTH_REVIEW.md), [PWA](PWA_PERFORMANCE_REVIEW.md) und [Befundkatalog](FINDINGS.md), A-010, A-075 bis A-083, A-110, A-140/A-141.

**Daten erhalten und Geld korrekt verarbeiten:** Ein simulierter Entschlüsselungsfehler löscht sensible Datensätze beim Lesen (A-086). Beim Bankimport kann ein Fehler nach der ersten Speicherung unvollständige Buchungen hinterlassen und eine Wiederholung weitere Buchungen erzeugen (A-060). Ebenso müssen Teilnahme, Forderung, Zahlung und Abschluss konsistent bleiben. Die erwarteten Regeln sind vor Änderungen an bereits bezahlten oder abgeschlossenen Vorgängen ausdrücklich festzulegen.

**Blockierende Bedienfehler:** Das Abschneiden von Inhalten im Desktoplayout ist reproduziert (A-014). Solche eng begrenzten Korrekturen sollten bei der späteren Umsetzung vor dem breiten Oberflächenumbau erfolgen. Die Priorität eines einzelnen Fehlers bleibt erhalten, auch wenn sein Gesamtpaket später kommt.

## Vorläufiges Zielbild für die Bedienung

### Vier Hauptbereiche und ein persönliches Menü

Die bestehenden Bereiche **Dashboard, Events, GGL und Verein** bleiben erhalten. Mobile zeigt sie unten, Desktop in der Seitenleiste. Jede Unterseite gehört zu einem dieser Bereiche; die Zuordnung folgt der Aufgabe. Event-Erstellung gehört zu Events, auch wenn die aktuelle Route technisch unter Administration liegt.

| Einstieg | Aufgabe im Zielbild |
|---|---|
| Dashboard | Nächster Anlass, eigene Teilnahme, offene Zahlungen und zu erledigende Aufgaben mit direktem Einstieg. |
| Events | Kommende und vergangene Anlässe; ein gemeinsamer Detailkontext für Teilnahme, BillBro und Bewertungen. |
| GGL | Saison, Rangliste und Entwicklung mit derselben fachlichen Datengrundlage. |
| Verein | Mitglieder, Dokumente, Merch und für Berechtigte Buchhaltung/Verwaltung. Die Darstellung unterscheidet verfügbare Aufgaben nach Rolle. |
| Persönliches Menü | Profil, Sicherheit, Kalender, Benachrichtigungen und Installation. |

Direkte Links in persönliche Aufgaben verkürzen den Weg, ersetzen aber keine Prüfung der Berechtigung auf dem Server. Die öffentliche Website behält ihren eigenen Einstieg mit Vereinsinformation, Restaurantübersicht und Anmeldung.

### Ein gemeinsamer Aufbau für Seiten und Aktionen

Eine Seite hat einen klaren Titel, einen nachvollziehbaren Rückweg und eine hervorgehobene Hauptaktion. Suche, Sortierung und Filter bilden einen eigenen Bereich; Erstellen, Bearbeiten und Löschen stehen bei den zugehörigen Inhalten. Filter dienen nicht gleichzeitig als verstecktes Menü für wichtige Aktionen.

Tabs wechseln zwischen Ansichten desselben Gegenstands. Unterschiedliche Arbeitsaufgaben erhalten eigene Einstiege. URL, ausgewählte Ansicht, abhängige Aktionen und Browser-Zurück müssen zusammenpassen. Die Buchhaltung wird deshalb vorläufig in **Buchen** (Import, Journal, offene Posten, Belege), **Planen und auswerten** (Budget, Statistik) und **Abschliessen und prüfen** gegliedert; der Kontenplan bleibt eine Verwaltungsaufgabe. Diese Gruppierung ist ein Gestaltungsvorschlag zur fachlichen Rückmeldung.

Formulare teilen Beschriftungen, Hilfen, Fehlermeldungen und Speichern/Abbrechen. Fehler erhalten eingegebene Werte. Dialoge benennen den betroffenen Gegenstand, führen den Tastaturfokus und geben ihn beim Schliessen zurück. Cards werden für zusammengehörige Inhalte verwendet; Tabellen bleiben dort, wo Zeilen und Beträge verglichen werden müssen.

### Drei repräsentative Ansichten

Diese Strukturentwürfe legen Inhalt und Reihenfolge fest. Sie sind noch keine grafischen Entwürfe oder geprüften Bildschirmansichten.

| Ansicht | Mobile | Tablet und Desktop | Woran die Verbesserung erkennbar wäre |
|---|---|---|---|
| Dashboard | Nächster Anlass zuerst, danach offene Aufgaben und Zahlungen; eine Spalte. | Anlass und Aufgaben dürfen nebeneinander stehen, Kennzahlen folgen darunter. | Ein Mitglied erkennt den nächsten nötigen Schritt und erreicht ihn direkt. Keine künstlichen Aufgaben bei leerem Bestand. |
| Eventdetail | Titel, Datum/Ort, eigene Teilnahme und relevante Aktion zuerst; BillBro/Bewertungen im selben Eventkontext. | Hauptinhalt mit ergänzenden Eventinformationen daneben, sofern genug Platz besteht. | Teilnahme, Schätzung und Abrechnung zeigen ihren Zustand und ihre zulässigen Aktionen. Beim Rückweg bleibt der Event-/Listenkontext erhalten. |
| Buchhaltung | Aufgabenübersicht vor Detailtabellen; wichtige Zeilenwerte sichtbar, weitere Spalten gezielt erreichbar. | Arbeitsbereich mit Filtern und gut vergleichbaren Tabellen; Detailbearbeitung mit klarem Rückweg. | Ein Import lässt sich prüfen, zuordnen und abschliessen, ohne zwischen unklaren Tabs zu suchen. Summen und Ergebnis bleiben nachvollziehbar. |

Tablet ist ein eigener Prüfbereich. Spalten entstehen nur, wenn der Inhalt Platz hat. Breite Tabellen dürfen in einem gekennzeichneten eigenen Bereich scrollen; die gesamte Seite darf nicht seitlich abgeschnitten werden. Lange Namen, grosse Schrift, Bildschirmtastatur, Tastaturbedienung und Hell-/Dunkelmodus gehören zur Abnahme.

### Technische Richtung hinter dem Zielbild

Gemeinsame Navigation, Formularfelder, Dialoge und Statusmeldungen erhalten jeweils eine gepflegte Implementierung mit begründeten Varianten. Fachliche Prozesse bleiben eigenständig: Ein Formularschritt, ein Eventwechsel und der Jahresabschluss dürfen ähnlich aussehen, haben aber unterschiedliche Regeln.

Zusammengehörige Datenänderungen brauchen eine ausdrücklich festgelegte Speichergrenze. Wiederholungen nach einem Fehler müssen denselben gewünschten Zustand ergeben. Bei Drive und Mail können externe Wirkung und lokale Speicherung auseinanderfallen; solche Teilzustände benötigen erkennbare Wiederaufnahme. Der gemeinsame Audit-Helfer darf nicht nebenbei fremde Änderungen speichern oder die weitere Datenverarbeitung blockieren (A-137 bis A-139).

Performance wird an den betroffenen Aufgaben gemessen. Der lokale GGL-Vergleich steigt beispielsweise von 46 auf 171 Datenbankabfragen bei 5 gegenüber 30 vergangenen Events; ein Teil stammt aus globaler Bereinigungsarbeit. Das zeigt vermeidbare Arbeit, aber keine entsprechende Vervielfachung der Ladezeit. Erst messen, dann gezielt zusammen laden, Ergebnisse wiederverwenden und unnötige Aufbereitung vermeiden. [Messbericht](QUERY_SCALING_REVIEW.md).

## Sechs vorgeschlagene Umsetzungspakete

Die Pakete sind die künftige Arbeitsgliederung, noch keine Umsetzungsfreigabe. Aufwand und Risiko sind relative Einschätzungen: **mittel** betrifft mehrere eng verbundene Teile, **gross** mehrere Abläufe oder gemeinsame Grundlagen. Daraus folgen keine belastbaren Tages- oder Kostenzusagen. Hoher Nutzen bedeutet Schutz vor Daten-/Zugangsproblemen oder eine häufig genutzte Verbesserung.

| Paket | Ergebnis und Nutzen | Aufwand und Änderungsrisiko | Abhängigkeit und Abnahme |
|---|---|---|---|
| U1 Zugang und Datenschutz | Einheitlicher Zugang, Widerruf von Sitzungen/Links/Freigaben, funktionierende Wiederherstellung, Datenbewahrung bei Lesefehlern und konsequente Sichtbarkeit. Nutzen: hoch. | Gross; hohes Risiko durch gemeinsame Authentifizierung. | Zuerst Regeln für Widerruf und Rechte festlegen. Abnahme: dieselben Rechte über alle Einstiege, frische 2FA wo erforderlich, alte Freigaben unwirksam, keine Secrets in Logs, Lesefehler ohne Löschung. Cacheprüfung gehört hierher. |
| U2 Datenintegrität und Geldflüsse | BillBro, Bestellungen, Import, Forderungen, Belege und Abschluss widerspruchsfrei speichern. Gemeinsame Transaktionsgrenzen klären. Nutzen: hoch. | Gross; hohes Risiko für Bestandsdaten und Historie. | Fachregeln für bezahlte/abgeschlossene Vorgänge klären; Audit-Helfer berücksichtigen. Abnahme: Teilfehler und Wiederholung erzeugen weder doppelte Buchungen noch halbe Zustände; Journal, Forderung und Auswertung stimmen überein. PostgreSQL-Prüfung erforderlich. |
| U3 Fachabläufe und Wiederaufnahme | Event-, GGL-, Merch-, Dokument- und Mitgliederabläufe funktionieren als zusammenhängende Ketten einschliesslich Abbruch, Fehler und Wiederholung. Nutzen: hoch. | Gross; mittleres bis hohes Risiko an Modulgrenzen. | Rechte aus U1 und Speicherregeln aus U2 übernehmen. Abnahme pro Ablauf: vollständiger Erfolgsweg, relevanter Fehler-/Rücknahmeweg und konsistente Ergebnisse; Eingaben bleiben bei Fehlern erhalten. |
| U4 Gemeinsame Oberfläche | Navigation, Seitenaufbau, Tabs, Formulare, Tabellen und Dialoge vereinheitlichen. Nutzen: hoch im täglichen Gebrauch. | Gross, in kleine Bausteine teilbar; mittleres bis hohes Risiko durch viele Verbraucher. | Zielbild und repräsentative Ansichten bestätigen; pro Baustein aktive Varianten erfassen. Abnahme: gleiche Bedienregeln, korrekter Rückweg, kein Abschneiden, Fokus und Fehlermeldungen funktionieren an den betroffenen Seiten und Breiten. A-014 als frühe Einzelkorrektur behandeln. |
| U5 Performance und Betrieb | Unnötige Abfragen reduzieren, Update-/Offlineverhalten und Versand verlässlich machen, reale Betriebsnachweise ergänzen. Nutzen: mittel bis hoch, Ladezeitgewinn noch zu messen. | Gross; mittleres bis hohes Risiko bei Cache, Updates und Zustellung. | Rechte/Datenschutz und fachliche Ergebnisse bewahren. Abnahme: definierter Vorher-/Nachher-Vergleich, gleiche Ergebnisse, sichere Updates mit Formulareingaben, nachvollziehbare Versandfehler; reale Geräte und Dienste gesondert belegen. |
| U6 Altlasten und Pflege | Alte Einstiege kontrolliert ablösen, Quellen und Build vereinheitlichen, Dokumentation berichtigen und wichtige Fehlerproben als Regressionstests übernehmen. Nutzen: mittel und dauerhaft. | Mittel bis gross; mittleres Risiko durch versteckte Aufrufer und alte PWA-Versionen. | Zielpfade aus U3/U4 festlegen. Abnahme: Redirects und verbleibende Verbraucher geprüft, reproduzierbare Assets, gültige Einstiegsdokumentation; keine Löschung allein aufgrund fehlender Suchtreffer. |

Empfohlene Umsetzungsfolge: zunächst kleine, getrennt abnehmbare Teile aus U1/U2 sowie blockierende Bedienfehler; danach U3/U4 anhand der vereinbarten Abläufe. Messungen für U5 beginnen vor der jeweiligen Optimierung. Dokumentationspflege und gezielte Regressionstests aus U6 begleiten jede Änderung; die abschliessende Bereinigung folgt nach dem Ablösen alter Pfade. Die Pakete sind keine sechs grossen Sammel-PRs.

Alle 141 bestehenden Befunde sind im [Paketregister](PAKETREGISTER.csv) genau einem federführenden Paket zugeordnet. Querschnittsabhängigkeiten bleiben bestehen, etwa U1 bei Uploadrechten, U2 beim Audit-Helfer und U4 bei Formularfehlern. Die Zuordnung ändert weder Belegstärke noch ursprüngliche Priorität und ist keine Bestätigung, dass alle Befunde bereits entscheidungsreif sind.

## Entscheidungen für die Rückmeldung

| Frage | Empfohlener Ausgangspunkt | Bedeutung |
|---|---|---|
| Wie weit soll der Umbau gehen? | Bestehende App gezielt überarbeiten und gemeinsame Oberfläche erneuern; Technik und Vereinsfunktionen erhalten. | Ein reiner Fehlerdurchlauf lässt Doppelspurigkeiten bestehen; ein Neubau braucht einen zusätzlichen, bisher fehlenden Nutzenbeleg. |
| Soll die Hauptnavigation bleiben? | Vier Bereiche beibehalten, Unterseiten eindeutig zuordnen und persönliche Einstellungen bündeln. | Bekanntes bleibt auffindbar; die Überarbeitung konzentriert sich auf Abläufe und Konsistenz. |
| Wie soll Buchhaltung aufgebaut sein? | Aufgabenbereiche Buchen, Planen/Auswerten und Abschliessen/Prüfen als Ausgangspunkt erproben. | Der Schatzmeister soll die Abfolge anhand eines Imports und Jahresabschlusses beurteilen. |
| Was gilt bei nachträglichen Änderungen an Zahlungen? | Bezahlte oder abgeschlossene Vorgänge nur über eine nachvollziehbare Korrektur ändern. | Vor U2 konkretisieren: Teilnahme, Zahlweg, Teilzahlung, Bestellpreis und Wiedereröffnung; keine rückwirkende Datenumschreibung ohne eigenen Plan. |
| Welche Fachregeln fehlen noch? | GGL-Rang-/Saisonregeln, Bewertungsrechte/-zeitpunkt, Preisbindung und blockierende Revisionsbeanstandungen ausdrücklich festhalten. | Ein dokumentiertes Verhalten ist nicht automatisch die gewünschte Vereinsregel. Betroffene Befunde unter anderem A-031/A-037/A-040/A-041/A-047/A-055/A-074. |

Bereits entschieden: Game bleibt ausgeschlossen. Alte Merch-Bestellseiten sollen später entfallen; die aktuelle gemeinsame Bestellverarbeitung und bestehende Einstiege müssen dabei erhalten oder gezielt umgeleitet werden. Die Zustimmung zur Zusammenführung ist keine Freigabe für Auth-Änderungen, Migrationen oder Deployment.

## Welche Prüfungen die Vorlage noch absichern müssen

| Nächste Prüfung | Konkrete Frage und Konsequenz | Abschlusskriterium |
|---|---|---|
| Gemeinsame Seitenmuster, K1 | Decken die drei repräsentativen Ansichten die aktiven Seitenfamilien ab? Welche Ausnahmen brauchen eigene Varianten? | Alle 83 Templates sind einer aktiven Familie, einem Partial oder einem begründeten Alt-/Sonderfall zugeordnet; vorhandene Belege wiederverwendet, offene Varianten einzeln benannt. Drei abgestimmte grafische Entwürfe folgen für die UI-Entscheidung. |
| Kritische Fachketten, K2 | Welche Änderungen sind nach Teilnahme, Rechnung, Zahlung und Abschluss erlaubt, und welche Wirkung muss gemeinsam gespeichert werden? | Für Event/BillBro, Merch, Import/Abschluss und Dokumentaktionen sind Zustände, Rollen und relevante Fehler-/Korrekturwege zusammengeführt; fachliche Entscheidungen ausdrücklich offen oder getroffen. |
| Sicherheits- und Speichergrenzen, K3 | Welche Einstiege umgehen gemeinsame Schutzregeln; welche Aufrufer brauchen eigene Transaktionsgrenzen? | Rollen-/Zugangsrestmatrix einschliesslich aktivem CSRF/Rate-Limit; Audit-Aufrufer nach Verantwortung klassifiziert. A-140/A-141 nicht erneut in bloss ähnlichen Varianten beweisen. |
| Reale Nutzungsbedingungen, K4 | Wie wirken Cache, Update, Netzwerk und Datenmenge auf zentrale Aufgaben? | Dokumentierter kalter/warmer Aufruf mit Datenumfang; PWA-Kontowechsel und Update mit offenen Eingaben im isolierten Browser; Produktions-/Gerätenachweise ausdrücklich getrennt. |
| Nachvollziehbarer Umfang, K5 | Welche Restobjekte und Doku-Aussagen fehlen noch, und beeinflussen sie ein Paket? | Jedes Restobjekt mit Nachweis, begründetem Ausschluss oder konkreter offener Frage verknüpft; kein neuer pauschaler Vollständigkeitsanspruch. |

Produktionskonfiguration, PostgreSQL, echte Zustellung, Drive-Freigaben, Safari/iOS sowie Backup und Wiederherstellung bleiben im [Betriebsnachweisregister](OPERATIONS_EVIDENCE_REGISTER.md). Sie sind weder bestätigte Fehler noch erteilte Freigaben. Lokale Lücken werden nicht als externe Einschränkungen umetikettiert.

Ein weiterer Test braucht eine offene Frage, eine Folge für Entscheidung oder Abnahme und ein Ende. Ähnliche Befunde werden unter ihrer gemeinsamen Ursache ergänzt. Der Abschluss richtet sich nach behandeltem Umfang und tragfähigen Empfehlungen, nicht nach einer Zielzahl von Befunden.

## Nächster Meilenstein

Als Nächstes wird das vorläufige Zielbild anhand der vorhandenen Seitenfamilien konkretisiert: Dashboard, Eventdetail und Buchhaltung erhalten repräsentative grafische Entwürfe für Mobile und Desktop, ergänzt um Tablet-Regeln. Gleichzeitig werden die noch offenen Fachentscheidungen für Zugang und Geldflüsse in wenigen klaren Fragen vorbereitet. Dabei entstehen noch keine Änderungen an der laufenden App.

Danach kann die Rückmeldung zu Umfang, Bedienung und Fachregeln in die endgültige Entscheidungsvorlage einfliessen. Die Restprüfung läuft gegen die oben genannten Abschlusskriterien weiter; sie wird nicht mehr zur Voraussetzung dafür, überhaupt ein Gesamtbild zu zeigen.

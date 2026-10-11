# Merch v2: Verwaltung der Bestellrunde

## Aktuelle Ergänzung: eine gemeinsame Beispielrunde

`merch-gemeinsame-runde.html` verbindet dieselben lokalen Daten in drei Rollen.
Nina: Shirt Navy M CHF 32 und Hoodie Navy L CHF 60, Zuschuss CHF 20, Anteil CHF 72.
Alex: Shirt Navy L CHF 34, Anteil CHF 14. Ben: Hoodie Navy M CHF 62, Anteil CHF 42.
Alex/Ben sind im Ausgangsbeispiel bezahlt und übergeben; Nina wird durchgespielt.
Gesamt CHF 188, Zuschuss CHF 60, Mitgliederanteile CHF 128.

Organisation fragt grauen Ersatzhoodie zu CHF 65 an; Nina sieht den neuen Anteil
CHF 77 und stimmt zu oder lehnt ab. Erst nach Zustimmung übernimmt Organisation
den Ersatz. Schatzmeister ordnet erste CHF 72 und zusätzliche CHF 5 getrennt zu;
erneute Zuordnung desselben Beispieleingangs gesperrt. Shirt/Hoodie separat
übergeben; Rundenabschluss erst nach vollständiger Zahlung und Übergabe.
Nach Ersatz Gesamt CHF 193, Zuschuss CHF 60, Mitgliederanteile CHF 133.
Bei Ablehnung bleiben bisherige Preise/Forderung; andere Lösung/Storno ist hier
ein sichtbarer Anschlussfall, kein fertig simulierter Folgeprozess.

Die Rundenauswahl beginnt nach verbindlicher Bestellung/definitiver Preisfestlegung.
Lieferantenzahlungen, Bankimport und Lagerzugang nicht simuliert; Übergabe setzt
vorliegende Ware voraus. Andere Ausnahmefälle bleiben im separaten Ausnahmeentwurf.
Rollenwahl ist ein Vorschauwerkzeug, kein echtes Berechtigungsmodell. Lokaler
Datenstand innerhalb des geöffneten Entwurfs; keine dateiübergreifende Speicherung.

Geprüft: drei Rollen bei sechs Breiten und Hell/Dunkel, Zustimmung vor Übernahme,
Zahlungserhalt, Nachzahlung, Teilübergabe, Abschlussblockade bei offenem Betrag,
Ablehnung. Mobile Abschlussansicht visuell geprüft. Die neue Ergänzung ist mit
«passt» gestalterisch bestätigt; keine App-Änderung.

Stand: 11. Oktober 2026. Gestaltung und gezeigte Benutzerführung mit
«ok, passt. weiter» bestätigt. Fachregeln und Sondervarianten bleiben offen.
Die Mitgliedersicht wurde vom Nutzer mit «top. passt. weiter mit dem nächsten»
hinsichtlich Gestaltung und gezeigter Benutzerführung bestätigt. Keine pauschale
Fachfreigabe von F7 und keine Umsetzungsfreigabe.

## Entwurf

**Nachführung 11. Oktober 2026:** Wiederöffnung im Hauptentwurf führt jetzt
zur Sammlung mit erhaltenen Bestätigungen, ohne erneute Einreichung unveränderter
Bestellungen. Bei der Verteilung bleibt die Beispielrunde nach drei Übergaben
offen, solange Bens Zahlung fehlt. Die simulierte Zuordnung dieses Eingangs
schliesst die vollständig übergebene Runde ab; keine offenen Lieferausnahmen
in diesem Normalfall. Die direkt wählbare abgeschlossene Ansicht bleibt ein
unabhängiger Beispielzustand, keine Berechtigung zum Überspringen echter Schritte.
Der Abweichungsdialog verweist inhaltlich auf die vier ergänzten Ausnahmefälle;
deren vollständige Integration als zusammenhängende Datenkette steht noch aus.

Prüfung dieser Nachführung gemeinsam mit Konto/Eventdetail: 36 Kombinationen
aus sechs Breiten und Hell/Dunkel ohne Seitenüberlauf oder Laufzeitfehler;
Wiederöffnung, Abschlussbedingung, Sitzungserhalt und optionale Bewertung lokal
durchgespielt. Bewertungsansicht auf Mobile visuell geprüft. Keine echten
Zahlungen, Sitzungen oder gespeicherten Bewertungen betroffen.

Interaktive Vorschau `merch-verwaltung-entwurf.html` im Visualisierungsordner
der Unterhaltung. Gemeinsamer App-Rahmen mit Logo, Navigation und Theme-Schalter.
Quelle der acht Schritte: `backend/services/merch_round_workflow.py` auf
`phase/10-merch-wip@c90082e`. Keine Übernahme von App-Code in den Auditbranch.

| Schritt | Dargestelltes Bedienmuster |
|---|---|
| Vorbereiten | Name, Frist, Zuschuss und Beispielsortiment; Öffnen mit Bestätigung. |
| Bestellungen sammeln | Drei Beispielbestellungen bei elf Mitgliedern; Schliessen mit Folgenvorschau. |
| Beim Lieferanten bestellen | Nach Ausführungen zusammengefasste Mengen, aufklappbare Bestellliste, Bestätigung einer extern aufgegebenen Bestellung. |
| Effektive Preise | Stückpreise, laufende Betragsvorschau und Bestätigung vor Übernahme. |
| Beleg | Rechnungssumme und mehrere Beispieldateien; Entfernen mit Dialog. |
| Wareneingang | Vollständige Lieferung bestätigen oder Abweichung anzeigen. |
| Verteilung | Übergabe je Bestellung mit Bestätigung und lokaler Rücknahme; Zahlungsstand bleibt separat. |
| Abgeschlossen | Gesonderter abgeschlossener Beispielstand mit Beträgen und Verlauf. |

Mobile: aktueller Schritt und einklappbare Schrittübersicht oberhalb des Inhalts,
Formularfelder und Aktionen bei Platzmangel untereinander. Desktop: Schrittübersicht
links, Arbeitsfläche rechts. Tablet: Übersicht oberhalb, Felder zweispaltig soweit
lesbar. Unter 850 Pixeln stapelt auch die Desktop-Vorschau. Keine breite Tabelle
für die mobile Verteilung. Vorschauauswahl erlaubt den direkten Blick auf jeden
Schritt; sie bildet keine produktive Berechtigungs-/Übergangsprüfung ab.

Schrittwechsel scrollt zum Arbeitsbereich. Eingaben bleiben innerhalb der lokalen
Vorschau erhalten. Kritische Übergänge verlangen eine Bestätigung; simulierter
Speicherfehler lässt den aktuellen Schritt und Eingaben bestehen. Native
Tastaturfokusanzeige bleibt erhalten, mobile Tapfläche ist transparent.

## Gezielt geklärte Codefrage

`MerchRoundService.apply_transition` und der Rückschritt aus Phase 3 rufen bei
Wiederöffnung `reset_confirmed_orders_to_draft_for_round` auf. Die gelesene
Implementierung in `backend/services/merch_order_service.py` setzt CONFIRMED
auf DRAFT, entfernt `confirmed_at` und berechnet Entwurfsbeträge neu.
Damit ist ein unveränderter Bestätigungsstatus bei Wiederöffnung aus der
Commit-Beschreibung allein nicht ableitbar. Kein neuer umfassender Audit.

**Zielregel anschliessend bestätigt:** Bei Wiederöffnung bleiben bestehende
Bestellungen bestätigt. Mitglieder dürfen während der erneuten Öffnung ändern;
unveränderte Bestellungen brauchen keine erneute Einreichung. Der oben gelesene
Code widerspricht diesem gewünschten Ziel und muss erst in der späteren
Umsetzung angepasst werden. Die alte Wiederöffnungsfolge im Mockup ist überholt
und vor Gesamtvorlage anzupassen; sie wird dort ohnehin nicht ausgeführt.

Auch bestätigt: keine zweite Bestätigung des definitiven Preises. Die Bestellung
ist trotz vorläufigem Preis verbindlich, der definitive Betrag wird mitgeteilt.
Rückschritte nach Lieferantenbestellung/Preisfestlegung/Zahlung sind damit nicht
pauschal freigegeben; Korrektur-/Stornofolgen bleiben offen.

Der gelesene `try_auto_close_if_complete` beschreibt automatischen Rundenschluss
nach vollständiger Zahlung und Abholung. Die Vorschau zeigt dies als Zielzustand;
sie erzeugt keine Zahlung, um den Abschluss zu erzwingen. Die abweichende
Mitglieder-Phasenzuordnung bleibt gemäss Mitgliederentwurf fachlich abzugleichen.

## Offene Varianten und Fachpunkte

### Bestätigter Abschluss und Lieferausnahmen

Die Abschlussregel wurde mit «ja das passt» bestätigt, die folgenden
Lieferausnahmen anschliessend mit «ja»:

- Bestellung erst abgeschlossen, wenn vollständig bezahlt und vollständig
  übergeben. «Bezahlt, Abholung offen» und «Übergeben, Zahlung offen» bleiben
  getrennt sichtbar. Die Runde schliesst automatisch, sobald alle Bestellungen
  erledigt und keine Liefer- oder Erstattungsfälle mehr offen sind.
- Teillieferung: gelieferte und fehlende Mengen getrennt führen. Bereits
  vorhandene Artikel dürfen übergeben werden; ausstehende Mengen bleiben offen.
- Endgültig nicht verfügbar: nur betroffene Position stornieren und definitiven
  Betrag neu berechnen. Unbetroffene Positionen bleiben erhalten.
- Bereits bezahlte Beträge bleiben nachvollziehbar erhalten. Entstehendes
  Guthaben als Rückzahlungsbedarf ausweisen, keine automatische Auszahlung.
- Ersatzartikel oder andere Ausführung benötigen ausdrückliche Zustimmung des
  betroffenen Mitglieds. Keine zweite Preisbestätigung bedeutet keine Erlaubnis
  für ungefragten Produktwechsel.
- Vollständiger Lieferantenausfall: betroffene Bestellungen gesammelt bearbeiten,
  zuvor Auswirkungen je Mitglied zeigen.
- Runde bleibt offen, bis Nachlieferung, Ersatz oder Storno einschliesslich
  erforderlicher Rückzahlung erledigt sind. Stornierte Mengen benötigen keine
  fiktive Übergabe; sie müssen als erledigter Ausnahmefall nachvollziehbar sein.

Diese Regeln ergänzen F7/R09. Die separate Vorschau `merch-lieferausnahmen.html`
zeigt jetzt vier konkrete Ausnahmefälle, siehe folgenden Abschnitt. Der ältere
Hauptablauf muss vor Gesamtvorlage noch damit zusammengeführt werden.
Ein Abschluss allein aufgrund PAID oder PICKED_UP ist im Ziel falsch.
Freiwillige Stornos/Rückgaben sind durch den Lieferausfallentscheid nicht
pauschal erlaubt. Buchhaltungsanbindung bleibt offen.

### Ergänzte Ausnahmeansichten: gestalterisch bestätigt

Stand 11. Oktober 2026: `merch-lieferausnahmen.html` im bestehenden
Visualisierungsordner. Mit «ok» am 11. Oktober 2026 gestalterisch bestätigt.
Die vier Fälle sind unabhängige synthetische Beispiele, kein gemeinsamer Datensatz:

- **Teillieferung:** Nina, Shirt CHF 32 vorhanden und Hoodie CHF 60 ausstehend;
  Zuschuss CHF 20, Eigenanteil CHF 72 bezahlt. Nur Shirt übergeben; Hoodie und
  Bestellung bleiben offen. Zahlung und Übergabe separat sichtbar.
- **Artikel nicht verfügbar:** Alex, Artikel CHF 75, Zuschuss CHF 20, bereits
  bezahlter Eigenanteil CHF 55. Hoodie CHF 60 fällt weg, Shirt CHF 15 bleibt;
  Zuschuss sinkt auf CHF 15, Eigenanteil auf null. CHF 55 Rückzahlung offen,
  kein Auszahlen der ungenutzten CHF 5 Zuschuss. Vorher/Nachher vor Storno sichtbar.
- **Ersatz:** Hoodie Navy CHF 60 durch Grau CHF 65. Eigenanteil steigt von
  CHF 72 auf CHF 77; CHF 72 bereits bezahlt, CHF 5 Nachzahlung bei Übernahme.
  Diese Preisfolgen sind vor der Zustimmung in der Mitgliedersicht sichtbar. Verwaltung
  legt Ersatz vor, Mitglied stimmt zu oder lehnt ab; erst nach Zustimmung kann
  Verwaltung den Ersatz übernehmen. Rollenwechsel ist nur eine Vorschaufunktion.
  Nach Übernahme bleiben Lieferung/Übergabe offen. Ablehnung zeigt Klärungsbedarf;
  erneutes Angebot oder Wechsel zum Storno ist noch nicht vollständig nachgebaut.
- **Lieferantenausfall:** Drei betroffene Mitglieder/vier Artikel, CHF 184
  Warenwert und CHF 124 bereits gezahlte Eigenanteile. Vor Sammelstorno explizite
  Folgen je Mitglied (CHF 12/40/72 zurück). Zuschuss/Warenwert danach null;
  Runde bleibt wegen Rückzahlungen offen. Keine automatische Auszahlung.

Mobile zeigt Vorgang und finanzielle Folgen untereinander; ab ausreichender
Entwurfsbreite (über 800 px) nebeneinander. Navigation und Hell-/Dunkelschalter
übernehmen den bestehenden App-Rahmen. Keine neue globale Designsprache.

Prüfung: 48 Kombinationen aus sechs Breiten (320 bis 1440 px), vier Fällen und
Hell/Dunkel ohne gemeldeten horizontalen Überlauf oder abgeschnittene Inhalte.
Teilübergabe, Einzelstorno, Ersatz-Zustimmungsweg und Folgenvorschau vor Sammelstorno
lokal geprüft; Mobile-/Desktopbilder visuell geprüft. Kein Backend-, Zahlungs-,
Lieferanten- oder echtes Gerät getestet. Zuschuss CHF 20 ist weiterhin nur Beispiel.
Lieferantenrückerstattung bei bereits bezahlter Lieferantenrechnung, andere
Ersatzpreise, Nachlieferungsabschluss und vollständiger Rückzahlungsabgleich
bleiben gezielte Ausarbeitung; keine pauschale Vollständigkeit von F7 behaupten.

### Bestätigte Zuschussregel

Ergänzung aus B01: Gesamte Lieferantenkosten, geschuldete Mitgliederanteile,
tatsächliche Mitgliedereingänge und Vereinszuschuss getrennt zeigen. Mit «ja»
bestätigt; offene Zahlungen erhöhen den Zuschuss nicht. Die Ausarbeitung der
Posten 6650/6660 teilt dieselbe Lieferantenausgabe auf und erzeugt keinen
zusätzlichen Bankabgang. Massgebliche Beispiele und noch zu spezifizierende
Sonderfälle: [Buchhaltungspraxis](BUCHHALTUNG_PRAXISABGLEICH.md).

Mit «ja» bestätigt: je Bestellrunde ein festgelegter Betrag pro bestellendem
Mitglied, höchstens der definitive Warenwert. Ungenutzter Zuschuss wird nicht
ausbezahlt. Bei Storno wird der Zuschuss anhand der verbleibenden Artikel neu
berechnet; bereits geleistete Eigenzahlungen bleiben erhalten und werden,
soweit sie den korrigierten Eigenanteil übersteigen, zurückerstattet.

Beispiel: CHF 20 Zuschuss, verbleibender Warenwert CHF 15 ergibt CHF 15
Zuschuss und CHF 0 Eigenanteil. Eine bereits geleistete Eigenzahlung ist dann
vollständig zurückzuerstatten. Die CHF 20 sind ein Beispiel, kein beschlossener
Standardbetrag für jede Runde. Die Regel gilt pro Mitglied/Runde, nicht pro
Artikel oder erneuter Einreichung.

### Preisregel je Ausführung: bestätigt

Mit «ja» bestätigt: Mitglieder tragen den tatsächlichen Einkaufspreis der
gewählten Ausführung, abzüglich Vereinszuschuss. Unterschiedliche Grössen oder
Varianten dürfen unterschiedliche Einkaufspreise haben. Keine zusätzliche
Marge des Vereins. Der Zuschuss bleibt einmal je Mitglied und Runde gedeckelt
auf den gesamten verbleibenden Warenwert, nicht einmal je Variante.

Ein Ersatzangebot zeigt auch den geänderten Preis und den neuen Mitgliederanteil
vor der Zustimmung. Daraus entstehende Nach- oder Rückzahlung wird bei Erhalt
bisheriger Zahlungen dargestellt. Die bereits bestätigte Verbindlichkeit der
ursprünglichen Bestellung trotz vorläufigem Preis bleibt bestehen; keine neue
zweite Bestätigung regulärer definitiver Preise.

Rechenbeispiel zur Ausarbeitung: Shirt CHF 32 plus Hoodie CHF 60, Zuschuss
CHF 20, Eigenanteil CHF 72 bereits bezahlt. Ersatz-Hoodie CHF 65 ergibt
Warenwert CHF 97, unverändert CHF 20 Zuschuss, CHF 77 Eigenanteil und CHF 5
Nachzahlung. Diese Folgen gehören in dieselbe Ersatz-Zustimmungsanfrage.
Keine beschlossenen Produktpreise. Ersatzmockup zeigt jetzt die CHF 5 Mehrkosten
und den neuen Eigenanteil vor Zustimmung, danach die offene Nachzahlung.
Der Hauptentwurf zeigt vier getrennte Ausführungspreise: Shirt M/L CHF 32/34,
Hoodie L/M CHF 60/62. Gesamtkosten CHF 188, Zuschüsse CHF 60, Eigenanteile CHF 128.
Zuschuss bleibt je Mitglied/Runde gedeckelt. Alle Zahlen sind synthetische Beispiele.
Summenänderung, ungültige Preisfelder und Zustimmungsweg mit Nachzahlung geprüft;
sechs Breiten für die Preisansicht und 48 Breiten-/Fall-/Themenkombinationen der
Lieferausnahmen geprüft. Mobile Ersatzansicht und Desktop-Preisfelder visuell geprüft.
Separate Liefernebenkosten sind mit dieser Artikelpreisregel nicht neu geregelt.

### Bestätigte Änderungen und freiwillige Stornos

Mit «passt» bestätigt:

- Solange die Runde offen ist, können Mitglieder selbst ändern oder stornieren.
- Nach Rundenschluss laufen Änderungen über Merch-Verantwortliche oder
  Systemadmin. Daraus folgt keine automatische Wiederöffnung der gesamten Runde.
- Nach Bestellung beim Lieferanten keine automatische Stornierung: Verwaltung
  klärt zuerst, ob Änderung oder Rückgabe möglich ist.
- Nach Zahlung zeigt jede bestätigte Änderung bisherigen und neuen Betrag,
  Zuschuss sowie nötige Nach- oder Rückzahlung. Bestehende Zahlungen bleiben
  erhalten. Rückzahlungsbedarf ist keine bereits ausgeführte Überweisung.

Dies ergänzt die Lieferausnahmen, bestätigt aber keine pauschale Zusage eines
Lieferanten zu Rücknahmen. Die Preisregel je Ausführung ist inzwischen oben
bestätigt; ihre konkrete Darstellung und Buchhaltungsanbindung bleiben auszuarbeiten.

### Verbleibende Ausarbeitung

- Einkaufspreise je Ausführung und Ersatz mit Preisfolge dargestellt; Mitgliedershop
  und vollständige Datenkette müssen bei der Zusammenführung dieselben Werte verwenden.
- Vier Lieferausnahmeansichten ergänzt; in Hauptablauf integrieren und verbleibende
  Änderungs-/Stornowege gezielt vervollständigen.
- Rückschritte nach Preisfestlegung, Beleg oder Zahlung und Umgang mit bestehenden
  Forderungen/Belegen. Kein beliebiges Zurücksetzen als freigegeben behandeln.
- Sortiment bearbeiten, echte Bestellliste exportieren, reale Uploads und
  Belegvorschau nutzen bestehende Muster, sind hier nicht vollständig nachgebaut.
- Rollen/Berechtigungen und Buchhaltungsanbindung müssen fachlich abgestimmt werden.

Die lokale Rücknahme einer Übergabe ist ein Bedienvorschlag, kein Nachweis eines
vorhandenen Serverpfads. Der finale Verlauf ist ein Beispiel, kein Auditprotokoll.

## Validierung und weiterer Ablauf

Lokaler Chromium-Test: acht Schritte auf 320, 390, 768, 820, 1024 und 1440 Pixeln,
kein äusserer Überlauf oder JavaScript-Fehler. Preisvalidierung/Betragsänderung,
gesperrte Wiederöffnung, Belegliste/Entfernen, Übergabebestätigung/Rücknahme und
Erhalt des Zahlungsstatus geprüft. Mobile/ Desktop visuell kontrolliert.
Keine Geräte-, Safari-, Produktions- oder Backendabnahme.

Nach Rückmeldung verbleibende Prozessvarianten in Block 3 bündeln; danach
Dokumente/Uploads (Block 4). Vor Gesamtvorlage bleiben insbesondere Import/
Bereinigung, Chartzuordnung mit elf Mitgliedern und Fachentscheidungen offen.

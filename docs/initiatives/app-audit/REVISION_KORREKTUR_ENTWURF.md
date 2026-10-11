# Revision und Abrechnungskorrektur – Darstellungsentwurf

Aktuelle Ergänzung R13 mit «ja» bestätigt: Während einer laufenden Revision
bleibt der eingereichte Stand unverändert. Schatzmeister oder Systemadmin kann
mit Grund zur Bearbeitung zurücknehmen, ohne Zustimmung abwarten zu müssen.
Danach neue Fassung vorlegen; frühere Fassungen und Prüfanmerkungen erhalten.
Eine alte Bestätigung gilt nicht automatisch für neue Daten. Diese Regel ist
fachlich festgelegt; die entsprechende Konkurrenzprüfung bleibt Umsetzungstest.

Stand: 10. Oktober 2026. Teil von Gestaltungsblock 3.
**Darstellung und gezeigte Benutzerführung am 11. Oktober 2026 bestätigt.
Fachlicher Gesamtabgleich der Buchhaltung offen. Keine Umsetzungsfreigabe.**

**F6 nachträglich geändert:** Systemadmin und Schatzmeister dürfen jeweils
allein ein abgeschlossenes Jahr mit Grund wiederöffnen, ohne Zustimmung des
Revisors. Berichtshistorie und anschliessende erneute Revision bleiben bestehen.
Die interaktive Vorschau ist jetzt nachgeführt: direkte Wiederöffnung mit Grund,
ohne Antrag oder Revisorzustimmung. Ebenfalls nachgeführt: reguläre Revision durch
Rechnungsprüfer, bei Bedarf stellvertretend durch Systemadmin mit sichtbarem
Vermerk; keine Revisionsbestätigung der eigenen Buchhaltung durch Schatzmeister.

Die Vorschau zeigt, wie Zuständigkeit, Sperre, Rückmeldung und finanzielle
Auswirkungen verständlich dargestellt werden können. Sie baut auf den ausdrücklich
besprochenen Regeln F3 und F6 auf. Zustimmung zu dieser Darstellung bestätigt
nicht automatisch die Vollständigkeit oder Praxistauglichkeit der Buchhaltung.
Keine Änderungen an App, Berichten, Buchungen oder Zahlungen.

## Darstellung der Revision

- Jahresstatus und Buchungssperre stehen unmittelbar unter dem Jahreskontext.
- Prüfpunkte unterscheiden Hinweise und blockierende Beanstandungen in Text
  und Status. Eine offene Beanstandung verhindert den Abschluss.
- Die Hauptaktion richtet sich nach Rolle und Zustand. Die Rollenwahl ausserhalb
  der App dient ausschliesslich der Vorschau; sie ist keine vorgeschlagene
  Möglichkeit, selbst Berechtigungen umzuschalten.
- Rückgabe und Wiedereröffnung verlangen einen Grund. Verlauf und bisherige
  Berichtsversionen bleiben sichtbar. Im aktuellen Ziel folgt nach Eingabe des
  Grundes direkt «Jahr wiederöffnen», ohne Antrag oder Revisorzustimmung.
- Mobile folgen Prüfpunkte/Aktionen vor Verlauf/Berichten; Desktop zeigt beides
  nebeneinander. Tablet verwendet bei knapper Breite dieselbe einspaltige Reihenfolge.
- Bestätigungsdialoge benennen die Folge der Aktion, behalten Fokus und erlauben
  Abbrechen/Escape. Nach einem Zustandswechsel wird der neue Seitenzustand sichtbar.

Durchspielbar: Beanstandung → begründete Rückgabe → beispielhafte Korrekturmeldung
durch Schatzmeister → erneute Freigabe → Bestätigung durch Revisor → abgeschlossener
Bericht v1 → begründete Wiederöffnung durch Schatzmeister oder Systemadmin
→ erneute Revision → Bericht v2,
während v1 erhalten bleibt. Die Korrekturmeldung simuliert lediglich einen
eine korrigierte Anlasszuordnung und bearbeitet keine echten Buchungsdaten.
Fehlende Belegdateien allein blockieren nicht; die Beanstandung ist inhaltlich.
Der erste Einstieg beginnt mit
einem bereits freigegebenen Jahr.

## Darstellung einer finanziellen Korrektur

Die Organisation bereitet eine begründete Korrektur vor. Der Ausschnitt zeigt zwei
synthetische Personen, kein vollständiges Essen mit allen elf Mitgliedern:

| Person | Bisheriger Anteil | Neuer Beispielanteil | Bezahlt bleibt | Ergebnis |
|---|---:|---:|---:|---|
| Nina | CHF 84.00 | CHF 78.00 | CHF 84.00 | CHF 6.00 Rückzahlung nötig |
| Alex | CHF 84.00 | CHF 78.00 | CHF 50.00 | CHF 28.00 weiterhin offen |

Alternativ lässt sich ein neuer Anteil von CHF 90.00 wählen. Diese Auswahl ist
eine Demonstration des Vorher/Nachher-Musters, kein vorgeschlagener Ersatz der
BillBro-Berechnung. Beträge werden später aus der tatsächlichen Korrektur berechnet.
Bezahlte Beträge bleiben erhalten; eine Rückzahlung wird nicht überwiesen.

Für betroffene Vereinszahlungen zeigt der Entwurf Vorlage an den Schatzmeister,
Bestätigung oder begründete Rückgabe. Eine Entwurfsoption demonstriert die Sperre
eines betroffenen Jahres. F2 ist inzwischen entschieden: Systemadmin darf
bereichsübergreifend bearbeiten; reguläre Fachrollen bleiben erhalten.

Nachführung am 11. Oktober 2026: Systemadmin als eigene Vorschaurolle, deutlich
gekennzeichnete stellvertretende Revisionsbestätigung im Verlauf, kein Selbsttestat
des Schatzmeisters. Neue Darstellung zur Rückmeldung, keine neue Fachentscheidung.

## Drei getrennte Abstimmungsstände

| Ebene | Status |
|---|---|
| Gestaltung/Benutzerführung dieser Vorschau | Am 11. Oktober 2026 bestätigt; nur im dargestellten Umfang. |
| Einzelregeln F3–F6 | Bereits ausdrücklich besprochen und bestätigt; weiterhin getrennt dokumentiert. |
| Gesamte Buchhaltung in der Vereinspraxis | Offen: vor Umsetzung anhand konkreter Vorgänge und Zuständigkeiten durchgehen. |

Im fachlichen Gesamtabgleich sind unter anderem tatsächliche Buchungsarten,
Konten-/Budgetbedarf, Bankabgleich, Zahlungen für andere Personen, Erstattungen,
Belegverantwortung, Prüfunterlagen und der reale Jahresabschluss zu behandeln.
Dies sind Themen für die spätere Abstimmung, keine hier beschlossenen Regeln.

## Grenzen und verbleibende Entwürfe

Private Auslagen und Zahlwegwechsel nach F4, komplette Buchungs-/Korrekturhistorie,
Berichtsinhalte, Fehler bei Berichtserstellung, Konkurrenz mehrerer Bearbeitender,
Importvorstufen/Sammelzuordnung und Inline-Kontenbearbeitung sind hier nicht
vollständig dargestellt. Ebenso bleiben Bereinigung und Merch in Block 3 offen.
Der Entwurf schliesst weder das Buchhaltungsmodul noch Block 3 ab.

Die Bedienung wurde lokal in Chrome bei 320, 390, 768, 820, 1024 und 1440 px geprüft:
kein horizontaler Seitenüberlauf, begründete Rückgabe, Rollen-/Statusaktionen,
Abschlusssperre durch Beanstandung, Berichtsversionen und Korrekturdifferenzen.
Mobile Korrektur und Desktop-Revision wurden visuell geprüft. Dies ist keine
Finanz-, Produktions-, Berechtigungs- oder Geräteabnahme der laufenden App.

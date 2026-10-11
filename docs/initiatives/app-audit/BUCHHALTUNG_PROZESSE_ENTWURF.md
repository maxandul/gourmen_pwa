# Buchhaltungsprozesse – erster Entwurfsblock

Stand: 10. Oktober 2026. Teil von Block 3 der Gestaltungsabdeckung.
**Darstellung und gezeigte Benutzerführung der drei Beispiele sind bestätigt.
Fachlicher Gesamtabgleich offen. Keine Umsetzungsfreigabe.**

**Aktueller Praxisabgleich:** BUCHHALTUNG_PRAXISABGLEICH.md konkretisiert jetzt
ein Vereinskonto ohne Kasse, Reise-Rechnung vor Zahlung, Kartenausgabe vor
Zuordnung sowie Budget/Ist und GV-Vorschlag/Beschluss. Bankabgleich muss Ein-
und Ausgänge gleichermassen abdecken. Frühere Mockups entsprechend nachführen.
Belege sind nach ausdrücklicher Nutzerregel generell optional: Buchung und
Zuordnung müssen ohne Rechnungsbeleg möglich sein. Ein freiwilliger Upload
behält seine technischen Dateiprüfungen; daraus entsteht keine Belegpflicht.
Die interaktive Buchungsvorschau ist jetzt nachgeführt: Standardbeispiel ohne
Belegdatei bis zum Speichern durchspielbar, Zuordnung zu vorhandenen Posten
6700/6541. Der freiwillige Beleg-Upload behält seinen eigenen Ablauf.

Nutzerklarstellung: Die Buchhaltung ist noch nicht im Detail auf die tatsächlichen
Bedürfnisse und Vereinsabläufe abgestimmt. «Sieht gut aus» gilt für Gestaltung
und Benutzerführung, nicht als fachliche Gesamtabnahme. Nur ausdrücklich
besprochene Einzelregeln wie F3–F6 werden als fachlich bestätigt geführt.

Die Bestätigung umfasst Buchung erfassen, Beleg einreichen und Bankzahlungen
zuordnen im dargestellten Umfang. Die unten aufgeführten Restvarianten bleiben
offen. Als Nächstes folgen Revision und finanzielle Korrekturen nach F3–F6.

Grundlage: ACCOUNTING_REVIEW.md, bestätigtes Formularmuster und bestätigte
Finanzregeln F3–F6 in OBERFLAECHENENTWUERFE.md. Keine neue Befundsuche.
Die Vorschau enthält ausschliesslich synthetische Beispiele und schreibt weder
Buchungen noch Dateien oder Zahlungen. Dateiauswahl liest nur den Dateinamen;
für eigene Dateien zeigt diese Vorschau noch keine Bild-/PDF-Vorschau.

## Drei bewusst unterschiedliche Abläufe

| Ablauf | Entwurf | Abschluss |
|---|---|---|
| Buchung erfassen | Angaben → Konto zuordnen → Prüfen. Geschäftsjahr sichtbar, CHF-Betrag rappengetreu, Datum innerhalb des Jahres. | «Buchung speichern» mit Ergebnisbestätigung; zurück zum Journal mit erhaltenem Kontext in der späteren App. |
| Beleg einreichen | Beleg → Angaben. Lesbarkeit prüfen, Beschreibung und eigener zugänglicher Anlass; Rückkehr zum Beleg ohne Eingabeverlust. | «Beleg einreichen» bedeutet zur Prüfung eingereicht, noch nicht verbucht. Rückziel: eigene Belege, keine unberechtigte Buchhaltungsseite. |
| Bankzahlungen zuordnen | Eingang auswählen → Zuordnung vorbereiten → Folgen prüfen → bestätigen. Desktop Liste und ausgewählter Eingang nebeneinander, Mobile untereinander. | Ergebnis mit aktualisierter Forderung, unveränderter Bankbewegung und nachvollziehbarer Zuordnung. |

Die Konten-/Forderungsauswahl ist im Beispiel reduziert. Der vollständige
Kontenplan, Rechte, Zuordnung zu mehreren Forderungen sowie Belegverknüpfung
müssen bei der Übertragung fachlich vollständig abgebildet werden. Aus diesen
Beispielfeldern folgt keine neue Pflichtfeld-, Konten- oder Berechtigungsregel.
F2 ist in ROLLEN_ENTSCHEIDUNGEN.md entschieden; gezeigte Rollen dieses Ausschnitts
sind Mitglied und Schatzmeister, nicht die vollständige Berechtigungsmatrix.

## Bankfälle nach bestätigtem F5

- CHF 50.00 auf CHF 84.00: CHF 34.00 bleiben offen.
- CHF 90.00 auf CHF 84.00: CHF 6.00 benötigen die ausdrückliche Zuordnung durch
  den Schatzmeister als freiwillige Aufrundung, weitere Forderung oder
  Rückzahlungsbedarf. Keine vorausgewählte Aufrundung.
- Eine mögliche echte Doppelzahlung bleibt zur Klärung offen. Sie wird nicht
  automatisch als Einnahme verbucht. Wiederimport derselben Banktransaktion ist
  davon getrennt und darf keinen neuen Zahlungseingang erzeugen.
- «Später klären» erstellt keine Buchung. Rückzahlungsbedarf ist ein Status,
  keine ausgelöste Banküberweisung.

Die Vorschau zeigt den Arbeitsplatz nach einem Import. Dateiimport, Fehler in
Importzeilen, Sammelzahlungen und Wiederimport sind noch kein vollständig
ausgestalteter Upload-/Importprozess. Erneute Versuche nach unklarem Servererfolg
müssen später den vorhandenen Vorgang prüfen und dürfen nicht doppelt buchen.

## Gemeinsame Interaktionsregeln

- Vorwärts prüft die Angaben des Schrittes. Fehler erhalten die Eingaben;
  Fehlermeldung und Fokus zeigen die notwendige Korrektur.
- Rückwärts und «Bearbeiten» erhalten den Entwurf; Schrittwechsel führt zum
  sichtbaren Beginn des neuen Schrittes. Kein automatisches endgültiges Speichern.
- Verlassen eines begonnenen Entwurfs verlangt Weiterbearbeiten oder Verwerfen.
- Abschlussfehler zeigt fehlende Bestätigung, behält Eingaben und ermöglicht
  Wiederaufnahme. Vorschau demonstriert den Fehler über eine Entwurfsoption;
  technische Wiederholsicherheit ist weiterhin ein Umsetzungskriterium.
- Jahr in Revision sperrt finanzielle Änderungen gemäss F6. Die Entwurfsoption
  zeigt die Sperre; sie ersetzt keine serverseitige Berechtigungsprüfung.
- Neue, noch nicht zugeordnete Mitgliedsbelege sind getrennt von der Änderung
  eines gesperrten Jahres zu betrachten. Zuordnung/Verschieben in gesperrte Jahre
  bleibt gesperrt; Detaildarstellung folgt beim Revisions-/Dokumentenablauf.

## Noch innerhalb von Block 3 auszuarbeiten

1. Revision/Jahresabschluss, Rückgabe und versionierte Wiedereröffnung nach F6.
2. Finanzielle Korrektur und Zahlwegwechsel mit Vorher/Nachher nach F3/F4.
3. Konten-/Budgetbearbeitung im Tabellenkontext, insbesondere lokale Aktionen.
4. Importvorstufe/Sammelzuordnung und konkrete Fehler-/Teilerfolgssituationen.
5. Bereinigung als Warteschlange mit Skip/Back/Undo.
6. Merch samt gezielter Klärung des Zielprozesses und F7.

Uploadfortschritt, Kamera, technische Dateigrenzen und Drive-Teilfehler werden mit
dem Dokumenten-/Uploadmuster in Block 4 konkretisiert. Damit wird ein einfacher
Belegeinreichungsentwurf nicht als vollständiger Uploadabschluss ausgegeben.

## Prüfung

Drei Einstiege bei 320, 390, 768, 820, 1024 und 1440 px in lokalem Chrome ohne
horizontalen Seitenüberlauf geprüft. Betragsvalidierung/19.99, Rückwege und
Eingabenerhalt, Abschlussfehler/erneuter Versuch, Jahrssperre, Teilzahlung,
Überzahlung/Rückzahlungsbedarf, Doppelzahlung und Belegeinreichung demonstriert.
Mobile Prüf-/Zuordnungsansicht und Desktop-Arbeitsplatz visuell geprüft.
Keine produktive Finanzprüfung und keine reale Geräte-/Safariabnahme.

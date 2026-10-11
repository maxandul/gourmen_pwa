# Dokumente und Uploads: Gestaltungsentwurf

Aktuelle Fachregel: R13 in ROLLEN_ENTSCHEIDUNGEN.md ist mit «ja» bestätigt.
Gemeinsame Dokumente für Mitglieder lesbar, Pflege durch zuständige Rolle oder
gezielte Pflegefreigabe; Vorstand/Event/Finanzbelege entsprechend eingeschränkt.
Archivieren/Wiederherstellen durch Pflegeberechtigte, endgültiges Löschen durch
Systemadmin unter Prüfung von Verknüpfungen/Aufbewahrung. Direkte Drive-Zugriffe
müssen die Grenzen ebenfalls einhalten. Ältere Offen-Markierungen dieser
Grundregeln sind überholt; technische Durchsetzung und Konfliktfälle bleiben Abnahme.

Stand: 11. Oktober 2026. Block 4, Gestaltung und gezeigte Benutzerführung durch
«passt, weiter» bestätigt. Genannte Fach-/Umsetzungsfragen bleiben offen.
Grundlage: vorhandener DOCS_REVIEW.md und Gestaltungsabdeckung. Kein neuer
Auditdurchlauf, kein Zugriff auf Drive und keine Änderung an der App.

## Darstellung

Interaktive Vorschau: `dokumente-upload-entwurf.html` im Visualisierungsordner
der Unterhaltung. Beispieldateien und Dokumentvorschau sind synthetisch.

| Ansicht | Gestaltung und gezeigtes Verhalten |
|---|---|
| Ordnerübersicht | Ordner und Dateien als unterscheidbare Zeilen mit Lucide-Icons; Dateiname, Format, Grösse und Datum. Leere Ordner haben einen expliziten Hinweis. |
| Suche | Suche nach Dateiname über alle aktiven bzw. archivierten Beispieldokumente. Suchumfang ist beschriftet, Treffer enthalten den Ablageort. Kein Treffer mit Rücksetzoption. |
| Dokumentdetail | Vorschau und Metadaten; Datei öffnen als Hauptaktion, Umbenennen/Verschieben daneben, Archivieren als nachgeordnete Aktion. |
| Upload | Datei, Titel und sichtbarer Zielordner; Fortschritt und anschliessende Bestätigung. Erfolgsaktion öffnet den tatsächlichen Zielordner. |
| Ordnerwahl | Eigener Schritt innerhalb derselben Arbeitsfläche. Eine Hierarchieebene gleichzeitig, Elternziel und gewählter Pfad bleiben sichtbar. Zurück/Abbrechen erhalten Uploadangaben. |
| Archiv | Getrennter Bestand, Archivieren mit Folgenbeschreibung und Bestätigung; Rücknahme sowie Wiederherstellen im Beispiel. |

Auf Mobile und Tablet stehen Ordnerinhalt, Detail und Upload jeweils in einer
Spalte. Der Rückweg führt zum Elternordner bzw. zur auslösenden Übersicht.
Desktop zeigt ergänzend eine eingerückte Ordnernavigation und Dokumentvorschau
neben Metadaten. Unter 850 Pixeln fällt auch diese Ansicht auf eine Spalte zurück.
Lange Dateinamen umbrechen. Keine horizontale Tabelle und keine zusätzlichen
verschachtelten Dialoge für den Zielordner. Ablagepfad ist eine Information,
keine neue globale Breadcrumb-Navigation.

## Interaktion und Fehler

- Suche und Ausgangsordner bleiben bei Detail/Zurück erhalten. Schrittwechsel
  scrollen an den Beginn der Arbeitsfläche; Fokus geht auf den passenden
  Rückweg, das Feld oder den auslösenden Button.
- Fehlende Datei oder fehlender Titel werden lokal mit Text und Feldfokus gezeigt.
  Gleicher Dateiname im Uploadziel führt zur Titelkorrektur statt Überschreiben.
- Verlassen eines bearbeiteten Uploads fragt nach Verwerfen oder Weiterbearbeiten.
  Ordnerwahl ist kein Verwerfen; Eingaben und Dateiauswahl bleiben erhalten.
- Während der Übertragung zeigt die Vorschau Fortschritt und verhindert
  mehrfaches Absenden. Sie bietet keinen vermeintlich sicheren Uploadabbruch.
- Sicher fehlgeschlagene Übertragung: Auswahl und Angaben bleiben erhalten,
  ausdrücklicher erneuter Versuch möglich.
- Unklarer Speicherstand nach Übertragung: Status zuerst prüfen statt erneut
  hochladen. Das Beispiel findet die vorhandene Datei und zeigt sie ohne Duplikat.
  Weitere mögliche Abgleichergebnisse gehören in die spätere Implementierung.
- Offline/Aktualisierungsfehler: letzter Bestand bleibt als solcher beschriftet;
  Änderungen benötigen eine Verbindung. «Erneut prüfen» simuliert Erholung.
- Native Fokusmarkierung bleibt erhalten; transparente mobile Tapfläche.

Die Entwurfsoptionen bieten Uploadausgang (Erfolg/Fehler/unklar) sowie eine
Lesesicht. Das ist keine neue Rechtevergabe. Die im Audit dokumentierte gemeinsame
Dokumentpflege und die getrennten Event-/Belegrechte sind weiter abzugleichen.

## Grenzen und offene Fach-/Umsetzungsfragen

- Keine tatsächliche Datei gewählt, übertragen oder geöffnet. «Beispieldatei»
  und Vorschau dienen nur dem Bedienablauf. Fortschritt ist simuliert.
- Uploadstatus-Abgleich, Duplikatschutz und Entwurfserhalt nach App-Neustart
  benötigen einen belastbaren Serververtrag; keine vorhandene Funktion behauptet.
- Nur ausgewählte UI-Zustände werden für die Unterhaltung gespeichert;
  Formulare und Dateiinhalt bleiben flüchtig und werden nicht an den Host gesendet.
- Zulässige Formate/Grössen, echte Vorschau/Kamera, Eventzuordnung und deren
  Sichtbarkeit, Synchronisationskonflikte und verschwundene Dateien bleiben offen.
- Endgültiges Löschen bleibt gesonderter Admin-/Archivfall gemäss vorhandenem
  Schutzkonzept. Hier keine neue Löschregel oder Löschfunktion vorgeschlagen.
- Rechte für Dokumente vs. Buchhaltungsbelege sind fachlich zu klären. «Alle sehen
  alles» für gemeinsame Dokumente darf keine Event-Sichtbarkeit aushebeln.
- Umbenennen zeigt Speichern/Abbrechen; Konflikte bei gleichem Namen, parallele
  Bearbeitung und externer Teilerfolg sind noch nicht vollständig simuliert.
- Grosse/tiefe Ordnerbäume, Pagination, mobile PDF-/Dateivorschau sowie native
  Zurück-Gesten und Fokus nach allen Fehlerkombinationen benötigen spätere Abnahme.

## Prüfung und Gesamtplan

Lokales Chromium: Ordnerübersicht bei 320, 390, 768, 820, 1024, 1440 Pixeln in
drei Verbindungszuständen ohne äusseren Überlauf oder JavaScript-Fehler.
Suche/Detail/Rückweg, Archivansicht, Ordnerwahl mit Entwurfserhalt, Pflichtfelder,
Verwerfen-Dialog, fehlgeschlagener und unklarer Upload, Statusprüfung ohne zweites
Dokument und Archiv-Rücknahme funktional geprüft. Mobile Upload-/Pickeransicht
und Desktopdetail zusätzlich kontrolliert, Upload/Detail visuell geprüft.
Kein Nachweis echter Geräte, Safari, Server- oder Drive-Verhalten.

Merch-Verwaltung ist durch «ok, passt. weiter» hinsichtlich Gestaltung und
gezeigter Benutzerführung bestätigt. Fachregeln bleiben offen. Block 3 wird durch
den Wechsel zu Block 4 nicht als vollständig abgeschlossen markiert: Import-
Vorstufe/Sammelaktionen, Bereinigungssonderfälle und die dokumentierten Merch- und
Buchhaltungsvarianten bleiben auf der Restliste. Nächster neuer Gestaltungsblock
nach Dokumenten: Einstellungen und Zugang (Block 5). Alle Restvarianten und
Chartzuordnung müssen vor Block 7 ausdrücklich entschieden oder zugeordnet sein.

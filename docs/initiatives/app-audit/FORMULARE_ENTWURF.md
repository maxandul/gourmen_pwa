# Formulare und Bearbeitungsseiten – Gestaltungsvorschlag

Stand: 10. Oktober 2026. Block 1 der [Gestaltungsabdeckung](ABDECKUNG_GESTALTUNG.md).
**Gemeinsames Formularmuster vom Nutzer bestätigt. Keine Umsetzungsfreigabe.**

Die interaktive Vorschau zeigt Event- und Profilbearbeitung in Mobile, Tablet
und Desktop sowie Hell-/Dunkelmodus. Sie verwendet ausschliesslich Beispieldaten.
Die Feldauswahl ist repräsentativ, kein vollständiger Ersatz der bestehenden
Formulare und keine neue Festlegung fachlicher Pflichtfelder oder Berechtigungen.

## Gemeinsamer Aufbau

- Elternziel oben als «Zum Event» bzw. «Zum Profil», darunter ein klarer Seitentitel.
- Inhalt nach fachlichen Gruppen ordnen; sichtbare Labels über den Feldern.
  Pflichtfelder mit Stern und Erklärung, optionale Hinweise direkt beim Feld.
- Normale Bearbeitung bleibt eine Seite ohne künstliche Prozessschritte.
  Lange oder fachlich gestufte Prozesse erhalten ihren eigenen Entwurf in Block 3.
- Eine Speicheraktion für das gesamte Formular. Kein automatisches Speichern.
  Status «Ungespeicherte Änderungen» nach tatsächlicher Änderung.
- Speichern und Abbrechen am Formularende. Mobile: Speichern zuerst, beide
  Aktionen volle Breite; Desktop: gemeinsame Zeile, Speichern rechts.
  Zunächst keine zusätzliche feste Aktionsleiste über der Bildschirmtastatur.

## Bedienregeln

| Situation | Vorgeschlagenes Verhalten |
|---|---|
| Erste Eingabe | Kein automatisches Scrollen, keine Fehlermeldung vor einer Prüfung. |
| Ungültiges Speichern | Eingaben behalten; Fehlerzusammenfassung mit Links und Meldung am jeweiligen Feld. Erstes ungültiges Feld fokussieren und sichtbar positionieren. |
| Speicherfehler | Eingaben behalten, verständliche Meldung oberhalb des Formulars fokussieren, erneuten Versuch ermöglichen. Kein Erfolg behaupten. |
| Erfolgreiches Speichern | Zur Detailansicht zurückkehren, Erfolg melden und Titel fokussieren. Listen-/Tabkontext in der späteren App erhalten. |
| Abbrechen oder anderer Bereich, unverändert | Ohne Rückfrage zurück bzw. zum gewählten Ziel. |
| Abbrechen oder anderer Bereich, verändert | Dialog «Weiter bearbeiten» / «Änderungen verwerfen». Escape entspricht Weiterbearbeiten; Fokus kehrt zum Auslöser zurück. Verwerfen verlässt zum gewählten Ziel. |
| Theme-/Breitenwechsel | Eingaben bleiben erhalten, keine Verlassen-Rückfrage. |
| Mobile Tippen | Keine blaue Browser-Tapfläche; eigene gedrückte Rückmeldung. Sichtbarer Tastaturfokus bleibt erhalten. |

Browser-Zurück, Reload und Schliessen brauchen in der späteren App dieselbe
Datenerhaltungsabsicht, soweit der Browser eine Warnung erlaubt. Diese Vorschau
demonstriert nur die Navigation innerhalb des Entwurfs. Sie speichert keine
Formulareingaben dauerhaft und schreibt keine Daten in die App.

## Aktionen und notwendige Varianten

Bearbeiten steht auf der Detailseite als beschriftete Aktion. Löschen gehört
nicht neben Speichern in das gewöhnliche Formular, sondern zu den weiteren
Aktionen des Objekts mit Folgenbeschreibung und Bestätigung. Ob ein Objekt
überhaupt gelöscht, abgesagt oder archiviert werden darf, bleibt der jeweilige
Fachprozess; hierfür wird kein allgemeiner Löschablauf erfunden.

| Variante | Regel / verbleibende Konkretisierung |
|---|---|
| Neu anlegen | Gleiches Feldmuster; Hauptaktion benennt das Ergebnis, z.B. «Event erstellen». Rückziel ist die auslösende Liste. |
| Geschützte Profil-/Mitgliederdaten | Separater Einstieg mit erforderlicher Identitätsprüfung. Bestehende Zugangsregeln bleiben bestehen; konkrete Sicherheitsseiten in Block 5. |
| Inline-Bearbeitung, z.B. Kontenplan | Lokales Speichern/Abbrechen direkt am bearbeiteten Eintrag; im Tabellenblock konkret zeigen. |
| Datei/Beleg | Vorschau, Fortschritt, Wiederholen und Teilfehler brauchen eigenes Muster in Prozess-/Dokumentenblock. |
| Bereits verwendete finanzielle Daten | Kein gewöhnliches Überschreiben; bestätigte Korrekturregeln F3–F6 gelten. |

## Responsive Regeln und Gestaltungsalternative

Mobile einspaltig. Tablet verwendet zwei Spalten nur, wenn im Formular selbst
mindestens 600 px verfügbar sind. Desktop begrenzt die Formularbreite auf circa
786 px innerhalb des gemeinsamen Rahmens. Nur zusammengehörige kurze Felder
(Datum/Zeit, Vor-/Nachname, PLZ/Ort) stehen nebeneinander; lange Texte bleiben
über die gesamte Breite. Lesereihenfolge und Tastaturreihenfolge stimmen überein.

Über die Entwurfsoption lässt sich auch Desktop vollständig einspaltig darstellen.
Empfehlung: die gezeigte Kombination aus einer Spalte und wenigen Feldpaaren.
Die zweite Entwurfsoption simuliert einen Speicherfehler bei erhaltenen Eingaben.

## Prüfstand und nächste Abstimmung

Vorschau in lokalem Chrome bei 320, 390, 768, 820, 1024 und 1440 px geprüft:
kein horizontaler Seitenüberlauf. Pflichtfeldfehler/Fokus, Weiterbearbeiten,
Verwerfen, erfolgreiche Rückkehr und beide Formularbeispiele funktional geprüft.
Mobile und Desktop visuell geprüft. Dies ist keine Geräte-/Safari-/App-Abnahme.

Bestätigt ist das gemeinsame Formularmuster einschliesslich Aktionsplatzierung
und Datenerhalt. Die genannten Sondervarianten bleiben explizit ihren Blöcken
zugeordnet; M04 wird mit diesen zwei Beispielen nicht vollständig abgeschlossen.
Danach folgen Listen/Tabellen/Filter und Charts gemäss Gesamtübersicht.

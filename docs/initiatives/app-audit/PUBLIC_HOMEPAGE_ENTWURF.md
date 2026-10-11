# Öffentlicher Auftritt: Homepage und Restaurantliste

Stand: 11. Oktober 2026. Block 6, Gestaltung und gezeigte Benutzerführung mit
«ja das passt doch. machen wir weiter» bestätigt. Offene Inhalts-/Fachfragen bleiben.
Konto/Zugang wurde mit «passt» gestalterisch bestätigt; F1/F2 bleiben offen.

## Expliziter Gestaltungsauftrag

Der Nutzer erlaubt für den öffentlichen Bereich ausdrücklich Abweichungen vom
bestehenden Design zugunsten einer modernen Homepage. Der öffentliche Auftritt
erhält deshalb eine eigene Komposition, Typografie und Navigation. Der bestätigte
App-Rahmen für den Mitgliederbereich bleibt bestehen. Dies ist eine Entwurfs-
entscheidung; permanente UI-Tokens und App-Dateien werden nicht geändert.

Vorschau: `oeffentliche-homepage-entwurf.html` im lokalen Visualisierungsordner
der Unterhaltung. Quellen für Vereinsinhalt: bereits vorhandene About-/Landing-
Texte (Zürich, seit 2021, Monatsessen, Ausflüge, «Meh isch meh!»), Nutzerangabe
elf Mitglieder und vorhandener PUBLIC_DASHBOARD_REVIEW.md. Kein neuer Audit.

## Gestaltung

- Magazinartige Startseite: grosse Serifentypografie, warme helle Flächen,
  Navy/Teal und Orange als Verbindung zur Marke. Bestehendes Gourmen-Logo.
- Einstieg mit Leitsatz, kurzer Vorstellung und primärem Zugang zur Restaurantliste.
  Bild und Text auf Desktop nebeneinander; Mobile Text vor Bild.
- Vorstellung des Vereins als ruhiger Textabschnitt mit den drei Motiven
  Entdecken, Zusammensitzen, Erinnern; keine App-Kacheln oder Finanzkennzahlen.
- Restaurantteaser als geordnete Liste, eigener Suchbereich mit Name/Ort und
  Sortierung nach Name oder letztem Besuch. Suchfehler von Nulltreffern getrennt.
- Öffentliche Navigation: Über uns, Restaurants, Kontakt. Mitgliederzugang
  getrennt sichtbar. Auf schmalen Geräten aufklappbares Menü, keine Bottom-Nav.
- Kontaktabschluss und Instagram-Link; Impressum/Datenschutz sind ausdrücklich
  Platzhalter und keine geprüften Rechtstexte.
- Hell-/Dunkelmodus bleibt verfügbar. Eine Entwurfsoption vergleicht geteilten
  Einstieg mit einem breiten Bild unterhalb des Textes; Standard ist geteilt.

Tablet behält die Bild/Text-Aufteilung, solange sie lesbar bleibt; Navigation
wechselt unter 900 Pixeln verfügbarer Breite ins Menü. Unter 560 Pixeln stehen
Einstieg, Vereinsabschnitt, Motive und Suchfelder untereinander. Textgrössen
richten sich nach der Vorschaufläche, lange Titel dürfen umbrechen.

## Bildmotiv und Daten

Das Tischmotiv ist mit dem eingebauten Imagegen-Werkzeug erzeugt, keine Aufnahme
eines Vereinsanlasses. Vorschau kennzeichnet KI-Bildmotiv und Beispieldaten.
Preview-Asset: `gourmen-tisch-konzept.webp`, im gleichen Visualisierungsordner.
Das generierte Original bleibt unverändert in Codex' generated_images-Verzeichnis;
WebP ist nur eine kompakte Kodierung für die Vorschau. Keine App-Asset-Änderung.

Verwendeter Bildprompt:

> Use case: photorealistic-natural. Asset: editorial hero photograph for a design preview of Gourmen, a small culinary club in Zurich. Wide landscape photograph of a convivial restaurant table seen obliquely from just above table height, tactile cream linen, generous shared seasonal dishes, rustic sourdough, wine glasses and water, hands of adult friends passing a plate at the edges, no recognisable faces. Rich natural food textures, candid intimate gathering rather than luxury advertisement, warm late afternoon side light, restrained terracotta orange and deep navy details, gently dark restaurant background. Main dishes fill centre and right, intentional composition suitable for a wide crop and a vertical crop. No typography, logo, watermark, signage, UI, collage. This is an illustrative fictional dining scene, not documentation of a real club event.

Für eine spätere Veröffentlichung Bildauswahl entscheiden: echtes freigegebenes
Vereinsfoto oder bewusst illustratives Motiv. Restaurantnamen und Besuchsdaten
sind fiktive Beispiele. Keine tatsächlichen Restaurantempfehlungen oder Bewertungen.
Kontakt-/Instagramziele stammen aus dem bestehenden About-Template; aktuelle
Freigabe vor Veröffentlichung prüfen. Kein Versand und kein externes Embed.

## Offene Entscheidungen und Grenzen

**Öffentliche Aufteilung mit «passt alles» bestätigt:**

- Restaurants öffentlich mit Gesamtbewertung, Kategorie-Durchschnitten und
  Anzahl Bewertungen. Berechnung nach BEWERTUNG_GGL_ENTSCHEIDUNGEN.md;
  fehlende optionale Kategorien nicht als null werten.
- Einzelbewertungen, Mitgliedernamen und persönliche Kommentare bleiben intern.
- Künftige Eventinformationen mit Ort, Uhrzeit und Teilnehmenden nur für
  angemeldete Mitglieder und innerhalb ihrer jeweiligen Eventberechtigung.
  Eine Anmeldung hebt die bestehenden Vorstandssichtbarkeiten nicht auf.
- Instagram zunächst als externer Link, ohne automatisch eingebettete Beiträge.

Die folgenden älteren Offen-Markierungen zu diesen vier Punkten sind damit
überholt. Foto-/Text-/Kontaktfreigabe und vollständige About-Inhalte bleiben
separat offen; keine Veröffentlichung oder Änderung der laufenden Homepage.

- F8/R11: bestätigte Bewertungsdarstellung nachgeführt. Liste zeigt Gesamtwert
  und Anzahl, Detaildialog zusätzlich Kategorie-Durchschnitte mit eigener Anzahl.
  Drei fiktive Fälle zeigen mehrere Bewertungen, nur Essen und keine Bewertungen.
  Fehlende optionale Angaben erscheinen als «Noch keine Angaben», nicht als null.
- «Nächstes Essen» aus bisheriger Homepage ist hier noch nicht platziert:
  diese Informationen gehören nach dem bestätigten Entscheid in den geschützten
  Mitgliederbereich (bestehender Befund A-042). Jetzt keine App-Änderung.
- Instagram-Link ist bestätigt; automatisches Embed gehört nicht zum Zielbild.
- Restaurantsuche ist lokal und hat nur drei Beispiele. Identität, Pagination,
  URL-/Browserhistorie, reale Suchantworten und Bewertungsdetails bleiben offen.
- Mitgliederaktion zeigt den Übergang zum bereits entworfenen Login nur als
  Hinweis; keine zweite oder tatsächliche Authentifizierung implementiert.
- Texte sind redaktionelle Vorschläge, keine finale Freigabe. Vereinsfunktionen
  der bisherigen About-Seite sind hier nicht vollständig wiedergegeben.
- SEO, strukturierte Daten, Bildauslieferung, echte Kontakt-/Rechtsangaben,
  Accessibility und Leistung brauchen Umsetzungsabnahme. Kein «state of the art»-
  Compliance- oder Performance-Nachweis allein durch das Mockup.

## Prüfstand und Fortsetzung

Lokales Chromium: Homepage und Restaurantliste bei 320, 390, 768, 820, 1024 und
1440 Pixeln geprüft. Ein anfänglicher Überlauf des Listentitels bei 320 Pixeln
wurde korrigiert; erneute Prüfung bestanden. Suche/Nulltreffer, Fehler/Wiederholen,
Detaildialog, mobiles Menü und Bildladen ohne JavaScript-Fehler geprüft.
Mobile/Desktop visuell geprüft, zusätzlich dunkle mobile Ansicht gerendert.
Zusätzlich Gesamtwert, fehlende Kategorien und keine Bewertungen bei 320, 390,
820 und 1440 Pixeln ohne Dialogüberlauf geprüft; dunkle mobile Detailansicht
visuell geprüft. Fragment etwa 338 KB inklusive Bild/Logo. Keine echte Geräte-/Safariabnahme.

Die nächsten Schritte stehen in RESTABDECKUNG_GESAMTVORLAGE.md. Für den öffentlichen
Bereich bleiben vollständige Inhalte und Foto-/Text-/Kontaktfreigaben offen.
Keine App-Umsetzung, kein Deploy.

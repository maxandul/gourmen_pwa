# Seitengeltung der Gesamtvorlage

Stand: 11. Oktober 2026. R01–R05 konkret zugeordnet, ohne neue Befundsuche.
Grundlage sind die 83 Einträge aus `GESTALTUNGSZUORDNUNG.csv`, die bereits
bestätigten Entwürfe und die separat geklärte Merch-Zielversion.
Die Zuordnung beschreibt das Ziel, nicht geprüfte Rechte oder fertig umgesetzte
Seiten. Zustimmung zu Mustern ersetzt keine Feld-, Rollen- oder Fachabnahme.

## R01/R02/R04 – Seiten, Hauptaktion und Rolle

Pfade sind relativ zu `templates/`. «Berechtigt» bedeutet jeweils die noch unter
F2 endgültig abzugleichende Rolle. Finanzabläufe bleiben zusätzlich unter B01.

| Seiten | Zielmuster / sichtbare Hauptaktion | Rolle und besondere Abnahme |
|---|---|---|
| `dashboard/index.html` | Bestätigtes Dashboard; wichtigste eigene Aufgabe zuerst. | Mitglied; Aufgaben nur im tatsächlich zugänglichen Kontext. |
| `member/index.html` | Vereinseinstieg im App-Rahmen; Bereich öffnen statt Sammelformular. | Mitglied; Finanz-/Adminaktionen ausblenden oder begründet sperren gemäss F2. |
| `admin/index.html` | Bereichseinstieg mit Mitglieder-/Verwaltungsaufgaben; ausgewählten Bereich öffnen. | Lesezugang und Änderungsrecht getrennt. Kein pauschaler Adminzwang nur wegen des Pfadnamens. |
| `admin/members.html` | Mitgliederliste mit Suche; Mitglied öffnen, «Mitglied anlegen» für Berechtigte. | Liste/Detail und sensible Angaben getrennt; elf Mitglieder vollständig erreichbar. |
| `admin/create_member.html`, `admin/edit_member_enhanced.html` | Formularmuster; Anlegen/Einladen bzw. Speichern. | Berechtigte Verwaltung; R10 trennt Speicherung und Versand. Doppelte Adresse vor erneuter Anlage klären. |
| `admin/member_sensitive.html`, `member/profile.html` | Gruppiertes Profilformular; Speichern/Abbrechen, geschützte Angaben hinter erneuter Bestätigung. | Eigene Angaben vs. Administration unterscheiden; vollständige Feldrechte unter F2. |
| `admin/member_security_overview.html`, `member/security.html`, `member/technical.html` | Konto-/Statusgruppen und R10; konkrete Aktion je Gruppe. | Eigenes Konto vs. fremdes Konto; keine Sitzungs-, Geräte- oder Rollenwirkung aus einem allgemeinen «Speichern» ableiten. |
| `admin/create_event.html`, `events/edit.html` | Bestätigtes Eventformular; Erstellen bzw. Speichern. | Berechtigte Organisation/Administration; Eventtyp und Sichtbarkeit F2, Felder je Typ erhalten. |
| `events/year_planning.html` | Vergleichstabelle mit lokalen Zeilenaktionen; Jahreskontext sichtbar. | Berechtigte Planende; Datum/Organisation pro Zeile bearbeiten, Fehler lokal; Massenänderung braucht explizite Vorschau. Mobile Tabelle darf im eigenen Bereich scrollen. |
| `events/index.html` | Liste/Archiv/Statistik; Event öffnen, Filter und Rückkehr erhalten. | Mitglieder gemäss Sichtbarkeit; Erstellen nur berechtigt. Charts gemäss R06, keine versteckten Detailwerte. |
| `events/detail.html` | Bestätigtes Eventdetail; Teilnahme, BillBro oder Bewertung je Phase. | Eigene Teilnahme vs. Organisation; Anwesenheitskorrektur und Rückweg zu Angaben bereits beschlossen. F8 für Bewertung. |
| `events/cleanup.html` | Bestätigte Warteschlange; Prüfen, Überspringen, Zurück/Rücknahme. | Berechtigte Organisation/Verwaltung; Fortschritt, bereits erledigte und fremd geänderte Fälle unterscheiden. |
| `ggl/index.html` | Schmale Rangliste, Filter, zwei Verlaufsdiagramme nach R06. | Mitglied; keine Rang-/Saisonregeln durch Anzeigeauswahl ändern, F8 bleibt offen. |
| `accounting/index.html` | Bestätigter Buchhaltungseinstieg mit Jahreskontext; Hauptaktion pro Tab. | Schatzmeister-/Revisionskontext nach F2/F6; Journal, offene Posten, Budget, Abschluss getrennt. |
| `accounting/booking_detail.html` | Detailmuster: Status, Betrag, Beleg, Zuordnung, Verlauf; zulässige Korrektur statt unbemerktem Überschreiben. | Berechtigte Finanzrolle; gesperrtes Jahr erkennbar, bezahlte Beträge erhalten. B01 für konkrete Buchungsarten. |
| `accounting/booking_new.html`, `accounting/receipt_upload.html` | Bestätigte Schrittformulare; Prüfen vor Speichern bzw. Einreichen. | Finanzrolle bzw. eigenes Mitglied; Einreichen bedeutet noch nicht Verbuchen. |
| `accounting/import_review.html` | Importergänzung und Zuordnungsarbeitsplatz; einzelne Zuordnung prüfen und bestätigen. | Schatzmeisterkontext; Teil-/Über-/Doppelzahlungen nach F5, keine automatische Sammelbuchung aus Sammelübernahme. |
| `accounting/_tab_kontenplan.html`, `accounting/account_edit.html` | Kontenliste mit lokaler Bearbeitung bzw. fokussiertes Formular; Speichern/Abbrechen. | Kontenverwaltung unter F2; bestehende Buchungen und gesperrte Jahre bei Änderungen berücksichtigen, B01. |
| `accounting/_tab_statistik.html` | Drei Diagramme gemäss R06, exakte Werte und Jahreskontext. | Finanz-/Revisionsrechte unter F2, Kennzahlbedeutung unter B01. |
| `member/receipts.html` | Eigene Belegliste; Einreichen/Detail öffnen, Status und Rückfragen. | Mitglied sieht eigenen Prozess, keine unbeabsichtigte Freigabe des Vereinsjournals. |
| `docs/index.html`, `docs/folder.html`, `docs/detail.html` | Dokumentbaum/Liste, Detail, Ordnerwahl; Öffnen bzw. berechtigter Upload. | Gemeinsame Dokumente vs. Belege/Eventdaten unterscheiden; Details R03. |
| `auth/*`, `admin/reset_member_2fa.html`, `admin/reset_member_password.html`, `admin/temp_password.html` | Bestätigte Anmeldung/Einrichtung/erneute Bestätigung/Wiederherstellung. Eine konkrete nächste Aktion je Zustand. | Eigene Wiederherstellung vs. Hilfe durch Verwaltung; F1 entscheidet die zulässigen Verfahren. Bestehendes temporäres Passwort ist kein automatisch bestätigter Zielprozess. |
| `base.html`, Navigations-/Kopf-/Icon-Partials | Bestätigter App-Rahmen, Theme-Schalter und Kontomenü. | Technische Kopf-/Script-Partials sind keine zusätzlichen Screens; Cache/Assets später technisch prüfen. |

Merch-v2-Zielseiten werden über `MERCH_ZIELVERSION.md` sowie Mitglieder- und
Verwaltungsentwurf ergänzt: Shop/Runde → eigene Bestellung; Hub/Rundendetail →
zustandsabhängige nächste Verwaltungsaktion; Artikel/Lieferant/Runde → Formular;
Farben/Grössen → lokale Listenbearbeitung. Lieferantenbelege → Uploadmuster R03.
Die 15 zusätzlichen v2-Templatepfade sind keine geprüfte vollständige Routenliste.
Die alten `admin/merch/*`- und `member/merch/*`-Seiten erhalten keine neuen
Shopentwürfe; Stilllegung und Datenerhalt nach R12. F7/R09 bleibt offen.

## R03 – verbindliche Darstellungs- und Abnahmekriterien

Gilt für `docs/_upload_modal.html`, `docs/_folder_picker_modal.html`,
`docs/_drive_quick_modals.html`, Dokumentseiten, Belegeinreichung und
Lieferantenbelege der Merch-Zielversion.

- **Kamera/Datei:** gemeinsame Vorschau und Angaben nach beiden Eingangswegen;
  Kameraabbruch verliert keine bereits eingegebenen Angaben. Tatsächliche
  Kamera-/Dateiformate und Grössenlimits erst mit technischem Vertrag festlegen.
- **Vorschau:** Bild/PDF lesbar öffnen; bei nicht unterstützter Vorschau
  Dateiname, Typ und gezieltes Öffnen anbieten. Kein leeres Vorschaufenster.
- **Eventzuordnung:** nur berechtigte Ziele anbieten; Auswahl bei Rückkehr erhalten.
  Entfallene Berechtigung vor Abschluss verständlich melden. F2 entscheidet,
  welche Beleg-/Eventinhalte für wen sichtbar sein dürfen.
- **Ordner:** vollständiger Zielpfad vor Abschluss; tiefe Struktur im eigenen
  Auswahlbereich navigieren, Such-/Rückkehrkontext erhalten. Kein neuer fixer
  Kategorienbaum entgegen der Drive-Strategie.
- **Namenskonflikt/parallele Änderung:** Konflikt zeigen, Entwurf erhalten,
  neuen Namen oder aktuellen Stand prüfen lassen. Kein stilles Überschreiben.
  Zulässige Auflösungen und Archiv-/Löschrechte sind vor Umsetzung festzulegen.
- **Teilfehler/unklarer Erfolg:** erfolgreich gespeicherte Dateien benennen,
  nur fehlgeschlagene wiederholen; bei unklarer Bestätigung bestehenden Vorgang
  abgleichen. Wiederaufnahme darf kein zweites Dokument erzeugen.

## R04 – Listen, Tabellen und Rückkehr

Gilt für Mitglieder, Events/Archiv/Jahresplanung, Journal/offene Posten/Budget,
eigene Belege, Dokumente sowie v2-Runden-/Bestelllisten. Suche, Sortierung,
Filter, Ergebnisseite und Scrollposition beim Öffnen/Zurückkehren erhalten.
Filterwechsel beginnt auf der ersten Ergebnisseite; nach Löschung/Archivierung
einer letzten Zeile auf eine gültige Ergebnisseite zurückführen.

Einzeldatensätze werden auf Mobile zu Listen, Vergleichswerte bleiben Tabellen
mit begrenztem horizontalem Scrollbereich und sichtbaren Zeilenbezeichnungen.
Serverpagination, Browser-Zurück, lange Namen, leere Ergebnisse und gleichzeitig
veränderte Daten später abnehmen. Nie fehlende Berechtigung als «keine Daten»
verschleiern. Fachlich erforderliche Spalten dürfen nicht ersatzlos entfallen.

## R05 – Meldungen und E-Mails

| Seiten / Vorlagen | Geltung des bestätigten Musters |
|---|---|
| `errors/403.html` | Fehlende Berechtigung; Rückweg zu einem erreichbaren Bereich. Keine geheimen Objektinformationen. |
| `errors/404.html` | Nicht gefunden/nicht mehr verfügbar; Rückweg, keine automatische Löschdiagnose. |
| `errors/500.html` | Aktion fehlgeschlagen oder Bestätigung unklar; passende Wiederaufnahme. Schreibaktionen nicht blind wiederholen. |
| `offline.html`, `partials/_flash_messages.html` | Offline, Teilfehler, Erfolg und Warnung gemäss Systementwurf; eingegebene Daten erhalten, wenn technisch möglich. |
| `emails/base.html` | Gemeinsame Mailgrundvorlage, gut lesbare Hauptaktion und ausgeschriebener Ersatzlink. |
| `emails/onboarding.html` | Einladung zur Einrichtung; Versand nicht mit Aktivierung gleichsetzen. |
| `emails/password_reset.html`, `emails/2fa_reset.html` | Konkreter Zweck und tatsächliche Gültigkeit; bereits verwendete/abgelaufene Links verständlich behandeln. Verfahren nach F1. |
| `emails/google_email_verify.html` | Bestätigung der ausdrücklich genannten Adresse; kein pauschaler Nachweis eines Drive-Zugangs. |
| `emails/test.html` | Klar als Test bezeichnet; kein irreführender Kontostatus. |

Genaue Fristen stammen später aus dem jeweiligen Sicherheitsvertrag, nicht aus
Beispieltexten. Mailzustellung, Clients/Hell-Dunkel, mobile Umbrüche, Links und
Gerätetexte sind separate Abnahme. Keine echte Mail in dieser Entwurfsphase.

Öffentliche Seiten `public/*` und `_landing_instagram.html` bleiben dem
bestätigten eigenständigen Homepage-Muster zugeordnet; Inhalte/Instagram/
Event-Sichtbarkeit und F8 stehen unter R11. `events/hamburg2026.html` sowie
`accounting/accounts.html` und `accounting/stats.html` sind unter R12 eingeordnet.

## Was jetzt abgeschlossen ist – und was nicht

R01–R05 haben eine konkrete Muster-/Seitengeltung und Abnahmekriterien.
Das CSV bleibt das vollständige Register der 83 Baseline-Einträge und verweist
jetzt auf die aktuellen Dokumente. Keine Behauptung, dass alle Datenfelder,
Funktionen oder echte Geräte bereits geprüft seien.

Alle bisher gezeigten Entwürfe einschliesslich R10 sind gestalterisch bestätigt.
Als Nächstes sind **F1/F2, F7, F8 und B01** zu entscheiden; R09/R11 hängen daran.
Danach Gesamtvorlage mit Umsetzungspaketen zusammenführen. Keine weitere
vollständige Befundsuche und keine App-Änderung aus dieser Zuordnung.

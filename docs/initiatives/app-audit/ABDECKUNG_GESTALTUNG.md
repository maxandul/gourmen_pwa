# Gestaltungsabdeckung und weiterer Ablauf

Stand: 10. Oktober 2026. **Entwurfsarbeit, keine Umsetzungsfreigabe.**

Die Gesamtvorlage soll alle unterschiedlichen Seiten- und Bedienmuster der App
abdecken. Dashboard, Eventdetail und Buchhaltung sind bestätigte Beispielansichten;
sie legen noch nicht die Gestaltung aller Formulare, Tabellen und Prozesse fest.
Diese fehlenden Grundsatzentscheide gehören vor die abschliessende Gesamtvorlage.
Die spätere Umsetzung konkretisiert und prüft das Verhalten auf echten Geräten.

## Grundlage und Aussagegrenze

**Ergänzung 11.10.2026:** Merch-Ziel ist die jüngere v2-Version auf separatem
Branch `phase/10-merch-wip`. [Versionsklärung](MERCH_ZIELVERSION.md) ergänzt die
Zuordnung um deren Seitenfamilien. Die 83 Baseline-Templates sind deshalb keine
vollständige Inventarliste der gewählten Merch-Zielversion.

Die [Gestaltungszuordnung](GESTALTUNGSZUORDNUNG.csv) ordnet alle **83 Templates**
aus TEMPLATE_MATRIX.csv genau einer primären Musterfamilie zu. Zusätzliche Muster
werden separat aufgeführt. Templates umfassen auch Teilansichten und E-Mails;
83 Templates bedeuten weder 83 Seiten noch 83 notwendige neue Mockups.

Grundlage sind ausschliesslich das vorhandene Inventar, UI_PATTERN_SURVEY.csv,
COMPONENT_REVIEW.md, UI_REGISTRY_REVIEW.md und die bestehenden Modulberichte.
Keine neue umfassende Befundsuche und keine neue Funktionsprüfung. Die Zuordnung
schliesst K1/K5 im [Auditabschlussplan](COMPLETION_PLAN.md) nicht ab und behauptet
keine vollständige aktive Routenabdeckung. Baseline bleibt `bf4d84a`.

## Welche Muster bereits entschieden sind und welche fehlen

**Aktualisierung 11.10.2026:** Alle gezeigten Entwürfe bis zur Finanzergänzung
und zu den Verwaltungszugängen sind bestätigt. Die konkrete aktuelle
[Seitengeltung](SEITENGELTUNG_GESAMTVORLAGE.md) und das aktualisierte CSV ersetzen
ältere Offen-Markierungen zur Grundgestaltung in den nachstehenden Tabellen.
Chartzuordnung und Sonderseiten sind in CHARTS_SONDERSEITEN_ZUORDNUNG.md geklärt.
Offen bleiben Fachfragen F1/F2/F7/F8/B01 und davon abhängige R09/R11 sowie echte
Implementierungsabnahmen. Keine neue umfassende Prüfung.

**Aktueller gemeinsamer Restplan:** [RESTABDECKUNG_GESAMTVORLAGE.md](RESTABDECKUNG_GESAMTVORLAGE.md)
führt R01–R12, Fachentscheidungen und Reihenfolge zusammen. Alle bisher gezeigten
Grundentwürfe einschliesslich System/E-Mail sind gestalterisch bestätigt.

Ergänzung 11. Oktober: [Direktes Bearbeiten und Warteschlangen](INLINE_WARTESCHLANGE_ENTWURF.md)
konkretisieren M04/M05/M06 als Bedienvorschläge. Darstellung und gezeigte Benutzerführung sind bestätigt;
fachliche Berechtigungen und Übertragbarkeit auf die tatsächlichen Vorgänge offen.

**Verbindliche Trennung nach Nutzerklarstellung:** Bestätigung eines Entwurfs
bedeutet Zustimmung zu Darstellung und gezeigter Benutzerführung. Fachliche
Vollständigkeit der Buchhaltung ist ausdrücklich offen. Einzelregeln F3–F6
sind davon getrennt bestätigt; vor Umsetzung folgt der Abgleich mit der
tatsächlichen Vereinspraxis. Jede weitere Abstimmung trennt Gestaltung,
ausdrückliche Fachentscheidung und noch offenen Fachbedarf.

«Bestätigt» bezieht sich immer auf den genannten Entwurf. «Teilweise» bedeutet,
dass ein Beispiel existiert, aber abweichende Varianten noch offen sind.

| ID / Musterfamilie | Primäre Templates | Gestaltungsstand | Noch erforderlicher Entwurf oder Entscheid |
|---|---:|---|---|
| M01 App-Rahmen und technische Teilansichten | 10 | Rahmen bestätigt | Gemeinsame Navigation, Logo, Icons, Theme-Schalter und Kontomenü als Basis übernehmen; technische Teilansichten sind damit nicht geprüft. |
| M02 Dashboard und Bereichseinstiege | 3 | Dashboard bestätigt | Mitglieder-/Admin-Einstiege auf denselben Rahmen abbilden; abweichende Aufgabenprioritäten zeigen. |
| M03 Detailseiten | 5 | Eventdetail bestätigt | Buchungs-, Artikel-, Bestell- und Dokumentdetail: Hauptaktion, Status, Verlauf, Bearbeiten und weitere Aktionen zuordnen. |
| M04 Formulare und Bearbeitungsseiten | 12 | Gemeinsames Muster bestätigt; Sondervarianten offen | [Event-/Profilformular](FORMULARE_ENTWURF.md) mit Validierung, Speichern/Abbrechen und ungespeicherten Eingaben ausgearbeitet; sensible Daten und Inline-Bearbeitung bleiben Varianten in späteren Blöcken. |
| M05 Schritte und Arbeitsabläufe | 4 | Gestaltung teilweise bestätigt; Fachgesamtabgleich offen | BillBro, [Buchung/Beleg/Zahlungszuordnung](BUCHHALTUNG_PROZESSE_ENTWURF.md), [Revision/Korrektur](REVISION_KORREKTUR_ENTWURF.md), Inline/Warteschlange sowie Merch-Verwaltung gestalterisch bestätigt. Importvorstufe, Sammelaktionen und dokumentierte Prozesssonderfälle bleiben offen. |
| M06 Listen, Tabellen und Auswertungsübersichten | 6 | Grundmuster bestätigt | [Listen-/Tabellenentwurf](LISTEN_CHARTS_ENTWURF.md): Mitglieder, Journal, Budgetvergleich, Rangliste mit Filter-/Sortier-/Paginationsregeln. Inline-/Sammelaktionen bleiben beim Fachprozess offen. |
| M07 Charts und Statistik | 1 | Grundmuster bestätigt; Chartzuordnung offen | [Balken und Punkteverlauf](LISTEN_CHARTS_ENTWURF.md) bestätigt. Alle bestehenden Charttypen vor Gesamtabschluss zuordnen; elf Mitglieder, Mehrfachreihen und spezielle Datenzustände berücksichtigen. Reale Mobile-Prüfung bei Umsetzung. |
| M08 Merch-Shop | 1 | Mitglieder- und Verwaltungssicht bestätigt | [Mitgliederentwurf](MERCH_MITGLIEDER_ENTWURF.md) und [Verwaltung](MERCH_VERWALTUNG_ENTWURF.md) gestalterisch bestätigt. Weitere v2-Varianten und Fachregeln offen; Baseline-Zahl unverändert. |
| M09 Dokumentbaum und Suche | 2 | Grundmuster bestätigt | [Dokumente/Uploads](DOKUMENTE_UPLOAD_ENTWURF.md): Hierarchie, Suche, Detail, Archiv, Upload und Ordnerwahl gestalterisch bestätigt. Grosse/tiefe Bestände und dokumentierte Sonderfälle offen. |
| M10 Einstellungen und Sicherheitsübersichten | 3 | Grundmuster bestätigt | [Konto/Zugang](KONTO_ZUGANG_ENTWURF.md): Gruppierung, Status, Theme, Gerätebenachrichtigungen und sensible Änderungen gestalterisch bestätigt. Admin-, Google-/Kalender- und weitere Sondervarianten offen. |
| M11 Anmeldung und Kontowiederherstellung | 13 | Grundmuster bestätigt | [Konto/Zugang](KONTO_ZUGANG_ENTWURF.md): Anmeldung/MFA, erneute Bestätigung, Reset, Einrichtung und Verlustfall gestalterisch bestätigt. F1/F2 vorbereitet, nicht entschieden; weitere Varianten dokumentiert. |
| M12 Dialog-Teilansichten | 3 | Teilweise | Bestätigungen, Upload/Ordnerwahl, sensible Bestätigungen und Update-Bestätigung gestalterisch bestätigt. Weitere Kalender-/Chartdialoge gemäss Restplan offen. |
| M13 Fehler, Offline und Meldungen | 5 | Grundmuster bestätigt | [System/E-Mail](SYSTEM_EMAIL_ENTWURF.md): Offline, Teilfehler, unklarer Speicherstand, Updates mit Entwurf, Sitzung, 403/404, Push und Installation gestalterisch bestätigt. Tatsächliche Cache-/Geräte-/Serverabnahme offen. |
| M14 Öffentlicher Bereich | 4 | Eigenständiger Entwurf bestätigt | [Homepage/Restaurants](PUBLIC_HOMEPAGE_ENTWURF.md) gestalterisch bestätigt. Öffentliche Eventdaten, Bewertungsregeln, Instagram-Einbindung und weitere Details offen. |
| M15 E-Mails | 6 | Grundvorlage bestätigt | [System/E-Mail](SYSTEM_EMAIL_ENTWURF.md): gemeinsame Grundvorlage plus Einladung, Passwort, 2FA, Google-Adresse und Test gestalterisch bestätigt. Fristen/Sicherheitsregeln offen, keine E-Mail-Client-Abnahme. |
| M16 Sonder-/Altseiten | 5 | Einordnung offen | Hamburg-Sonderseite sowie ältere Buchhaltungsvarianten gezielt behalten/angleichen/archivieren einordnen. Alte Merch-Seiten zur Entfernung vorgemerkt, keine neuen Entwürfe dafür. |

Die Anzahlen sind eine eindeutige Inventarzuordnung, kein Mass für Arbeitsumfang.
Ein Formular in einer Detailseite bleibt beispielsweise zusätzlich ein Formular.
Das ausgeschlossene Game ist nicht Teil der Gestaltungsarbeit.

## Prozesse brauchen unterschiedliche Muster

| Prozess | Vorhandener Stand | Vor der Gesamtvorlage noch darzustellen |
|---|---|---|
| BillBro | Schritte und wesentliche Bedienregeln bestätigt; Anwesenheitskorrekturen, Rückkehr zu Angaben, Trinkgeld in CHF/% aufgenommen | Korrektur nach Abschluss und Zahlwegwechsel in den bestehenden Entwurf einordnen, Rollen-/Fehlerzustände sichtbar machen. |
| Merch | v2-Mitglieder- und Verwaltungssicht gestalterisch bestätigt | F7, Abschluss-/Wiederöffnungsregeln und Sonderfälle gemäss MERCH_VERWALTUNG_ENTWURF.md offen. Zielversion auf separatem Branch, siehe MERCH_ZIELVERSION.md. |
| Buchung und Bankimport | Buchhaltungsübersicht bestätigt, F5 Teil-/Überzahlungen entschieden | Schrittformular und Prüf-/Zuordnungsarbeitsplatz getrennt darstellen; unklare Zahlungen, Korrektur, Wiederaufnahme. |
| Beleg erfassen | Zweistufiger Ablauf im Inventar | Kamera/Datei, Vorschau, Angaben, Uploadfortschritt, Teilfehler und erneuter Versuch. |
| Jahresabschluss und Revision | F6 fachlich bestätigt | Freigabe, Buchungssperre, Hinweise/Beanstandungen, Rückgabe, erneute Prüfung und versionierter Abschluss je Rolle. |
| Bereinigung | Queue mit Skip/Back/Undo im Audit | Stapelbearbeitung mit Fortschritt und Rücknahme; kein gewöhnliches Schrittformular. |

Bestätigte Finanzregeln F3 bis F6 bleiben bestehen. Offen sind F1/F2 Zugang/Rollen,
F7 Merch und F8 Bewertungen/GGL. Diese Fragen werden beim passenden Entwurf mit
Empfehlung, Alternative und sichtbarer Auswirkung vorgelegt, nicht als losgelöste
lange Fragenserie. Details stehen in OBERFLAECHENENTWUERFE.md und BILLBRO_INTERAKTION.md.

## Reihenfolge der verbleibenden Gestaltungsarbeit

| Block | Konkretes Ergebnis |
|---|---|
| 1. Formulare, Bearbeiten und einfache Dialoge | Repräsentativer Event-/Profilentwurf mit Speichern, Abbrechen, Fehlern, ungespeicherten Eingaben sowie Aktionsplatzierung; Regeln für sensible und Inline-Varianten. |
| 2. Listen, Tabellen, Filter und Charts | Vergleich an Mitgliederliste, Buchhaltungstabelle und GGL/Statistik; bewusst unterschiedliche mobile Darstellung, Filter-/Sortierverhalten und Chartbedienung. |
| 3. Fachprozesse und zugehörige Details | Merch, Buchung/Import, Beleg, Revision und Bereinigung nach obiger Prozessmatrix; bestätigte BillBro-/Finanzregeln einarbeiten und offene Fachfragen im Kontext entscheiden. |
| 4. Dokumente | Baum/Suche, Detail, Upload, Ordnerwahl und Dialogketten als zusammenhängendes Beispiel. |
| 5. Einstellungen und Zugang | Profil-/Sicherheitsübersichten, Anmeldung, MFA/Reset und sensible Änderungen; offene Rollen-/Zugangsentscheidungen einbeziehen. |
| 6. Öffentlicher Bereich und besondere Zustände | Öffentlicher Einstieg/Suche, System-/Offline-/Updatezustände, E-Mail-Grundvorlage und explizite Behandlung der Sonder-/Altseiten. |
| 7. Gesamtvorlage zusammenführen | Abgestimmte Muster, fachliche Ausnahmen, Entscheidungsregister und priorisierte Umsetzungspakete mit Abnahmekriterien. |

Pro Block werden gemeinsame Muster an wenigen repräsentativen Ansichten gezeigt.
Ein weiterer Einzelentwurf ist nur nötig, wenn eine Seite davon relevant abweicht.
Die Abdeckungstabelle und CSV werden bei jeder Abstimmung fortgeschrieben.

## Was in jedem Muster festgelegt wird

- Mobile und Desktop konkret; Tablet-Regeln für Spalten, Breiten, Navigation und Aktionen.
- Hell-/Dunkelmodus, konsistente Icons und verständliche Beschriftung.
- Hauptaktion, Bearbeiten/Löschen, Zurück/Abbrechen sowie Erhalt von Eingaben.
- Rollen und gesperrte Zustände, Leer-/Lade-/Fehler-/Erfolgszustände.
- Fokus, Scrollziel nach relevanten Aktionen, Tastatur und Touch; sichtbare
  Rückmeldung ohne unerwünschte blaue Browser-Tapfläche. Zugänglicher Fokus bleibt erhalten.

Die Grundsatzregeln dafür werden jetzt gestaltet. Ihre technische Umsetzung,
Feinabstimmung und Prüfung auf echten Geräten folgen später. Ein Muster darf nicht
als abgeschlossen gelten, wenn eine wesentliche Interaktion nur auf «später» vertagt ist.

## Wann die Gesamtvorlage vollständig ist

Jede relevante Musterfamilie hat einen bestätigten Entwurf oder eine ausdrücklich
begründete Ausnahme. Die Zuordnung zeigt, welche Seiten ihn verwenden. Fachfragen
sind entschieden oder mit konkreter Auswirkung als offene Entscheidung sichtbar;
offene Punkte werden nicht als Zustimmung behandelt. Umsetzungspakete benennen
Abhängigkeiten und Abnahmekriterien. Die dringlichen technischen Pakete U1/U2 aus
der Gesamtbeurteilung bleiben priorisiert und werden nicht durch Layoutarbeit ersetzt.

Erst danach folgt eine gesonderte Entscheidung über die Umsetzung. Diese Übersicht
ist eine Planung der Gestaltungsabdeckung, keine technische Abnahme und keine
Freigabe für Änderungen an der laufenden App.

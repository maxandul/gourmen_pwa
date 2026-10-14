# Konto, Einstellungen und Zugang

**Technische Fortsetzung 14.10.2026:** [U1w](U1W_AKTIONSBESTAETIGUNG.md) konkretisiert
die aktionsgebundene Bestätigung für bestehende Passwort-/MFA-/Berechtigungs-
änderungen. Passwortbeweis direkt im POST, 10-Minuten-Formularnachweis mit
Konto-/Sitzungs-/Zielbindung und Verbrauch durch atomare Zugangsversion-Rotation.
Mitgliederanlage/initiale Rechte und umfassende F1-/U1-Abnahme bleiben offen.


**Nachführung 11. Oktober 2026:** Die Vorschau erhält bei normaler selbst
ausgelöster Passwortänderung jetzt die aktuelle Anmeldung; andere Sitzungen und
deren Gerätevertrauen werden im Ergebnis als beendet erklärt. Passwort-Reset
über den Wiederherstellungsweg führt weiterhin zur Anmeldung mit bestehender MFA.
Nur UI-Simulation, keine echten Zugangsdaten/Sitzungen geändert. Frühere Absätze
über einen pauschalen Logout nach jeder Passwortänderung sind damit überholt.

Stand: 11. Oktober 2026. Block 5, Gestaltung und gezeigte Benutzerführung mit
«passt» bestätigt. F1/F2 und dokumentierte Sondervarianten bleiben offen.
Dokumente/Uploads sind durch «passt, weiter» hinsichtlich Gestaltung und gezeigter
Benutzerführung bestätigt. Keine pauschale Fach- oder Umsetzungsfreigabe.

## Umfang und Quellen

Interaktive Work-Vorschau `konto-zugang-entwurf.html` im Visualisierungsordner
der Unterhaltung. Grundlage: bestehender AUTH_REVIEW.md, F1/F2 aus
OBERFLAECHENENTWUERFE.md und bestätigter App-/Formularrahmen. Keine neue
Befundsuche, keine echten Zugangsdaten, Nachrichten, Authenticator-Schlüssel,
Browserberechtigungen oder Sicherheitsänderungen.

| Ansicht | Dargestelltes Muster |
|---|---|
| Kontoübersicht | Gruppen Mein Konto, Sicherheit, Darstellung, Gerätebenachrichtigungen; Status und konkrete Aktion zusammen. Profil führt auf das schon bestätigte Formularmuster, hier nur als Verweis. |
| Geschützte Angaben / Passwort | Gewünschte Aktion zunächst mit erneuter Identitätsbestätigung; danach direkt zur Aktion. Geschützte Daten bleiben Platzhalter. |
| Zwei-Faktor-Verwaltung | Aktiv/inaktiv, Einrichtung, neue Wiederherstellungscodes, Deaktivierung mit Folgenbestätigung. |
| Einrichtung | Authenticator-Platzhalter, Codebestätigung und Sicherung der Wiederherstellungscodes als getrennte Schritte. Keine echte QR- oder Codeerzeugung. |
| Gemerkte Geräte | Gerätevertrauen getrennt von laufenden Sitzungen; Widerruf mit Folgenbeschreibung. |
| Anmeldung | E-Mail/Passwort, Passwortsichtbarkeit, anschliessender zweiter Faktor, Alternative Wiederherstellungscode und Hilfe bei Verlust beider Möglichkeiten. |
| Passwort vergessen | Adresseingabe, neutrale Antwort ohne Kontobestätigung, Beispiellink zu neuem Passwort. |
| Einladung / ungültiger Link / gesperrter Zugang | Eigene verständliche Zustände mit einem passenden nächsten Schritt. Aktivierung entfernt keine bestehende MFA. |

Mobile: eine Spalte, jede Gruppe für sich lesbar. Desktop: zwei Spalten für die
Kontoübersicht, begrenzte Formularbreite für Eingaben. Tablet nutzt zwei Spalten
nur bei ausreichend Platz; unter 850 Pixeln eine Spalte. Vor der Anmeldung sind
interne Navigation und Kontomenü verborgen; Logo und Theme-Schalter bleiben.

## Interaktion

Formulare verwenden native Eingaben, sichtbare Labels, Passwortsichtbarkeit und
bei Einmalcodes ein gemeinsames Feld statt sechs getrennten Feldern. Fehler stehen
beim Formular; relevante Eingaben erhalten Fokus. Weiterleitung nach der
Beispielanmeldung erhält das ursprüngliche interne Ziel «Monatsessen Oktober».
Schrittwechsel scrollt zur Arbeitsfläche und fokussiert den nächsten Einstieg.

Die Vorschau akzeptiert ausschliesslich den Beispiel-MFA-Code `123456` bzw.
`BEISPIEL-CODE`; dies ist kein Sicherheitsmechanismus. Passwortformulare prüfen
nur vorhandene/übereinstimmende Beispiele. Passwortregeln werden hier nicht
erfunden. Die Option «Fehlgeschlagene Bestätigung» zeigt einen Fehler im Formular.
Passwörter/Codes werden nicht in den Unterhaltungszustand geschrieben; nur
Darstellung, Theme und gewählter Beispielweg werden gespeichert.

Erneute Passwortbestätigung zeigt das Bedienmuster, legt aber nicht die nötige
Authentifizierungsstärke für jede Aktion fest. Freigabedauer, weitere Faktoren,
Widerruf und Sessionbindung bleiben F1. Die Vorschau besitzt keine echten
Sicherheitsgrenzen. Sensible Eingaben werden beim Seitenwechsel verworfen.

## Fachentscheidungen – aktueller Stand

**F1 für Mitglieder mit «ja passt» bestätigt:**

- Passwort vergessen: Wiederherstellung über E-Mail-Link; bestehende
  Zwei-Faktor-Anmeldung bleibt erhalten.
- Authenticator und Wiederherstellungscodes verloren: Systemadmin prüft die
  Identität persönlich oder telefonisch und ermöglicht die Wiederherstellung.
- Sicherheitsreset oder Deaktivierung: bestehende Anmeldungen und gemerkte
  Geräte werden ungültig.
- Normale eigene Passwortänderung: aktuelle Sitzung bleibt angemeldet,
  andere Sitzungen werden beendet. Ob andere Geräte ihre MFA-Vertrauensfreigabe
  behalten, wurde dabei nicht ausdrücklich entschieden.

**Eigener Systemadmin-Notfallzugang mit «passt» bestätigt:**
Wiederherstellungscodes getrennt vom Handy sicher aufbewahren. Bei Verlust
auch dieser Codes einen dokumentierten technischen Wiederherstellungsweg über
den eigenen Hostingzugang vorsehen. Kein zusätzlicher dauerhafter Ersatzadmin
für diesen Zweck. Technische Machbarkeit, Identitäts-/Zugriffsnachweis und
konkreter Ablauf sind bei der Umsetzung zu prüfen; kein bestehender oder
bereits getesteter Notfallweg behauptet. Keine Hostingrechte geändert.

Das anschliessende F1-Regelpaket ist ebenfalls bestätigt, siehe unten.
Offen bleiben technische Ausgestaltung, konkrete Linkfristen, Stärke der
erneuten Identitätsbestätigung sowie detaillierte Fehler-/Widerrufsabnahme.
Keine bestehende Sicherheitsfunktion oder tatsächliche Zustellung damit geprüft.
Die bisherige Vorschau mit erneuter Anmeldung nach normaler Passwortänderung
ist in diesem Detail überholt und vor Gesamtvorlage anzupassen.

**Ergänzendes F1-Regelpaket mit «ja, passt» bestätigt:**

- Passwort-/2FA- und Berechtigungsänderungen erfordern eine erneute
  Identitätsbestätigung für die konkrete Aktion. Gewöhnliche Profil-, Event-
  oder Buchhaltungsbearbeitung erhält dadurch keine zusätzliche Passwortabfrage.
- Neuer Wiederherstellungs-/Bestätigungslink ersetzt ältere desselben Zwecks
  und Kontos; Links sind einmalig und an die konkrete Adresse/Aktion gebunden.
  Konkrete Ablaufzeiten bleiben im Umsetzungskonzept auszuweisen.
- Deaktivierung entzieht App-, persönlichen Kalender- und Vereins-Drive-Zugang.
  Beim Wechsel der Google-Adresse entfällt die alte Vereinsfreigabe, die neue
  benötigt Verifikation. Externe Fehler bleiben als offene Adminaufgabe sichtbar;
  kein unbestätigter Entzug wird als erledigt dargestellt.
- Normale Passwortänderung behält nur die aktuelle Sitzung samt Gerätevertrauen;
  andere Sitzungen und Gerätefreigaben entfallen. Dies ergänzt die bereits
  bestätigte Sitzungsregel um die bisher offene MFA-Gerätefreigabe.

**Aktualisierung F2:** Der Nutzer hat anschliessend bereichsübergreifende
Bearbeitungsrechte des Systemadmins ausdrücklich gewünscht, auch für Finanzen.
Die unten früh vorgeschlagene Beschränkung ist damit überholt. Massgeblich ist
`ROLLEN_ENTSCHEIDUNGEN.md`; Vorstand/Funktion und Admin sollen differenziert
werden. Bereichsrechte und Abschluss-/Revisionsausnahmen sind inzwischen in
ROLLEN_ENTSCHEIDUNGEN.md bestätigt; diese Quelle ersetzt ältere Empfehlungen.

Die nachstehende Tabelle dokumentiert die ursprünglichen Vorschläge. Für
bereits entschiedene Punkte gelten die aktuellen Festlegungen oben.

| Entscheidung | Empfehlung zur Abstimmung | Alternative / sichtbare Auswirkung |
|---|---|---|
| F1a Widerruf bei Sicherheitsereignissen | Deaktivierung, Passwort-/MFA-Reset und sicherheitsrelevanter Rollenentzug widerrufen betroffene Sitzungen, Gerätefreigaben und alte Links gezielt. Neue Resetlinks ersetzen ältere desselben Zwecks. | Normale selbst ausgelöste Passwortänderung könnte die aktuelle Sitzung erhalten; Ausnahme und Wirkung auf andere Sitzungen müssten ausdrücklich feststehen. Mockup zeigt konservativ erneute Anmeldung, keine beschlossene Gesamtregel. |
| F1b Verlust beider Faktoren | Wiederherstellung durch benannte verantwortliche Person nach dokumentierter Identitätsprüfung; einmaliger Wiederherstellungsweg, bestehende MFA nicht stillschweigend umgehen. | Zuständigkeit und konkreter Identitätsnachweis sind noch festzulegen; UI zeigt deshalb Hilfe statt automatischem Sicherheitsreset. |
| F1c Sensible Änderungen | Erneute Bestätigung an Konto, Sitzung und konkrete Aktion binden. Freigaben nicht über Konto-/Sitzungswechsel übernehmen. | Gemeinsames kurzes Freigabefenster wäre bequemer; Dauer und zulässige Aktionen benötigen eine Entscheidung. |
| F2 Finanz-/Revisionsrechte | Aktionen nach Vereinsfunktion vergeben, Admin-Sonderrechte explizit benennen. Notfallzugriff begründen/protokollieren. | Breite Adminrechte beibehalten; dann muss insbesondere dieselbe Person als Buchende und Revisor ausdrücklich erlaubt oder ausgeschlossen werden. Layoutzustimmung entscheidet das nicht. |

Diese Vorschläge präzisieren die vorhandenen Fragen, ersetzen keine Zustimmung.
F3–F6 bleiben separat bestätigte Regeln; keine rückwirkende Änderung daran.

## Restvarianten und Grenzen

- Google-/Drive-Adresse, Verifikation/Einladung und externe Berechtigungen sowie
  Kalenderabonnement/Linkerneuerung brauchen gezielte Zuordnung zum Einstellungs-
  und Bestätigungsmuster vor der Gesamtvorlage.
- Admin-Sicherheitsübersicht, Mitgliederanlage, verpflichtender Passwortwechsel
  und Hilfe bei fehlgeschlagenem Einladungsversand sind noch nicht durchgespielt.
- Vollständige Rollen-/Zustandsmatrix, Rate-Limits, parallele Sitzungen,
  Gerätevertrauensdauer und Pflicht-MFA sind nicht beschlossen oder geprüft.
- Backup-Codes exportieren/kopieren, manuelle Authenticator-Einrichtung,
  erneute Freigabe während Bearbeitung sowie native Zurück-Wege offen.
- Benachrichtigungen zeigen nur an/aus je Gerät. Browserseitig verweigert,
  nicht unterstützt und PWA-Voraussetzungen gehören in Block 6.
- Die Vorschau meldet nach Passwortänderung erneut an; das ist ein sichtbarer
  Vorschlag zu F1 und kein Nachweis vorhandener Sessionwiderrufe.

## Prüfstand und weiterer Ablauf

Lokales Chromium: sechs Einstiege bei 320, 390, 768, 820, 1024 und 1440 Pixeln
ohne äusseren Überlauf/JavaScript-Fehler. Pflichtfelder, MFA-Fehler/Erfolg mit
Rückziel, erneute Identitätsbestätigung, Passwortabweichung, neutrale Resetantwort,
Deaktivierungs-/Einrichtungsfolge und Sicherungsbestätigung der Codes geprüft.
Mobile-Anmeldung und Desktopkonto visuell kontrolliert. Keine echte Authentifizierung,
Sicherheitsabnahme, Produktions-, Safari- oder Geräteprüfung.

Nach Rückmeldung Block 6: öffentlicher Bereich, System-/Offline-/Updatezustände
und E-Mail-Grundvorlage. Danach vor Gesamtvorlage die dokumentierten Restvarianten,
Chartzuordnung und offenen Fachentscheidungen konsolidieren; keine neuen
isolierten Befundserien und keine App-Umsetzung.

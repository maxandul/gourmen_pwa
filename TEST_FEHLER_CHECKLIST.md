# 🐛 Gourmen PWA - Test Fehler Checkliste

## 📋 Übersicht
Diese Datei sammelt systematisch alle Fehler, die während des Tests der Gourmen PWA gefunden werden. Nach Abschluss des Tests werden alle Fehler behoben.

**Test-Datum:** 14.08.2025  
**Tester:** [Ihr Name]  
**Version:** Development

---

## 🔧 Phase 1: Grundlagen & Setup

### 1.1 Entwicklungsumgebung
- [x] **Python 3.12+** ✅ (bereits erfüllt)
- [x] **Virtuelle Umgebung** ✅ (bereits erfüllt)
- [x] **Dependencies** ✅ (bereits erfüllt)
- [x] **Umgebungsvariablen** ✅ (bereits erfüllt)
- [x] **Datenbank** ✅ (bereits erfüllt)
- [x] **App starten** ✅ (funktioniert mit FLASK_APP)

**Gefundene Fehler Phase 1.1:**
- [x] **Flask-Pfad Problem**: `venv/Scripts/flask.exe` nicht gefunden
  - **Beschreibung**: `Fatal error in launcher: Unable to create process using '"C:\gourmen_webapp\venv\Scripts\python.exe"`
  - **Lösung**: ✅ Mit FLASK_APP=backend.app in .env behoben
  - **Priorität**: 🔴 Hoch

### 1.2 Admin-Account
- [x] **Admin-Login** ✅ (funktioniert)
- [ ] **2FA-Setup** (noch zu testen)
- [ ] **Berechtigungen** (noch zu testen)

**Gefundene Fehler Phase 1.2:**
- [ ] (wird während Test hinzugefügt)

---

## 🔐 Phase 2: Authentifizierung & Sicherheit

### 2.1 Benutzer-Registrierung
- [ ] **Neuen Benutzer erstellen** (noch zu testen)
- [x] **E-Mail-Validierung** ⚠️ (getestet, Handy-Problem)
- [ ] **Passwort-Richtlinien** (noch zu testen)

**Gefundene Fehler Phase 2.1:**
- [ ] **E-Mail-Eingabe auf Handy**: Erster Buchstabe wird automatisch groß geschrieben
  - **Beschreibung**: Bei E-Mail-Eingabe auf dem Handy wird der erste Buchstabe automatisch groß geschrieben
  - **Problem**: E-Mail wird nicht akzeptiert, da E-Mail-Adressen klein geschrieben sein müssen
  - **Betroffen**: Login-Formular auf mobilen Geräten
  - **Priorität**: 🔴 Hoch

### 2.2 Login & 2FA
- [x] **Normaler Login** ✅ (funktioniert)
- [x] **2FA-Einrichtung** ⚠️ (getestet, aber fehlgeschlagen)
- [ ] **2FA-Login** (noch zu testen - 2FA muss erst funktionieren)
- [ ] **Backup-Codes** (noch zu testen - 2FA muss erst funktionieren)

**Gefundene Fehler Phase 2.2:**
- [ ] **2FA-Code Problem**: "Falscher Code" trotz korrekter Eingabe
  - **Beschreibung**: 2FA-Einrichtung schlägt fehl mit "Falscher Code", obwohl Code korrekt eingegeben wird
  - **Betroffen**: Microsoft Authenticator, private E-Mail-Adresse
  - **Häufigkeit**: 2x getestet, beide Male fehlgeschlagen
  - **Priorität**: 🔴 Hoch

- [ ] **UI Padding Problem**: Titelblöcke "Schritt 1" und "Schritt 2"
  - **Beschreibung**: Padding in den Titelblöcken stimmt nicht
  - **Betroffen**: 2FA-Einrichtungsseite
  - **Priorität**: 🟡 Mittel

- [ ] **Sicherheitshinweis Kontrast**: Weiße Schrift auf weißem Hintergrund
  - **Beschreibung**: Sicherheitshinweis ist nicht lesbar (weiß auf weiß)
  - **Erwartung**: Dunkle Schrift für bessere Lesbarkeit
  - **Priorität**: 🟡 Mittel

- [ ] **Profil-Sicherheit Padding**: Text "Zwei-Faktor-Authentifizierung, 2FA ist nicht aktiviert"
  - **Beschreibung**: Padding im Sicherheitsblock auf dem Profil nicht korrekt
  - **Betroffen**: Profil-Seite, Sicherheitsbereich
  - **Priorität**: 🟢 Niedrig

### 2.3 Sicherheitsfeatures
- [ ] **Step-Up-Authentifizierung** (noch zu testen)
- [ ] **Passwort-Änderung** (noch zu testen)
- [ ] **Passwort-Reset** (noch zu testen)
- [ ] **Session-Management** (noch zu testen)

**Gefundene Fehler Phase 2.3:**
- [ ] (wird während Test hinzugefügt)

---

## ⭐ Phase 3: Kern-Features

### 3.1 Dashboard

- [x] **Dashboard-Layout** ✅ (passt)
- [x] **Navigation** ✅ (funktioniert)
- [x] **Responsive Design** ✅ (passt)

**Gefundene Fehler Phase 3.1:**
- [x] **BillBro Button führt zu 500-Fehler** ✅ **BEHOBEN**
  - **Beschreibung**: BillBro-Seite führte zu 500-Fehler beim Klick auf BillBro-Button
  - **Ursache**: `TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'` in Template
  - **Lösung**: Null-Check für `betrag_sparsam_rappen` hinzugefügt
  - **Priorität**: 🔴 Hoch

- [x] **Event wird nicht in Liste angezeigt** ✅ **BEHOBEN**
  - **Beschreibung**: Erstellte Events werden nicht in der Event-Liste angezeigt
  - **Ursache**: Events werden mit `published=False` erstellt, aber nur `published=True` werden angezeigt + Datum-Filter schließt Events für heute aus + Organisatoren sind nicht automatisch Teilnehmer
  - **Lösung**: Standardwert auf `published=True` geändert + bestehende Events manuell auf published=True gesetzt + Datum-Filter korrigiert (Events für heute werden jetzt angezeigt) + Organisatoren werden automatisch als Teilnehmer hinzugefügt + Dashboard zeigt nächstes Event für alle Benutzer an
  - **Priorität**: 🔴 Hoch

- [x] **Browser-Cache Problem**: Ungestylte Seite im Inkognito-Modus ✅ **BEHOBEN**
  - **Beschreibung**: Inkognito-Fenster zeigt ungestylte/weiße Seite, Dashboard zeigt falsches Event
  - **Ursache**: Browser-Cache + Zeitzonen-Problem (UTC vs. lokale Zeit)
  - **Lösung**: Browser-Cache leeren, Flask mit Debug-Modus starten + Dashboard verwendet jetzt lokale Zeit statt UTC
  - **Priorität**: 🔴 Hoch

- [x] **Zeitzonen-Problem zwischen Laptop und Handy** ✅ **BEHOBEN**
  - **Beschreibung**: Laptop zeigt September-Event, Handy zeigt heutiges Event auf Dashboard
  - **Ursache**: Unterschiedliche Zeitzonen-Einstellungen zwischen Geräten + Events mit 00:00:00 Zeit
  - **Lösung**: Events werden jetzt mit 23:59:59 erstellt + Dashboard zeigt Events ab "morgen" an + Alle bestehenden Events aktualisiert
  - **Priorität**: 🔴 Hoch

- [ ] **Datum-Schriftart nicht CD**: Datumsfelder haben falsche Schriftart
  - **Beschreibung**: Schriftart der Datumsfelder sind noch nicht CD (Corporate Design)
  - **Betroffen**: Dashboard, Event-Anzeige
  - **Priorität**: 🟡 Mittel

- [x] **BillBro Button führt zu 500-Fehler**: Technischer Fehler bei BillBro-Aufruf ✅ **BEHOBEN**
  - **Beschreibung**: Auf kommenden Events wird BillBro angezeigt, führt aber zu Technischem Fehler 500
  - **Ursache**: Fehlender datetime Import in dashboard.py + Template-Fehler in billbro/index.html
  - **Lösung**: datetime Import korrigiert + Null-Check für betrag_sparsam_rappen hinzugefügt
  - **Betroffen**: Dashboard, kommende Events
  - **Priorität**: 🔴 Hoch

### 3.2 Event-Management
- [x] **Event erstellen** ✅ (getestet, funktioniert)
- [x] **Event bearbeiten** ✅ (getestet, funktioniert)
- [x] **Event löschen** ✅ (getestet, funktioniert)
- [x] **Event-Details** ✅ (getestet, funktioniert)
- [x] **Teilnahme eintragen/abmelden** ✅ (getestet, funktioniert)

**Gefundene Fehler Phase 3.2:**
- [ ] **Button "Statistiken" ungestylt**
  - **Beschreibung**: Button "Statistiken" hat kein Styling
  - **Betroffen**: Event-Management
  - **Priorität**: 🟡 Mittel

- [ ] **Event Lösch-Funktion fehlt**
  - **Beschreibung**: Keine Lösch-Funktion für Events vorhanden
  - **Erwartung**: Event-Lösch-Funktion implementieren
  - **Betroffen**: Event-Management
  - **Priorität**: 🔴 Hoch

- [x] **Organisator-Abtausch Teilnahme-Logik** ✅ **BEHOBEN**
  - **Beschreibung**: Beim Organisator-Abtausch werden Teilnahme-Einträge nicht korrekt angepasst
  - **Lösung**: Alter Organisator wird als Teilnehmer entfernt, neuer Organisator wird automatisch als Teilnehmer hinzugefügt
  - **Betroffen**: Event-Bearbeitung
  - **Priorität**: 🔴 Hoch

- [ ] **Hinweis "Organisatoren können sich hier austauschen" überflüssig**
  - **Beschreibung**: Text ist überflüssig beim Event erstellen
  - **Erwartung**: Entfernen oder ändern zu "Organisatoren können sich hier abtauschen"
  - **Betroffen**: Event-Erstellung
  - **Priorität**: 🟢 Niedrig

- [ ] **Google Places Autocomplete funktioniert nicht**
  - **Beschreibung**: Google Places Autocomplete funktioniert nicht in Testumgebung
  - **Frage**: Funktioniert das überhaupt in der Testumgebung?
  - **Betroffen**: Event-Erstellung, Ort-Eingabe
  - **Priorität**: 🟡 Mittel

- [ ] **Google Places Daten unvollständig**
  - **Beschreibung**: Preisniveau und Google Place Link werden nicht erfasst
  - **Erwartung**: Preisniveau und Link zu Google Place sollten erfasst werden
  - **Betroffen**: Event-Erstellung, Ort-Details
  - **Priorität**: 🟡 Mittel

- [ ] **Menü Icons nicht optimal**
  - **Beschreibung**: GGL Logo muss komplett neu gemacht werden, Events ist nur ein Viereck
  - **Betroffen**: Navigation, Menü
  - **Priorität**: 🟡 Mittel

### 3.3 Mitglieder-Verwaltung
- [x] **Mitglieder-Liste** ✅ (getestet, funktioniert)
- [x] **Mitglieder-Details** ✅ (getestet, funktioniert)
- [x] **Sensible Daten** ✅ (getestet, funktioniert)
- [x] **Mitglied bearbeiten** ✅ (getestet, funktioniert)

**Gefundene Fehler Phase 3.3:**
- [ ] **Mobile Layout Mitglieder nicht optimal**: Zu linksbündig, Buttons nicht mobile optimiert
  - **Beschreibung**: Mobile Layout der Mitglieder gefällt nicht, alle zu linksbündig
  - **Betroffen**: Buttons "Bearbeiten" und "Sensible Daten" noch nicht mobile optimiert
  - **Priorität**: 🟡 Mittel

- [ ] **Header-Zeilen weiße Schrift auf weißem Hintergrund**: Mitglied bearbeiten
  - **Beschreibung**: Auf Mitglied bearbeiten sind die Header-Zeilen noch weiße Schrift auf weißem Hintergrund
  - **Betroffen**: Mitglied bearbeiten Seite
  - **Priorität**: 🟡 Mittel

- [ ] **Speichern bei neuem Mitglied funktioniert nicht**
  - **Beschreibung**: Speichern beim neuen Mitglied erstellen funktioniert nicht
  - **Betroffen**: Mitglied erstellen
  - **Priorität**: 🔴 Hoch

- [ ] **Sensible Daten Weiterleitung falsch**: Auf Dashboard weitergeleitet
  - **Beschreibung**: Bei Zugriff auf sensible Daten wird nach der erneuten Sicherheitsprüfung auf Dashboard weitergeleitet
  - **Erwartung**: Sollte auf sensible Daten-Seite weiterleiten
  - **Betroffen**: Step-Up-Authentifizierung
  - **Priorität**: 🔴 Hoch

- [ ] **"Führerschein" ist kein sensible Daten**: Sollte bereits angezeigt werden
  - **Beschreibung**: "Führerschein" ist kein sensible Daten, soll bereits im Account und auf Mitgliederliste angezeigt werden
  - **Betroffen**: Mitglieder-Liste, Account-Anzeige
  - **Priorität**: 🟡 Mittel

---

## 🍽️ Phase 4: BillBro-System

### 4.1 BillBro-Workflow
- [x] **BillBro-Session starten** ✅ (getestet, funktioniert)
- [x] **Push-Benachrichtigungen** ⚠️ (getestet, funktioniert nicht)
- [x] **Ess-Typ auswählen** ✅ (getestet, funktioniert)
- [x] **Rechnungsbetrag schätzen** ⚠️ (getestet, UI-Problem)
- [x] **Rechnungsbetrag eingeben** ⚠️ (getestet, UI-Problem)
- [x] **Gesamtbetrag festlegen** ⚠️ (getestet, UI-Problem)
- [x] **Ergebnisse anzeigen** ❌ (getestet, 500-Fehler)

**Gefundene Fehler Phase 4.1:**
- [ ] **Push-Benachrichtigungen funktionieren nicht**: "Erinnerungen konnten nicht gesendet werden"
  - **Beschreibung**: Erinnerungen senden schlägt fehl, keine Push-Benachrichtigungen auf Handy
  - **Anmerkung**: Erinnerung senden kann komplett weggelassen werden, da alle am Tisch sitzen
  - **Betroffen**: BillBro-Organisator-Ansicht
  - **Priorität**: 🟢 Niedrig (kann entfernt werden)

- [ ] **Zahlenfelder nur eine Kommastelle**: Rechnungsbetrag und Gesamtbetrag
  - **Beschreibung**: Zahlenfelder erlauben nur eine Kommastelle, sollten mehr erlauben
  - **Betroffen**: BillBro-Eingabefelder
  - **Priorität**: 🟡 Mittel

- [x] **"Ergebnisse anzeigen" führt zu 500-Fehler**: Technischer Fehler ✅ **BEHOBEN**
  - **Beschreibung**: Klick auf "Ergebnisse anzeigen" führt zu 500 Technischer Fehler
  - **Ursache**: Null-Werte in betrag_*_rappen Feldern verursachten Division-by-zero Fehler
  - **Lösung**: Null-Checks in Template und Route hinzugefügt
  - **Betroffen**: BillBro-Organisator-Ansicht
  - **Priorität**: 🔴 Hoch

- [x] **"WhatsApp teilen" führt zu 500-Fehler**: Technischer Fehler ✅ **BEHOBEN**
  - **Beschreibung**: Klick auf "WhatsApp teilen" führt zu 500 Technischer Fehler
  - **Ursache**: Null-Werte in betrag_*_rappen Feldern verursachten Division-by-zero Fehler
  - **Lösung**: Null-Checks in share_whatsapp Route hinzugefügt
  - **Anmerkung**: WhatsApp teilen erübrigt sich, da alle am Tisch sitzen
  - **Betroffen**: BillBro-Organisator-Ansicht
  - **Priorität**: 🟢 Niedrig (kann entfernt werden)

- [x] **Fehlende Teilnehmer-Ansicht**: UX-Problem ✅ **BEHOBEN**
  - **Beschreibung**: Teilnehmer haben keine eigene BillBro-Ansicht für Schätzungen
  - **Ursache**: BillBro-Button wurde nur angezeigt, wenn BillBro bereits aktiv war
  - **Lösung**: BillBro-Button wird immer für Teilnehmer angezeigt, mit Status-Information
  - **Betroffen**: Event-Detail-Seite, Event-Liste, Dashboard
  - **Priorität**: 🔴 Hoch

- [x] **Ergebnisse nicht für alle sichtbar**: UX-Problem ✅ **BEHOBEN**
  - **Beschreibung**: Teilnehmer können keine BillBro-Ergebnisse sehen
  - **Ursache**: Ergebnisse wurden nur in Organisator-View angezeigt
  - **Lösung**: Ergebnisse-Sektion für Teilnehmer hinzugefügt
  - **Betroffen**: BillBro-Teilnehmer-Ansicht
  - **Priorität**: 🟡 Mittel

- [x] **Organisator fehlt eigene Schätzung**: UX-Problem ✅ **BEHOBEN**
  - **Beschreibung**: Organisator kann keine eigene Schätzung abgeben
  - **Ursache**: Organisator-View hatte keine Schätzungssektion
  - **Lösung**: Eigene Schätzungssektion für Organisator hinzugefügt
  - **Betroffen**: BillBro-Organisator-Ansicht
  - **Priorität**: 🟡 Mittel

- [x] **Fehlender BillBro-Abschluss**: UX-Problem ✅ **BEHOBEN**
  - **Beschreibung**: Organisator kann BillBro nicht abschließen/wieder öffnen
  - **Ursache**: Keine Toggle-Funktion für BillBro-Status
  - **Lösung**: Toggle-Route und Button hinzugefügt, Schätzungen werden blockiert
  - **Betroffen**: BillBro-Organisator-Ansicht
  - **Priorität**: 🟡 Mittel

### 4.2 BillBro-Berechnungen
- [ ] **Gewichtungssystem** (noch zu testen - 500-Fehler verhindert Test)
- [ ] **Schätzungs-Rangliste** (noch zu testen - 500-Fehler verhindert Test)
- [ ] **Individuelle Anteile** (noch zu testen - 500-Fehler verhindert Test)
- [ ] **Trinkgeld-Berechnung** (noch zu testen - 500-Fehler verhindert Test)

**Gefundene Fehler Phase 4.2:**
- [ ] **Berechnungen können nicht getestet werden**: 500-Fehler verhindert Zugriff auf Ergebnisse
  - **Beschreibung**: "Ergebnisse anzeigen" führt zu 500-Fehler, daher können Berechnungen nicht getestet werden
  - **Betroffen**: BillBro-Berechnungslogik
  - **Priorität**: 🔴 Hoch

---

## 🏆 Phase 5: GGL (Gourmen Guessing League)

### 5.1 GGL-System
- [ ] **Punktevergabe** (noch zu testen - BillBro-Eingabemaske fehlt)
- [x] **Saisonwertungen** ⚠️ (getestet, UI-Problem)
- [x] **Ranglisten** ⚠️ (getestet, UI-Problem)
- [x] **GGL-Regeln** ✅ (getestet, funktioniert)

**Gefundene Fehler Phase 5.1:**
- [ ] **GGL Saison-Statistik Kontrast**: Weiße Schrift auf hellem Hintergrund
  - **Beschreibung**: Saisonstatistik hat weiße Schrift auf hellem Hintergrund, nicht lesbar
  - **Betroffen**: GGL Saison-Statistik
  - **Priorität**: 🟡 Mittel

- [ ] **GGL Saison-Übersicht Kontrast**: Weiße Schrift auf hellem Hintergrund
  - **Beschreibung**: Saison-Übersicht Titel hat weiße Schrift auf hellem Hintergrund, nicht lesbar
  - **Betroffen**: GGL Saison-Übersicht
  - **Priorität**: 🟡 Mittel

- [ ] **Alte Saisons nicht einsehbar**: Unklar ob DB-Problem oder nicht implementiert
  - **Beschreibung**: Alte Saisons können nicht eingesehen werden
  - **Frage**: Liegt es daran, dass sie nicht in der DB erfasst sind oder ist es nicht implementiert?
  - **Betroffen**: GGL Saison-Historie
  - **Priorität**: 🟡 Mittel

---

## 📱 Phase 6: PWA-Features

### 6.1 Installation
- [x] **PWA installieren** ✅ (Browser funktioniert, Handy noch unklar)
- [x] **Install-Prompt** ⚠️ (Browser funktioniert, Handy nicht)
- [x] **App-Icon** ✅ (Desktop funktioniert, Handy noch unklar)

**Gefundene Fehler Phase 6.1:**
- [ ] **PWA Install-Button Problem**: Unnötige zusätzliche Box ohne Funktionalität
  - **Beschreibung**: Install-Button oben rechts hat eine zusätzliche Box ohne Symbol/Text, die nicht klickbar ist
  - **Erwartung**: Sollte ein X-Symbol zum Schließen des Hinweises sein
  - **Lösung**: 
  - **Priorität**: 🟡 Mittel

- [ ] **PWA Install-Button Position**: Permanentes Feld rechts unterhalb des Headers
  - **Beschreibung**: Button liegt nicht auf "Installieren", sondern ist permanent da
  - **Betroffen**: Kleines Feld rechts unterhalb des Headers
  - **Priorität**: 🟡 Mittel

- [ ] **Install-Prompt auf Handy nicht sichtbar**: Kein Install-Hinweis auf mobilen Geräten
  - **Beschreibung**: Install-Prompt wird auf dem Handy nicht angezeigt
  - **Betroffen**: Mobile PWA-Installation
  - **Priorität**: 🔴 Hoch

### 6.2 Offline-Funktionalität
- [ ] **Offline-Modus** (noch zu testen)
- [ ] **Cache-Verhalten** (noch zu testen)
- [ ] **Background Sync** (noch zu testen)
- [ ] **Offline-Seite** (noch zu testen)

**Gefundene Fehler Phase 6.2:**
- [ ] (wird während Test hinzugefügt)

### 6.3 Push-Benachrichtigungen
- [x] **Benachrichtigungen aktivieren** ❌ (getestet, funktioniert nicht auf Handy)
- [ ] **Event-Benachrichtigungen** (noch zu testen - Push muss erst funktionieren)
- [ ] **BillBro-Benachrichtigungen** (noch zu testen - Push muss erst funktionieren)
- [ ] **Erinnerungen** (noch zu testen - Push muss erst funktionieren)

**Gefundene Fehler Phase 6.3:**
- [ ] **Push-Benachrichtigungen auf Handy nicht verfügbar**: Keine Möglichkeit, Benachrichtigungen zu aktivieren
  - **Beschreibung**: Push-Benachrichtigungen können auf dem Handy nicht aktiviert werden
  - **Betroffen**: Mobile Push-Benachrichtigungen
  - **Priorität**: 🔴 Hoch

---

## 🔧 Phase 7: Erweiterte Features

### 7.1 Dokumenten-Management
- [ ] **Dokumente hochladen** (noch zu testen)
- [ ] **Dokumente anzeigen** (noch zu testen)
- [ ] **Soft-Delete** (noch zu testen)

**Gefundene Fehler Phase 7.1:**
- [ ] (wird während Test hinzugefügt)

### 7.2 Bewertungssystem
- [ ] **Event bewerten** (noch zu testen - UI-Änderungen erforderlich)
- [ ] **Bewertungen anzeigen** (noch zu testen - UI-Änderungen erforderlich)
- [ ] **Durchschnittsbewertungen** (noch zu testen - UI-Änderungen erforderlich)

**Gefundene Fehler Phase 7.2:**
- [ ] **Event bewerten nur auf Event-Details**: Bewertung sollte auch auf Dashboard-Event möglich sein
  - **Beschreibung**: Event bewerten ist nur auf Event-Details-Seite möglich
  - **Erwartung**: Bewertung sollte auch direkt auf dem Dashboard-Event möglich sein
  - **Betroffen**: Dashboard, Event-Bewertung
  - **Priorität**: 🔴 Hoch

- [ ] **Bewertungsskala falsch**: Zahlenfeld statt klickbare Skala
  - **Beschreibung**: Bewertung erfolgt über Zahlenfeld statt klickbare Skala
  - **Erwartung**: Klickbare Skala von 1 bis 5 Sternen
  - **Betroffen**: Event-Bewertung
  - **Priorität**: 🔴 Hoch

- [ ] **Gesamtbewertung nicht prominent**: Gesamtbewertung wird nicht groß angezeigt
  - **Beschreibung**: Gesamtbewertung wird nicht prominent auf Event-Details angezeigt
  - **Erwartung**: Gesamtbewertung sollte groß und prominent auf Event-Details angezeigt werden
  - **Betroffen**: Event-Details-Seite
  - **Priorität**: 🟡 Mittel

- [ ] **Archiv-Button fehlt**: Button "Archiv anzeigen" nicht vorhanden
  - **Beschreibung**: Button "Archiv anzeigen" fehlt bei Event-Verwaltung
  - **Erwartung**: Button sollte oben bei "Neues Event" und "Statistiken" angezeigt werden
  - **Betroffen**: Event-Verwaltung
  - **Priorität**: 🟡 Mittel

- [ ] **Logo im Header muss umgestylt werden**: Logo zur Startseite führt
  - **Beschreibung**: Logo im Header, das zur Startseite führt, muss umgestylt werden
  - **Betroffen**: Header, Navigation
  - **Priorität**: 🟡 Mittel

- [ ] **Eventarchiv braucht mehr Filtermöglichkeiten**: Nach Organisator, Eventtyp und Bewertung
  - **Beschreibung**: Eventarchiv hat zu wenige Filtermöglichkeiten
  - **Erwartung**: Filter nach Organisator, Eventtyp und Bewertung hinzufügen
  - **Betroffen**: Eventarchiv
  - **Priorität**: 🟡 Mittel

- [ ] **Nicht-Admins werden zu "Zugriff verweigert" weitergeleitet**: Zu harte Fehlermeldung
  - **Beschreibung**: Nicht-Admins werden beim Klick auf "Neues Event" zu "Zugriff verweigert" weitergeleitet
  - **Erwartung**: Benachrichtigung "Nur Admins können Events erstellen" reicht
  - **Betroffen**: Event-Erstellung, Berechtigungen
  - **Priorität**: 🟡 Mittel

- [ ] **Anmeldung an Events nach Eventdatum +2 Tage nicht mehr möglich**: Keine zeitliche Begrenzung
  - **Beschreibung**: Anmeldung an Events sollte nach Eventdatum +2 Tage nicht mehr möglich sein
  - **Betroffen**: Event-Teilnahme
  - **Priorität**: 🟡 Mittel

- [ ] **Zusage/Absage-Buttons nicht farblich gekennzeichnet**: Keine visuelle Unterscheidung
  - **Beschreibung**: Zusage- und Absage-Buttons haben keine farbliche Kennzeichnung
  - **Erwartung**: Zusage-Button grün, Absage-Button rot, beide mit schönem Fade
  - **Betroffen**: Event-Teilnahme
  - **Priorität**: 🟡 Mittel

- [ ] **Teilnehmerliste zeigt nicht alle aktiven Member**: Unvollständige Anzeige
  - **Beschreibung**: Teilnehmerliste zeigt nicht alle aktiven Member permanent an
  - **Erwartung**: Alle aktiven Member mit "nimmt teil", "abgesagt" und "antwort ausstehend" anzeigen
  - **Betroffen**: Event-Details
  - **Priorität**: 🟡 Mittel

- [ ] **Push-Benachrichtigung für ausstehende Antworten fehlt**: Organisator kann nicht erinnern
  - **Beschreibung**: Organisator kann keine Push-Benachrichtigung an ausstehende Antworten senden
  - **Erwartung**: Push-Benachrichtigung, die direkt zu Event-Details führt
  - **Betroffen**: Event-Management
  - **Priorität**: 🟡 Mittel

- [ ] **Zu-/Absage auf Dashboard nicht möglich**: Keine direkte Teilnahme vom Dashboard
  - **Beschreibung**: Zu- oder Absage sollte auch auf dem Dashboard bei kommenden Events möglich sein
  - **Erwartung**: Nach Antwort sollte das wieder verschwinden
  - **Betroffen**: Dashboard
  - **Priorität**: 🟡 Mittel

- [ ] **GGL Rangliste im Dashboard unvollständig**: Fehlende Informationen
  - **Beschreibung**: GGL Rangliste im Dashboard zeigt nicht alle relevanten Informationen
  - **Erwartung**: Erste drei Ränge mit Punkten + Rang und Punkte des jeweiligen Teilnehmers
  - **Betroffen**: Dashboard, GGL
  - **Priorität**: 🟡 Mittel

- [ ] **Sensible Daten im Profil zu oberst statt zu unterst**: Falsche Position
  - **Beschreibung**: Sensible Daten werden im Profil zu oberst angezeigt
  - **Erwartung**: Sensible Daten sollten zu unterst angezeigt werden
  - **Betroffen**: Profil-Seite
  - **Priorität**: 🟡 Mittel

### 7.3 Statistiken
- [ ] **Event-Statistiken** (noch zu testen)
- [ ] **Teilnahme-Statistiken** (noch zu testen)
- [ ] **BillBro-Statistiken** (noch zu testen)

**Gefundene Fehler Phase 7.3:**
- [ ] (wird während Test hinzugefügt)

---

## 👨‍💼 Phase 8: Admin-Features

### 8.1 Admin-Panel
- [ ] **Admin-Dashboard** (noch zu testen)
- [ ] **Benutzer-Verwaltung** (noch zu testen)
- [ ] **Event-Verwaltung** (noch zu testen)
- [ ] **System-Einstellungen** (noch zu testen)

**Gefundene Fehler Phase 8.1:**
- [ ] (wird während Test hinzugefügt)

### 8.2 Audit-Logging
- [ ] **Audit-Logs** (noch zu testen)
- [ ] **Sicherheits-Events** (noch zu testen)
- [ ] **Benutzer-Aktivitäten** (noch zu testen)

**Gefundene Fehler Phase 8.2:**
- [ ] (wird während Test hinzugefügt)

---

## ⚡ Phase 9: Performance & Stabilität

### 9.1 Performance
- [ ] **Ladezeiten** (noch zu testen)
- [ ] **Datenbank-Performance** (noch zu testen)
- [ ] **PWA-Caching** (noch zu testen)

**Gefundene Fehler Phase 9.1:**
- [ ] (wird während Test hinzugefügt)

### 9.2 Fehlerbehandlung
- [ ] **404-Fehler** (noch zu testen)
- [ ] **500-Fehler** (noch zu testen)
- [ ] **Validierungsfehler** (noch zu testen)
- [ ] **Berechtigungsfehler** (noch zu testen)

**Gefundene Fehler Phase 9.2:**
- [ ] (wird während Test hinzugefügt)

---

## 📚 Phase 10: Dokumentation & Wartung

### 10.1 Dokumentation
- [ ] **README-Dateien** (noch zu testen)
- [ ] **Code-Kommentare** (noch zu testen)
- [ ] **API-Dokumentation** (noch zu testen)

**Gefundene Fehler Phase 10.1:**
- [ ] (wird während Test hinzugefügt)

### 10.2 Wartung
- [ ] **Logs überprüfen** (noch zu testen)
- [ ] **Datenbank-Backup** (noch zu testen)
- [ ] **Update-Prozess** (noch zu testen)

**Gefundene Fehler Phase 10.2:**
- [ ] (wird während Test hinzugefügt)

---

## 📊 Zusammenfassung

### 🔴 Kritische Fehler (Hoch)
- [x] Flask-Pfad Problem (Phase 1.1) ✅ Behoben
- [x] BillBro Button führt zu 500-Fehler (Phase 3.1) ✅ Behoben
- [ ] 2FA-Code Problem (Phase 2.2)
- [ ] Event Lösch-Funktion fehlt (Phase 3.2)
- [ ] Speichern bei neuem Mitglied funktioniert nicht (Phase 3.3)
- [ ] Sensible Daten Weiterleitung falsch (Phase 3.3)
- [ ] "Ergebnisse anzeigen" führt zu 500-Fehler (Phase 4.1) ✅ Behoben
- [x] Fehlende Teilnehmer-Ansicht (Phase 4.1) ✅ Behoben
- [x] Ergebnisse nicht für alle sichtbar (Phase 4.1) ✅ Behoben
- [x] Organisator fehlt eigene Schätzung (Phase 4.1) ✅ Behoben
- [x] Fehlender BillBro-Abschluss (Phase 4.1) ✅ Behoben
- [ ] E-Mail-Eingabe auf Handy (Phase 2.1)
- [ ] Install-Prompt auf Handy nicht sichtbar (Phase 6.1)
- [ ] Push-Benachrichtigungen auf Handy nicht verfügbar (Phase 6.3)
- [ ] Event bewerten nur auf Event-Details (Phase 7.2)
- [ ] Bewertungsskala falsch (Phase 7.2)

### 🟡 Wichtige Fehler (Mittel)
- [ ] PWA Install-Button Problem (Phase 6.1)
- [ ] PWA Install-Button Position (Phase 6.1)
- [ ] UI Padding Problem (Phase 2.2)
- [ ] Sicherheitshinweis Kontrast (Phase 2.2)
- [ ] Datum-Schriftart nicht CD (Phase 3.1)
- [ ] Button "Statistiken" ungestylt (Phase 3.2)
- [ ] Google Places Autocomplete funktioniert nicht (Phase 3.2)
- [ ] Google Places Daten unvollständig (Phase 3.2)
- [ ] Menü Icons nicht optimal (Phase 3.2)
- [ ] Mobile Layout Mitglieder nicht optimal (Phase 3.3)
- [ ] Header-Zeilen weiße Schrift auf weißem Hintergrund (Phase 3.3)
- [ ] "Führerschein" ist kein sensible Daten (Phase 3.3)
- [ ] Zahlenfelder nur eine Kommastelle (Phase 4.1)
- [ ] GGL Saison-Statistik Kontrast (Phase 5.1)
- [ ] GGL Saison-Übersicht Kontrast (Phase 5.1)
- [ ] Alte Saisons nicht einsehbar (Phase 5.1)
- [ ] Gesamtbewertung nicht prominent (Phase 7.2)
- [ ] Archiv-Button fehlt (Phase 7.2)
- [ ] Logo im Header muss umgestylt werden (Phase 3.1)
- [ ] Eventarchiv braucht mehr Filtermöglichkeiten (Phase 3.2)
- [ ] Nicht-Admins werden zu "Zugriff verweigert" weitergeleitet (Phase 3.2)
- [ ] Anmeldung an Events nach Eventdatum +2 Tage nicht mehr möglich (Phase 3.2)
- [ ] Zusage/Absage-Buttons nicht farblich gekennzeichnet (Phase 3.2)
- [ ] Teilnehmerliste zeigt nicht alle aktiven Member (Phase 3.2)
- [ ] Push-Benachrichtigung für ausstehende Antworten fehlt (Phase 3.2)
- [ ] Zu-/Absage auf Dashboard nicht möglich (Phase 3.1)
- [ ] GGL Rangliste im Dashboard unvollständig (Phase 3.1)
- [ ] Sensible Daten im Profil zu oberst statt zu unterst (Phase 2.2)

### 🟢 Kleine Fehler (Niedrig)
- [ ] Profil-Sicherheit Padding (Phase 2.2)
- [ ] Hinweis "Organisatoren können sich hier austauschen" überflüssig (Phase 3.2)
- [ ] Push-Benachrichtigungen funktionieren nicht (Phase 4.1) - kann entfernt werden
- [ ] "WhatsApp teilen" führt zu 500-Fehler (Phase 4.1) - kann entfernt werden

### 🔧 Technische Verbesserungen
- [ ] **ID-Erstellung in DB überprüfen**: Doppelungen vermeiden
  - **Beschreibung**: Überprüfung der ID-Erstellung in der Datenbank, dass es zu keinen Doppelungen kommen kann
  - **Betroffen**: Datenbank-Design
  - **Priorität**: 🟡 Mittel

### ✅ Behobene Fehler
- [x] Flask-Pfad Problem (Phase 1.1) - Mit FLASK_APP=backend.app behoben
- [x] BillBro Button führt zu 500-Fehler (Phase 3.1) - Fehlender datetime Import behoben

---

## 🎯 Nächste Schritte

1. **Test vollständig durchführen**
2. **Alle Fehler dokumentieren**
3. **Prioritäten setzen**
4. **Fehler systematisch beheben**
5. **Retest durchführen**

---

**Status:** 🟡 Test läuft  
**Letzte Aktualisierung:** 14.08.2025

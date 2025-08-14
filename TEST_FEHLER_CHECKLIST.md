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
- [ ] **E-Mail-Validierung** (noch zu testen)
- [ ] **Passwort-Richtlinien** (noch zu testen)

**Gefundene Fehler Phase 2.1:**
- [ ] (wird während Test hinzugefügt)

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
- [ ] **Datum-Schriftart nicht CD**: Datumsfelder haben falsche Schriftart
  - **Beschreibung**: Schriftart der Datumsfelder sind noch nicht CD (Corporate Design)
  - **Betroffen**: Dashboard, Event-Anzeige
  - **Priorität**: 🟡 Mittel

- [ ] **BillBro Button führt zu 500-Fehler**: Technischer Fehler bei BillBro-Aufruf
  - **Beschreibung**: Auf kommenden Events wird BillBro angezeigt, führt aber zu Technischem Fehler 500
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
- [ ] **Mitglieder-Liste** (noch zu testen)
- [ ] **Mitglieder-Details** (noch zu testen)
- [ ] **Sensible Daten** (noch zu testen)
- [ ] **Mitglied bearbeiten** (noch zu testen)

**Gefundene Fehler Phase 3.3:**
- [ ] (wird während Test hinzugefügt)

---

## 🍽️ Phase 4: BillBro-System

### 4.1 BillBro-Workflow
- [ ] **BillBro-Session starten** (noch zu testen)
- [ ] **Push-Benachrichtigungen** (noch zu testen)
- [ ] **Ess-Typ auswählen** (noch zu testen)
- [ ] **Rechnungsbetrag schätzen** (noch zu testen)
- [ ] **Rechnungsbetrag eingeben** (noch zu testen)
- [ ] **Gesamtbetrag festlegen** (noch zu testen)
- [ ] **Ergebnisse anzeigen** (noch zu testen)

**Gefundene Fehler Phase 4.1:**
- [ ] (wird während Test hinzugefügt)

### 4.2 BillBro-Berechnungen
- [ ] **Gewichtungssystem** (noch zu testen)
- [ ] **Schätzungs-Rangliste** (noch zu testen)
- [ ] **Individuelle Anteile** (noch zu testen)
- [ ] **Trinkgeld-Berechnung** (noch zu testen)

**Gefundene Fehler Phase 4.2:**
- [ ] (wird während Test hinzugefügt)

---

## 🏆 Phase 5: GGL (Gourmen Guessing League)

### 5.1 GGL-System
- [ ] **Punktevergabe** (noch zu testen)
- [ ] **Saisonwertungen** (noch zu testen)
- [ ] **Ranglisten** (noch zu testen)
- [ ] **GGL-Regeln** (noch zu testen)

**Gefundene Fehler Phase 5.1:**
- [ ] (wird während Test hinzugefügt)

---

## 📱 Phase 6: PWA-Features

### 6.1 Installation
- [x] **PWA installieren** ✅ (funktioniert)
- [x] **Install-Prompt** ✅ (funktioniert)
- [x] **App-Icon** ✅ (funktioniert)

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

### 6.2 Offline-Funktionalität
- [ ] **Offline-Modus** (noch zu testen)
- [ ] **Cache-Verhalten** (noch zu testen)
- [ ] **Background Sync** (noch zu testen)
- [ ] **Offline-Seite** (noch zu testen)

**Gefundene Fehler Phase 6.2:**
- [ ] (wird während Test hinzugefügt)

### 6.3 Push-Benachrichtigungen
- [ ] **Benachrichtigungen aktivieren** (noch zu testen)
- [ ] **Event-Benachrichtigungen** (noch zu testen)
- [ ] **BillBro-Benachrichtigungen** (noch zu testen)
- [ ] **Erinnerungen** (noch zu testen)

**Gefundene Fehler Phase 6.3:**
- [ ] (wird während Test hinzugefügt)

---

## 🔧 Phase 7: Erweiterte Features

### 7.1 Dokumenten-Management
- [ ] **Dokumente hochladen** (noch zu testen)
- [ ] **Dokumente anzeigen** (noch zu testen)
- [ ] **Soft-Delete** (noch zu testen)

**Gefundene Fehler Phase 7.1:**
- [ ] (wird während Test hinzugefügt)

### 7.2 Bewertungssystem
- [ ] **Event bewerten** (noch zu testen)
- [ ] **Bewertungen anzeigen** (noch zu testen)
- [ ] **Durchschnittsbewertungen** (noch zu testen)

**Gefundene Fehler Phase 7.2:**
- [ ] (wird während Test hinzugefügt)

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
- [ ] 2FA-Code Problem (Phase 2.2)
- [ ] BillBro Button führt zu 500-Fehler (Phase 3.1)
- [ ] Event Lösch-Funktion fehlt (Phase 3.2)

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

### 🟢 Kleine Fehler (Niedrig)
- [ ] Profil-Sicherheit Padding (Phase 2.2)
- [ ] Hinweis "Organisatoren können sich hier austauschen" überflüssig (Phase 3.2)

### ✅ Behobene Fehler
- [x] Flask-Pfad Problem (Phase 1.1) - Mit FLASK_APP=backend.app behoben

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

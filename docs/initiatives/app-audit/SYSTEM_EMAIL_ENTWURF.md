# Systemzustände und E-Mail-Grundvorlage

Stand: 11. Oktober 2026. Gestaltung und gezeigte Benutzerführung des verbleibenden
Entwurfsblocks 6 mit «ok. passt.» bestätigt. Technische/Fachgrenzen bleiben offen.
Öffentliche Homepage durch «ja das passt doch. machen wir weiter» hinsichtlich
Gestaltung und gezeigter Benutzerführung bestätigt. Fach-/Inhaltsfragen bleiben offen.

Vorschau `system-email-entwurf.html` im Visualisierungsordner der Unterhaltung.
Grundlage: vorhandener PWA_PERFORMANCE_REVIEW.md, Konto-/Dokumentenentwürfe und
bestehende E-Mail-Templates. Keine neue Befundserie oder Änderung an laufender App.

## Systemmuster

| Zustand | Darstellung und nächster Schritt |
|---|---|
| Offline ohne verfügbare Seite | Verständliche Ersatzansicht, manuelles Wiederholen. Keine erfundene Offline-Verfügbarkeit privater Inhalte. |
| Teilbereich nicht geladen | Erfolgreich geladene Nachbarbereiche bleiben sichtbar. Fehlender Betrag wird nicht als null ausgegeben. Erneuter Versuch nur für den betroffenen Bereich. |
| Speicherung unklar | Status abfragen, bevor die Aktion erneut gesendet wird. Fehlgeschlagene Statusprüfung bleibt unklar; Beispielerfolg bestätigt die schon vorhandene Zusage. |
| Update bei offenen Eingaben | Nicht blockierender Hinweis, Später oder Aktualisieren. Bei offenen Eingaben Bestätigung mit Abbrechen/Verwerfen; vorheriges Speichern als regulärer Weg. Kein automatischer Reload. |
| Anmeldung abgelaufen | Geschützten Inhalt nicht weiter anzeigen; erneute Anmeldung mit Rückkehr zum ursprünglichen internen Ziel. |
| Nicht gefunden / kein Zugriff | Unterschiedliche Texte, keine internen Fehlerdetails; Rückweg zu erreichbarer Übersicht. |
| Push | Nicht eingerichtet, aktiv, browserseitig blockiert und nicht unterstützt getrennt. Blockierung wird nicht durch wiederholte App-Anfrage scheinbar aufgehoben. |
| Installation | Unterstützte Browserabfrage oder manuelle Anleitung; keine überall gleiche Installation behauptet. |

Fehler/Speicherstand werden textlich erklärt und nicht nur über Farbe signalisiert.
Update-Entwurf bleibt beim Abbrechen/Zurückstellen erhalten. Bei simuliert nicht
erreichbarem Update wird auch nach Bestätigung nichts verworfen. Die Vorschau
lädt die App niemals tatsächlich neu. Eine erfolgreiche Speicherung wird nur
lokal simuliert; langlebiger Entwurfserhalt ist nicht bewiesen.

Mobile/Tablet stapeln Bereiche und Aktionen bei Platzmangel, Desktop lässt
unabhängige Inhaltsbereiche nebeneinander stehen. Fehlertext bleibt bei dem
betroffenen Objekt; globale Unterbrechungen bekommen eine eigene Ansicht.
Bestehender App-Rahmen und Hell-/Dunkelmodus bleiben erhalten.

## E-Mail-Muster

Fünf Varianten decken die bestehenden Inhaltstemplates ab; `base.html` ist die
gemeinsame sechste Inventarposition:

- Einladung: Zugang einrichten, unerwartete Einladung an Vorstand melden.
- Passwort: neues Passwort setzen, unverlangte Anfrage ignorieren.
- Zwei-Faktor-Wiederherstellung: sicheren Ablauf öffnen, kein unmittelbarer
  Sicherheitsreset durch das reine Öffnen der E-Mail oder Vorschau.
- Google-Adresse: konkreten Zweck Drive-Zugang nennen; keine Passwortänderung
  suggerieren und eine noch nicht erfolgte externe Einladung nicht als erledigt melden.
- Versandtest: keine unnötige Hauptaktion.

Gemeinsam: verständlicher Betreff, Gourmen-Absendergestaltung, persönliche Anrede,
Anlass, eine Hauptaktion, tatsächliche Ablaufzeit, verständliche Hilfe und
lesbarer Ersatzlink. Wenige Bilder, Text bleibt auch ohne Logo verständlich.
Keine App-Navigation oder Homepage-Hero innerhalb der Nachricht. Maximal circa
620 Pixel breite Nachricht auf Desktop, mobile Umbrüche ohne horizontales Scrollen.

Die Vorschau verwendet Beispieldatum/-adresse und `gourmen.example`, keine
gültigen Links oder Tokens. Fristen kommen später aus dem jeweiligen tatsächlichen
Token-Ablauf; eine einheitliche neue Frist ist nicht beschlossen. F1 bleibt offen.
Kein Versand und keine Änderung an Absender-/Reply-to-Konfiguration.

## Grenzen und Abnahmebedarf

- Kein Service Worker, Browser-Push, Netzwerkabruf, Login oder echter E-Mail-Client
  beteiligt. Die Zustandsauswahl simuliert die jeweilige Situation.
- Private Cachegrenzen, Kontowechsel, sichere Entwurfswiederaufnahme und Mehrtab-
  Updates benötigen die technische Korrektur und Abnahme aus U1/U5.
- Statusprüfung muss später echte idempotente Serverantworten verwenden. Der
  Entwurf beweist weder Duplikatschutz noch Offline-Schreibfähigkeit.
- Nicht unterstützt, verweigert und fehlgeschlagene Push-Registrierung sind im
  Backend getrennt zu behandeln; genaue Geräteanleitungen aktuell verifizieren.
- E-Mail-Umsetzung weiterhin mit E-Mail-tauglichem Layout, Inline-Stilen und
  Textalternative. Vorschau ist kein versandfertiges Template und kein Nachweis
  für Outlook/Gmail, Bildblockierung oder deren Dunkelmodus.
- 2FA-Wiederherstellung und externe Drive-Berechtigungen nicht durch Layoutfreigabe
  fachlich beschliessen. Gültigkeit, Identitätsprüfung und Widerruf bleiben F1/F2.

## Prüfung

Lokales Chromium: 14 Beispielzustände auf 320, 390, 768, 820, 1024 und 1440 Pixeln,
kein äusserer Überlauf oder JavaScript-Fehler. Update-Abbrechen/Zurückstellen,
Erhalt ungespeicherter Eingaben bei nicht erreichbarem Update, Speichern und
Aktualisieren, unklare/erfolgreiche Statusprüfung, weiterhin blockiertes Push und
E-Mail-Aktionsdialog geprüft. Mobile Update-/E-Mail-Ansichten visuell kontrolliert.
Keine reale Geräte-, E-Mail-Client-, Safari- oder Produktionsabnahme.

## Nächster Schritt im Gesamtplan

Die grossen Musterfamilien haben nun Beispiele; die Gesamtvorlage ist trotzdem
noch nicht abgeschlossen. Als Nächstes eine konsolidierte Restabdeckung erstellen:
alle bisherigen offenen Varianten, bestehende Charts mit elf Mitgliedern,
Sonder-/Altseiten und F1/F2/F7/F8 zusammenführen. Je Restpunkt ausdrücklich
festhalten: vorhandenes Muster genügt, gezielte Ergänzung nötig oder Fachentscheid
erforderlich. Kein neuer umfassender Audit und keine weitere lose Entwurfsserie.
Erst danach Gesamtvorlage und Umsetzungspakete abschliessen; App-Umsetzung separat.

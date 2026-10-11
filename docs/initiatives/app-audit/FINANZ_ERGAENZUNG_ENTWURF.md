# Import, private Auslagen und Zahlwegwechsel

Stand: 11. Oktober 2026. Gezielte Ergänzung R07/R08.
**Gestaltung und gezeigte Benutzerführung mit «ok. weiter» am 11. Oktober 2026
bestätigt; keine fachliche Gesamtabnahme und keine Umsetzungsfreigabe.**
F3–F6 bleiben Grundlage. B01 bleibt ausdrücklich offen.

Interaktive Vorschau: `finanz-ergaenzung.html` im bisherigen Visualisierungsordner.
Fünf Einstiege: Importprüfung, private Auslage, Zahlweg vor Abschluss, Zahlweg
nach Abschluss ohne Zahlungen und mit Zahlungen. Ausschliesslich Beispieldaten;
keine Datei wird hochgeladen, kein Eingang gebucht oder Geld überwiesen.

## Importvorstufe R07

Datei → Prüfung → Ergebnis → bestehender Zuordnungsarbeitsplatz. Gültige neue
Zeilen sind auswählbar; bereits importierte und fehlerhafte Zeilen nicht.
Anzahl und Status bleiben explizit. Zurück erhält die Auswahl. Die Übernahme
von Bankbewegungen ist keine automatische Zuordnung zu Forderungen.

Der Beispielimport enthält zwei neue Bewegungen, eine bereits bekannte und
eine Zeile ohne Betrag. Fehler werden in der Quelldatei korrigiert und erneut
geprüft; bekannte Bewegungen dürfen dadurch nicht nochmals entstehen. Eine
echte Doppelzahlung bleibt davon getrennt und folgt F5.

Die Entwurfsoption «Importausgang» zeigt Erfolg, Teilerfolg und unklare
Bestätigung. Bei Teilerfolg nur fehlgeschlagene Bewegungen erneut übernehmen.
Bei unklarer Bestätigung zuerst den bestehenden Importstatus prüfen, kein
blinder Neuimport. Der gezeigte Statusabgleich simuliert einen bereits
erfolgreichen Import. Serverprüfung, Wiederholsicherheit und weitere
Antwortfälle sind technische Abnahmekriterien, hier nicht implementiert.

Der Übergang zeigt die übernommenen, noch unzugeordneten Eingänge und schliesst
inhaltlich an `BUCHHALTUNG_PROZESSE_ENTWURF.md` an. Dessen kompletter
Zuordnungsablauf wird nicht ein zweites Mal nachgebaut. Sammelübernahme ist
keine pauschale Sammelbuchung. Eine Forderungsauswahl ohne Einzelprüfung wird
damit nicht fachlich freigegeben.

Gezielter Bestandsvergleich: `bank_import_upload` in `backend/routes/accounting.py`
importiert aktuell über `BankImportService.import_statement` und leitet dann
zur Prüfung der Zuordnung. Die vorgelagerte Auswahlprüfung ist ein Zielentwurf,
keine Behauptung über bereits bestehende Funktionalität.

## Private Betragserinnerung R08

Aktuelle Ergänzung B02: Persönliches Ausblenden und Wiederanzeigen ist bestätigt
und im Modell `finance-supplement-v3` dargestellt. Eventbetrag bleibt zugänglich;
eine simulierte Betragskorrektur zeigt die Erinnerung erneut. Kein Zahlungsstatus.
Ältere Angaben zum noch unentschiedenen Mechanismus unten sind damit überholt.

Nach B01 ist die Vorschau am 11. Oktober 2026 angepasst: persönlich geschuldeter
Anteil CHF 84.00 und auslegende Person, keine Erfassung oder Bestätigung privater
Ein-/Rückzahlungen. Mitglieder überweisen selbstständig ausserhalb der App;
keine Vereinsbuchung. Der frühere Zahlungsbestätigungsablauf ist ersetzt.
Ein Erledigt-/Ausblenden-Mechanismus ist weiterhin nicht entschieden und wird
nicht als verifizierter Zahlungsstatus eingeführt. Private Vereinsauslagen mit
Erstattung vom Vereinskonto bleiben davon getrennt (siehe B01).

Auch die Texte nach einem Zahlwegwechsel führen jetzt zur privaten
Betragserinnerung. Bereits vorhandene Vereinszahlungen müssen weiterhin durch
den Schatzmeister geklärt werden; sie werden nicht zu privaten Eingängen umgebucht.

## Zahlwegwechsel nach F4

| Zustand | Gezeigte Folge |
|---|---|
| Vor Abschluss | Organisation ändert den Zahlweg im laufenden Entwurf; noch kein Ersatz abgeschlossener Forderungen. |
| Nach Abschluss ohne Zahlung | Person und Grund wählen, Folgen prüfen, nachvollziehbaren Ersatz unbezahlter Forderungen bestätigen. Historie bleibt erhalten. |
| Nach Abschluss mit Zahlung | Bereits bezahlte Beträge separat zeigen; Korrektur dem Schatzmeister vorlegen. Bis zur Freigabe bleibt die bisherige Abrechnung massgeblich. |

Gezeigt wird Vereinskonto → privates Mitglied. Keine automatische Umbuchung
eines Vereinseingangs in einen privaten Zahlungseingang und keine automatische
Überweisung. Der konkrete Ausgleich zwischen Verein und Auslegendem,
Gegenrichtung privat → Verein sowie Wechsel zwischen zwei privaten Auslegenden
werden im Praxisabgleich B01 an tatsächlichen Zahlungswegen festgelegt.
Diese Fälle übernehmen anschliessend das Vorher/Nachher-/Freigabemuster;
R08 ist mit dieser Vorschau nicht fachlich vollständig erledigt.

## Bedienung und responsive Regeln

Mobile: Angaben und Zusammenfassung untereinander, Status pro Zeile lesbar.
Desktop: Importliste und Übernahmehinweis nebeneinander; private Auslage mit
Forderungsübersicht neben der Eingabe. Tablet verwendet bei knapper Inhaltsbreite
dieselbe einspaltige Anordnung. App-Rahmen und Hell/Dunkel bleiben erhalten.

Rückwärts erhält Angaben; Schrittwechsel führt zum Anfang des neuen Abschnitts.
Fehler zeigen eine Meldung ohne Eingaben zu löschen. Wechsel des Beispielablaufs
bei offenen Angaben verlangt Weiterbearbeiten oder Verwerfen. Bestätigungen
privater Zahlungen werden nach Rückkehr zum Eingabeschritt erneut verlangt.
Mobile Klickmarkierung ist transparent; Tastaturfokus bleibt sichtbar.

Prüfung: fünf Einstiege und ihre Folgeschritte bei 320/390/768/820/1024/1440 px
in lokalem Chrome. Auswahl/Rückwege, Teilerfolg/Wiederaufnahme, unklarer
Importstatus, Betragspräzision, Bestätigung privater Eingänge/Rückzahlungen und
Erhalt des Korrekturentwurfs erfolgreich geprüft. Mobile-Import und Desktop-
Zahlwegvorschau zusätzlich visuell geprüft. Keine reale Geräte-, Berechtigungs-,
Bankimport- oder Produktionsabnahme.

Nächster Block: R10 Verwaltungszugänge; R01–R05 danach konkret zuordnen.
F1/F2/F7/F8 und Buchhaltungspraxis B01 bleiben vor Gesamtvorlage separat offen.

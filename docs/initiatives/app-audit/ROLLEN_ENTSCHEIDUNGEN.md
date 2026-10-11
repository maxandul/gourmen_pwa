# Rollen und Berechtigungen – F2

Stand: 11. Oktober 2026. Fachliche Abstimmung, keine App-Änderung.

## Ergänzung R13: drei Regeln bestätigt

Mit «ja» am 11. Oktober bestätigt. Die Regeln konkretisieren
bestehende Bereichsrechte, ohne jetzt Rollen, Drive-Freigaben oder Daten zu ändern.

1. **Sensible Mitgliederdaten:** eigenes Mitglied und Systemadmin erhalten Zugang
   zu den eigenen bzw. allen sensiblen Angaben nach erneuter Identitätsbestätigung.
   Funktionsrollen erhalten nur die für ihren Bereich erforderlichen Felder:
   Schatzmeister Zahlungsangaben, Reisekommissar benötigte Reisedokumentangaben.
   Kein pauschaler Zugriff des Vorstands, der Eventorganisation oder der
   Merch-Verwaltung auf den gesamten sensiblen Datensatz. Zweckbezogene zusätzliche
   Freigaben durch Systemadmin gemäss bestehendem Rollenmodell, nachvollziehbar
   angezeigt. Fehlende Felder nicht allein für die neue Rechteverteilung einführen.
   Gezielte Quelleneinordnung: MemberSensitive ist ein verschlüsselter JSON-Inhalt;
   das bestehende Admin-Template zeigt Passnummer und Ausstellungs-/Ablaufdatum.
   Keine echten Mitgliederdaten gelesen. Der Reisekommissar benötigt daher eine
   begrenzte Ansicht statt automatisch das vollständige Admin-Formular.
2. **Dokumente:** gemeinsame Vereinsdokumente sind für Mitglieder lesbar; Pflege
   durch die jeweils zuständige Bereichsrolle oder gezielte Pflegefreigabe.
   Vorstandsdokumente bleiben vorstandsbezogen, Finanzbelege bei Finanz-/Revisions-
   rollen plus Systemadmin; Einreichende sehen ihren eigenen Vorgang. Bei Dokumenten
   mit Eventbezug zusätzlich Eventberechtigung prüfen. Archivieren und Wiederherstellen
   durch zuständige Pflegeberechtigte; endgültiges Löschen nur Systemadmin nach
   Prüfung von Verknüpfungen und Aufbewahrung. Ein gebuchter Beleg wird nicht über
   eine allgemeine Dokumentaktion unbemerkt entfernt. Archivieren erweitert keine
   Leserechte. App und direkte Drive-Zugriffe müssen dieselben Grenzen wahren;
   UI-Ausblenden allein genügt nicht. Kein Auftrag, bestehende Freigaben zu entziehen.
3. **Laufende Revision:** geprüfter Stand bleibt stabil. Schatzmeister oder
   Systemadmin kann die Prüfung mit Grund zur Bearbeitung zurücknehmen, ohne
   Zustimmung abwarten zu müssen. Danach neue Fassung zur Revision vorlegen;
   vorherige Prüfanmerkungen und Fassungen bleiben erhalten. Bisherige Bestätigung
   gilt nicht automatisch für geänderte Daten. Revisor kann weiterhin beanstanden
   und zurückgeben. Keine stille Änderung des Stands, den der Revisor gerade prüft.
   Keine automatische Benachrichtigung oder E-Mail aus diesem Vorschlag ableiten.

Die endgültige serverseitige Aktions-/Feldmatrix, Freigabeentzüge und technische
Zugangsfristen bleiben Umsetzungsverträge unter U1. R13 entscheidet die fachlichen
Grenzen; es bestätigt weder eine vorhandene Durchsetzung noch eine neue Datenpflicht.

## Bestätigter Grundsatz

Der Nutzer ist der einzige Systemadmin und muss im kleinen, familiären Verein
im Bedarfsfall alle Bereiche bearbeiten können, einschliesslich Buchhaltung.
Die vorherige Empfehlung «Adminrechte allein vergeben keine Finanzrechte» ist
damit verworfen. Der Systemadmin erhält im Zielbild bereichsübergreifende
Bearbeitungsrechte unabhängig von seiner Vereinsfunktion.

Der Nutzer regt zugleich differenzierte Berechtigungen an: Vorstandsmitglieder
sollen nicht allein aufgrund ihres Vorstandsamts Systemadmins sein müssen.
Die anschliessend vorgelegte Bereichsaufteilung und gezielte Zusatzrechte wurden
mit «passt» bestätigt. Keine bestehenden Rollen jetzt entziehen oder umstellen.

## Bestätigtes Zielmodell

| Ebene | Bedeutung |
|---|---|
| Mitglied | Eigene Teilnahme, Bestellungen, Belege, Profil und freigegebene Vereinsinhalte. |
| Vorstand | Zugang zu vorstandsbezogenen Inhalten und Aufgaben; kein automatisches Systemadminrecht. |
| Vereinsfunktion | Bereichsrechte gemäss folgender bestätigter Aufteilung. |
| Eventorganisation | Bearbeitung des zugewiesenen Events und seiner Abläufe, ohne allgemeinen Adminzugang. |
| Systemadmin | Übergreifende Bearbeitung aller Bereiche und Verwaltung der Berechtigungen; bestätigt. |
| Zusätzliche Bereichsfreigabe | Systemadmin kann einzelnen Mitgliedern gezielte Bereichsrechte als Stellvertretung geben, ohne vollständigen Systemadminstatus. |

| Person/Funktion | Bestätigte Bearbeitungsrechte |
|---|---|
| Schatzmeister | Gesamte Buchhaltung einschliesslich Wiedereröffnung. |
| Rechnungsprüfer | Buchhaltung einsehen, prüfen, beanstanden und Revision bestätigen. |
| Marketingchef | Merch und öffentliche Inhalte verwalten. |
| Reisekommissar | Reisen und Ausflüge verwalten. |
| Eventorganisator | Zugewiesenes Event einschliesslich Teilnahme, BillBro und Korrekturen. |
| Übrige Vorstandsmitglieder | Vorstandsinhalte einsehen; zusätzliche Bearbeitungsrechte gezielt vergeben. |

Die Bereichszuweisung hebt bestehende Prozessregeln nicht auf: Beispielsweise
bleibt die Schatzmeisterbestätigung bei Korrekturen betroffener Vereinszahlungen
nach F3/F4 erhalten. «Gesamte Buchhaltung» umfasst für den Schatzmeister nicht
die Bestätigung seiner eigenen Revision; die bestätigte Ausnahme für den
Systemadmin steht unten.

Die Ebenen dürfen sich ergänzen. Ein Vorstandsmitglied kann zugleich
Schatzmeister und Organisator sein. Für elf Mitglieder genügt eine verständliche
Anzeige «Vorstand», «Vereinsfunktion» und «Zusätzliche Zugriffe»; kein frei
konfigurierbarer Berechtigungsbaukasten nötig. Diese Einfachheit ist eine
Darstellungsempfehlung. Die Bereichszuweisung ist beschlossen; die genaue
Abbildung auf einzelne Aktionen und Sichtbarkeiten wird noch konkretisiert.

Das bestehende Datenmodell trennt `Role`, `Funktion` und `vorstandsmitglied`
bereits begrifflich (`docs/DOMAIN.md`). Daraus folgt keine Behauptung, dass die
gewünschte differenzierte Durchsetzung heute vollständig vorhanden ist.
Neue Tabellen oder Migrationen werden hier nicht vorgeschlagen oder umgesetzt.

## Bearbeitungsrecht und verbindlicher Abschluss

**F6 ausdrücklich geändert:** Systemadmin und Schatzmeister dürfen jeweils
allein ein abgeschlossenes Buchhaltungsjahr wiederöffnen. Die zuvor verlangte
Zustimmung des Revisors entfällt für beide Rollen. Nutzer hat die frühere
Angabe ausdrücklich zurückgenommen.

Dokumentierter Grund, handelnde Person und Zeitpunkt bleiben im Verlauf;
bisherige Berichtsversionen bleiben erhalten. Nach Änderungen erfolgt die
erneute Revision mit neuer Berichtsversion wie bisher vereinbart.
Die Zustimmung zur Wiederöffnung ist von der späteren Revisionsbestätigung
getrennt.

**Revisionsbestätigung anschliessend mit «passt, weiter» beschlossen:**
Regulär bestätigt der Rechnungsprüfer. Der Systemadmin darf bei Bedarf
stellvertretend bestätigen; der Verlauf kennzeichnet ausdrücklich die
handelnde Person und die stellvertretende Bestätigung als Systemadmin.
Der Schatzmeister darf seine eigene Buchhaltung nicht als geprüft bestätigen.
Diese Ausnahme betrifft die Rolle Systemadmin, nicht sämtliche Personen mit
zusätzlichen Buchhaltungsrechten. Sie ersetzt keinen offenen Prüfpunkt:
Blockierende Beanstandungen und die übrigen F6-Prozessregeln bleiben bestehen.
Änderungen während einer laufenden Revision folgen der bestätigten R13-Regel:
mit Grund zur Bearbeitung zurücknehmen, danach neue Fassung zur Prüfung vorlegen.

F1 zu Zugangswiderruf/Wiederherstellung, die exakte Rollen-/Sichtbarkeitsmatrix
und der Buchhaltungs-Praxisabgleich B01 bleiben offen.

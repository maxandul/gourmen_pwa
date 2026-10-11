# Verwaltungszugänge – Ergänzung R10

Stand: 11. Oktober 2026. **Darstellung und gezeigte Benutzerführung mit
«ok. weiter» bestätigt. F1/F2 bleiben davon getrennt offen.**
Keine Änderung von Konten, Rollen, Links, externen Freigaben oder App-Code.
Keine echte Nachricht und kein Zugriff auf Google. F1/F2 bleiben offen.

Interaktive Vorschau `verwaltungszugaenge-entwurf.html` im bisherigen
Visualisierungsordner. Vier Einstiege: Google-Zugang, Kalender, Mitglied einladen
und Berechtigungen. Über Entwurfsoptionen lassen sich Versand-/Einladungsfehler
und die Situation «einziger aktiver Admin» zeigen.

Grundlage: `KONTO_ZUGANG_ENTWURF.md`, `AUTH_REVIEW.md` (vierter Durchlauf),
`UI_REGISTRY_REVIEW.md` (UIR-129–136) sowie `docs/STRATEGY_2026.md`.
Keine neue Befundsuche. Bestehende Auditbefunde A-088/A-089/A-090 werden durch
die Oberfläche nicht behoben; sie behalten ihre technische Priorität.

## Vier Zuordnungen

| Bereich | Darstellung / Benutzerführung | Noch ausdrücklich offen |
|---|---|---|
| Google-Adresse | Adresse erfassen → Bestätigung ausstehend → Adresse bestätigt → Drive-Einladung ausstehend → Zugriff bestätigt. Versand-/Einladungsfehler getrennt wiederholen. Adresswechsel zeigt erneute Verifikation und separat zu prüfenden alten Zugriff. | F1: Zeitpunkt und verantwortlicher Ablauf des Widerrufs alter Freigaben. Technisch: Links an die konkrete Adresse binden, externe Zustände verlässlich ermitteln. |
| Kalender | Aktiv/inaktiv; persönlicher Link mit Kopieren, Erneuern, Deaktivieren. Bestätigungsdialog nennt ungültigen alten Link und nötige Neueinrichtung des Abonnements. Heruntergeladene Termine können verbleiben. | F2: genaue Ereignis-/Rollensichtbarkeit; reale Kalenderclients, Aktualisierungsintervalle und Endgerättexte prüfen. Keine neue Frist erfunden. |
| Mitgliederanlage | Name und E-Mail als exemplarischer Ausschnitt, danach «Mitglied angelegt» getrennt von Einladungs-/Aktivierungsstatus. Bei Versandfehler nur Einladung wiederholen, keine zweite Anlage. Aktivierung schliesst an bestehendes Zugangsmuster an. | Vollständige Profilfelder und Pflichtfelder zuordnen; doppelte Adressen, unklarer Versandstatus, tatsächliche Linkfristen und erneute Versandberechtigung festlegen. |
| Rollen / Deaktivierung | Rolle und Vereinsfunktion unterscheiden. Letzter aktiver Admin kann im vorgeschlagenen Muster weder herabgestuft noch deaktiviert werden; erst Nachfolge bestimmen. Bei weiterem Admin zeigt der Dialog vorbereitete Folgenprüfung. | F1/F2: wer darf ändern, erneute Identitätsbestätigung, Sitzungswiderruf, externe Freigaben, Finanz-/Revisionsrechte und Selbstprüfung. Keine simulierte Rollenänderung als beschlossene Fachregel. |

Die Google-Schritte zeigen unterschiedliche Zustände, nicht zwingend zusätzliche
manuelle Arbeit: ob nach Verifikation automatisch eingeladen wird oder wer die
Einladung anstösst, bleibt im Rollenabgleich zu bestimmen. «Beispiellink öffnen»,
«Beispielstatus prüfen» und «Beispielaktivierung zeigen» sind Vorführhilfen;
die echte App benötigt das tatsächliche Ereignis bzw. einen verlässlichen Status.
Kein manueller Klick darf dort Besitz oder Berechtigung als erwiesen setzen.

Kalenderlink ist ein ungültiger Platzhalter. Der Kopierknopf erklärt dies und
schreibt nichts in die Zwischenablage. Keine echten Token, Adressen oder
personenbezogenen Eingaben werden im gespeicherten Vorschauzustand abgelegt;
nur Beispielwahl, Darstellung und Entwurfsoptionen.

## Responsive und gemeinsame Bedienung

Mobile: Aufgabenfläche vor Folgen-/Statushinweisen, eine Spalte. Desktop:
Arbeitsfläche und ergänzende Statusbeschreibung nebeneinander. Tablet bei
wenig Inhaltsbreite einspaltig (Entwurfsschwelle 760 px). Theme-Schalter,
Lucide-Navigation und Kontomenü bleiben im bestätigten Rahmen.

Adressänderung lässt sich abbrechen und stellt vorherige Adresse samt Status
wieder her. Wechsel des Beispiels bei ungespeicherten Angaben fragt nach
Weiterbearbeiten/Verwerfen. Dialoge verwenden native Fokusführung und Escape;
Abbrechen ändert den Status nicht. Fehler erhalten Eingaben und fokussieren
das relevante Feld. Aktionen haben verständliche Statusrückmeldungen.

## Entscheidungsvorbereitung F1/F2

Für die spätere gemeinsame Fachrunde sind jetzt sichtbar vorbereitet:

1. **Adresswechsel/Deaktivierung:** Wann alte Drive-Freigaben, Kalenderlinks und
   App-Sitzungen entziehen? Empfehlung: Folgen explizit auflisten, bestätigten
   Erfolg je System unterscheiden und Fehler mit zuständiger Person offen halten.
2. **Admin-Nachfolge:** Letzten aktiven Admin schützen; zulässige Nachfolge und
   Schutz vor gleichzeitigen Änderungen serverseitig festlegen. Der Entwurf
   zeigt die Empfehlung, keine schon bestehende Absicherung.
3. **Einladungen:** Wer darf erneut senden, welche bisherigen Links werden ungültig,
   und wie wird ein Versand mit unklarem Ergebnis geprüft? Mitglied und
   Versandvorgang bleiben getrennt, erneute Anlage ist keine Fehlerbehebung.
4. **Rollen:** Administration ist nicht automatisch Schatzmeister/Revisor.
   Finanzrechte und Selbstprüfung ausdrücklich in einer Rollenmatrix entscheiden.

Weitere F1-Fragen zu Faktorverlust und erneuter Identitätsbestätigung bleiben
in `KONTO_ZUGANG_ENTWURF.md` erhalten. Keine neue Fachfreigabe durch R10.

## Prüfung und Weiterarbeit

Vier Einstiege bei 320/390/768/820/1024/1440 px in lokalem Chrome geprüft:
kein äusserer Überlauf oder JavaScript-Fehler. Verifikation/Einladungsfehler/
Wiederholung, Abbruch des Adresswechsels, Kalenderdialoge und Linkwechsel,
Mitgliederanlage trotz Versandfehler, letzter Admin und Entwurfserhalt geprüft.
Google-Mobile und Rollen-Desktop zusätzlich visuell kontrolliert.
Keine Authentifizierungs-, Berechtigungs-, Zustellungs-, Produktions- oder
echte Geräteabnahme. Entwurfsoptionen sind keine App-Berechtigungsschalter.

Als Nächstes R01–R05 konkret auf bestehende Seiten und Abnahmekriterien abbilden;
dafür vorhandene Zuordnung und Muster verwenden, keine weitere lose Mockupserie.
Danach Fachentscheidungen bündeln und Gesamtvorlage/Umsetzungspakete abschliessen.

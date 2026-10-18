# U2-17c: Zahlungsstand erhalten und korrekt einordnen

## Quellen und Abgrenzung vor Code

BILLBRO_INTERAKTION.md F3/F4, BUCHHALTUNG_PRAXISABGLEICH.md B01/B02/G1-G3/K1
und FINANZ_ERGAENZUNG_ENTWURF.md. Spaetere bestaetigte B01-Regel hat Vorrang:
Private Essen erhalten eine Betragserinnerung, keine allgemeine App-Erfassung
privater Ein-/Rueckzahlungen. Zahlungsstand privat unbekannt; paid=0 allein
ist kein Beweis fuer Unbezahlt. Der bisherige b1-Weg hat an dieser Stelle eine
Luecke trotz gruener Tests. Keine erneute Abstimmung bestaetigter Regeln.

## c0: Explizite Klaerung vor unbezahlter privater Korrektur

Begrenzte Ergaenzung des vorhandenen unbezahlten Korrekturwegs. Ist der
Ausgangszahlweg privat, muss die Organisation ausdruecklich angeben, dass sie
geklaert hat, dass noch keine privaten Zahlungen erfolgt sind, und einen
Klaerungsvermerk hinterlegen. Ohne diese Aussage keine Vorschau/Bestaetigung.
Bekannte Zahlungen/Alteingaenge bleiben auch mit Aussage gesperrt. Sobald
Zahlungen stattgefunden haben oder dies unklar ist, ist der spaetere Finanz-
klaerungsweg erforderlich; eine Checkbox darf keine Zahlung zuruecknehmen.

Aussage und Vermerk an signierte Vorschau v5 binden, in Korrekturhistorie
speichern und dort lesbar halten. Vermerk ist eine dokumentierte Erklaerung,
kein Banknachweis und kein laufender privater Zahlungsstatus. Keine neue
Migration: vorhandene JSON-Historie verwenden. Alte Vorschautokens ablehnen.
Vereinsausgang ohne Zahlungen behält den vorhandenen Ablauf. In der Vorschau
private Aussage zutreffend benennen, nicht als technisch verifiziert ausgeben.

Regression: privater Ausgang mit paid=0 ohne Aussage/ohne Vermerk abgewiesen;
geklaerter unbezahlter Fall mit signiertem Vermerk und Historie; bekannte
Zahlung weiterhin gesperrt, manipulierte oder alte Vorschau abgewiesen,
unsigned Formularwert ersetzt keine bestaetigte Aussage. Fehler/Retry und
bestehende Vereinskorrekturen erhalten. Kein Versand oder echter Geldfluss.

## c1 danach: Bezahlte Vereinskorrektur

Auf unveraenderten Vereinsglaeubiger begrenzen. Vor Code die Verbindung von
bestehenden Zahlungszuordnungen, offenem Mehrbetrag und Rueckzahlungsbedarf
konkretisieren. Alte Bankbewegungen unveraendert; tatsaechlicher Ausgang
separat auf 6710. Keine negative Ersatzbuchung und keine automatische Auszahlung.
Private Ausnahmefaelle und bezahlter Glaeubigerwechsel bleiben getrennte Pakete.


## c0 lokal umgesetzt und geprueft

Vorschauvertrag v5, ausdrueckliche private_unpaid_confirmed=yes und getrimmter
Vermerk mit 1..1000 Zeichen. Erklaerung in after_json.private_unpaid_clarification
mit bestehendem Akteur/Zeitpunkt der Korrektur erhalten; keine Migration.
Template zeigt Ausgangslage, Aussage und Vermerk in Vorschau/Verlauf; bestehende
unbezahlte Vereinskorrektur bleibt unveraendert. Zwei vorhandene Privatfalltests
liefern nun ihre erforderliche Erklaerung explizit; kein genereller Test-Bypass.

Isolierter Lauf private_clarification, correction, attendance, invoice_correction,
type_correction: **79 bestanden, 2840 Warnungen, 38.52 s**. Neue Faelle: fehlende/
ungueltige Aussage, leerer/zu langer Vermerk, signierter Vermerk statt ersetzter
unsignierter Felder, HTML-Escaping, Retry, Zahlung vor bzw. nach Vorschau und
alter v4-Nachweis. Node Worker **19 bestanden**; git diff --check ohne Fehler.
PWA 3.16.41 / pwa.a93228ba.js. Keine neue Gesamtregression nach dem kleinen
Folgeschritt; Gesamtbasis ae43000 zuvor 1467 bestanden. Kein echter Zahlungs-,
Browser- oder PostgreSQL-Nachweis.

B02-Erinnerungsoberflaeche und Ersatz des noch vorhandenen Legacy-Privat-
Eingangsbestaetigungswegs bleiben beauftragte Folgearbeit, keine neue
Zahlungskontrolle durch c0. Bezahlte Vereinskorrektur und privater Ausgleich
bleiben offen.


## Vertrag vor Code: c1a bezahlten Vereinsentwurf vorbereiten

C1 wird in Vorbereitung (c1a) und finanzielle Bestaetigung mit Rueckzahlungs-
modell (c1b) getrennt. C1a speichert einen unveraenderlichen Entwurf; Event,
Anteile, Forderungen, Zahlungen und Buchungen bleiben bis c1b unveraendert.
Expliziter Hinweis in der UI: Entwurf ist keine Freigabe und noch nicht wirksam.

Nur bestehender Vereinsglaeubiger bleibt Vereinsglaeubiger. Organisation darf
vorbereiten, Grund/Vorher/Nachher einschliesslich gespeicherter Zahlung und
abgeleitetem Mehrbetrag/Rueckzahlungsbedarf pruefen und Entwurf speichern.
Bei Revision/geschlossenem Jahr Vorbereitung mit sichtbarer Sperrgrenze erlauben;
keine Jahresoeffnung. Private Ausgangs-/Zielwege, Erlasse und inkonsistente
Forderungen bleiben gesperrt. Kein Zahlungsstand aus externen Quellen erfinden.

Signierte Vorschau bindet Akteur/Zugang, Vorschlag und Ausgangszustand samt
Zahlungszuordnungen/Buchungen. Speichern unter Event-Sperre prueft diesen Stand
neu; Tokenwiederholung erzeugt keinen zweiten Entwurf. Neuer Entwurf ersetzt
keine Zahlung, sondern markiert einen aelteren offenen Entwurf als ueberholt.
Zurueckziehen mit Grund erhaelt Entwurf/Autor/Zeit und veraendert keine Finanzen.
Finanz-Leserecht plus Eventzugriff erlaubt lesende Einsicht; Organisation darf
nur eigene verwaltbare Events vorbereiten. Noch keine Freigabeaktion in c1a.
Eventloeschung muss Entwuerfe und explizite Anwesenheitsdaten bewahren.

Separate additive Migration fuer BillBroCorrectionDraft. Kein historischer
Backfill, Downgrade mit Entwurfshistorie verweigern. Tests fuer Vorschau ohne DML,
bezahlte Beispiele (84->90 ergibt 6 offen; 84->78 ergibt 6 Rueckzahlungsbedarf),
Erhalt aller Fachwerte/Bankzeilen, Rollback/Retry, alte Vorschau, nachtraegliche
Zahlung/Zuordnungsruecknahme, Rollen/Sichtbarkeit, Zurueckziehen und Migrationszyklus.
C1b danach fuer echte Finanzbestaetigung und abgleichbare Rueckzahlungen.


C1a-Migration u217c1a20261018 nach u217b3b20261018: synthetischer SQLite-
Upgrade/Downgrade/Upgrade und Historien-Downgrade-Sperre **1 bestanden,
0.18 s**. Ignorierter pyreadline3-Handlefehler nach Testende, Prozessstatus 0.
Anwendungsintegration noch in Arbeit; keine Live-Migration.

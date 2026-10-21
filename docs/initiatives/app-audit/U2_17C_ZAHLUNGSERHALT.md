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


## c1a lokal umgesetzt und geprueft

Migration separat in 0856609. BillBroDraftService, persistente Entwuerfe,
gebundene Vorschau, Ersetzen/Rueckzug und Finanz-Leseweg umgesetzt. Aktuelle
Abrechnung und Banknachweise unveraendert, keine Freigabeaktion. Gemeinsames
Formular mit unbezahltem Weg; Anzeige einschliesslich Ess-Typ/Anwesenheit/GGL.
Eventloeschung schuetzt Entwuerfe und explizite Anwesenheitswerte.

Isolierte Regression: draft, draft_migration, private_clarification, correction,
attendance, invoice_correction, type_correction, event_deletion_atomicity,
payment_allocations: **138 bestanden, 4431 Warnungen, 65.61 s**.
Anschliessend reine Vorschauerzeugung aus demselben gesperrten Zustand statt
zweiter Abfrage; erweiterte Draft-Suite: **22 bestanden, 1260 Warnungen,
14.93 s**. Ignorierter pyreadline3-Handlefehler nach Testende, Prozessstatus 0.
24 JavaScript-Tests bestanden; git diff --check ohne Fehler.

Geprueft: 84->90/78, echte synthetische Zuordnung und Ruecknahme, keine Vorschau-
DML, unveraenderte Fach-/Bankwerte beim Speichern/Rueckzug, Rollback bei Insert/
Commit/Statusfehlern, Retry, zwei Vorschauen, veraltete Zahlungsstaende,
CSRF, Rechte/Eventzugriff, Tokenzeit/-manipulation/-Zugang/-Akteur, geschlossenes
Jahr, ungueltige Forderungsstaende, Anwesenheit/Ess-Typ/GGL ohne Anwendung und
abgewiesene Freigabeaktion. Kein dotenv oder ausgehendes Netz.
PWA 3.16.42 / pwa.96f8a9f1.js. Reale PostgreSQL-Sperren und Migrationen sowie
Browser/Geraete bleiben offen. C1b Finanzbestaetigung/Rueckzahlungsmodell ist
naechster Auftrag; C1/F3/F4 und U1 insgesamt bleiben offen.


## Vertrag vor Code: c1b Finanzbestaetigung und Rueckzahlung

C1b wird fuer pruefbare lokale Abschluesse in zwei Teile geschnitten:
c1b1 liefert die Zahlungsbilanz/Journalgrundlage, c1b2 verbindet Freigabe und
Bankarbeitsplatz. C1b1 allein aktiviert keinen bezahlten Korrekturabschluss.

Die bisherige Forderungs-ID und paid_rappen (Bruttoeingang) bleiben erhalten.
Nach Finanzfreigabe wird nur expected_rappen an den korrigierten Anteil
angepasst; abwesende bisherige Schuldner behalten ihren Posten mit Soll 0.
Neue Anwesende bekommen neue Forderungen. Historie haelt Vorher/Nachher fest.
Schatzmeister/Systemadmin bzw. bestehendes accounting_write mit Eventzugriff
bestätigt einen aktuellen Entwurf; Organisation allein reicht nicht. Keine
Selbsttestat-Regel aus Revision auf die normale Finanzbearbeitung uebertragen.
Betroffene Jahre muessen fuer echte Korrektur offen sein; Vorbereitung allein
bleibt erlaubt. Fehlende Zahlungsnachweise/inkonsistenter Altbestand sperren
Freigabe gezielt statt neue Bankbewegungen zu erfinden.

Separate additive Tabelle ClaimRefundPayment verbindet tatsaechliche
Ausgangszuordnung, erhaltene Forderung und wirksame BillBroCorrection.
Kein Backfill. Ein Ausgang kann nur einmal verknuepft werden; alte Links bleiben
bei Zuordnungsruecknahme erhalten. Downgrade mit Historie verweigern.
Rueckzahlungsbedarf ist eigenstaendig in der Anzeige, berechnet am stabilen
Forderungsposten: Bruttoeingang minus aktive tatsaechliche Rueckzahlungen minus
korrigierter Sollbetrag, mindestens 0. Offene Forderung umgekehrt Soll minus
Nettoeingang, mindestens 0. Niemals beides gleichzeitig positiv.

Beispiel 84 bezahlt, Soll 78: 6 Rueckzahlung offen. Nach Ausgang 6 bleiben
84 Brutto und 6 Rueckfluss, netto 78. Spaeter Soll 90 ergibt 12 offen. Ein
weiterer Eingang 12 ergibt Brutto 96, Rueckfluss 6, netto 90. Kein erneutes
Fordern bereits verbleibender Zahlung und kein doppelter Rueckzahlungsbedarf.
Vorhandene Status-/Offen-/Mitgliederuebersicht nutzt dieselbe Nettobilanz;
paid_rappen/paid_chf bleibt ausdruecklich Bruttohistorie.

C1b1: Modell und Bilanz, Statusfortschreibung beim Eingang, Ruecknahme von
verknuepften Ausgaengen und Schutz der Eingangsruecknahme bei aktiven
Rueckzahlungen. Bestehende Ueberschuss-Rueckzahlung bleibt separat unveraendert.
C1b2: signierte Finanzbestaetigung mit unveraendertem Entwurfs-/Zahlungsstand,
atomarer Forderungs-/Anteils-/GGL-Historie und danach getrennter Bankabgleich
auf 6710. Keine neue 3620-Einnahme bei Senkung eines schon verbuchten Anteils.
Ausgang darf im Folgejahr liegen; nur sein Zahlungsjahr muss offen sein.
Keine automatische Ueberweisung, Benachrichtigung oder externe Abfrage.

Pruefung c1b1: Migrationszyklus/Historienerhalt; Betragsszenarien mit Teil-/Voll-
rueckzahlung, erneuter Sollerhoehung/Zahlung, Status/Offen/Netto, Nullbedarf,
aktiven und zurueckgenommenen Ausgaengen; Eingangsruecknahme erst nach
Ruecknahme zugehoeriger Ausgaenge; Fehler atomar. C1b2 prueft zusaetzlich
Freigabe-/Abgleichrollen, Ausgangsstand, Entwurfsstatus, Wiederholung, Fehler,
Jahressperre, Ausgangsrichtung/Datum/Konto/Betrag und komplette Zuordnungskette.
PostgreSQL-Parallelitaet bleibt separate Abnahme, keine Behauptung aus SQLite.

C1b1-Migration u217c1b120261018: Upgrade/Downgrade/Upgrade, FK- und
Eindeutigkeitspruefung sowie Downgrade-Historiensperre: **1 bestanden, 0.13 s**.
pyreadline3-Handlefehler erst nach Testende, Exit 0. Keine Live-Migration.


### C1b2: konkrete Freigabe- und Abgleichgrenzen vor Implementierung

- Finanzfreigabe hat eine eigene signierte Pruefansicht, gebunden an Akteur/
  Zugang, Event, Entwurfs-ID/-inhalt/-status und aktuellen Zahlungsstand.
  GET schreibt nichts; POST wiederholt erfolgreiche Bestaetigung ohne zweite
  Historie. Neuer/entzogener/ersetzter Entwurf oder neue Zahlung erfordert
  erneute Vorlage. Finanzrolle kann mit Grund zur Bearbeitung zurueckgeben;
  vorhandener Status withdrawn mit ausdruecklichem Rueckgabevermerk genuegt.
- Bestehende Forderungen niemals ersetzen/loeschen; bei Abwesenheit Soll 0.
  Brutto und aktive Rueckfluesse bleiben unangetastet. Neue Anwesende erhalten
  neue Posten. Anteil, Anwesenheit, Ess-Typ, GGL, Soll/Status, Entwurfsstatus und
  Korrekturhistorie werden gemeinsam gespeichert oder vollstaendig verworfen.
- Vor Freigabe muessen aktive Claim-Eingangszuordnungen den Bruttoeingang
  belegen und zu Mitglied/Event/Buchung/Richtung/Betrag passen. Ungeklaerte
  Legacy-Summen werden nicht als neuer Bankbeweis ausgegeben. Jahresgrenze
  fuer Korrektur ist das Event-/Forderungsjahr; fehlendes Jahr gezielt klaeren.
- Auszahlung ist ein neuer getrennter Bankabgleich. Nur offene Ausgangsbewegung,
  aktuelle Bankversion, positive Rappen bis Bankrest und Rueckzahlungsbedarf,
  aktives 6710 und berechtigte Finanzperson mit Eventzugriff. Auswahl bindet
  aktuelle wirksame Korrektur und erhaltene Forderung. Bereits anderweitig
  zurueckgezahlte Betraege stehen nicht erneut zur Verfuegung.
- Ausgang wird mit dem Claim und seiner aktuellen Finanzkorrektur verknuepft;
  die erhaltenen Claim-Eingangszuordnungen liefern die Originaleingangskette.
  Kein Ausgang vor den zugehoerigen aktiven Eingaengen. Folgejahr erlaubt,
  Ausgangsjahr muss offen sein; Originaljahr nicht allein wegen Ausgang oeffnen.
- Rueckzahlungsbedarf auf eigener Finanzuebersicht und im Korrekturkontext
  zeigen. Bankzeile/Verlauf verlinkt den Ursprungsfall. Private Faelle und
  Zahlwegwechsel bleiben im G1-Folgepaket. Keine Versand- oder Transferaktion.


## c1b1 lokal umgesetzt und geprueft (21.10.2026)

Migration separat **16d8f3d** (u217c1b120261018). ClaimRefundPayment erhaelt
Ausgang/Forderung/Korrektur. Bruttoeingang bleibt erhalten; aktive Rueckfluesse
liefern die Nettobilanz fuer Offen/Status/Mitgliederuebersicht. Die Ruecknahme
passt diese Bilanz atomar an und sperrt Eingaenge mit aktiven Rueckzahlungen.
Entwurf v2 bindet Rueckflussnachweise und zeigt Brutto/Rueckfluss/Netto.
Keine Finanzfreigabe oder neue Ausgangsaktion in diesem Grundlagenpaket.

Isolierter Lauf claim_refund_balance, claim_refund_migration, billbro_drafts,
payment_allocations, refund_payment: **64 bestanden, 2119 Warnungen, 31.83 s**.
Erweiterte Bilanztests anschliessend: **9 bestanden, 495 Warnungen, 7.82 s**;
Null-Soll bei Abwesenheit mit erhaltener ID und fehlerhafte Mitgliedsverknuepfung
zusaetzlich geprueft. 24 JavaScript-Tests bestanden.

Gesamte Python-Regression auf unveraendertem Anwendungscode abgeschlossen:
**1510 bestanden, 24300 Warnungen, Prozessstatus 0**. Gemeldete Laufzeit
**261968.09 s (3 Tage, 0:46:08)** enthaelt die mehrtaegige Unterbrechung vom
18. bis 21.10.; ausdruecklich kein Performance-Nachweis. Die beiden zuletzt
ergaenzten Bilanzfaelle waren nicht in dieser bereits gestarteten Sammlung,
sondern im separaten erfolgreichen Neuner-Lauf enthalten. Kein dotenv/Netz.

PWA 3.16.43 / pwa.1286f295.js; git diff --check ohne Fehler. PostgreSQL-
Migration/Sperren, Browser/Geraete bleiben offen. C1b2 ist nun bereit:
Finanzfreigabe des Entwurfs und echter 6710-Ausgangsabgleich gemaess Vertrag
oben. C1/F3/F4 und U1 bleiben insgesamt offen.


## c1b2 lokal umgesetzt und geprueft (21.10.2026)

BillBroFinanceService liefert signierte Pruefansicht, ausdrueckliche Freigabe
und begruendete Rueckgabe. Bestehende Claim-IDs/Bruttoeingaenge bleiben erhalten;
Soll 0 bei Abwesenheit loescht nichts. Anteil/Teilnahme/GGL, Soll/Status,
Entwurfsstatus und Historie atomar. ClaimPaymentEvidence sperrt ungeklaerte
Legacy-Summen. Aktuelle Vereinskorrektur bei gleichem Glaeubiger umgesetzt;
private Klaerung und bezahlter Glaeubigerwechsel bleiben getrennte Folgearbeit.

ClaimRefundService gleicht reale Ausgaenge auf 6710 ab, mit Bankversion,
aktuellem Finanzkorrekturbezug, positivem Betrag bis Rest/Bedarf, Datum und
Jahressperre. Teilbetraege/Folgejahr und Ruecknahme erhalten die Nachweiskette.
Keine automatische Ueberweisung, keine neue 3620-Einnahme aus Betragssenkung,
kein Versand. Eigene Zahlungsansicht serverseitig auf Mitglied begrenzt;
Organisation/Finanz sieht Eventposten, Banklinks nur mit Finanz-Leserecht.
Kein neues Schema in c1b2; Migration 16d8f3d aus c1b1 bleibt separat.

Erster isolierter Lauf finance/correction: **45 bestanden, 2219 Warnungen,
48.85 s**. Erweiterter Lauf zunaechst **194 bestanden, 1 fehlgeschlagen**:
Der Hidden-Event-Negativtest verwendete den weiterhin berechtigten Organisator.
Test auf Finanzperson ohne Organisations-/Vorstandszugriff korrigiert; keine
Aufweichung der bestehenden Sichtbarkeitsregel. Danach Finanzsuite **33 bestanden,
2224 Warnungen, 38.56 s**.

Abschliessender Lauf finance, drafts, correction, attendance, invoice_correction,
type_correction, claim_refund_balance, payment_allocations, allocation_reversal,
refund_payment, accounting_year_guards: **196 bestanden, 7160 Warnungen,
136.70 s**. Danach zwei erweiterte Faelle (zweite Bankbewegung nach voller
Erstattung und Tokenwechsel auf anderen Finanzakteur): **2 bestanden,
155 Warnungen, 7.07 s**. 24 JavaScript-Tests bestanden; git diff --check sauber.
Bei einzelnen gezielten Laeufen pyreadline3-Handlefehler nach Testende,
Erfolgsläufe trotzdem Exit 0. Kein dotenv oder ausgehendes Netz.

Geprueft: Freigabe/Retry ohne neue Claim-ID oder Bankmutation, Rollback bei
Historien-/Commitfehler, Rollen/CSRF/Eventzugriff, veralteter/ersetzter Entwurf,
Zeit/Signatur/Zugang/Akteur, neue Anwesende ohne erfundenes RSVP, GGL/Null-Soll,
Teil-/Vollrueckzahlung, Jahreswechsel, erneute Sollerhoehung, Ruecknahme,
Ueberbetrag/Bankrest/Datum/Richtung/Konto/Bankversion/Korrekturbezug sowie
Insert-/Commitfehler beim Ausgang. Persoenliche Ansicht ohne fremde Posten
oder Bankarbeitsplatzlinks geprueft.

PWA 3.16.44 / pwa.e8bff355.js. Letzte Gesamtregression war c1b1 (1510 Tests),
nicht als neuer Gesamtlauf fuer c1b2 ausgeben. Echte PostgreSQL-Sperren/FK-
Konkurrenz und Migrationen, Browser/Geraete bleiben offen. U1 bleibt offen.
Naechstes unabhaengiges Paket: U3-01/B02 private Betragserinnerung mit eigenem
Ausblenden/Wiederanzeigen; Legacy-Privatbestaetigung ersetzen. U2-17c2/G1
bezahlter Glaeubigerwechsel und Merch-Folgepakete bleiben geplant.

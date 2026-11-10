# U3-01 / B02: persoenliche private Betragserinnerung

## Vertrag vor Code (21.10.2026)

Quellen: BUCHHALTUNG_PRAXISABGLEICH.md B01/B02/G1 und
FINANZ_ERGAENZUNG_ENTWURF.md. Bestaetigt: private Zahlung ist unbekannt,
keine private Eingangs-/Rueckzahlungsbestaetigung. Persoenliches Ausblenden
ist keine Zahlung, wirkt nur fuer das Mitglied und kann rueckgaengig gemacht
werden. Betrag/Empfaenger bleiben im zugreifbaren Event sichtbar. Aenderung
von Betrag/Empfaenger zeigt die Erinnerung erneut; Textaenderung nicht.

## Begrenzte Umsetzung

Drei additive Felder auf MemberClaim: private_reminder_hidden (False),
private_reminder_changed (False), private_reminder_version (0). Kein Backfill
privater Zahlungswahrheit: bestehende paid/status/settled-Werte unveraendert
bewahren. Bereits als bezahlt gefuehrte Altposten werden nicht automatisch
als ausgeblendet uebernommen. Positive private Essensanteile erscheinen als
Betragserinnerung ohne laufenden Zahlungsstatus; historisch erlassene Posten
bleiben ausgenommen (keine neue Forderung aus altem Erlass erzeugen).
Migration separat; Downgrade bei verwendeten Praeferenzfeldern verweigern.

Ausblenden/Wiederanzeigen: eigene aktive Mitgliedsidentitaet, CSRF, signierter
aktueller Betrag/Empfaenger/Claim/Zugang/Versionsstand und ausdrueckliche
Zielaktion. Versionspruefung verhindert veraltete/ABA-Toggles, unmittelbare
Wiederholung derselben Aktion ist wirkungslos. Nur Praeferenzfelder schreiben,
keine Vereinsbuchung, kein paid/status, keine Benachrichtigung.

Dashboard trennt Vereinsforderungen von privaten Erinnerungen. Hide entfernt
die Erinnerung und bietet direkt Wiederanzeigen; eigene Liste bietet spaetere
Wiederaufnahme. Eventdetail zeigt eigene private Erinnerung mit Empfaenger und
Toggle. Nicht sichtbare Events bleiben im eigenen Finanzhinweis generisch;
keine versteckten Titel oder Eventlinks. Eigene Anzeige-Praeferenz darf auch
fuer den erhaltenen eigenen Posten ohne Eventzugriff geaendert werden.

Unbezahlte Korrektur kopiert persoenliches Ausblenden nur bei identischem
Betrag/Empfaenger. Geaenderter Betrag/Empfaenger setzt es zurueck und zeigt
Aenderungshinweis. Auch bestehende interne BillBro-Claim-Synchronisierung
respektiert diese Regel. Neues Claim-ID verhindert alte Formularwiederholung;
Korrekturhistorie bewahrt alte Praeferenzwerte. Keine private Zahlung behaupten.

Legacy-Privatbestaetigung wird an Route und Service ohne Mutation stillgelegt.
Auch generelles manuelles Begleichen darf private Posten nicht weiter als
bezahlt markieren. Vereins-Postenuebersicht summiert nur Vereinsforderungen.
Historische private Daten bleiben gespeichert und in Korrekturbelegen erhalten.
Bezahlter Glaeubigerwechsel bleibt G1; dieses Paket nimmt keinen Ausgleich vor.

## Regression

Migrationszyklus und Verwendungssperre; Eigentum/Rollen/CSRF, Tokenzeit/
Zugang/Ziel/Versionsstand, Wiederholung/ABA, echter Rollback, kein Finanz-DML;
Dashboard/Event/Liste, kein fremder Zahlungsstatus, versteckte Eventdaten,
Legacy-Bestaetigung ohne Wirkung; Betrag/Empfaenger-Korrektur setzt Anzeige
zurueck, Titel-/Textaenderung und unveraenderte Betraege erhalten sie. Wechsel
zum Verein erzeugt keine private Zahlungsbestaetigung. Bestehende Finanz-/
BillBro-/Sichtbarkeitsregressionen mit synthetischen Daten ohne dotenv/Netz.
Browser/Geraete und PostgreSQL-Parallelitaet bleiben separate Abnahmen.

Migration u30120261021 nach u217c1b120261018: **3 bestanden, 0.30 s**;
Upgrade/Downgrade/Upgrade, Legacy-Zahlungswerte unveraendert, jedes verwendete
Praeferenzfeld sperrt Downgrade. pyreadline3-Handlefehler nach Testende, Exit 0.
Anwendungsintegration lokal geprueft, keine Live-Migration.

## Abschlussnachweis (10.11.2026)

Migration separat in b9727e4. Eigene Erinnerungen, Wiederaufnahme, gesperrter
Legacy-Zahlungseingang und Korrektur-Praeferenzerhalt implementiert.
Erster Erinnerungstestlauf: 3 fehlgeschlagen, 15 bestanden. Ursache war der
weiter sichtbare Betrag in der Dashboard-Kachel Letzter Anteil. Anwendung
korrigiert; ausgeblendete private Betraege sind auch dort ausgeblendet.

Aktueller gezielter Lauf: **122 bestanden, 5444 Warnungen, 305.27 s, Exit 0**.
Enthaelt private_reminders (22), private_reminder_migration (3),
billbro_private_clarification, billbro_finance, billbro_correction, bank_import
und event_visibility. Bootstrap via run_existing_tests.py (run_name=audit_bootstrap),
danach pytest.main mit diesen sieben Testdateien, -q --disable-warnings
--tb=short -p no:cacheprovider. Synthetische Daten, dotenv und Netz gesperrt.
Nach Testende meldet pyreadline3 einen ignorierten Windows-Handlefehler;
dieser ist getrennt vom erfolgreichen Testergebnis (Exit 0).

`node --test tests/js/sw_cache_isolation.test.cjs tests/js/merch_order_edit.test.cjs`:
**24 bestanden, 0 fehlgeschlagen, Exit 0**. PWA 3.16.45 / pwa.9af46541.js.
Die frueher gestarteten, unterbrochenen Oktober-Laeufe werden mangels gesicherter
Endausgabe nicht als weitere bestandene Tests ausgewiesen. Gesamtsuite 1510
gehoert zum aelteren c1b1-Stand, nicht zu diesem Abschluss.

PostgreSQL-Sperren/Migration unter PostgreSQL, echte Browser/Geraete und
Darstellungsabnahme bleiben offen. Keine Produktionsfreigabe, kein Versand.
Separat entdeckt und noch nicht korrigiert: Dashboard verwendet fuer GGL
Listenposition statt berechnetem Saisonrang; Folgeauftrag U3-02 im Plan.

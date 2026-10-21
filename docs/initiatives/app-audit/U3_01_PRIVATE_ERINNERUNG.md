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
Anwendungsintegration noch in Arbeit, keine Live-Migration.

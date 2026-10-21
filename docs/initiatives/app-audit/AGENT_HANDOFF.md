# Agenteneinstieg: App-Audit-Umsetzung

Stand: 21.10.2026. **U1 ist insgesamt offen.**

1. AGENTS.md, [README](README.md) und [Umsetzungsplan](IMPLEMENTATION_PLAN.md)
   lesen. Plan steuert die aktuelle Paketfolge, README ist das Nachweisregister.
2. Bestehende Kette auf codex/app-audit-implementation-plan erhalten. Einstieg
   war 5b6d28d; Branch/HEAD/Status pruefen, nicht zuruecksetzen oder von master starten.
3. Naechstes Paket: **U2-17c1b2 – Finanzbestaetigung und Bankabgleich**.
   U1z bis R08 sowie U2-01 bis U2-17c1b1 sind im dokumentierten Umfang lokal
   geprueft. U1 bleibt offen, C1/F3/F4 sind noch nicht insgesamt abgeschlossen.
4. Relevante Anchor-Docs und Paketquellen vor Code lesen. Konkreter Vertrag:
   [Zahlungserhalt](U2_17C_ZAHLUNGSERHALT.md), insbesondere c1b2-Grenzen.
5. [Isolierter Runner](run_existing_tests.py): synthetische Daten, kein dotenv
   oder ausgehendes Netz. Versionierte Login-Identitaeten verwenden.
6. Jedes Paket mit Tests, Dokumentation, Plan/Handoff und lokalen Commits
   abschliessen, Migrationen separat. Danach naechstes bereites Paket fortsetzen.

Kein Push, Merge, Deploy, Produktionszugriff, Schluesselwechsel oder automatisches
Starten von Chats/Agenten. Fremde unversionierte Dateien bewahren:
build_logs.txt, docs/GDD_FOOD_POKEMON.md, docs/GDD_FOOD_POKEMON_REVIEW.md,
docs/capabilities/game.md, static/js/pwa.6af171c6.js, static/js/pwa.fa8699c7.js.
Zusaetzlich jeweils aktuellen Status pruefen.

## Bestaetigte Regeln

- Interne Einzelbewertungen: alle Mitglieder mit Eventzugriff.
- Unklassifizierte Drive-Dateien: nur Systemadmin in der App; direkte Drive-
  Rechte unveraendert bis separat erlaubter Abnahme.
- Bestaetigter Eingangsueberschuss 3620, tatsaechliche Rueckzahlung 6710;
  keine automatische Ueberweisung. Senkung eines bereits verbuchten Anteils
  erzeugt keine neue 3620-Einnahme. Originalbankbewegungen erhalten.
- BillBro rappengenau/summengleich, Restrappen nach groesstem Rechenrest,
  Gleichstand nach Mitglied-ID; keine automatische historische Neuberechnung.
- Tatsaechliche Anwesenheit getrennt vom urspruenglichen RSVP; keine erfundene
  Zusage/Absage. Organisation bereitet bezahlte Korrektur nur vor, Finanzrolle
  bestaetigt. Bezahlter Glaeubigerwechsel bleibt getrenntes G1-Folgepaket.
- B01/B02/G1 ersetzt private Zahlungsbestaetigung als Ziel: private Zahlungen
  unbekannt, paid=0 kein Unbezahlt-Beweis. C0 verlangt Erklaerung nach Klaerung
  und Vermerk fuer unbezahlte Privatkorrektur. Legacy-Privatbestaetigungsroute
  noch in eigenem B02-Paket ersetzen; keine allgemeine Zahlungskontrolle.
- F1/F2/R13, F3/F4, G1-G3/K1 und weitere bestaetigte Entwuerfe gelten weiterhin.
  Keine bestaetigten Regeln erneut abstimmen.

## Aktueller lokaler Nachweis und Grenzen

Gesamte Python-Regression zum c1b1-Anwendungsstand: **1510 bestanden,
24300 Warnungen, Exit 0**. Gemeldete 261968.09 s enthalten mehrtaegige
Unterbrechung 18.-21.10.2026 und sind kein Performance-Nachweis.
Gezielt c1b1: 64 Tests; erweitert 9 Bilanztests (zwei neue Faelle ausserhalb
der bereits gestarteten Gesamtsammlung), 24 JavaScript-Tests bestanden.
Migration **16d8f3d** (u217c1b120261018) separat, SQLite-Zyklus/FK/Unique/
Historien-Downgrade-Sperre geprueft. PWA **3.16.43 / pwa.1286f295.js**.
C1a davor **3ec23f8**, Migration **0856609**; 138 Tests, erweitert 22, 24 JS.
Weitere konkrete Nachweise im README und den Paketvertraegen.

C1a speichert Entwuerfe ohne Finanzmutation, c1b1 liefert ClaimRefundPayment
und Nettobilanz. Keine Finanzfreigabe oder neuer Ausgangsabgleich aktiviert.
MemberClaim.paid_rappen bleibt Brutto; aktive Rueckfluesse separat, Netto fuer
Offen/Status. Ruecknahme erhaelt Links. BankRefundConfirmation bleibt gesondert
fuer Eingangsueberschuesse. C1b2 verbindet aktuellen Entwurf, erhaltene Claim-
IDs, atomare Finanzhistorie und tatsaechlichen 6710-Ausgang. Vertragsdetails
und Testgrenzen vor Code in U2_17C_ZAHLUNGSERHALT.md lesen.

Echte PostgreSQL-Sperren/Migrationen, Browser/Geraete, Mail, Drive und Hosting-
Recovery bleiben externe Abnahmen. D-01 Google-Mehrfachzuordnung offen;
unabhaengige lokale Arbeit fortsetzen. Keine pauschale Produktionsfreigabe.
Merch-Runden-/Zuschuss-/Korrekturmodell, bezahlter Glaeubigerwechsel und B02
bleiben Folgearbeit; anschliessend weitere U2-U6-Pakete nach Plan ableiten.

Aeltere U1-Uebergabe: [Verlauf](AGENT_HANDOFF_HISTORY_20261016.md).
Datierte alte Naechstes-Absaetze sind Verlauf, keine aktuelle Warteschlange.

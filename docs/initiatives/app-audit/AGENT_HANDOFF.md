# Agenteneinstieg: App-Audit-Umsetzung

Stand: 10.11.2026. B02-Anwendungsabschluss: `4bc210e`; separate Migration: `b9727e4`. **U1 ist insgesamt offen.**

1. AGENTS.md, [README](README.md) und [Umsetzungsplan](IMPLEMENTATION_PLAN.md)
   lesen. Plan steuert die aktuelle Paketfolge, README ist das Nachweisregister.
2. Bestehende Kette auf codex/app-audit-implementation-plan erhalten. Einstieg
   war 5b6d28d; Branch/HEAD/Status pruefen, nicht zuruecksetzen oder von master starten.
3. Naechstes Paket: **U3-02 – GGL-Dashboard-Rangabgleich**.
   U3-01/B02 sowie U1z bis R08 und U2-01 bis U2-17c1b2 sind im dokumentierten Umfang lokal
   geprueft. U1 bleibt offen; Vereinskorrektur C1 lokal, private F3/F4/G1-Faelle noch offen.
4. Relevante Anchor-Docs und Paketquellen vor Code lesen. Konkreter Vertrag:
   [Zahlungserhalt](U2_17C_ZAHLUNGSERHALT.md), c1b2-Nachweis; fuer U3-02 DOMAIN und U2_17B_BILLBRO_KORREKTUR.md lesen.
5. [Isolierter Runner](run_existing_tests.py): synthetische Daten, kein dotenv
   oder ausgehendes Netz. Versionierte Login-Identitaeten verwenden.
6. Jedes Paket mit Tests, Dokumentation, Plan/Handoff und lokalen Commits
   abschliessen, Migrationen separat. Danach naechstes bereites Paket fortsetzen.

Einmalige GitHub-Veroeffentlichung der bestehenden Kette fuer die Uebergabe am
10.11.2026 beauftragt. Danach ohne neuen Auftrag kein Push. Kein Merge, Deploy,
Produktionszugriff, Schluesselwechsel oder automatisches
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
  seit B02 stillgelegt (410); nur eigene Anzeige, keine Zahlungskontrolle.
- F1/F2/R13, F3/F4, G1-G3/K1 und weitere bestaetigte Entwuerfe gelten weiterhin.
  Keine bestaetigten Regeln erneut abstimmen.

## Aktueller lokaler Nachweis und Grenzen

Gesamte Python-Regression zum c1b1-Anwendungsstand: **1510 bestanden,
24300 Warnungen, Exit 0**. Gemeldete 261968.09 s enthalten mehrtaegige
Unterbrechung 18.-21.10.2026 und sind kein Performance-Nachweis.
Gezielt c1b1: 64 Tests; erweitert 9 Bilanztests (zwei neue Faelle ausserhalb
der bereits gestarteten Gesamtsammlung), 24 JavaScript-Tests bestanden.
Migration **16d8f3d** (u217c1b120261018) separat, SQLite-Zyklus/FK/Unique/
Historien-Downgrade-Sperre geprueft. Danach c1b2: **196 Tests bestanden**, erweitert 2; 24 JS.
PWA **3.16.44 / pwa.e8bff355.js**. Gesamtbasis 1510 war vor c1b2.
C1a davor **3ec23f8**, Migration **0856609**; 138 Tests, erweitert 22, 24 JS.
Weitere konkrete Nachweise im README und den Paketvertraegen.

C1a speichert Entwuerfe ohne Finanzmutation, c1b1 liefert ClaimRefundPayment
und Nettobilanz (Anwendung be9d133). C1b2 bestaetigt aktuelle Vereinsentwuerfe
finanziell mit erhaltenen Claim-IDs und gleicht reale Ausgaenge auf 6710 ab.
MemberClaim.paid_rappen bleibt Brutto; aktive Rueckfluesse separat, Netto fuer
Offen/Status. BankRefundConfirmation bleibt gesondert fuer Eingangsueberschuss.
Persoenliche Zahlungsansicht filtert Mitglied; alle Eventposten nur Organisation/
Finanz, Banklinks nur Finanz-Leserecht. Private und Glaeubigerwechsel-Faelle offen.

B02 ist lokal abgeschlossen: Migration b9727e4 separat; 122 Python-Tests
(5444 Warnungen, 305.27 s, Exit 0) und 24 JS am 10.11.2026 bestanden.
PWA aktuell 3.16.45 / pwa.9af46541.js. Kein neuer Gesamtsuite-Nachweis.
Details/Fehlerkorrektur: [B02](U3_01_PRIVATE_ERINNERUNG.md).

Naechstes U3-02: Dashboard berechnet GGL-Rang derzeit als Listenposition.
Berechneten Saisonrang verwenden und Gleichstand regressiv pruefen, ohne
historische Neuberechnung. Auftrag und Abschlusskriterien stehen im Plan.
Reproduzierbarer Einstieg: [START_NEXT_AGENT.md](START_NEXT_AGENT.md).

Echte PostgreSQL-Sperren/Migrationen, Browser/Geraete, Mail, Drive und Hosting-
Recovery bleiben externe Abnahmen. D-01 Google-Mehrfachzuordnung offen;
unabhaengige lokale Arbeit fortsetzen. Keine pauschale Produktionsfreigabe.
Merch-Runden-/Zuschuss-/Korrekturmodell und bezahlter Glaeubigerwechsel
bleiben Folgearbeit; anschliessend weitere U2-U6-Pakete nach Plan ableiten.

Aeltere U1-Uebergabe: [Verlauf](AGENT_HANDOFF_HISTORY_20261016.md).
Datierte alte Naechstes-Absaetze sind Verlauf, keine aktuelle Warteschlange.

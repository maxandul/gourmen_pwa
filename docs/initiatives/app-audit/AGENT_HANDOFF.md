# Agenteneinstieg: App-Audit-Umsetzung

Stand: 18.10.2026. **U1 ist insgesamt offen.**

1. AGENTS.md, [README](README.md) und den [Umsetzungsplan](IMPLEMENTATION_PLAN.md)
   lesen. Plan ist die aktuelle Reihenfolge, README das Nachweisregister.
2. Bestehende Kette auf codex/app-audit-implementation-plan erhalten. Einstieg
   war 5b6d28d; Branch/HEAD/Status pruefen, nicht zuruecksetzen oder neu von master.
3. Naechstes Paket: **U2-17c1 – bezahlte Vereinskorrektur**. U1z bis R08 sowie
   U2-01 bis U2-17c0 sind im dokumentierten Umfang lokal geprueft. U1 bleibt offen.
4. Relevante Anchor-Docs und Paketquellen vor Code lesen. Bestaetigte Regeln
   nicht erneut abstimmen; fehlende konkrete Fachentscheidung gezielt isolieren.
5. [Isolierter Runner](run_existing_tests.py): synthetische Daten, kein dotenv
   oder ausgehendes Netz. Versionierte Login-Identitaeten (U1v) verwenden.
6. Jedes Paket mit Regression, Doku, Plan/Handoff und lokalen Commits schliessen;
   Migrationen separat. Danach selbststaendig naechstes bereites Paket fortsetzen.

Kein Push, Merge, Deploy, Produktionszugriff, Schluesselwechsel oder automatisches
Starten von Chats/Agenten. Fremde unversionierte Dateien bewahren:
build_logs.txt, docs/GDD_FOOD_POKEMON.md, docs/GDD_FOOD_POKEMON_REVIEW.md,
docs/capabilities/game.md, static/js/pwa.6af171c6.js, static/js/pwa.fa8699c7.js.
Zusaetzlich jeweils aktuellen Status pruefen.

## Bestaetigte Fachentscheidungen

- Interne Einzelbewertungen: alle Mitglieder mit Eventzugriff.
- Unklassifizierte Drive-Dateien: nur Systemadmin in der App; direkte Drive-Rechte
  bleiben bis separat erlaubter Abnahme unveraendert.
- Bestaetigter Eingangsueberschuss 3620, tatsaechliche Rueckzahlung 6710;
  keine automatische Ueberweisung. U2-02c1/c2 lokal, Zahlungsjournal erhalten.
- BillBro: rappengenau/summengleich, Restrappen nach groesstem Rechenrest,
  Gleichstand nach Mitglied-ID. U2-12 implementiert Erstabschluss und
  individuelle Anzeige; keine automatische Neuberechnung alter Abschluesse.
- F1/F2/R13, F3/F4, G1–G3/K1 und weitere bestaetigte Entwuerfe gelten weiterhin.

## Aktueller lokaler Nachweis und Grenzen

Breite Regression auf ae43000: **1467 bestanden, 22209 Warnungen, 580.93 s**;
24 JavaScript-Tests bestanden. Danach GGL-Anzeige-Nachkorrektur: 23 Tests bestanden (705 Warnungen, 11.11 s);
halbe Gesamtpunkte und gleiche Saisonraenge erhalten.
Vor diesem Gesamtlauf U2-11: 92 Tests; U2-12: 114 und erweitert 36; U2-13: 45 und erweitert 5;
U2-14: 61. Danach U2-15: 80 Python-/23 JS-Tests. Einzelvertraege im README.
Migration U2-14 **e9d6f95** (u21420261018), Snapshotfelder ohne erfundene
Altbezeichnungen; SQLite-Zyklus und Historie-Downgrade-Sperre geprueft.
U2-15-Nachkorrektur: 82 Python-/24 JS-Tests; Reihenfolge/Varianten-Schluessel
und unvollstaendige Fehlereingaben. Danach U2-16a: 119 Python-/24 JS-Tests; U2-17a: 160 Python-Tests. U2-17b1: 139 Tests, nach Ergaenzung 41; Migration 3f16cb4 separat
(u217b120261018). B2: 91 Tests, erweitert 14; Migration 37e081c
(u217b220261018) fuer halbe GGL-Werte, fehlende Legacy-Punktespalte beruecksichtigt.
B3a: 82 Tests. B3b: 230 Tests, Anschluss 47/40, erweitert 23; 24 JS-Tests.
Migration 3f09db1 (u217b3b20261018) separat. C0: 79 Python-/19 Worker-Tests; PWA 3.16.41 / pwa.a93228ba.js.
Gesamtlauf auf unveraendertem ae43000 abgeschlossen, Prozessstatus 0.

U2-14 erhaelt Varianten-IDs/Preise und Bestellbezeichnungen, sperrt Altduplikate.
U2-15 erhaelt Positionspreise/IDs, Nulloperationen schreiben nichts; Versions-
vergleich und Mengen-Erhalt im Edit-JS. Breiter Gesamttest bestanden; gezielte Nachkorrektur separat geprueft.
U2-16a speichert Status/Forderung atomar und sperrt einfache Rueckschritte.
Merch-Runden-/Zuschuss-/Korrekturmodell sowie F3/F4-Vorschau/Korrektur bleiben
Folgepakete. U2-17a sperrt direkte Mutation bei Abschluss-/Forderungs-/
Anteilshistorie; U2-17b1 liefert Gesamtbetrag/Zahlweg mit Vorschau/Grund/Historie.
B2 liefert Rechnung/GGL, B3a Ess-Typ-Korrektur, B3b getrennte Anwesenheit/RSVP
mit Vorschau und Historie. C1 beginnt bezahlt bei gleichem Zahlweg;
bezahlter Glaeubigerwechsel folgt getrennt. F3/F4 daher noch nicht insgesamt abgeschlossen.
Echte PostgreSQL-Sperren/Migrationen, Browser/Geraete, Mail, Drive und
Hosting-Recovery bleiben externe Abnahmen. D-01 Google-Mehrfachzuordnung offen;
unabhaengige lokale Arbeiten fortsetzen. Keine pauschale Produktionsfreigabe.

Aeltere U1-Uebergabe: [Verlauf](AGENT_HANDOFF_HISTORY_20261016.md).
Datierte alte Naechstes-Absaetze sind Verlauf, keine aktuelle Warteschlange.


B01/B02/G1 ersetzt den alten privaten Zahlungsbestaetigungsentwurf.
C0 verlangt nun ausdrueckliche Klaerung und signierten Vermerk fuer private
Ausgangsfaelle; paid=0 ist kein Unbezahlt-Beweis. C1 auf Vereinszahlungen
begrenzen. Legacy-Privatbestaetigung bleibt in B02 zu ersetzen; keine neue
private Zahlungskontrolle. Keine pauschale Finanzfreigabe.

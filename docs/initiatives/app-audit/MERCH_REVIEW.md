# Merch – erster vertiefter Durchlauf

Stand 2026-09-20. App unveraendert, Baseline `bf4d84a` erneut verifiziert. **Teilpruefung, kein
abgeschlossenes Modulreview.** Schwerpunkt: Bestellen, Aendern, Varianten,
Status und Forderungsschnittstelle. Nun 18 isolierte Szenarien, Befunde
A-048 bis A-056 sowie Ergaenzungen zu A-035/A-048; insgesamt 56 Befunde im Katalog.

## Nachweise und Grenzen

[MERCH_CHECKS.json](MERCH_CHECKS.json), erzeugt mit `check_merch_workflows.py`.
Original-Routes und Models, SQLite im Arbeitsspeicher mit explizit eingeschalteten
und verifizierten Fremdschluesseln (`PRAGMA foreign_keys=ON`). Pro Fall neue DB,
synthetischer Admin/Member und Artikel/Variante. Keine ENV-Secrets, kein Netzwerk,
kein Versand, keine echten Bestellungen. Ein Fall ersetzt den Claim-Service
gezielt durch einen Fehler, um die Transaktionsgrenze zu pruefen.
CSRF/Rate-Limit in Testing aus; PostgreSQL und Browserinteraktionen nicht bewiesen.

| Szenario | Beobachtung |
|---|---|
| order_0_M | Leere Bestellung erfolgreich angelegt, A-048 |
| order_-1_M | Negative Menge still ignoriert, leere Bestellung, A-048 |
| order_1_missing | Unbekannte Groesse still ignoriert, leere Bestellung, A-048 |
| order_1_M | Positiv: gueltige Position, serverseitiger Preis CHF 20 |
| reopen_edit_stale_claim | Summe CHF 60, Claim CHF 20, altes Lieferdatum, A-049 |
| edit_article_with_existing_order | Variantenloeschen scheitert an Referenz; Rollback erhaelt Daten, A-050 |
| inactive_variant_silently_removed | Beim Bearbeiten geht die alte Position verloren, A-048 |
| ownership_and_status_guards | Fremde Detail-/Edit-URLs 404; Statusmutation als Member 403; Daten unveraendert |
| repeat_order_post | Zwei gleiche Requests erzeugen zwei Bestellungen, A-052 |
| get_shop_inactive_ordered_variant | GET verursacht ORM-Loeschversuch/IntegrityError, A-051 |
| status_committed_before_claim_failure | Status bleibt gesetzt, Claim fehlt nach injiziertem Fehler, A-049 |
| price_decimal_precision | 19.99 wird zu 1998 Rappen, A-053 |
| price_negative | Negativer Preis wird gespeichert, A-053 |
| duplicate_variant_input | Zweimal dieselbe Farbe erzeugt doppelte Variante, A-054 |
| uneven_form_arrays | Ueberzaehlige Menge still abgeschnitten, Ergaenzung A-048 |
| status_protocol_relative_redirect | Admin-next erlaubt externes protokollrelatives Ziel, Ergaenzung A-035 |
| unchanged_order_repriced | Gleiche Bestellung wird nach Katalogaenderung neu bepreist, A-055 |
| grouping_changes_status_filter | Artikelgruppierung setzt zusaetzlich Status Offen, A-056 |

Die erweiterten 18 Szenarien wurden am 20.09. gemeinsam erneut ausgefuehrt.
JSON und Laufprotokoll enthalten diesen aktuellen Lauf. Das Wiederholen der
ersten 11 Faelle ist eine Gegenpruefung, keine Erhoehung der Szenarienzahl.

## Tatsaechlicher Ablauf und Dokumentationsabweichung

Implementiert sind Artikel mit Farbe/Groesse, Bestellung mit gespeicherten
Stueckpreisen und drei Statuswerten. Die internen Namen sind missverstaendlich:
BESTELLT wird als «Offen» angezeigt; WIRD_GELIEFERT als «Bestellt»; GELIEFERT
als «Geliefert». Offene Bestellungen duerfen vom Eigentuemer bearbeitet werden.
Bei den beiden spaeteren Statuswerten entsteht eine Forderung, bei der ersten
Bestellung noch nicht. Normale Mitglieder duerfen die Vereins-Merch-Uebersicht
laut Anchor-Docs lesend sehen; dies wird nicht als unberechtigter Zugriff gewertet.

`docs/capabilities/accounting.md:564` beschreibt Bestellrunden mit Listenpreis
und spaeterem effektivem Lieferantenpreis. `docs/UI.md:204` ff. nennt Rundenshop,
MerchRoundItem und `templates/admin/merch_v2/article_form.html`. Diese Runden-
Struktur ist im bisher inventarisierten aktiven Merch-Code nicht implementiert.
Damit besteht ein weiterer konkreter Dokumentationsabgleich zu A-012. Nicht
automatisch als fehlendes Feature interpretieren: zuerst klaeren, ob Zielbild,
veralteter Stand oder umzuziehende Implementierung gemeint ist.

Zwei parallele Statusrouten duplizieren dieselbe Logik. Beide committen Status
vor Claim-Erstellung; eine davon druckt das gesamte Formular in Debug-Ausgaben.
Diese Doppelspurigkeit gehoert in die Konsolidierung, nicht in zwei separate
fachliche Workflows. Die bestehende Trennung Shop / eigene Bestellungen / Admin
ist grundsaetzlich nachvollziehbar; die Status- und Korrekturregeln fehlen darunter.

## Noch offen

- Farbnamen/Leerzeichen, weitere Preisformate, Mengenobergrenzen und extreme
  Datenmengen; Kernfaelle fuer Erstellung, Float-Umrechnung, negative Preise,
  Duplikate und ungleich lange Arrays inzwischen geprueft.
- Varianten-/Artikelhistorie bei Preis-, Text- und Sortimentaenderungen; Snapshots
  fuer alte Bestellungen; Status-Zuruecknahme mit bereits bezahlten Forderungen.
- Beide Status-Endpoints vollstaendig vergleichen; externer Rueckleitungsfall
  inzwischen bestaetigt, weitere Kodierungen/Fehlerpfade noch offen.
  Audit-Logging und Wiederholungen mit echten parallelen Requests.
- GET-Ladegraph, Query-Skalierung, alle Admin-Statistiken und Summenfilter.
- Shop/Edit/Bestellansicht im Browser: lange/zahlreiche Varianten, Fehlereingaben,
  Tastatur, Mobile/Tablet/Desktop. A-017 zu Formularlabels bleibt relevant.
- Runden-/Lieferanten-Zielbild gegen weitere Initiative-Dokumente abgleichen.

Naechster Modulschwerpunkt: Buchhaltung. Die oben genannten Restfaelle und
Browserpruefungen bleiben fuer die Gegenpruefung offen. Keine Umsetzung vor
konsolidiertem User-Feedback.

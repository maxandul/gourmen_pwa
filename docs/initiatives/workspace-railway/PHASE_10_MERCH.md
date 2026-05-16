# Phase 10 – Merch-Verwaltung neu

> **Branch**: `phase/10-workspace-merch` (Empfehlung: Feature-Branches; Merge-Ziel ist `master`)
> **Spec (autoritativ)**: [`docs/capabilities/merch.md`](../../capabilities/merch.md). **Zielbild Sortiment (Artikel/Farbe/Groesse/Matrix)**: [`merch-article-variant-target-state.md`](../../capabilities/merch-article-variant-target-state.md) — Umsetzung schrittweise oder Folge-Phase; zunaechst Capability-Baseline in `merch.md` Sektion 6.
> **Strategie-Anker**: [`docs/STRATEGY_2026.md`](../../STRATEGY_2026.md) MVP-Punkt 4
> **Status**: in_progress auf `master` (MERCH-V2‑Cockpit, Shop, Statistik/Jahresreport, Audit, Legacy‑Receivables; Sortiment/Stammdaten v2 schrittweise). **Aufwand**: ~2 Wochen.

**Umsetzungsstand (laufend, nicht gleich Release):** Lieferanten- und **Sortimentspflege (Artikel, Varianten, Bild)** im Cockpit (`/admin/merch-v2/suppliers`, `/admin/merch-v2/articles`); **Lookups Farbe/Grösse** (`/admin/merch-v2/lookups`, Migration `c4e8a9012b71`) und **`variant_key`**; **Mitglieder-Shop** mit Konfigurator pro Artikel (Dropdown Ausführung); Runden-KPI + Vereinsjahresstatistik + CSV; Merch-Historie im Admin-Mitglied-Detail; Lieferantenbeleg nach Drive (`MERCH_SUPPLIER_INVOICE_DRIVE_FOLDER_ID`); Artikelbilder nach Drive (`MERCH_ARTICLE_IMAGE_DRIVE_FOLDER_ID`). **Nächster Agent:** Ziel-/Handoff siehe [`docs/capabilities/merch-article-variant-target-state.md`](../../capabilities/merch-article-variant-target-state.md) §9; offen u.a. Bulk-Bestätigung, Hinweis nach Massen-Anlage Varianten.

**Feinschliff:** Cockpit-Subnavigation (`_subnav.html`); weiteres Polish nach Bedarf.

---

## Worum geht es

Vollstaendige Neuimplementation der Merch-Verwaltung — kein Polieren der bestehenden vier Tabellen, sondern ein Prozess-Redesign mit **Bestellrunden** als zentrales Konzept. Die heutige Implementation (Daueroffener Shop, Status `BESTELLT/WIRD_GELIEFERT/GELIEFERT`) wird durch das in `docs/capabilities/merch.md` beschriebene Modell ersetzt.

Hintergrund und Detail-Entscheide stehen im Capability-Doc; dieses Phase-Briefing ist nur der Rahmen fuer Cursor.

## Pre-Conditions

- Phase 3 (Drive-Integration) produktiv. `DriveStorageService` einsatzbereit.
- Phase 9 (Drive-Browser-Refactor) hilfreich, aber nicht hart noetig — Merch nutzt Drive ueber den Service-Layer, nicht ueber die Drive-UI.
- `Funktion.MARKETINGCHEF` und `Funktion.SCHATZMEISTER` im `Member`-Modell existieren bereits.
- Redis ist auf Railway konfiguriert (fuer Bild-Cache).
- Capability-Doc `docs/capabilities/merch.md` ist gelesen und verstanden.

## Migrations-Strategie (wichtig vorab)

Phase 10 fasst die **Bestandsdaten nicht an**. Die alten Tabellen (`merch_articles`, `merch_variants`, `merch_orders`, `merch_order_items`) werden in der ersten Migration auf `_legacy`-Suffix umbenannt und bleiben sonst unveraendert. Die neuen Tabellen werden mit den sauberen Hauptnamen frisch angelegt. Eine Bestand-Migration aus den `_legacy`-Tabellen ist **nicht Teil dieser Phase** — sie wird in einer separaten Folge-Phase mit Production-Daten-Probe gemacht oder ganz verworfen.

## Reihenfolge der Commits

Detail siehe `docs/capabilities/merch.md` Sektion 21.1. Kurz:

1. Rename-Migration: alte Tabellen auf `_legacy`-Suffix (rein SQL, reversibel)
2. Code-Refactor alte Models: `__tablename__='..._legacy'`, ggf. Klassennamen umbenennen, Bestand-Routes auf neuen Namen
3. Schema-Migration: neue Tabellen `merch_suppliers`, `merch_articles`, `merch_variants`, `merch_rounds`, `merch_round_items`, `merch_orders`, `merch_order_items`
4. Service-Layer (`MerchSortimentService`, `MerchRoundService`, `MerchOrderService`, `MerchImageService`) mit Tests
5. Drive-Bild-Proxy mit Cache
6. Routes + Cockpit-UI (Marketingchef)
7. Mitglieder-UI (Shop, Warenkorb, Detail, Dashboard-Card)
8. Legacy-Receivables-Sicht (`/admin/merch/legacy-receivables`, read-only Aggregat pro Mitglied)
9. Feature-Flag-Cutover

Schema-Migrationen sind separate Alembic-Commits. Service-Layer und UI je eigene Code-Commits.

## Akzeptanzkriterien

Vollstaendige Liste in `docs/capabilities/merch.md` Sektion 21.3. Highlights:

- Marketingchef kann Lieferanten, Artikel mit Schema und Bild, Runden anlegen
- Mehrere parallele Runden moeglich
- Lifecycle-Uebergaenge inkl. Backwards `LOCKED → OPEN` und `CANCELLED` funktional
- Subventions-Berechnung mit Cap = Bestellbetrag korrekt
- Sammelbestellungs-Aggregat exportierbar (Text-Copy + CSV)
- Drei Statistik-Sichten (Runde, Mitglied, Jahr) live
- Bilder via Drive-Proxy mit Cache
- Audit-Log fuer alle Lifecycle- und Bezahl-Aktionen
- Permissions korrekt (Marketingchef + Schatzmeister + Admin, sonst nichts)
- Feature-Flag `MERCH_V2_ENABLED` schaltet die Capability ein

## Out of Scope

Vollstaendige Liste in `docs/capabilities/merch.md` Sektion 21.4. Wichtig:

- **Keine Push-Notifications** (Vereinskommunikation ueber WhatsApp-Chat)
- **Keine TWINT-Integration** (kommt mit Phase 6 / Buchhaltung; im MVP manuelle Bezahl-Markierung)
- **Keine BillBro-Integration** (BillBro deckt Merch nicht ab, ist event-spezifisch)
- **Keine AI-Hebel** (Auto-Beschreibung und Mengen-Empfehlung sind Backlog)
- **Kein Lager-Konzept** (Verein fuehrt kein Lager)
- **Keine MwSt-Behandlung im Detail** (kommt mit Buchhaltung)
- **Keine Daten-Migration aus `_legacy`-Tabellen** (separate spaetere Phase mit Production-Daten-Probe)
- **Keine Bilder-Migration** der alten `static/img/merch/`-Bestaende (laeuft mit der Bestand-Migrationsphase)
- **Kein Drop der `_legacy`-Tabellen** (erst nach erfolgreicher Bestand-Migration)

## Lokale Verifikation vor Push

- Lifecycle-Uebergaenge alle durchspielen
- Backwards-Uebergang `LOCKED → OPEN` testen
- `CANCELLED` auf jedem Status testen
- Mitglied-Bestellung waehrend `OPEN` aendern, stornieren
- Subventions-Berechnung an der Beispielrechnung in `merch.md` Sektion 7.3 verifizieren
- Bild-Upload nach Drive, Proxy-Auslieferung, Cache-Hit beim 2. Request
- Sammelbestellungs-CSV-Export Format pruefen
- Statistik-Werte gegen manuell berechnete Werte verifizieren
- Permissions: Mitglied erhaelt 403/404 auf Cockpit-Routes; Schatzmeister kann nur Bezahl-Markieren
- `flask db upgrade && flask db downgrade && flask db upgrade` lokal sauber durchlaufen

## Production-Cutover

Nach Merge auf `master`:

1. Backup Production-DB (manuell oder Railway-Snapshot)
2. Migrationen laufen lassen (Rename + neue Tabellen)
3. Verifikation: `_legacy`-Tabellen unveraendert vorhanden, neue Tabellen leer und mit Constraints angelegt, Bestand-Routes funktionieren weiter
4. `MERCH_V2_ENABLED=true` in Railway-Env setzen
5. UI smoke-testen mit Test-Marketingchef-Account: erste Test-Runde anlegen, Test-Bestellung als Mitglied, Bezahlung markieren
6. Stabilisierungsphase 1–2 Wochen mitlaufen lassen (echte erste Runde durchspielen)
7. Bestand-Migration als **separate Folge-Phase** angehen (nicht Teil von Phase 10): Production-Daten der `_legacy`-Tabellen inspizieren, entscheiden migrieren oder verwerfen, ggf. Migrations-Script schreiben, danach `_legacy`-Tabellen droppen

## Verweise

- Capability-Doc (Spec): `docs/capabilities/merch.md`
- Strategie: `docs/STRATEGY_2026.md` MVP-Punkt 4 + Decision Log
- Drive-Capability (genutzt fuer Bilder + Belege): `docs/capabilities/drive.md`
- Conventions (Service-Pattern, Permissions, Routes): `docs/CONVENTIONS.md`
- Vorbild (Doc-Konvention + Phase-Briefing-Stil): `docs/capabilities/calendar.md` + `docs/initiatives/workspace-railway/PHASE_05_ICAL_FEED.md`

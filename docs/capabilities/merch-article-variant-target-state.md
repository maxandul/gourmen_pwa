# Merch: Zielzustand Artikel, Farben, Grössen, Varianten

> **Zweck**: Festhalten des **vereinbarten Zielbilds** für die Sortiments-Stammdaten (Artikel → Varianten → Rundeneinbindung → Mitglieder-Shop). Dient als Single Source of Truth für Implementierungs-Agenten **nach** dem heute produktiven Merch-v2-Modell mit Freitext-/JSON-Variantenlogik.
>
> **Status**: **Kern umgesetzt** (Migration, Lookups, `variant_key`, Cockpit, Mitglieder-Konfigurator); **Feinpolitur offen** (siehe **§9**). **Owner**: Verein (Product: Marketing/Andreas). **Stand**: 2026-05-16.
>
> **Verwandte Docs**: [`merch.md`](merch.md) (Gesamt-Capability, Lifecycle, Preise, Migration-Hinweise), [`PHASE_10_MERCH.md`](../initiatives/workspace-railway/PHASE_10_MERCH.md) (Phasen-Rahmen), [`DOMAIN.md`](../DOMAIN.md) (Rollen `Role.ADMIN`, `Funktion.MARKETINGCHEF`).

---

## 1. Abgrenzung zu `merch.md` Sektion 6 (heute)

Die Capability [`merch.md`](merch.md) beschreibt u.a. `variant_schema` am Artikel und `attributes` als JSON an der Variante. **Dieses Dokument ersetzt diese Modellierung als Zielzustand:** normierte **Lookup-Tabellen** für Farbe und Grösse, **FKs** an der Variante, plus klar definierte **Matrix-Generierung** und **Stammdaten-Regeln**.

**Stand Code (siehe §9):** Migration `c4e8a9012b71` und Anbindung im Backend/UI sind umgesetzt; `attributes` bleibt parallel für Rückwärtskompatibilität und Anzeige. Offene Punkte (Bestätigungsdialoge, optionale Hinweise, Rundeneinlage «ganzer Artikel») siehe **§9**.

---

## 2. Betriebsmodell (Kurz)

- **Kein Lager**; Bestellungen werden in der App gesammelt und extern beim Lieferanten wie bei einer Privatperson aufgegeben.
- **Typischer Rhythmus**: etwa ein Merch-Durchgang pro Jahr (Kollektion), danach ist «für das Jahr erledigt»; Stammdaten (Farben, Grössen) bleiben **wiederverwendbar**.
- **Globaler Katalog**: Keine rundenbezogenen Sichtbarkeits-Overrides auf Variantenebene nötig; **Sichtbarkeit und «nicht mehr lieferbar»** werden über **Variante** (und ggf. **Artikel**) gesteuert.

---

## 3. Rollen (bestehend)

| Fähigkeit | Wer |
|---|---|
| Sortiment / Artikel / Varianten / Runden (Cockpit) | `Funktion.MARKETINGCHEF` oder `Role.ADMIN` (Fallback) |
| **Umbenennen** von Farb- und Grössen-Stammdaten (Anzeigename o.ä.) | **nur** `Funktion.MARKETINGCHEF` oder `Role.ADMIN` |
| Bezahl-Markierung (unverändert Merch-Gesamtprozess) | siehe `merch.md` Permission-Matrix |

---

## 4. Konzeptionelles Datenmodell (englische Tabellennamen, wie im übrigen Projekt)

**Hinweis**: Konkrete SQLAlchemy-Namen folgen `docs/CONVENTIONS.md`; unten nur Fachlogik.

### 4.1 Artikel (`MerchArticle` o.ä.)

- Repräsentiert die **Produktfamilie** (z. B. «Hoodie»), **nicht** eine lose «Artikelgruppe» im Sinne von Bundles.
- Felder mindestens: Bezeichnung, Beschreibung, Lieferantenbezug, Standard-Listenpreis (Rappen), Bild-Referenz, Archiv-Flag, Timestamps.
- **Archivierung** auf Artikelebene: ganzer Artikel aus dem aktiven Sortiment.

### 4.2 Farbe und Grösse (Lookups)

- **`merch_colors`**, **`merch_sizes`** (Beispielnamen): globale Vokabeln.
- Pro Zeile u.a.: technischer Schlüssel/Name, **Anzeigetext**, **`sort_order`** (für UI: S, M, L, XL, XXL, … — nicht alphabetisch).
- **Kein `is_active` / keine Deaktivierung** dieser Lookups im Marketing-Cockpit: mehrere Artikel können dieselbe Farbe/Grösse nutzen; Einträge bleiben für **spätere Kollektionen** relevant.
- **Neue Farben und Neues Grössen** können beim **Erfassen/Bearbeiten von Artikeln oder Varianten** angelegt werden (schneller Flow für den Marketingchef).
- **Aufräumen** (Duplikate, seltene Fehleinträge): vor allem **Admin** ausserhalb des Tagesgeschäfts; im Betrieb **selten nötig**.
- **Umbenennen** (Anzeigetext): **nur Marketingchef oder Admin**, damit keine versehentlichen globalen Umbenennungen durch andere Rollen.

### 4.3 Variante (`MerchVariant`)

- Verkaufbare Einheit: **genau ein Artikel** + Referenzen auf **optional** `color_id`, `size_id` (FKs auf Lookups). Semantik von **NULL** und Eindeutigkeit: **§8.1**.
- **`list_price_rappen`**: überschreibt den Artikel-Standard falls gesetzt, sonst Fallback Artikel. Default für **neu generierte** Varianten: **§8.2**.
- **`is_active`** (oder äquivalent): **hier** wird «für diesen Artikel nicht mehr bestellbar» abgebildet (z. B. alle Kombinationen mit Farbe Schwarz für diesen Artikel). Bulk-Aktionen: **§8.3**.
- **Eindeutigkeit**: s. **§8.1** (inkl. technischer Hinweis PostgreSQL).

### 4.4 Matrix-Generierung und Nachziehen

- Beim Definieren der **erlaubten Farben und Grössen eines Artikels** erzeugt das System **alle Kombinationen** als Varianten (oder aktualisiert fehlende).
- **Beispiel**: Artikel hat 3 Farben × 3 Grössen → 9 Varianten. Wird **nachträglich eine Grösse** (z. B. XXL) hinzugefügt, werden **automatisch** Varianten für **alle bestehenden Farben** mit XXL angelegt (keine Duplikate).
- **Einzelvarianten**: Zusätzlich müssen **manuelles Anlegen** und **Bearbeiten** einzelner Varianten** möglich sein (Sonderfälle, Korrekturen).

### 4.5 Neue Attribut**typen** (nicht nur neue Werte)

- **Neue Farbe / neue Grösse** = neuer Lookup-Eintrag → **Marketingchef** (beim Erfassen).
- **Neue Dimension** (z. B. Material, Passform) = **Schema- und Produktänderung** → **Systemadministration / Entwicklung** (Migration, UI, Mitgliederauswahl). Im Admin-UI ein **Hinweis** für den Marketingchef, solche Erweiterungen **nicht** selbst «einzubauen».

---

## 5. Runden und «Live»-Katalog

- **Runde `OPEN`**: Mitglieder sehen den Katalog **live** aus dem Stamm: neue Varianten erscheinen **sofort**; Deaktivierung/Preisänderungen am Stamm wirken **sofort** (global, wie vereinbart).
- **Artikel in die Runde**: Der Marketingchef nimmt mindestens **ganze Artikel** in die Runde auf; technisch bedeutet das: alle **aktuell aktiven** Varianten dieses Artikels sind in dieser Runde **bestellbar** (über bestehende `MerchRoundItem`-Semantik pro Variante, siehe `merch.md`).
- **Feinanpassung** nach Aufnahme: weiterhin möglich (ganzer Artikel / Gruppen-Aktion z. B. «alle Varianten mit Farbe X für diesen Artikel» / Einzelvariante) — umgesetzt über **Varianten-`is_active`** (und bestehende Rundeneinbindung), nicht über Deaktivieren der globalen Farbe.
- **Snapshot**: Wie in `merch.md`: nach Schliessen / Lieferantenbestellung sind **Bestell- und Abrechnungsdaten** über Snapshots an Order/Round-Items nachvollziehbar; der **offene** Shop liest den **Stamm live**.

---

## 6. Mitglieder-Shop (Ziel-UX)

- Darstellung **pro Artikel** (eine Karte/Fläche), nicht als lange Liste isolierter Varianten ohne Kontext.
- Auswahl der passenden **Farbe/Grösse** (und künftig weiterer Dimensionen, falls je implementiert) in **einem** Konfigurator.
- **Mehrere Positionen** desselben Artikels im Warenkorb erlaubt (z. B. zwei Grössen oder zwei Farben) — mehrere **Order-Items** oder Mengen pro Variante gemäss bestehendem Order-Modell.

---

## 7. Implementation-Hinweise für Agenten

1. Vor Code: [`merch.md`](merch.md), [`ARCHITECTURE.md`](../ARCHITECTURE.md), [`CONVENTIONS.md`](../CONVENTIONS.md), [`UI.md`](../UI.md) lesen.
2. **DB-Änderungen**: eigener Alembic-Commit (Repo-Regel: nicht mischen mit Feature-Code).
3. **Migration alter Daten**: Freitext/JSON-Varianten auf `color_id`/`size_id` mappen (evtl. neue Lookup-Zeilen erzeugen) — separat planen; nicht ohne Daten-Review auf Production.
4. Nach UI/Template-Änderungen: Cache-Buster laut `docs/UI.md` / `update_pwa_version.py`.

---

## 8. Festgelegte Feinentscheide

### 8.1 NULL-Semantik und Eindeutigkeit

| Fall | `color_id` | `size_id` | Bedeutung |
|---|---|---|---|
| Reiner Einzelartikel (keine textile Variantenwahl) | `NULL` | `NULL` | Genau **eine** verkaufbare Variante für diesen Artikel. |
| Nur Grösse (Farbe gibt es nicht / wird nicht angeboten) | `NULL` | gesetzt | Eine Variante pro Grösse. |
| Nur Farbe (Einheitsgrösse) | gesetzt | `NULL` | Eine Variante pro Farbe. |
| Typischer Hoodie | gesetzt | gesetzt | Kombinationsmatrix wie besprochen. |

**Mitglieder-UI:** Wenn eine Dimension `NULL` ist, wird für diese Dimension **kein Auswahlschritt** angezeigt (Konfigurator reduziert sich auf die vorhandenen Dimensionen).

**Produkteindeutigkeit:** Pro Artikel existiert höchstens **eine** Variante für dieselbe Kombination aus `(color_id, size_id)` im Sinne der Tabelle oben — inklusive der Zeile `(NULL, NULL)` höchstens **einmal**.

**Technik-Hinweis PostgreSQL:** `UNIQUE (article_id, color_id, size_id)` allein verhindert **nicht zuverlässig** mehrfache Zeilen mit identischen NULLs (NULL-Semantik in Unique-Constraints). Umsetzung muss das absichern, z. B. durch:

- **`variant_key`** (stabiler String aus `article_id` und normalisierten IDs, Schema z. B. `{article_id}|c={color_id oder '-'}|s={size_id oder '-'}`, exakt zu definieren im Migration-Review) mit **UNIQUE(article_id, variant_key)**, oder
- **partielle Unique-Indizes** (z. B. separater Index für «beide NULL») **plus** Index für belegte Dimensionen — konkretes Schema wählen die implementierenden Agenten im Migrations-Review.

### 8.2 Default-Listenpreis für neu generierte Varianten

- Varianten, die durch **Matrix** oder **Nachziehen** (z. B. neue Grösse XXL) neu entstehen: **`list_price_rappen` der Variante bleibt unset (`NULL`)**, sofern nicht explizit anders konfiguriert.
- **Effektiver Listenpreis** im Shop und in der Admin-Ansicht: wie heute in der Spez-Kette — **Fallback auf `MerchArticle.list_price_rappen`**.
- **Sonderpreis** (z. B. XXL teurer): Marketingchef setzt **`list_price_rappen` auf der Variante**; dieser Wert hat Vorrang vor dem Artikel-Default.
- **UI:** Nach einer Massenanlage optional ein **unaufdringlicher Hinweis** (Flash/Info-Box): «Neue Varianten nutzen den Artikel-Listenpreis; Sonderpreise pro Variante bei Bedarf anpassen.» Kein Blocker vor Speichern.

### 8.3 Bulk-Deaktivierung «alle Varianten mit Farbe X für Artikel Y»

- **MVP:** Im Service-Layer explizite Methoden (Namen belassen sich an `CONVENTIONS.md`), z. B.:
  - alle Varianten eines Artikels mit `color_id = X` auf `is_active = false` setzen;
  - analog für `size_id` falls nötig.
- **Cockpit-UI:** Pro Artikel-Detail eine **gezielte Aktion** (Button oder Dropdown) «Alle Varianten mit dieser Farbe deaktivieren» / «… mit dieser Grösse …» mit **Bestätigungsdialog** (Farbe-/Grösse-Name anzeigen).
- **Nice-to-have (später):** Mehrfachauswahl in einer Variantentabelle oder gleichwertige gefilterte Bulk-Aktion — **nicht** MVP-Pflicht, solange die obige Aktion existiert.

### 8.4 Reaktivierung und Matrix-Synchronität

- **Reaktivieren** einzelner Varianten oder des ganzen Artikels: weiterhin möglich; **`is_active = true`** stellt Live-Sicht für offene Runden wieder her (siehe §5).
- Wird eine Kombination wieder «angeboten», die schon als Zeile existiert aber inaktiv war: keine zweite Zeile anlegen — **bestehende Variante reaktivieren**.

---

## 9. Umsetzungsstand & Agent-Handoff (Stand 2026-05-16)

**Ziel für einen neuen Agenten:** Diese Sektion ist der Einstieg; danach [`merch.md`](merch.md), [`ARCHITECTURE.md`](../ARCHITECTURE.md), [`CONVENTIONS.md`](../CONVENTIONS.md), [`UI.md`](../UI.md).

### 9.1 Erledigt (Kern)

| Bereich | Kurz |
|--------|------|
| **DB** | Alembic **`c4e8a9012b71`**: Tabellen `merch_colors`, `merch_sizes`; `merch_variants.color_id`, `size_id`, `variant_key`; UNIQUE `(article_id, variant_key)`; Backfill aus `attributes`. |
| **Domain** | `MerchColor`, `MerchSize`, erweitertes `MerchVariant` in `backend/models/merch_v2.py`; `before_insert` setzt fehlenden `variant_key` aus FKs/Attributen. |
| **Keys** | `backend/utils/merch_variant_key.py`; Tests `tests/utils/test_merch_variant_key.py`. |
| **Sortiment** | `MerchSortimentService` schreibt Lookups + `variant_key`; nested Savepoints bei Lookup-Anlage. |
| **Stammdaten-UI** | `GET`/POST unter `/admin/merch-v2/lookups` (neu/umbenennen Farbe/Grösse), Template `templates/admin/merch_v2/lookups_hub.html`; Link im Sortiment-Hub. |
| **Bulk** | `MerchVariantBulkService` in `backend/services/merch_lookup_service.py` + `POST …/articles/<id>/variants/bulk-deactivate-color` bzw. `-size`; Panel im Artikel-Formular. |
| **Shop** | Mitglied: eine Karte pro Artikel, Ausführung per Dropdown; `static/js/v2/merch-round-shop.js`; Eager Loading `variant.article` / `color` / `size` in `backend/routes/merch.py`. |
| **Skripte** | `scripts/update_pwa_version.py` ohne Emojis (Windows-Konsole); `scripts/validate_railway_schema.py` um neue Tabellen/Spalten. |
| **Doku / PWA** | `docs/ARCHITECTURE.md`, `docs/UI.md`, `docs/CONVENTIONS.md`; PWA-Version **3.12.19**, `fingerprint_assets.py`. |

### 9.2 Noch offen / Spec-Abweichung (Folgearbeit)

- **§8.3:** Bulk ohne **Bestätigungsdialog** (nur POST); nach Wunsch `confirm()` oder Dialog nach `UI.md`.
- **§8.2:** Optionaler Hinweis (Flash), wenn neue Varianten nur Artikel-Listenpreis nutzen.
- **§4 / §5:** «Ganzen Artikel in die Runde» vs. bestehende pro-Varianten-Einlage — gegen `MerchRoundService` und Runden-UI prüfen.
- **§4:** Manuelles Verwalten einzelner Varianten ohne Schema-Text — nicht gebaut.

### 9.3 Tests

- `pytest tests/routes/test_merch_v2_routes.py` (Shop, Lookups, Bulk, …).

### 9.4 Deploy

- Migration auf Railway **vor** oder **mit** Deploy (`flask db upgrade`). Keine Drops in Production ohne Freigabe.


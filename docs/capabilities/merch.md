# Capability: Merch-Verwaltung

> **Zweck**: Der Verein verkauft eigens designte Merch-Artikel (T-Shirts, Polos, Caps, Accessoires) an seine Mitglieder. Die App deckt den vollstaendigen Prozess vom Sortiments-Anlegen ueber zeitlich begrenzte **Bestellrunden** bis zur Auslieferung und Bezahlung ab. Buchhalterische Endverarbeitung ist explizit *nicht* hier, sondern wird in der spaeteren Buchhaltungs-Capability ueber eine definierte Schnittstelle uebernommen.
>
> **Status**: Merch v2 wird in der App gebaut (`MERCH_V2_ENABLED` fuer Cutover); Konzept fuer Betrieb weiterhin autoritativ. **Owner**: Andreas. **Stand**: 2026-05-16.
>
> **Verwandte Docs**: `docs/STRATEGY_2026.md` (strategischer Rahmen, MVP-Punkt 4), `docs/initiatives/workspace-railway/PHASE_10_MERCH.md` (Phasen-Briefing fuer Cursor), `docs/capabilities/drive.md` (Drive-Integration fuer Bilder und Lieferantenbelege), `docs/capabilities/calendar.md` (Schwester-Capability, gleiche Doc-Konvention), `docs/ARCHITECTURE.md` (Stack-Detail), `docs/CONVENTIONS.md` (Code-Standards).

---

## 1. Strategie-Anker

Aus `STRATEGY_2026.md` als Source-of-Truth:

- *MVP-Punkt 4*: «Merch von Grund auf neu denken — nicht «alte Models polieren», sondern den **gesamten Prozess** durchdenken: Sortiment-Pflege, Bestell-Annahme, Bezahlung (TWINT?), Produktion/Beschaffung, Auslieferung an Mitglied, Lagerbestand, Statistik. Capability-Doc soll erst Prozess beschreiben, dann technische Umsetzung ableiten. AI-Optionen explizit pruefen (Bestell-Triage, Lager-Forecast).»
- *Datenhaltung*: Strukturierte App-Daten leben in Postgres. Belege und Bilder leben in Drive (Strategie-Aktualisierung gegenueber dem urspruenglichen «Repo-Pfad»-Eintrag fuer Merch-Bilder, siehe Sektion 8 und Decision Log).
- *AI-first*: pro Capability bewusste Pruefung. Hier explizit verworfen — siehe Sektion 17.
- *Reihenfolge*: Merch ist MVP, Buchhaltung ist Hauptbrocken danach. Merch fuehrt im MVP einen eigenen Forderungs-Stub mit definierter Schnittstelle an die spaetere Buchhaltung (Sektion 13).

Bewusst verworfen wurde, die Buchhaltung vorzuziehen oder beide parallel zu machen. Begruendung: Buchhaltung hat unbeantwortete strategische Vorlauf-Entscheide (n8n vs. reines Flask-Modul, TWINT-Acquirer Stripe vs. RaiseNow), die Merch nicht braucht. Merch erzeugt strukturell drei klar abgrenzbare Buchungs-Sachverhalte (Mitglieder-Forderung, Lieferanten-Eingangsrechnung, Subventions-Verbrauch), die eine spaetere Buchhaltung konsumiert, statt selbst zu erzeugen.

## 2. User Stories

| Rolle | Story |
|---|---|
| Marketingchef | «Ich pflege das Merch-Sortiment, lege neue Artikel mit Bild und Variantenschema an und archiviere alte.» |
| Marketingchef | «Ich eroeffne eine Bestellrunde mit gewaehlten Artikeln, kommunizierter Deadline und vereinbartem GV-Subventionsbetrag.» |
| Marketingchef | «Wenn die Frist vorbei ist, schliesse ich die Runde und erhalte eine sammelbestellungs-fertige Aggregat-Sicht pro Variante.» |
| Marketingchef | «Nach der Lieferantenbestellung trage ich die effektiven Lieferantenpreise und die definitiven Mitgliederpreise pro Variante ein und lade die Lieferantenrechnung in Drive hoch.» |
| Marketingchef | «Bei Wareneingang markiere ich die Runde als geliefert; pro Mitglied hake ich Abholung und Bezahlung ab.» |
| Mitglied | «Ich sehe im Shop alle aktuell laufenden Bestellrunden mit Sortiment, Preisen (vorerst geschaetzt), Subventionsbetrag und Frist.» |
| Mitglied | «Ich baue meinen Warenkorb pro Runde, bestaetige die Bestellung und kann sie waehrend der OPEN-Phase aendern oder stornieren.» |
| Mitglied | «Nach der Lieferantenbestellung sehe ich den definitiven Endbetrag und weiss, was ich bezahlen muss.» |
| Mitglied | «Im Dashboard sehe ich auf einen Blick, ob ich offene Merch-Bestellungen oder offene Forderungen habe.» |
| Schatzmeister | «Ich markiere Bestellungen als bezahlt, sobald das Geld eingegangen ist, und sehe pro Mitglied die offenen Forderungen.» |
| Vorstand | «Ich sehe pro Jahr Marge, Subventions-Verbrauch und Top-Artikel fuer den Jahresbericht und die GV.» |
| Admin | «Ich kann im Notfall fuer den Marketingchef einspringen und alle seine Aktionen ausfuehren.» |

## 3. Prozess End-to-End (Ist-Prozess)

Der Prozess ist durch die Vereinsrealitaet vorgegeben und wird von der Capability *abgebildet*, nicht erfunden. Reihenfolge:

1. **Sortimentspflege**: Marketingchef designt Logos, sucht passende Artikel bei einem Lieferanten (Webshop oder Mail), notiert sich den Listenpreis und legt den Artikel inklusive Variantenschema (z.B. Farbe + Groesse), Beschreibung, Bild und Lieferanten-Bezug in der App an.
2. **Runde eroeffnen**: Marketingchef erstellt eine neue Bestellrunde, waehlt die enthaltenen Artikel aus dem Sortiment aus, setzt die kommunizierte Deadline und den GV-Subventionsbetrag pro Mitglied. Nach internem Check (z.B. mit dem Vorstand) eroeffnet er die Runde.
3. **Mitglieder bestellen**: Mitglieder sehen die Runde im Shop, bauen ihren Warenkorb, bestaetigen die Bestellung. Aenderung und Stornierung sind moeglich, solange die Runde OPEN ist.
4. **Frist abgelaufen, Marketingchef schliesst manuell**: Mitglieder-Bestellungen sind eingefroren. Marketingchef sieht im Cockpit die aggregierte Sammelbestellung pro Variante.
5. **Lieferantenbestellung**: Marketingchef bestellt beim Lieferanten (Mail, Webshop, Telefon — je Lieferant unterschiedlich). Erst dabei wird der effektive Stueckpreis pro Variante (oft mit Mengenrabatt) bekannt.
6. **Effektivpreise erfassen**: Marketingchef traegt pro Variante den effektiven Lieferantenpreis und den definitiven Mitgliederpreis ein und laedt die Lieferantenrechnung in Drive hoch. Die Runde geht in den Status `ORDERED_AT_SUPPLIER`. Aus den eingetragenen Preisen werden die finalen Mitglieder-Forderungen berechnet und festgeschrieben.
7. **Wareneingang**: Lieferung trifft beim Verein ein, Marketingchef markiert die Runde als `DELIVERED`.
8. **Verteilung an Mitglieder**: Typischerweise gestaffelt ueber mehrere Anlaesse (Monatsessen, Verein-Treffen). Marketingchef hakt pro Mitglieds-Bestellung «abgeholt» ab.
9. **Bezahlung**: Mitglieder bezahlen (Cash, TWINT-Link an Marketingchef oder Schatzmeister, Ueberweisung). Marketingchef oder Schatzmeister markiert pro Bestellung «bezahlt».
10. **Runde schliessen**: Wenn alle Bestellungen einer Runde abgeholt und bezahlt sind, geht die Runde automatisch (oder per Klick) in `CLOSED`.

Der Verein fuehrt **kein Lager**. Es gibt keine «am Lager verfuegbar»-Logik, keine Sofort-Bestellung, keine Restposten-Verwaltung. Jede Bestellung gehoert zu genau einer Runde.

## 4. Lifecycle

Wir trennen zwei Lebenszyklen, weil sie unterschiedlichen Realitaeten folgen: die **Runde** beschreibt, was der Marketingchef tut; die **Bestellung pro Mitglied** beschreibt, was pro Person passiert. Die Lifecycles sind verzahnt, aber unabhaengig — eine Runde kann `DELIVERED` sein, waehrend einzelne Bestellungen noch `INVOICED` (nicht abgeholt) sind.

### 4.1 Round-Lifecycle

| Status | Bedeutung | Auslöser fuer Uebergang |
|---|---|---|
| `DRAFT` | Marketingchef bereitet die Runde vor: Titel, Artikel-Auswahl, kommunizierte Deadline, Subventionsbetrag pro Mitglied | Marketingchef legt Runde an |
| `OPEN` | Bestellfenster offen, Mitglieder sehen Sortiment der Runde und koennen bestellen, aendern, stornieren | Marketingchef oeffnet aktiv (`DRAFT → OPEN`) |
| `LOCKED` | Frist durch, Mitglieder-Bestellungen sind eingefroren, Marketingchef hat Aggregat-Sicht fuer Lieferantenbestellung | Marketingchef schliesst manuell (`OPEN → LOCKED`) |
| `ORDERED_AT_SUPPLIER` | Lieferantenbestellung ist raus, effektive Preise und Mitgliederpreise sind erfasst, Mitglieder-Forderungen sind festgeschrieben | Marketingchef bestaetigt nach Erfassung aller Preise (`LOCKED → ORDERED_AT_SUPPLIER`) |
| `DELIVERED` | Ware beim Verein eingetroffen, Verteilung kann beginnen | Marketingchef bestaetigt Wareneingang (`ORDERED_AT_SUPPLIER → DELIVERED`) |
| `CLOSED` | Alle Mitglieder-Bestellungen `PICKED_UP` und `PAID`; Runde im Archiv | Automatisch sobald alle Orders abgeschlossen, oder Marketingchef setzt manuell |
| `CANCELLED` | Komplettes Verwerfen der Runde (z.B. Lieferant springt ganz ab), alle zugehoerigen Orders werden auf `CANCELLED` gesetzt | Marketingchef bricht ab, Pflicht-Begruendung |

**Backwards-Uebergang** ausdruecklich erlaubt: `LOCKED → OPEN`. Wird genutzt, wenn der Lieferant z.B. eine Variante nicht liefern kann und Mitglieder ihre Bestellung anpassen sollen, statt die Runde zu kippen. Audit-Log dokumentiert mit Begruendungs-Pflicht. Beim Re-Open werden alle Orders auf `DRAFT` zurueckgesetzt, damit Mitglieder bewusst neu bestaetigen muessen.

Vorwaerts-Uebergaenge ab `ORDERED_AT_SUPPLIER` sind dagegen *nicht* zurueckdrehbar — ab dem Moment ist die Lieferantenbestellung in der echten Welt aufgegeben und die Forderungen sind bindend.

### 4.2 Order-Lifecycle (pro Mitglieds-Bestellung)

| Status | Bedeutung |
|---|---|
| `DRAFT` | Mitglied baut Warenkorb, hat noch nicht bestaetigt |
| `CONFIRMED` | Mitglied hat bestaetigt; bei Round-Lock wird die Order automatisch festgeschrieben |
| `INVOICED` | Effektivpreise stehen fest (Round → `ORDERED_AT_SUPPLIER`), Mitglied sieht Endbetrag |
| `PICKED_UP` | Mitglied hat Artikel erhalten, Marketingchef abgehakt |
| `PAID` | Bezahlt, Marketingchef oder Schatzmeister abgehakt |
| `CANCELLED` | Storniert (Mitglied selbst waehrend OPEN, oder Marketingchef bei Nicht-Lieferbarkeit) |

`PICKED_UP` und `PAID` sind unabhaengig — die Reihenfolge kann variieren (manchmal bezahlt das Mitglied beim Abholen, manchmal vorab per TWINT, manchmal Wochen spaeter). Beide Felder werden separat als `picked_up_at` und `paid_at` gefuehrt.

### 4.3 Verzahnung Round ↔ Order

| Round-Uebergang | Effekt auf zugehoerige Orders |
|---|---|
| `DRAFT → OPEN` | Mitglieder koennen erstmals Orders im Status `DRAFT`/`CONFIRMED` anlegen |
| `OPEN → LOCKED` | Alle `DRAFT`-Orders werden verworfen (nicht bestaetigte Warenkoerbe). Alle `CONFIRMED`-Orders bleiben `CONFIRMED` |
| `LOCKED → OPEN` (Re-Open) | Alle `CONFIRMED`-Orders werden auf `DRAFT` zurueckgesetzt — Mitglieder muessen aktiv neu bestaetigen |
| `LOCKED → ORDERED_AT_SUPPLIER` | Alle `CONFIRMED`-Orders werden auf `INVOICED` gesetzt, drei Betragsfelder werden befuellt |
| `ORDERED_AT_SUPPLIER → DELIVERED` | Keine automatische Order-Aenderung; Marketingchef hakt einzeln ab |
| `* → CANCELLED` | Alle aktiven Orders werden auf `CANCELLED` gesetzt; bereits bezahlte Orders behalten ihren Bezahl-Status (Geld bleibt nicht im System haengen, Schatzmeister muss ggf. zurueckueberweisen — Edge-Case wird im Capability-Doc als offener Punkt gefuehrt) |

## 5. Permissions

Permission-Matrix:

| Aktion | Marketingchef | Schatzmeister | Admin | Mitglied |
|---|---|---|---|---|
| Sortiment pflegen (Artikel/Varianten/Lieferanten anlegen, archivieren) | ja | nein | ja (Fallback) | nein |
| Runde anlegen, oeffnen, schliessen, Re-Open, Cancel | ja | nein | ja (Fallback) | nein |
| Effektivpreise erfassen, Lieferantenbeleg hochladen | ja | nein | ja (Fallback) | nein |
| Order als `PICKED_UP` markieren | ja | nein | ja (Fallback) | nein |
| Order als `PAID` markieren | ja | ja | ja | nein |
| Eigene Bestellung anlegen, aendern (waehrend OPEN), stornieren | nein | nein | nein | ja |
| Eigene Bestellung ansehen (alle Stadien) | nein | nein | nein | ja |
| Statistik pro Mitglied lesen | nein | ja | ja | nur eigene Daten |
| Statistik Vereinsuebersicht / Jahresreport | ja | ja | ja | nein |

Permission-Check im Code basiert auf:

- `current_user.funktion == Funktion.MARKETINGCHEF` (Funktion-Enum existiert bereits in `backend/models/member.py`)
- `current_user.funktion == Funktion.SCHATZMEISTER`
- `current_user.role == Role.ADMIN` als Fallback fuer alle Marketingchef-Aktionen

Empfohlene Decorator (siehe `backend/routes/admin.py` fuer `@admin_required` als Vorbild):

```python
def marketing_chief_or_admin_required(fn):
    """Erlaubt Marketingchef oder Admin."""
    ...

def treasury_or_admin_required(fn):
    """Erlaubt Marketingchef, Schatzmeister oder Admin (fuer Bezahl-Aktionen)."""
    ...
```

## 6. Datenmodell

Die heutigen vier Tabellen (`MerchArticle`, `MerchVariant`, `MerchOrder`, `MerchOrderItem`) werden ueberarbeitet. Vier neue Konzepte kommen hinzu: `MerchSupplier`, `MerchRound`, `MerchRoundItem` (Preis-Snapshot), und Drive-Integration fuer Bilder und Belege.

### 6.1 MerchSupplier

```python
class MerchSupplier(db.Model):
    __tablename__ = 'merch_suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(200))
    website_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    articles = db.relationship('MerchArticle', backref='supplier')
```

### 6.2 MerchArticle

```python
class MerchArticle(db.Model):
    __tablename__ = 'merch_articles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_suppliers.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    list_price_rappen = db.Column(db.Integer, nullable=False)  # Schaetzwert vom Lieferanten
    image_drive_file_id = db.Column(db.String(200))  # Google-Drive-File-ID
    variant_schema = db.Column(db.JSON)  # z.B. {"farbe": ["schwarz", "weiss"], "groesse": ["S", "M", "L"]}
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship('MerchVariant', backref='article', cascade='all, delete-orphan')
```

`variant_schema` definiert die Dimensionen des Artikels. Ein Artikel ohne Varianten (z.B. Geschirrtuch) hat `variant_schema = {}` und genau eine Variante mit `attributes = {}`.

### 6.3 MerchVariant

```python
class MerchVariant(db.Model):
    __tablename__ = 'merch_variants'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_articles.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    attributes = db.Column(db.JSON, nullable=False)  # z.B. {"farbe": "schwarz", "groesse": "M"}
    list_price_rappen = db.Column(db.Integer)  # Optional: ueberschreibt Article-Wert (z.B. XXL teurer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

`attributes` matcht das Schema des Artikels. App generiert beim Anlegen alle Kombinationen aus `variant_schema`; Marketingchef kann einzelne deaktivieren (`is_active=False`) oder Sonderpreis pro Variante setzen.

### 6.4 MerchRound

```python
class RoundStatus(Enum):
    DRAFT = 'DRAFT'
    OPEN = 'OPEN'
    LOCKED = 'LOCKED'
    ORDERED_AT_SUPPLIER = 'ORDERED_AT_SUPPLIER'
    DELIVERED = 'DELIVERED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'


class MerchRound(db.Model):
    __tablename__ = 'merch_rounds'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(RoundStatus), default=RoundStatus.DRAFT, nullable=False, index=True)
    deadline_communicated = db.Column(db.Date)  # Reiner Hinweis fuer Mitglieder, kein Trigger
    subsidy_per_member_rappen = db.Column(db.Integer, default=0, nullable=False)
    supplier_invoice_drive_file_id = db.Column(db.String(200))
    supplier_invoice_total_rappen = db.Column(db.Integer)  # Gesamtbetrag der Lieferantenrechnung (kann von Stueckpreis-Summe abweichen)
    notes = db.Column(db.Text)  # Marketingchef-Bemerkungen, z.B. Versandkosten-Differenz
    cancellation_reason = db.Column(db.Text)
    marketing_chief_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )

    opened_at = db.Column(db.DateTime)
    locked_at = db.Column(db.DateTime)
    ordered_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    round_items = db.relationship('MerchRoundItem', backref='round', cascade='all, delete-orphan')
    orders = db.relationship('MerchOrder', backref='round', cascade='all, delete-orphan')
```

### 6.5 MerchRoundItem (Preis-Snapshot pro Runde + Variante)

```python
class MerchRoundItem(db.Model):
    """Preis-Snapshot pro Runde und Variante. Erlaubt unterschiedliche Effektiv- und Mitgliederpreise je Runde."""
    __tablename__ = 'merch_round_items'

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_rounds.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_variants.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    list_price_snapshot_rappen = db.Column(db.Integer, nullable=False)  # aus Variant/Article zum Round-Anlege-Zeitpunkt
    effective_supplier_price_rappen = db.Column(db.Integer)  # nach ORDERED_AT_SUPPLIER
    member_price_rappen = db.Column(db.Integer)  # nach ORDERED_AT_SUPPLIER

    __table_args__ = (
        db.UniqueConstraint('round_id', 'variant_id', name='uq_round_variant'),
    )
```

Ein `MerchRoundItem` wird beim Round-Anlegen pro ausgewaehlter Variante erzeugt, mit `list_price_snapshot_rappen` befuellt. Die Felder `effective_supplier_price_rappen` und `member_price_rappen` werden beim Uebergang `LOCKED → ORDERED_AT_SUPPLIER` befuellt. Vorher zeigt die App bei Mitglieder-Bestellungen den Listenpreis-Snapshot mit Hinweis «Preis vorlaeufig».

### 6.6 MerchOrder

```python
class OrderStatus(Enum):
    DRAFT = 'DRAFT'
    CONFIRMED = 'CONFIRMED'
    INVOICED = 'INVOICED'
    PICKED_UP = 'PICKED_UP'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'


class MerchOrder(db.Model):
    __tablename__ = 'merch_orders'

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_rounds.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False, index=True)

    # Drei Betraege, befuellt beim Uebergang LOCKED → ORDERED_AT_SUPPLIER
    gross_amount_rappen = db.Column(db.Integer)
    subsidy_amount_rappen = db.Column(db.Integer)
    member_amount_due_rappen = db.Column(db.Integer)

    confirmed_at = db.Column(db.DateTime)
    invoiced_at = db.Column(db.DateTime)
    picked_up_at = db.Column(db.DateTime)
    picked_up_by_member_id = db.Column(db.Integer, db.ForeignKey('members.id'))  # wer hat abgehakt
    paid_at = db.Column(db.DateTime)
    paid_by_member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship('MerchOrderItem', backref='order', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('round_id', 'member_id', name='uq_round_member'),
    )
```

`UniqueConstraint(round_id, member_id)` erzwingt: pro Mitglied genau eine Bestellung pro Runde. Das Mitglied kann seinen Warenkorb beliebig oft veraendern, aber es ist immer dieselbe Bestellung.

Bestellnummer entfaellt — die Kombination Runde + Mitglied ist eindeutig genug. Falls eine sprechende Nummer im UI gewuenscht ist, wird sie aus `<round_id>-<member_id>` formatiert.

### 6.7 MerchOrderItem

```python
class MerchOrderItem(db.Model):
    __tablename__ = 'merch_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_orders.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    round_item_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_round_items.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    quantity = db.Column(db.Integer, nullable=False)

    # Preis-Snapshot zur Bestaetigungszeit, ueberschrieben beim Uebergang INVOICED
    unit_price_at_confirm_rappen = db.Column(db.Integer, nullable=False)
    unit_price_final_rappen = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('order_id', 'round_item_id', name='uq_order_round_item'),
    )
```

### 6.8 Indexes

```sql
CREATE INDEX ix_merch_rounds_status ON merch_rounds (status);
CREATE INDEX ix_merch_orders_round_status ON merch_orders (round_id, status);
CREATE INDEX ix_merch_orders_member ON merch_orders (member_id);
CREATE UNIQUE INDEX uq_round_variant ON merch_round_items (round_id, variant_id);
CREATE UNIQUE INDEX uq_round_member ON merch_orders (round_id, member_id);
```

### 6.9 Migrationen vom heutigen Modell

**Strategie (Entscheid 2026-05-15)**: Phase 10 fasst die Bestandsdaten *nicht* an. Die alten Tabellen werden einmalig auf `_legacy`-Suffix umbenannt und bleiben sonst unveraendert. Die neuen Tabellen werden mit den sauberen Hauptnamen frisch angelegt. Eine Daten-Migration aus den `_legacy`-Tabellen erfolgt als **separate, spaetere Phase** mit echten Production-Daten — oder wird ganz weggelassen, falls die historischen Bestellungen nicht mehr gebraucht werden.

Begruendung: Implementations-Phase und Daten-Migrationsphase haben unterschiedliche Risiko-Profile; die Trennung erlaubt Cursor, sich in Phase 10 voll auf das neue Modell zu konzentrieren. Die Bestand-Migration wird mit einer Production-Daten-Probe in Ruhe durchgespielt, statt unter Phase-10-Druck.

**Migrations-Schritte fuer Phase 10:**

1. **Backup** der Production-DB vor Beginn (Standard-Vorsicht).
2. **Rename-Migration**: `merch_articles` → `merch_articles_legacy`, `merch_variants` → `merch_variants_legacy`, `merch_orders` → `merch_orders_legacy`, `merch_order_items` → `merch_order_items_legacy`. Reine SQL-Renames, keine Datenaenderung.
3. **Code-Anpassung der alten Models**: `MerchArticle`, `MerchVariant`, `MerchOrder`, `MerchOrderItem` bekommen `__tablename__ = 'merch_articles_legacy'` etc. (kleiner Refactor). Optional: Klassennamen umbenennen auf `MerchArticleLegacy` etc., um Verwechslung mit den neuen Modellen zu vermeiden. Bestand-Routes (`/admin/merch/...` alt, `/merch/order` alt) verweisen weiter auf die `_legacy`-Tabellen, bleiben hinter dem alten Pfad-Prefix erreichbar fuer Lesezugriff (Bestellhistorie der Mitglieder).
4. **Neue Tabellen anlegen**: `merch_suppliers`, `merch_articles`, `merch_variants`, `merch_rounds`, `merch_round_items`, `merch_orders`, `merch_order_items` mit dem in Sektion 6 beschriebenen Schema. Alle Constraints (FKs, Unique-Indexes) wie spezifiziert.
5. **Neue Models und Routes** auf den neuen Tabellen entwickeln (siehe Sektion 10, 11).
6. **Feature-Flag-Cutover**: `MERCH_V2_ENABLED=true` schaltet die neue Capability scharf. Alte Routes werden zu Lesezugriff degradiert (z.B. `/merch/legacy/orders` als Read-only-Sicht der historischen Bestellungen) oder komplett deaktiviert, je nach Entscheid (siehe Sektion 23).

**Spaetere, separate Bestand-Migrationsphase (nicht Phase 10):**

Wird gestartet, sobald Phase 10 produktiv stabilisiert ist. Inhalt:

- Inspektion der `_legacy`-Tabellen mit Production-Daten-Kopie.
- Entscheid: «Bestand wird migriert» oder «Bestand wird verworfen». Beides legitim.
- Falls Migration: Migrations-Script `scripts/migrate_merch_legacy_to_v2.py`, das pro `_legacy`-Order eine Pseudo-Round «Historische Bestellungen vor Phase 10» anlegt, Lieferanten als «Unbekannt» (oder manuelle Zuordnung), Variant-Attributes aus alten `color`/`size`-Feldern.
- Nach erfolgreicher Migration und Validierung: Drop der `_legacy`-Tabellen via separate Alembic-Migration.

Lokal Phase-10-Migrationen testen via `flask db upgrade && flask db downgrade && flask db upgrade`. Rename-Migration muss reversibel sein (Downgrade benennt zurueck).

## 7. Pricing & Subvention

### 7.1 Preisstufen pro Variante in einer Runde

Drei Werte:

- **Listenpreis** (`MerchVariant.list_price_rappen` oder `MerchArticle.list_price_rappen` als Fallback) — Schaetzwert, beim Anlegen vom Marketingchef erfasst. Wird beim Round-Anlegen als Snapshot in `MerchRoundItem.list_price_snapshot_rappen` festgehalten.
- **Effektiver Lieferantenpreis** (`MerchRoundItem.effective_supplier_price_rappen`) — der reale Stueckpreis nach Sammelbestellung beim Lieferanten, oft mit Mengenrabatt. Pro Runde unterschiedlich.
- **Mitgliederpreis** (`MerchRoundItem.member_price_rappen`) — der Verkaufspreis an Mitglieder, vom Marketingchef pro Variante manuell festgesetzt. Differenz zum Effektivpreis ist die Verein-Marge pro Stueck.

### 7.2 Berechnung pro Bestellung

Sobald die Runde in `ORDERED_AT_SUPPLIER` uebergeht, werden pro `MerchOrder` drei Betraege festgeschrieben:

```
Bruttobetrag      = Σ (member_price_rappen × quantity) für alle order_items
Subventionsabzug  = min(round.subsidy_per_member_rappen, Bruttobetrag)
Mitglieder-Forderung = Bruttobetrag − Subventionsabzug
```

Subvention deckt maximal den Bestellbetrag — wer fuer 12 CHF bestellt und 15 CHF Subvention zur Verfuegung haette, zahlt 0, der Rest verfaellt. Wer nicht bestellt, bekommt nichts (kein Auszahlungsanspruch).

### 7.3 Beispielrechnung

Runde «Polo Sommer 2026», Subvention 15 CHF pro Mitglied:

- Polo schwarz M: Effektiv 18.50, Member 25.00
- Polo schwarz L: Effektiv 19.20, Member 25.00 (gleicher Preis trotz hoeherer Lieferantenkosten)
- Cap weiss: Effektiv 8.00, Member 12.00

Mitglied A bestellt 1× Polo schwarz M + 1× Cap weiss:
- Brutto = 25.00 + 12.00 = 37.00
- Subvention = min(15, 37) = 15.00
- Forderung = 22.00

Mitglied B bestellt 1× Cap weiss:
- Brutto = 12.00
- Subvention = min(15, 12) = 12.00
- Forderung = 0.00 (Rest 3 CHF verfaellt)

Verein-Sicht zur Runde:
- Marge Polo schwarz M = (25 − 18.50) × Stueckzahl
- Marge Cap weiss = (12 − 8) × Stueckzahl
- Subventions-Verbrauch = Σ subsidy_amount_rappen aller Orders
- Vereins-Netto = Σ Margen − Subventions-Verbrauch

### 7.4 Edge Cases

- *Mitglied tritt zwischen Bestellung und Lieferung aus*: Order bleibt aktiv. Marketingchef entscheidet manuell (entweder gegen Bezahlung ausliefern oder stornieren); kein Auto-Refund-Mechanismus im MVP.
- *Effektivpreis-Erfassung unvollstaendig*: Uebergang `LOCKED → ORDERED_AT_SUPPLIER` ist nur moeglich, wenn alle `MerchRoundItem`-Eintraege `effective_supplier_price_rappen` und `member_price_rappen` befuellt haben.
- *Lieferantenrechnung weicht von Stueckpreis-Summe ab*: `MerchRound.supplier_invoice_total_rappen` darf separat erfasst werden (z.B. inkl. Versand und MwSt). Differenz zur App-berechneten Summe wird im Marketingchef-Cockpit angezeigt; Behandlung kommt mit der Buchhaltungs-Capability.
- *Mitglied bestellt 0-Stueck-Items oder loescht den Warenkorb komplett*: Order wird auf `CANCELLED` gesetzt (gezaehlt nicht in der Sammelbestellung).

## 8. Bild-Speicherung (Drive + Backend-Proxy)

### 8.1 Upload-Pfad

Marketingchef laedt im Artikel-Form ein Bild hoch. Backend speichert es ueber den bestehenden `DriveStorageService` in einem definierten Drive-Ordner (z.B. `Verein/Merch/Bilder/`). Die Drive-File-ID wird in `MerchArticle.image_drive_file_id` gespeichert.

### 8.2 Proxy-Endpoint mit Cache

Frontend rendert Artikel-Bilder ueber einen Backend-Endpoint:

```
GET /merch/image/<article_id>
```

Backend:

1. Liest `image_drive_file_id` aus DB.
2. Prueft lokalen Cache (Datei-Cache mit ETag oder Redis-Cache mit Expiry).
3. Falls Miss: holt Datei via `DriveStorageService.download()`, cached lokal.
4. Liefert Datei mit Content-Type aus DB-Metadaten und langem `Cache-Control: public, max-age=86400`.
5. Setzt ETag basierend auf Drive-File-Modified-Time.

Cache-Invalidation: bei Bild-Update (neuer Upload an existierendem Artikel) wird der lokale Cache-Eintrag explizit geloescht.

### 8.3 Sicherheit

Der Endpoint ist `@login_required` — Bilder sind nur Mitgliedern und Vorstand sichtbar, nicht oeffentlich. Konsistent mit dem Mitglieder-Shop, der ohnehin nur eingeloggten Mitgliedern offen steht.

### 8.4 Bestandsbilder

Phase 10 fasst die heutigen Bilder unter `static/img/merch/` *nicht* an. Sie verbleiben dort, solange die `_legacy`-Tabellen aktiv sind und ggf. eine Read-only-Bestand-Sicht angeboten wird (siehe Sektion 6.9).

Falls in der spaeteren Bestand-Migrationsphase (Sektion 6.9) Artikel aus `_legacy` ins neue Modell uebernommen werden, koennen die zugehoerigen Bilder im selben Migrations-Script nach Drive uebertragen werden:

1. Pro `_legacy`-Artikel mit gesetzter `image_url` wird die Datei aus `static/img/merch/` gelesen, via `DriveStorageService` hochgeladen.
2. `image_drive_file_id` am neuen `MerchArticle`-Datensatz wird gesetzt.
3. Nach erfolgreichem Run koennen die alten Repo-Bilder geloescht werden (separater Commit).

`STRATEGY_2026.md` Source-of-Truth-Karte ist mit der Capability bereits aktualisiert (Bilder via Drive mit Backend-Proxy).

## 9. Lieferantenbeleg-Speicherung

Marketingchef laedt nach Lieferantenbestellung den Beleg (PDF oder Foto) in der Round-Detail-Seite hoch. Backend speichert via `DriveStorageService` in einem definierten Drive-Ordner (z.B. `Verein/Merch/Lieferanten-Belege/`). `MerchRound.supplier_invoice_drive_file_id` wird gesetzt.

Anzeige im Cockpit: Link «Beleg in Drive oeffnen» (Drive-Web-URL aus File-ID berechnet). Im MVP keine eigene Beleg-Vorschau in der App — Drive-Webview reicht.

Wenn die Buchhaltungs-Capability spaeter Belege referenziert (Eingangsrechnungs-Tabelle), wird die Drive-File-ID am Round als FK in die Buchhaltungs-Belegtabelle uebernommen — kein Doppel-Upload.

## 10. Service-Layer

Vier Service-Klassen, jeweils unter `backend/services/`. Alle nach dem Pattern in `docs/CONVENTIONS.md` (Static-Methods, strukturierte Rueckgaben, Logging, Konfiguration aus `current_app.config`).

### 10.1 MerchSortimentService

Stamm-Daten: Lieferanten, Artikel, Varianten, Bilder.

```python
class MerchSortimentService:
    @staticmethod
    def create_supplier(name, contact_email, website_url, notes) -> dict: ...
    @staticmethod
    def create_article(name, description, supplier_id, list_price_rappen, variant_schema) -> dict: ...
    @staticmethod
    def upload_article_image(article_id, file_storage) -> dict: ...
    @staticmethod
    def archive_article(article_id) -> dict: ...
    @staticmethod
    def update_variant_active(variant_id, is_active) -> dict: ...
    @staticmethod
    def regenerate_variants_from_schema(article_id) -> dict: ...
```

### 10.2 MerchRoundService

Lifecycle-Maschine fuer Runden. Erlaubte Uebergaenge sind hart kodiert; jeder Uebergang wirft `MerchRoundError` bei Verletzung.

```python
class MerchRoundService:
    @staticmethod
    def create_round(title, description, deadline, subsidy_per_member_rappen, variant_ids, marketing_chief_id) -> dict: ...
    @staticmethod
    def open_round(round_id) -> dict: ...
    @staticmethod
    def lock_round(round_id) -> dict: ...
    @staticmethod
    def reopen_round(round_id, reason) -> dict: ...  # LOCKED → OPEN
    @staticmethod
    def set_supplier_prices(round_id, prices: list[dict]) -> dict: ...
    @staticmethod
    def transition_to_ordered(round_id) -> dict: ...  # LOCKED → ORDERED_AT_SUPPLIER, befuellt Order-Betraege
    @staticmethod
    def upload_supplier_invoice(round_id, file_storage, total_rappen) -> dict: ...
    @staticmethod
    def transition_to_delivered(round_id) -> dict: ...
    @staticmethod
    def cancel_round(round_id, reason) -> dict: ...
    @staticmethod
    def get_supplier_aggregate(round_id) -> list[dict]: ...  # fuer Cockpit Sammelbestellungs-Sicht
    @staticmethod
    def get_round_statistics(round_id) -> dict: ...
```

### 10.3 MerchOrderService

Bestell-Logik fuer Mitglieder.

```python
class MerchOrderService:
    @staticmethod
    def get_or_create_draft_order(round_id, member_id) -> MerchOrder: ...
    @staticmethod
    def update_order_items(order_id, items: list[dict]) -> dict: ...
    @staticmethod
    def confirm_order(order_id) -> dict: ...
    @staticmethod
    def cancel_order(order_id, by_member_id, reason=None) -> dict: ...
    @staticmethod
    def mark_picked_up(order_id, by_member_id) -> dict: ...
    @staticmethod
    def mark_paid(order_id, by_member_id) -> dict: ...
    @staticmethod
    def calculate_amounts(order_id) -> dict: ...  # Brutto/Subv./Forderung
```

### 10.4 MerchImageService

Drive-Proxy mit Cache.

```python
class MerchImageService:
    @staticmethod
    def get_article_image(article_id) -> tuple[bytes, str, str]:
        """Liefert (content, content_type, etag). Holt aus Cache oder Drive."""
        ...
    @staticmethod
    def invalidate_cache(article_id) -> None: ...
```

Cache-Implementation entweder Datei-Cache unter `tmp/merch_image_cache/` oder Redis (vorhanden auf Railway). Empfehlung: Redis mit 24h-TTL, weil das schon fuer andere Zwecke aufgesetzt ist.

## 11. Routes

### 11.1 Marketingchef-Cockpit

```
GET  /admin/merch                              → Cockpit-Uebersicht aller Runden
GET  /admin/merch/rounds/new                   → Form: neue Runde anlegen
POST /admin/merch/rounds                       → Anlegen
GET  /admin/merch/rounds/<round_id>            → Round-Detail (3 Modi je nach Status)
POST /admin/merch/rounds/<round_id>/open       → DRAFT → OPEN
POST /admin/merch/rounds/<round_id>/lock       → OPEN → LOCKED
POST /admin/merch/rounds/<round_id>/reopen     → LOCKED → OPEN (mit Begruendung)
POST /admin/merch/rounds/<round_id>/prices     → Effektivpreise erfassen
POST /admin/merch/rounds/<round_id>/order-supplier → LOCKED → ORDERED_AT_SUPPLIER
POST /admin/merch/rounds/<round_id>/invoice    → Lieferantenbeleg-Upload
POST /admin/merch/rounds/<round_id>/delivered  → ORDERED → DELIVERED
POST /admin/merch/rounds/<round_id>/cancel     → → CANCELLED (mit Begruendung)
POST /admin/merch/rounds/<round_id>/close      → DELIVERED → CLOSED
GET  /admin/merch/rounds/<round_id>/aggregate.csv → CSV-Export Sammelbestellung

GET  /admin/merch/articles                     → Sortimentsuebersicht
GET  /admin/merch/articles/new                 → Neuer Artikel
POST /admin/merch/articles                     → Anlegen
GET  /admin/merch/articles/<article_id>        → Artikel-Detail mit Varianten
POST /admin/merch/articles/<article_id>/edit   → Bearbeiten
POST /admin/merch/articles/<article_id>/archive
POST /admin/merch/articles/<article_id>/image  → Bild-Upload nach Drive

GET  /admin/merch/suppliers                    → Lieferantenliste
POST /admin/merch/suppliers                    → Neuer Lieferant

GET  /admin/merch/orders/<order_id>            → Order-Detail (Marketingchef-Sicht)
POST /admin/merch/orders/<order_id>/picked-up  → markieren
POST /admin/merch/orders/<order_id>/paid       → markieren

GET  /admin/merch/statistics                   → Vereins-Jahresuebersicht
```

### 11.2 Mitglieder-Shop und Bestellung

```
GET  /merch                                    → Shop: alle aktiven Runden + eigene Bestellungen
GET  /merch/rounds/<round_id>                  → Sortiment der Runde + eigener Warenkorb
POST /merch/rounds/<round_id>/cart             → Warenkorb-Item add/update/remove
POST /merch/rounds/<round_id>/confirm          → CONFIRMED
POST /merch/rounds/<round_id>/cancel           → eigene Order CANCELLED (waehrend OPEN)

GET  /merch/orders                             → Eigene Bestellhistorie
GET  /merch/orders/<order_id>                  → Detail eigener Bestellung
```

### 11.3 Bild-Proxy

```
GET /merch/image/<article_id>  →  liefert Drive-Bild via Backend-Proxy
```

`@login_required`. Cache-Header gesetzt.

### 11.4 Permissions in Routes

Alle `/admin/merch/...`-Routes mit `@marketing_chief_or_admin_required`. `paid`-Routes zusaetzlich `@treasury_or_admin_required`. Member-Routes mit `@login_required`. CSRF aktiv. Rate-Limit auf POST-Endpoints (`10 per minute`).

## 12. UX

### 12.1 Marketingchef-Cockpit

Drei UI-Komponenten:

**Cockpit-Uebersicht** (`/admin/merch`):

- Tabs: «Aktive Runden», «Sortiment», «Lieferanten», «Statistik».
- Aktive Runden: Liste aller Runden mit Status ≠ `CLOSED`, sortiert nach Status (DRAFT → OPEN → LOCKED → ORDERED → DELIVERED). Pro Runde Karte mit Titel, Status-Chip, Anzahl Bestellungen, naechste faellige Aktion (z.B. «3 Bestellungen warten auf Verteilung»).
- Hinweis-Banner fuer ueberfaellige Runden («Frist war vor 3 Tagen, schliessen?»).

**Round-Detail mit drei Modi je nach Status**:

- *Modus A — Sammelbestellung vorbereiten* (sichtbar wenn Status = `LOCKED`): Aggregat-Tabelle pro Variante (Spalten: Artikel, Variante, Stueckzahl, Listenpreis-Snapshot, Bestellungs-Notiz). Buttons «Tabelle kopieren» (formatierter Text in Clipboard), «CSV exportieren». Zusatz: Gruppierung optional pro Lieferant.
- *Modus B — Effektivpreise erfassen* (sichtbar wenn Status = `LOCKED` oder `ORDERED_AT_SUPPLIER`): Tabelle mit allen Round-Items, je Zeile zwei Eingabefelder (Effektiver Lieferantenpreis, Mitgliederpreis). Live-Berechnung der Spalten «Lieferanten-Gesamt» (Stueckzahl × Effektivpreis) und «Member-Gesamt» (Stueckzahl × Memberpreis) und «Marge». Button «Lieferantenbestellung bestaetigen» (Uebergang in `ORDERED_AT_SUPPLIER`) erst aktiv, wenn alle Preise befuellt sind.
- *Modus C — Verteilung & Bezahlung* (sichtbar wenn Status ≥ `ORDERED_AT_SUPPLIER`): Tabelle aller Mitglieder-Orders dieser Runde (Spalten: Mitglied, Brutto, Subvention, Forderung, Abgeholt, Bezahlt). Pro Zeile zwei Toggle-Buttons fuer Picked-Up/Paid. Filter nach «nicht abgeholt» / «nicht bezahlt». Lieferanten-Beleg-Upload-Slot oben.

**Sortimentspflege**:

- Artikel-Liste mit Filter «aktiv / archiviert».
- Artikel-Form: Name, Beschreibung, Lieferant (Dropdown aus `MerchSupplier`), Listenpreis, Bild-Upload (geht nach Drive ueber Bild-Service), Variant-Schema-Editor (Keys + Werteliste).
- Beim Speichern: App generiert `MerchVariant`-Eintraege fuer alle Kombinationen, Marketingchef kann einzelne deaktivieren oder Sonderpreise setzen.

### 12.2 Mitglieder-Shop

`/merch`-Seite zeigt drei Sektionen:

- **«Aktuelle Bestellrunden»**: pro aktiver Runde (Status `OPEN`) eine Karte mit Titel, Hero-Bild des ersten Artikels, Frist, Subventionsbetrag, Button «In dieser Runde bestellen». Mehrere parallele Runden untereinander.
- **«Bestellungen in Bearbeitung»**: eigene Orders in Status `CONFIRMED`/`INVOICED`/`PICKED_UP` (also alles, was noch nicht `PAID` ist). Pro Order: Runden-Titel, Status, ggf. offener Forderungsbetrag.
- **«Abgeschlossene Bestellungen»**: Historie, kollabiert per Default.

### 12.3 Bestellungs-Flow

Klick auf «In dieser Runde bestellen» fuehrt zu `/merch/rounds/<id>`:

- Sortiment der Runde als Karten (Bild, Name, Beschreibung, Listenpreis, Hinweis «Definitiver Preis steht nach Lieferantenbestellung fest»).
- Klick auf Artikel oeffnet Konfigurator: Variantenwahl (Dropdowns je nach Schema), Stueckzahl, Button «Zum Warenkorb hinzufuegen».
- Warenkorb-Block am Seitenende mit allen aktuellen Items, Brutto-Summe, geschaetzte Subvention, geschaetzte Forderung. Buttons «Bestellung bestaetigen» (CONFIRMED) und «Stornieren».
- Solange Runde `OPEN` ist: jederzeit aenderbar.
- Sobald Runde `LOCKED` ist: nur noch Anzeige, Hinweis «Bestellung ist eingefroren, definitive Preise folgen nach Lieferantenbestellung».
- Sobald Runde `ORDERED_AT_SUPPLIER` ist: definitive Preise sichtbar, Forderungsbetrag final.
- Sobald Runde `DELIVERED` ist: Hinweis «Abholung bei naechstem Anlass» (oder spezifischer Text, falls der Marketingchef das im Round-Description-Feld festgehalten hat).

### 12.4 Dashboard-Card

Auf dem Mitglieder-Dashboard (`templates/dashboard/index.html`) eine zusaetzliche Karte «Merch» mit drei Zustaenden:

- *Keine offenen Aktionen*: kompakter Hinweis «Keine offenen Merch-Bestellungen».
- *Offene Bestellung in laufender Runde*: «Du hast eine Bestellung in Runde X (Status: …)», Link zur Detailseite.
- *Offene Forderung*: «Endbetrag CHF X aus Runde Y, noch nicht bezahlt», Link zur Detailseite.

Bei mehreren Runden parallel: jede mit eigener Mini-Zeile.

### 12.5 Legacy-Receivables-Sicht (Notfall-Nachschlag)

Solange die `_legacy`-Tabellen existieren (siehe Sektion 6.9), gibt es genau eine Backend-Sicht, die ihre Daten nutzt: eine Read-only-Aggregat-Tabelle pro Mitglied, damit im Notfall nachvollzogen werden kann, wer aus der alten Welt noch wieviel offen hat.

**Pfad**: `/admin/merch/legacy-receivables`. Permission: Marketingchef, Schatzmeister, Admin.

**Uebersicht** (eine Zeile pro Mitglied mit mindestens einer Bestellung in `merch_orders_legacy`):

| Mitglied | Anzahl Bestellungen | Total Mitgliederpreis (CHF) | Letzter Bestelltag |
|---|---|---|---|

Sortiert standardmaessig nach Total absteigend. Ein Klick auf eine Zeile oeffnet die Detail-Sicht.

**Detail-Sicht** (`/admin/merch/legacy-receivables/<member_id>`):

| Datum | Bestellnr | Status (alt) | Artikel (kurze Zusammenfassung) | Betrag (CHF) |
|---|---|---|---|---|

Bewusst weggelassen: **kein Bezahl-Status**, weil das alte Modell keinen kannte. Status (`BESTELLT`/`WIRD_GELIEFERT`/`GELIEFERT`) bezieht sich nur auf Lieferung. Wer was bezahlt hat, weiss der Schatzmeister aus seinen externen Aufzeichnungen (Excel, WhatsApp); die App liefert nur die Bestell-Beträge zum Abgleich.

Bewusst weggelassen: jede Schreib-Aktion. Keine «als bezahlt»-Markierung, keine Stornierung, keine Mutation. Wenn der Schatzmeister eine alte Bestellung «klären» will, macht er das ausserhalb der App.

Diese Sicht entfaellt komplett, sobald die Bestand-Migrationsphase entscheidet, die Bestandsdaten zu verwerfen und die `_legacy`-Tabellen zu droppen.

### 12.6 Sprache und Stil

DB-Spalten-Namen englisch (`merch_round`, `member_amount_due_rappen`), UI-Labels deutsch in schweizerischer Schreibweise (Doppel-S statt Eszett, Guillemets «…»). BEM-Klassen und Tokens gemaess `docs/UI.md`. Lucide-Icons (Sprite) konsistent mit existierender Admin-Merch-UI.

## 13. Forderungs-Stub und Buchhaltungs-Schnittstelle

### 13.1 Was Merch erzeugt

Merch fuehrt einen eigenen Forderungs-Stub und stellt drei klar abgrenzbare Sachverhalte bereit, die spaeter von der Buchhaltung konsumiert werden:

| Datenpunkt | Quelle | Buchhaltungs-Konsequenz |
|---|---|---|
| **Mitglieder-Forderung** | `MerchOrder.member_amount_due_rappen`, `paid_at` | Forderung an Mitglied, bei Bezahlung Eingang verbuchen |
| **Lieferanten-Eingangsrechnung** | `MerchRound.supplier_invoice_total_rappen`, `supplier_invoice_drive_file_id`, `MerchSupplier` | Eingangsrechnung mit verlinktem Beleg, Verbindlichkeit gegenueber Lieferant |
| **Subventions-Verbrauch** | `MerchOrder.subsidy_amount_rappen` summiert pro Runde / pro Jahr | Aufwand «Mitgliederfoerderung Merch», Belastung Vereinskasse |

Felder sind so designed, dass Buchhaltung sie nicht erst transformieren muss: Betraege in Rappen als `int`, Datumsfelder als `DateTime`, Referenzen als FK auf bestehende Models.

### 13.2 Was Merch explizit nicht macht

- Keinen Kontenplan, keine Soll/Haben-Buchungen.
- Keine doppelte Buchfuehrung.
- Keine Steuerthemen (MwSt-Differenzierung, Vorsteuer, Mehrwertsteuer-Reports).
- Keinen Jahresabschluss.
- Keine TWINT-Webhook-Integration (Bezahl-Markierung manuell im MVP).
- Keine BillBro-Integration (BillBro ist event-spezifisch, deckt Merch-Forderungen nicht ab — siehe Decision Log).

Diese Themen kommen mit der Buchhaltungs-Capability (`docs/initiatives/workspace-railway/PHASE_04_*.md` bzw. spaetere Phase, abhaengig von n8n-vs-Flask-Entscheid in `STRATEGY_2026.md`).

### 13.3 Zukuenftige Uebergabe

Wenn die Buchhaltungs-Capability live geht:

- Pro `MerchOrder` mit `member_amount_due_rappen > 0` und `paid_at IS NULL` wird ein Buchhaltungs-Forderungseintrag erstellt (Migrations-Script, einmalig fuer Bestand).
- Pro `MerchRound` mit `supplier_invoice_drive_file_id` wird ein Eingangsrechnungs-Eintrag erstellt mit verknuepftem Drive-Beleg.
- Pro `MerchOrder.subsidy_amount_rappen > 0` wird ein Aufwand-Buchungssatz «Mitgliederfoerderung Merch» erzeugt, summiert pro Runde.
- Das Bezahl-Markierungs-UI in Merch bleibt erhalten, wirft aber zusaetzlich einen Eingang-verbuchen-Trigger an die Buchhaltung.

Bis dahin: Merch fuehrt Forderungen autonom, Schatzmeister markiert manuell, kein Datenfluss in andere Module.

## 14. Statistik

Drei Sichten, alle live aus den Tabellen berechnet (keine Aggregat-Materialisierung):

### 14.1 Pro Runde (im Cockpit, Round-Detail-Seite)

Live-Werte:

- Anzahl Bestellungen / Anzahl Besteller
- Brutto-Summe ueber alle Orders der Runde
- Subventions-Verbrauch (Σ subsidy_amount_rappen)
- Effektive Lieferantenkosten (Σ effective_supplier_price × Stueckzahl)
- Marge (Σ (member_price − effective_supplier_price) × Stueckzahl)
- Vereins-Netto (Marge − Subventions-Verbrauch)
- Stueckzahl pro Variante (Sammelbestellungs-Ansicht reuse)
- Anteil bezahlt / nicht bezahlt
- Anteil abgeholt / nicht abgeholt

### 14.2 Pro Mitglied (im Admin-Mitglieder-Detail)

Im bestehenden Admin-Member-Detail eine Sektion «Merch-Historie»:

- Liste aller `MerchOrder` des Mitglieds mit Runde, Status, Betrag, Bezahl-Datum
- Total bezahlt (Σ member_amount_due bei Status PAID)
- Total Subventions-Verbrauch (Σ subsidy_amount)
- Aktuell offene Forderungen

### 14.3 Vereins-Jahresuebersicht

Eigener Tab/Seite `/admin/merch/statistics`:

- Filter nach Jahr (Default: aktuelles Vereinsjahr)
- KPI-Karten: Anzahl Runden, Anzahl Bestellungen, Brutto-Umsatz, Marge, Subventions-Verbrauch, Vereins-Netto
- Top-5-Artikel nach Stueckzahl
- Top-5-Artikel nach Marge
- Subventions-Verbrauch pro Runde als Balkendiagramm (optional, Chart.js falls vorhanden)
- Export-Button «Jahresreport als CSV»

Implementation pragmatisch: SQL-Aggregate, keine Vor-Materialisierung. Bei aktueller Vereinsgroesse vernachlaessigbar.

## 15. Notifications

**Im MVP keine Push-Notifications fuer Merch-Lifecycle-Uebergaenge.** Vereinskommunikation laeuft ueber den bestehenden WhatsApp-Vereinschat (Marketingchef informiert dort). App-Sichtbarkeit erfolgt passiv:

- Mitglieder-Shop zeigt aktive Runden
- Mitglieder-Bestellhistorie zeigt aktuellen Status
- Dashboard-Card hebt offene Aktionen hervor

Begruendung: Der Verein nutzt WhatsApp ohnehin als zentralen Kommunikationskanal; zusaetzliche Pushes wuerden Doppelinformation erzeugen. Falls sich das im Betrieb als unzureichend erweist, ist Push-Integration eine kleine Folge-Erweiterung (Service-Hook in `MerchRoundService.transition_*`-Methoden, kein Schema-Change).

## 16. Audit-Log

`SecurityService.log_audit_event` wird fuer folgende Aktionen aufgerufen (Enum-Erweiterung in `AuditAction`):

| AuditAction | Auslöser |
|---|---|
| `MERCH_SUPPLIER_CREATED` / `MERCH_SUPPLIER_UPDATED` | Lieferant angelegt/geaendert |
| `MERCH_ARTICLE_CREATED` / `MERCH_ARTICLE_UPDATED` / `MERCH_ARTICLE_ARCHIVED` | Artikel-Aktionen |
| `MERCH_ROUND_CREATED` | Runde angelegt |
| `MERCH_ROUND_OPENED` / `MERCH_ROUND_LOCKED` / `MERCH_ROUND_REOPENED` | Lifecycle-Uebergaenge inkl. Re-Open mit Begruendung |
| `MERCH_ROUND_ORDERED_AT_SUPPLIER` | Effektivpreise erfasst, Order-Forderungen festgeschrieben |
| `MERCH_ROUND_DELIVERED` / `MERCH_ROUND_CLOSED` / `MERCH_ROUND_CANCELLED` | restliche Lifecycle-Uebergaenge |
| `MERCH_ORDER_CONFIRMED` / `MERCH_ORDER_CANCELLED` | Mitglieds-Aktionen |
| `MERCH_ORDER_PICKED_UP` / `MERCH_ORDER_PAID` | Marketingchef/Schatzmeister-Aktionen |
| `MERCH_SUPPLIER_INVOICE_UPLOADED` | Beleg-Upload nach Drive |

Audit-Eintrag enthaelt User-ID, Action, optional Begruendung (z.B. bei Re-Open), Ziel-Entity (Round-ID oder Order-ID). Keine sensiblen Daten im Audit.

## 17. AI/Automation — geprueft und verworfen

Die Strategie 2026 verlangt fuer jede Capability eine ehrliche Sektion zu AI/Automation-Optionen. Fuer die Merch-Capability lautet die Antwort: **nicht im MVP-Scope.**

| Ansatz | Bewertung |
|---|---|
| Bestell-Triage aus Mail-Eingang | Entfaellt — Bestellungen laufen ausschliesslich ueber die App, keine Mail-Eingangsverarbeitung. |
| Lager-Forecast | Entfaellt — Verein fuehrt kein Lager. |
| Auto-Beschreibung fuer Artikel beim Anlegen (LLM-Aufruf) | Geprueft. Sinnvoller Komfort, aber kein MVP-Pflichtteil. Backlog. Setzt API-Key in `Config` voraus, kostet pro Aufruf wenige Cents. |
| Mengen-Empfehlung beim Sammelbestellen (historische Bestellmuster analysieren) | Geprueft. Erfordert mehrere Live-Runden Historie, vor 4–5 Runden Datenbasis nicht aussagekraeftig. Backlog. |
| AI-generierte Marketing-Texte fuer WhatsApp-Ankuendigung | Out of Scope — Marketingchef schreibt selbst, Tonality ist Vereinssache. |
| Auto-Klassifikation der Lieferantenrechnung | Out of Scope — gehoert in die Buchhaltungs-Capability, dort kommt der Hebel zum Tragen. |

**Entscheidung MVP**: Kein AI-Einsatz. Beide tatsaechlich relevanten Hebel (Auto-Beschreibung, Mengen-Empfehlung) als Backlog dokumentiert. Capability ist eine reine Prozess- und Daten-Schicht, AI-Hebel kommen sinnvollerweise erst mit Vorlauf-Daten (Mengen-Empfehlung) bzw. wenn Sortiment haeufiger geaendert wird (Auto-Beschreibung).

## 18. Datenschutz

Sichtbarkeitsmatrix:

| Datum | Mitglied selbst | Andere Mitglieder | Marketingchef/Admin | Schatzmeister |
|---|---|---|---|---|
| Eigene Bestellung (Inhalt, Status, Betrag) | ja | nein | ja | ja |
| Eigene Forderung | ja | nein | ja | ja |
| Bestellung anderer Mitglieder | nein | nein | ja (alle) | ja (alle) |
| Aggregat-Sicht ueber alle Bestellungen einer Runde | nein | nein | ja | ja |
| Lieferantenpreise (effektiv) | nein | nein | ja | ja |
| Sortiments-Stammdaten (Listenpreise) | ja | ja | ja | ja |

Datenschutz-Erklaerung (siehe `docs/capabilities/drive.md` Sektion 13.3 fuer den noch zu erstellenden Entwurf) bekommt einen Absatz:

> Merch-Bestellungen: Wenn du in einer Bestellrunde bestellst, speichern wir deine Bestellung mit Inhalt, Endbetrag und Bezahl-Status. Diese Daten sind fuer dich selbst sowie fuer den Marketingchef, Schatzmeister und Vorstand sichtbar. Andere Mitglieder sehen deine Bestellung nicht. Bilder von Merch-Artikeln liegen im Vereins-Google-Drive und werden ueber unseren Server ausgeliefert; sie sind nur fuer eingeloggte Mitglieder erreichbar.

## 19. Operations

### 19.1 Monitoring

Standard-Railway-Metriken reichen. Spezifische Anomalien:

- Drive-Upload-Fehlerrate (z.B. wenn Service-Account-Quota zuschlaegt) wird ueber `DriveStorageService`-Logs sichtbar.
- Image-Proxy 5xx-Rate: bei Haeufung Cache-Konfiguration pruefen.

### 19.2 Backups

Postgres ist durch bestehendes Railway-Backup abgedeckt. Drive-Bilder und Belege sind durch Drive-eigene Versionierung abgedeckt (Workspace-Standard 30 Tage Trash). Bei groesseren Sortimentsaenderungen empfiehlt sich vor der Migration ein DB-Snapshot.

### 19.3 Feature-Flag

Wie in `docs/CONVENTIONS.md` gefordert, laeuft die Capability hinter einem Boolean-Flag `MERCH_V2_ENABLED` (oder `MERCH_FEATURE_ENABLED`). Solange das Flag nicht gesetzt ist, bleiben die alten Routes aktiv und das neue Cockpit ist nicht erreichbar. Cutover ist dann ein einziger Config-Switch.

## 20. Verzahnung mit Folge-Capabilities

### 20.1 Buchhaltung (Hauptschnittstelle)

Siehe Sektion 13. Drei Datenpunkte werden bereitgestellt: Mitglieder-Forderung, Lieferanten-Eingangsrechnung, Subventions-Verbrauch. Buchhaltungs-Capability uebernimmt Verbuchung, Kontenplan, Reports.

### 20.2 TWINT/Payments

Im MVP keine Verzahnung. Sobald TWINT-Acquirer entschieden ist (Stripe vs. RaiseNow, Strategie-Open-Decision) und Payment-Capability existiert: Mitglieder bekommen pro `INVOICED`-Order einen Bezahl-Link mit QR / TWINT-Auslöser. Eingangs-Webhook setzt automatisch `paid_at` an der Order. Bis dahin: manuelle Markierung.

### 20.3 Drive

Bilder und Lieferantenbelege via `DriveStorageService` (Capability seit Phase 3 produktiv). Konsistent mit anderen Drive-konsumierenden Modulen.

### 20.4 BillBro — explizit nicht verzahnt

BillBro ist event-spezifisch (Restaurant-Rechnungen aufteilen, Anzahl-Schaetzungen sammeln) und deckt Merch-Forderungen *nicht* ab. Merch fuehrt seinen Forderungs-Stub eigenstaendig, Uebergabe erfolgt erst in die spaetere Buchhaltungs-Capability — nicht in BillBro.

### 20.5 Member-Modell

Funktion `MARKETINGCHEF` und `SCHATZMEISTER` (existieren bereits) werden fuer Permissions genutzt. Keine Schema-Aenderung am Member.

### 20.6 Dashboard

Bestehendes `templates/dashboard/index.html` wird um eine Merch-Karte erweitert (Sektion 12.4). Erfordert kleine Anpassung im Dashboard-Service.

## 21. Cursor-Briefing fuer Phase 10

### 21.1 Reihenfolge der Commits

| # | Commit | Inhalt |
|---|---|---|
| 1 | Rename-Migration alte Tabellen | `merch_articles → merch_articles_legacy`, dito fuer `merch_variants`, `merch_orders`, `merch_order_items`. Reine SQL-Renames, keine Daten beruehrt. Reversibel im Downgrade |
| 2 | Code-Refactor alte Models | `MerchArticle`/`MerchVariant`/`MerchOrder`/`MerchOrderItem` bekommen `__tablename__='..._legacy'`. Klassennamen optional umbenannt auf `MerchArticleLegacy` etc. Bestand-Routes auf den neuen `_legacy`-Namen umgestellt. Tests gruen |
| 3 | Schema-Migration neue Tabellen | `merch_suppliers`, `merch_articles`, `merch_variants`, `merch_rounds`, `merch_round_items`, `merch_orders`, `merch_order_items` mit dem in Sektion 6 spezifizierten Schema, Constraints, Indexes |
| 4 | Service-Layer | `MerchSortimentService`, `MerchRoundService`, `MerchOrderService`, `MerchImageService` mit Unit-Tests fuer Sanitization und Lifecycle-Validierung |
| 5 | Drive-Bild-Proxy | Endpoint `/merch/image/<article_id>`, Cache-Implementation, Bild-Upload via Drive-Service. Tests gegen gemockten Drive-Service |
| 6 | Routes und Cockpit-UI | Marketingchef-Cockpit mit drei Modi, Sortimentspflege, Statistik. BEM-Klassen, Lucide-Icons, Disclosure-Pattern |
| 7 | Mitglieder-UI | Shop, Warenkorb, Bestelldetail, Dashboard-Card |
| 8 | Legacy-Receivables-Sicht | Read-only-Aggregat pro Mitglied unter `/admin/merch/legacy-receivables` (Marketingchef/Schatzmeister/Admin), Detail-Sicht pro Mitglied. Ausschliesslich Anzeige, keine Schreib-Aktionen. Spec: Sektion 12.5 |
| 9 | Feature-Flag-Cutover | `MERCH_V2_ENABLED=true` in Production schaltet die neue Capability scharf, alte Bestell-Routes deaktiviert (oder zu Legacy-Read-Only degradiert) |

**Bestand-Migration aus `_legacy`-Tabellen ist NICHT Teil von Phase 10.** Sie wird in einer separaten Folge-Phase mit Production-Daten-Probe gemacht; ggf. wird ganz darauf verzichtet, falls die historischen Bestellungen nicht gebraucht werden.

### 21.2 Cursor-Briefing-Block

```
Branch: phase/10-workspace-merch
Lies vor Implementation: docs/capabilities/merch.md (autoritativ).
Lies docs/initiatives/workspace-railway/PHASE_10_MERCH.md nur fuer Rahmen.

Implementations-Reihenfolge: Rename-Migration _legacy → Code-Refactor Legacy-Models → neue Tabellen
→ Service-Layer mit Tests → Bild-Proxy → Routes und Cockpit-UI → Mitglieder-UI →
Legacy-Receivables read-only → Feature-Flag-Cutover (MERCH_V2_ENABLED).
**Datenmigration aus `_legacy`, Bild-Migration Repo→Drive sowie Drop `_legacy`** sind keine Phase-10-Schritte (§21.4).

Schema-Migrationen sind separate Alembic-Commits. Service-Layer und UI sind
eigene Code-Commits.

Drive-Integration ueber bestehenden DriveStorageService (Phase 3, produktiv).
Bild-Cache-Backend: Redis (vorhanden auf Railway).

Permission-Decorators: marketing_chief_or_admin_required (Sortiment, Runden,
Verteilung), treasury_or_admin_required (Bezahl-Markierung).

Pricing in Rappen als int. UI-Texte deutsch, schweizerische Schreibweise mit
Guillemets «…», Doppel-S statt Eszett. BEM-Klassen und Tokens gemaess docs/UI.md.

Audit-Log fuer alle Lifecycle-Uebergaenge und Bezahl-Markierungen, AuditAction-Enum
erweitern.

Lokale Verifikation:
- Lifecycle-Uebergaenge alle durchspielen (DRAFT → OPEN → LOCKED → ORDERED → DELIVERED → CLOSED)
- Backwards-Uebergang LOCKED → OPEN testen
- CANCELLED auf jedem Status testen (Edge Cases)
- Mitglied-Bestellung waehrend OPEN aendern, stornieren
- Subventions-Berechnung an Beispielrechnung verifizieren
- Bild-Upload nach Drive, Proxy-Auslieferung, Cache-Hit nach 2. Request
- Sammelbestellungs-CSV-Export Format pruefen
- Statistik-Werte gegen manuell berechnete Werte verifizieren
```

### 21.3 Akzeptanzkriterien fuer Phase 10

- [ ] Marketingchef kann Lieferanten im Cockpit anlegen, bearbeiten und archivieren (`GET/POST /admin/merch-v2/suppliers`)
- [ ] Marketingchef kann Artikel mit Variantenschema, Drive‑Bildanbindung sowie Archivierung im Cockpit pflegen (Zwischenweise: `scripts/seed_merch_v2_dev.py` / technische Schulden dokumentieren bis UI vollstaendig)
- [ ] Marketingchef kann Runde anlegen, oeffnen, schliessen, re-oeffnen (mit Begruendung), abbrechen (mit Begruendung)
- [ ] Mehrere Runden parallel `OPEN` moeglich
- [ ] Mitglied sieht aktive Runden im Shop und in Dashboard-Card
- [ ] Mitglied baut Warenkorb pro Runde, bestaetigt, kann waehrend OPEN aendern und stornieren
- [ ] Beim Uebergang `LOCKED → ORDERED_AT_SUPPLIER` werden Brutto/Subvention/Forderung pro Order korrekt berechnet
- [ ] Subventions-Cap (max. Bestellbetrag) wird respektiert
- [ ] Marketingchef sieht Sammelbestellungs-Aggregat pro Variante, kann als Text/CSV exportieren
- [ ] Marketingchef kann Effektivpreise erfassen, Lieferantenbeleg in Drive hochladen
- [ ] Marketingchef/Admin kann Order als `PICKED_UP` markieren, Marketingchef/Schatzmeister/Admin kann als `PAID` markieren
- [ ] Bild-Proxy liefert Bilder aus Drive, Cache-Hit beim 2. Request
- [ ] Statistik pro Runde, pro Mitglied, Vereins-Jahresuebersicht funktional
- [ ] Audit-Log enthaelt alle Lifecycle- und Bezahl-Aktionen
- [ ] Permissions korrekt: Mitglied sieht keine fremden Bestellungen, kein Mitglied kann Cockpit aufrufen
- [ ] Feature-Flag `MERCH_V2_ENABLED` schaltet die neue Capability ein

**Abgrenzung (kein Abnahme-Blocker fuer Phase 10, §21.4 Out of Scope):** automatische Bilder-Migration aus `static/img/merch/` nach Drive; Schema-Aufraeum fuer `_legacy`-Tabellen ohne vorherige Bestandsmigration; Datenmigration aus `_legacy` ins v2-Modell — jeweils **Folgephase** nach Phase‑10‑Stabilisierung.

- [ ] Tests gruen, keine sensiblen Daten in Logs
- [ ] Mitglieder-Shop und Cockpit nutzen BEM, Lucide-Icons, Disclosure-Pattern konsistent
- [ ] Rename-Migration alte Tabellen reversibel (Downgrade benennt zurueck)
- [ ] Alte Mitglieder-Routes (`/merch/order` etc.) sind beim Cutover deaktiviert; alte Admin-Routes ebenfalls
- [ ] Legacy-Receivables-Sicht zeigt korrekte Aggregat-Werte aus `merch_orders_legacy`, ist nur fuer Marketingchef/Schatzmeister/Admin erreichbar, hat keine Schreib-Aktionen

### 21.4 Out of Scope fuer Phase 10

- Push-Notifications zu Lifecycle-Uebergaengen (laeuft ueber WhatsApp-Vereinschat)
- TWINT-Bezahllinks und Webhook-Integration (kommt mit Phase 6 / Buchhaltung)
- BillBro-Integration (BillBro deckt Merch nicht ab)
- AI-Auto-Beschreibung fuer Artikel
- AI-Mengen-Empfehlung
- Lager-Konzept (nicht relevant)
- Mehrere Bilder pro Artikel (Galerie)
- Subventions-Uebertrag in Folgerunden
- Subventions-Anspruch fuer Nicht-Besteller
- Eigene MwSt-Behandlung (kommt mit Buchhaltung)
- Jahresabschluss-Export (Schatzmeister exportiert manuell aus Statistik)
- Public-Sichtbarkeit von Merch-Artikeln auf gourmen.ch
- **Daten-Migration aus `_legacy`-Tabellen** (separate spaetere Phase mit Production-Daten-Probe; ggf. ganz verworfen)
- **Bilder-Migration** der alten `static/img/merch/`-Bestaende nach Drive (laeuft mit der Bestand-Migrationsphase)
- **Drop der `_legacy`-Tabellen** (erst nach erfolgreicher Bestand-Migration und Stabilisierung)

## 22. Decision Log

| Datum | Entscheid | Begruendung |
|---|---|---|
| 2026-05-15 | Reihenfolge: erst Merch, dann Buchhaltung | Strategie-Reihenfolge respektieren, Buchhaltung hat ungeklaerte Vorlauf-Entscheide (n8n vs. Flask, TWINT-Acquirer), Merch braucht sie nicht. Schnittstelle wird sauber definiert |
| 2026-05-15 | Zwei verzahnte Lifecycles: Round + Order | Realwelt trennt das ohnehin (Round = was Marketingchef macht, Order = was pro Mitglied passiert). Single-Status waere ueberladen |
| 2026-05-15 | Backwards-Uebergang `LOCKED → OPEN` erlaubt | Praktisch noetig, wenn Lieferant einzelne Varianten nicht liefern kann und Mitglieder anpassen sollen. Audit-Log dokumentiert mit Begruendung |
| 2026-05-15 | `CANCELLED`-Endzustand fuer Round | Komplettes Verwerfen explizit moeglich; alle aktiven Orders werden auf CANCELLED gesetzt |
| 2026-05-15 | Marketingchef-Permission via `Funktion.MARKETINGCHEF` (existierend) | Bestehende Funktion nutzen, kein neues Rollen-Konstrukt. Admin als Fallback fuer Vertretung |
| 2026-05-15 | Bezahl-Markierung auch durch Schatzmeister | Realistischer Workflow: Schatzmeister hat das Geld, Marketingchef die Operative. Beide muessen markieren koennen |
| 2026-05-15 | Mehrere Runden parallel `OPEN` moeglich | Marketingchef kann z.B. zwei Lieferanten parallel haben. UI stemmt das mit Karten-Liste |
| 2026-05-15 | Manuelles Schliessen, Deadline ist nur kommunikativ | Vereinsalltag flexibel. App zeigt sanften «Frist ueberfaellig»-Hinweis |
| 2026-05-15 | Keine Push-Notifications im MVP | Vereinskommunikation laeuft ueber WhatsApp-Chat, App zeigt Status passiv |
| 2026-05-15 | Drei Preisstufen: Listenpreis, Effektiver Lieferantenpreis, Mitgliederpreis | Realer Prozess hat zwei Preis-Erhebungs-Zeitpunkte (Listenpreis bei Anlegen, Effektivpreis nach Sammelbestellung), Mitgliederpreis kann unabhaengig festgesetzt werden |
| 2026-05-15 | Pricing pro `MerchRoundItem`, nicht ueberschreiben am Variant | Erlaubt Preis-Differenzen zwischen Runden, erhaelt Historie fuer Buchhaltung |
| 2026-05-15 | Mitgliederpreis pro Variante manuell vom Marketingchef | Maximale Flexibilitaet, kein starres Aufschlagsmodell |
| 2026-05-15 | Subvention pro Runde fix, Subventions-Cap = Bestellbetrag | Einfaches Modell, kein Uebertrag, kein Anspruch ohne Bestellung |
| 2026-05-15 | Forderungs-Stub: drei Felder am `MerchOrder`, manuell als bezahlt | MVP ohne TWINT-Integration; Buchhaltung uebernimmt spaeter |
| 2026-05-15 | Lieferantenbeleg via direktem App-Upload nach Drive | Konsistent mit Drive-Strategie, Marketingchef autonom |
| 2026-05-15 | `MerchSupplier` als eigene Entitaet | Wiederverwendung, sauberer Stamm, ermoeglicht spaetere Lieferantenbewertung |
| 2026-05-15 | Bilder via Drive mit Backend-Proxy + Cache | Marketingchef autonom, kein Repo-Commit pro Bild. Strategie-Aktualisierung gegenueber «Repo unter static/img/merch/» |
| 2026-05-15 | Variantenschema als JSON `attributes` am `MerchVariant` | Generisch fuer beliebige Dimensionen (Farbe, Groesse, Material, …), pragmatisch fuer kleine Datenmengen |
| 2026-05-15 | Klassischer Warenkorb pro Runde im Mitglieder-UI | Erwartbares E-Commerce-Pattern, sauberer Order-pro-Runde-Mapping |
| 2026-05-15 | Dashboard-Card fuer Merch-Status | Erhoeht Sichtbarkeit ohne Push-Konkurrenz |
| 2026-05-15 | Statistik in drei Stufen (Runde, Mitglied, Jahr) im MVP | Direkt aus Daten berechnet, ohne Vor-Materialisierung; deckt Cockpit-Bedarf, Schatzmeister-Bedarf und GV-Bedarf |
| 2026-05-15 | Keine AI im MVP, beide Hebel im Backlog dokumentiert | Auto-Beschreibung und Mengen-Empfehlung waeren sinnvoll, brauchen aber API-Konfiguration / Vorlauf-Daten. Prozess-/Daten-Schicht hat Vorrang |
| 2026-05-15 | BillBro NICHT verzahnt mit Merch | BillBro ist event-spezifisch (Restaurantrechnungen aufteilen, Anzahl-Schaetzungen). Merch braucht eigenen Forderungs-Stub |
| 2026-05-15 | Feature-Flag `MERCH_V2_ENABLED` fuer Cutover | Konsistent mit Drive-Capability-Pattern; alte Implementation bleibt parallel bis Cutover |
| 2026-05-15 | Phase 10 fasst Bestandsdaten nicht an, alte Tabellen werden auf `_legacy`-Suffix umbenannt | Implementations-Phase und Daten-Migrationsphase haben unterschiedliche Risiko-Profile. Trennung erlaubt fokussierten Bau in Phase 10; Bestand-Migration laeuft separat mit Production-Daten-Probe oder wird ganz verworfen, falls historische Bestellungen nicht gebraucht werden |
| 2026-05-15 | Einzige Bestand-Sicht ist Legacy-Receivables-Aggregat fuer Marketingchef/Schatzmeister/Admin, read-only | Notfall-Nachschlag, wer aus alter Welt noch was schuldet. Keine Bezahl-Markierung (altes Modell hatte keinen Bezahl-Status). Keine Mitglieder-Sichtbarkeit auf alte Bestellhistorie — Bestellungen aus alter Welt sind App-seitig erledigt |

## 23. Offene Punkte und Trade-offs

- *CANCELLED-Edge-Case mit bereits bezahlten Orders*: Falls die Runde nach `ORDERED_AT_SUPPLIER` und ggf. `DELIVERED` doch noch storniert wird (sehr ungewoehnlich), behalten bezahlte Orders ihren Status, Schatzmeister muss manuell zurueckueberweisen. Buchhaltungs-Capability klaert die Verbuchung.
- *Mitglied tritt zwischen `CONFIRMED` und Lieferung aus*: Order bleibt aktiv, Marketingchef entscheidet manuell. Kein Auto-Refund.
- *Nicht abgeholte Artikel nach >X Monaten*: Heute keine technische Behandlung. Fall-Back: Marketingchef setzt manuell auf `CANCELLED` mit Begruendung «nicht abgeholt».
- *Mehrere Bilder pro Artikel (Galerie)*: Backlog. Erweiterung minimal (Bilder als eigene Tabelle mit `article_id`, `drive_file_id`, `sort_order`).
- *Subventions-Anspruch fuer Nicht-Besteller*: Falls Andreas spaeter entscheidet, dass die Subvention auch ohne Merch-Bestellung dem Mitglied zusteht (z.B. als Vereinskassen-Beitrag in BillBro oder Buchhaltung), ist das eine kleine Schema-Erweiterung — heute nicht implementiert.
- *Subventions-Uebertrag in Folgerunden*: Backlog, falls jaehrliche Ueberlegungen das verlangen.
- *Lieferanten-Mail-Templates*: Heute nur Copy-to-Clipboard und CSV. Falls einzelne Lieferanten regelmaessig per Mail bestellt werden, koennte ein lieferantenspezifisches Mail-Template am `MerchSupplier`-Modell hinzugefuegt werden.
- *Outlook der Effektivpreis-Erfassung beim Lieferanten mit Versandkosten/MwSt*: Die App rechnet Stueckpreis-Summen, der Marketingchef kann eine abweichende Lieferantenrechnungs-Summe separat erfassen. Saubere Verbuchung der Differenz erfolgt mit Buchhaltungs-Capability.
- *Variantenschema-Aenderung an existierendem Artikel mit historischen Bestellungen*: Heute parken — wenn Marketingchef das Schema aendert, koennen alte `MerchVariant`-Eintraege (mit alten attributes) bestehen bleiben, neue Schema-Werte erzeugen neue Varianten. Doku fuer Marketingchef noetig: «Schema-Aenderungen sind additiv, nicht destruktiv».
- *PRODID/Vereins-Identitaet im Sortimentsexport*: Falls CSV-Export spaeter standardisiert werden soll (z.B. fuer Lieferanten-Webshops mit CSV-Import), kommt eine Mapping-Schicht.
- *Bestand-Migration aus `_legacy`-Tabellen*: Eigene Folge-Phase nach Phase-10-Stabilisierung. Vorgehen: Production-Daten-Probe inspizieren → Entscheid migrieren oder verwerfen → bei Migration `scripts/migrate_merch_legacy_to_v2.py` mit Pseudo-Round «Historische Bestellungen», Default-Lieferant «Unbekannt» (oder manuelle Zuordnung), Variant-Attributes aus `color`/`size`. Danach `_legacy`-Tabellen droppen.

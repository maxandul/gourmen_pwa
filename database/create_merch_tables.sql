-- ==============================================================================
-- Merch-Tabellen für Railway PostgreSQL
-- ==============================================================================
-- Dieses Script erstellt alle Tabellen für die Merchandise-Verwaltung
-- 
-- Ausführung:
-- 1. Railway CLI: railway connect Postgres
-- 2. SQL-Script kopieren und einfügen
-- ==============================================================================

-- Tabelle 1: Merch-Artikel
-- ==============================================================================
CREATE TABLE IF NOT EXISTS merch_articles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    base_supplier_price_rappen INTEGER NOT NULL,
    base_member_price_rappen INTEGER NOT NULL,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Tabelle 2: Merch-Varianten (Größen/Farben)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS merch_variants (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES merch_articles(id) ON DELETE CASCADE,
    color VARCHAR(50) NOT NULL,
    size VARCHAR(20) NOT NULL,
    supplier_price_rappen INTEGER NOT NULL,
    member_price_rappen INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Tabelle 3: Merch-Bestellungen
-- ==============================================================================
CREATE TABLE IF NOT EXISTS merch_orders (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'BESTELLT' NOT NULL,
    total_member_price_rappen INTEGER NOT NULL,
    total_supplier_price_rappen INTEGER NOT NULL,
    total_profit_rappen INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    delivered_at TIMESTAMP
);

-- Tabelle 4: Merch-Bestellpositionen
-- ==============================================================================
CREATE TABLE IF NOT EXISTS merch_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES merch_orders(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES merch_articles(id) ON DELETE RESTRICT,
    variant_id INTEGER NOT NULL REFERENCES merch_variants(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_member_price_rappen INTEGER NOT NULL,
    unit_supplier_price_rappen INTEGER NOT NULL,
    total_member_price_rappen INTEGER NOT NULL,
    total_supplier_price_rappen INTEGER NOT NULL,
    total_profit_rappen INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indizes für Performance
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_merch_orders_member_id ON merch_orders(member_id);
CREATE INDEX IF NOT EXISTS idx_merch_orders_order_number ON merch_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_merch_variants_article_id ON merch_variants(article_id);
CREATE INDEX IF NOT EXISTS idx_merch_order_items_order_id ON merch_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_merch_order_items_article_id ON merch_order_items(article_id);
CREATE INDEX IF NOT EXISTS idx_merch_order_items_variant_id ON merch_order_items(variant_id);

-- Überprüfung der erstellten Tabellen
-- ==============================================================================
SELECT 
    table_name,
    (SELECT COUNT(*) 
     FROM information_schema.columns 
     WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name LIKE 'merch_%'
ORDER BY table_name;

-- Erfolgsmeldung
-- ==============================================================================
SELECT '✅ Alle Merch-Tabellen wurden erfolgreich erstellt!' as status;


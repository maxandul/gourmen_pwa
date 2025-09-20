from flask import Blueprint, jsonify
from backend.extensions import db
from sqlalchemy import text

init_db_bp = Blueprint('init_db', __name__)

@init_db_bp.route('/init/merch', methods=['GET'])
def init_merch_tables():
    """Initialisiert die Merch-Tabellen beim ersten Aufruf"""
    
    try:
        # Prüfe ob Tabellen bereits existieren
        result = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE 'merch_%'
        """))
        
        existing_tables = [row[0] for row in result.fetchall()]
        
        if len(existing_tables) >= 4:
            return jsonify({
                'success': True,
                'message': '✅ Merch-Tabellen existieren bereits',
                'tables': existing_tables
            })
        
        print("🚀 Erstelle Merch-Tabellen...")
        
        # Erstelle merch_articles Tabelle
        db.session.execute(text("""
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
        """))
        
        # Erstelle merch_variants Tabelle
        db.session.execute(text("""
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
        """))
        
        # Erstelle merch_orders Tabelle
        db.session.execute(text("""
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
        """))
        
        # Erstelle merch_order_items Tabelle
        db.session.execute(text("""
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
        """))
        
        # Erstelle Indizes
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_orders_member_id ON merch_orders(member_id);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_orders_order_number ON merch_orders(order_number);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_variants_article_id ON merch_variants(article_id);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_order_items_order_id ON merch_order_items(order_id);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_order_items_article_id ON merch_order_items(article_id);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_merch_order_items_variant_id ON merch_order_items(variant_id);"))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Alle Merch-Tabellen erfolgreich erstellt!',
            'tables': ['merch_articles', 'merch_variants', 'merch_orders', 'merch_order_items']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'❌ Fehler beim Erstellen der Tabellen: {str(e)}'
        }), 500

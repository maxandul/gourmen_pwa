#!/usr/bin/env python3
"""
Script to seed merch test data
Creates T-Shirt and Hoodie with variants
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant

def seed_merch_data():
    """Seed merch test data"""
    app = create_app()
    
    with app.app_context():
        # Check if data already exists
        if MerchArticle.query.count() > 0:
            print("Merch data already exists, skipping...")
            return
        
        print("Creating merch test data...")
        
        # Create T-Shirt article
        tshirt = MerchArticle(
            name="Gourmen T-Shirt",
            description="Klassisches Gourmen T-Shirt aus 100% Baumwolle",
            base_supplier_price_rappen=2500,  # 25.00 CHF
            base_member_price_rappen=3500,   # 35.00 CHF
            image_url="/static/img/merch/tshirt.jpg",
            is_active=True
        )
        db.session.add(tshirt)
        db.session.flush()  # Get the ID
        
        # Create T-Shirt variants
        tshirt_colors = ["Schwarz", "Weiß", "Rot"]
        tshirt_sizes = ["S", "M", "L", "XL", "XXL"]
        
        for color in tshirt_colors:
            for size in tshirt_sizes:
                # Different prices for different colors
                if color == "Rot":
                    supplier_price = 2700  # 27.00 CHF
                    member_price = 3700    # 37.00 CHF
                elif color == "Weiß":
                    supplier_price = 2600  # 26.00 CHF
                    member_price = 3600    # 36.00 CHF
                else:  # Schwarz
                    supplier_price = 2500  # 25.00 CHF
                    member_price = 3500    # 35.00 CHF
                
                variant = MerchVariant(
                    article_id=tshirt.id,
                    color=color,
                    size=size,
                    supplier_price_rappen=supplier_price,
                    member_price_rappen=member_price,
                    is_active=True
                )
                db.session.add(variant)
        
        # Create Hoodie article
        hoodie = MerchArticle(
            name="Gourmen Hoodie",
            description="Warmes Gourmen Hoodie mit Kapuze",
            base_supplier_price_rappen=4500,  # 45.00 CHF
            base_member_price_rappen=6500,    # 65.00 CHF
            image_url="/static/img/merch/hoodie.jpg",
            is_active=True
        )
        db.session.add(hoodie)
        db.session.flush()  # Get the ID
        
        # Create Hoodie variants
        hoodie_colors = ["Schwarz", "Grau", "Navy"]
        hoodie_sizes = ["S", "M", "L", "XL", "XXL"]
        
        for color in hoodie_colors:
            for size in hoodie_sizes:
                # Different prices for different colors
                if color == "Navy":
                    supplier_price = 4700  # 47.00 CHF
                    member_price = 6700    # 67.00 CHF
                elif color == "Grau":
                    supplier_price = 4600  # 46.00 CHF
                    member_price = 6600    # 66.00 CHF
                else:  # Schwarz
                    supplier_price = 4500  # 45.00 CHF
                    member_price = 6500    # 65.00 CHF
                
                variant = MerchVariant(
                    article_id=hoodie.id,
                    color=color,
                    size=size,
                    supplier_price_rappen=supplier_price,
                    member_price_rappen=member_price,
                    is_active=True
                )
                db.session.add(variant)
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Created {MerchArticle.query.count()} articles")
        print(f"✅ Created {MerchVariant.query.count()} variants")
        
        # Print summary
        print("\n📊 Merch Data Summary:")
        for article in MerchArticle.query.all():
            variants = MerchVariant.query.filter_by(article_id=article.id).count()
            print(f"  {article.name}: {variants} variants")
            print(f"    Base Price: {article.base_supplier_price_chf:.2f} CHF → {article.base_member_price_chf:.2f} CHF")
            print(f"    Profit: {article.base_profit_chf:.2f} CHF")

if __name__ == "__main__":
    seed_merch_data()


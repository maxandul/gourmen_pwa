from decimal import Decimal, ROUND_UP

class MoneyService:
    """Money service for Rappen↔CHF conversion"""
    
    @staticmethod
    def to_franken(rappen):
        """Convert Rappen to CHF string format"""
        if rappen is None:
            return None
        
        # Convert to Decimal for precise arithmetic
        rappen_decimal = Decimal(str(rappen))
        franken_decimal = rappen_decimal / 100
        
        # Format as CHF with 2 decimal places
        return f"CHF {franken_decimal:.2f}"
    
    @staticmethod
    def to_rappen(franken_input):
        """Convert CHF input (string/Decimal) to Rappen integer"""
        if franken_input is None:
            return None
        
        # Handle different input types
        if isinstance(franken_input, str):
            # Remove CHF prefix and spaces if present
            franken_input = franken_input.replace('CHF', '').replace(' ', '').strip()
            # Replace comma with dot for decimal
            franken_input = franken_input.replace(',', '.')
        
        # Convert to Decimal
        franken_decimal = Decimal(str(franken_input))
        
        # Convert to Rappen (multiply by 100 and round up)
        rappen_decimal = franken_decimal * 100
        rappen_int = int(rappen_decimal.quantize(Decimal('1'), rounding=ROUND_UP))
        
        return rappen_int
    
    @staticmethod
    def format_rappen(rappen):
        """Format Rappen as CHF string (alias for to_franken)"""
        return MoneyService.to_franken(rappen)
    
    @staticmethod
    def parse_franken(franken_str):
        """Parse CHF string to Rappen (alias for to_rappen)"""
        return MoneyService.to_rappen(franken_str)
    
    @staticmethod
    def validate_franken_amount(amount_str):
        """Validate CHF amount string"""
        if not amount_str:
            return False, "Betrag ist erforderlich"
        
        try:
            # Clean input
            clean_amount = amount_str.replace('CHF', '').replace(' ', '').replace(',', '.')
            
            # Try to convert
            amount_decimal = Decimal(clean_amount)
            
            # Check for reasonable range (0 to 10,000 CHF)
            if amount_decimal < 0:
                return False, "Betrag muss positiv sein"
            if amount_decimal > 10000:
                return False, "Betrag ist zu hoch (max. CHF 10'000)"
            
            return True, "Betrag ist gültig"
            
        except (ValueError, DecimalException):
            return False, "Ungültiges Betragsformat"
    
    @staticmethod
    def calculate_tip(bill_amount_rappen, tip_percentage=7):
        """Calculate tip amount in Rappen"""
        if bill_amount_rappen is None:
            return 0
        
        tip_amount = (bill_amount_rappen * tip_percentage) / 100
        return int(tip_amount)
    
    @staticmethod
    def round_up_to_nearest(amount_rappen, nearest_rappen=10):
        """Round up amount to nearest Rappen value"""
        if amount_rappen is None:
            return 0
        
        remainder = amount_rappen % nearest_rappen
        if remainder == 0:
            return amount_rappen
        
        return amount_rappen + (nearest_rappen - remainder) 
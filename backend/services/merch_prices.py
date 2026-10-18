"""Exact catalogue prices, allowing full subsidy without a negative member share."""
import re
from backend.services.money import MoneyService


class MerchPriceError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('Preise prüfen.')


class MerchPriceService:
    @staticmethod
    def parse(value):
        text = str(value).strip() if value is not None else ''
        if len(text) <= 40 and re.fullmatch(r'(?:CHF )?0+(?:[.,]0{1,2})?', text):
            return 0
        return MoneyService.parse_positive_rappen(text)

    @classmethod
    def form_prices(cls, form):
        errors, values = {}, {}
        for field in ('base_supplier_price_chf', 'base_member_price_chf'):
            try:
                values[field] = cls.parse(form.get(field))
            except ValueError:
                errors[field] = 'Nichtnegativen CHF-Betrag mit höchstens zwei Nachkommastellen im unterstützten Wertebereich eingeben.'
        if not errors and values['base_member_price_chf'] > values['base_supplier_price_chf']:
            errors['base_member_price_chf'] = 'Mitgliederpreis darf den Einkaufspreis nicht übersteigen (keine Marge).'
        if errors:
            raise MerchPriceError(errors)
        return values['base_supplier_price_chf'], values['base_member_price_chf']

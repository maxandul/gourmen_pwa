#!/usr/bin/env python3
"""Seed fuer das Buchhaltungsmodul (Phase 4, Kontenplan verschlankt 2026-07).

Legt an (idempotent, mehrfach ausfuehrbar ohne Fehler):
- Verschlankter Kontenplan gemaess docs/capabilities/accounting.md Sektion 6
  (orientiert an den real bebuchten Kategorien der ZKB-Kontoauszuege und den
  Kostenstellen aus vorlagen_buchhaltung/Vereinsfinanzen_2026.xlsx)
- FiscalYears 2021-2026 (2021-2025 closed, 2026 open)
- Budget-Werte 2025 und 2026 (aus der Excel-Vorlage, auf neue Konten remappt)

Cleanup: Konten aus dem alten PDF-Vorlagen-Kontenplan, die nie eine Buchung
gesehen haben, werden entfernt (nur relevant fuer DBs, in denen der alte
Seed bereits lief). Alt-Konten mit Buchungen werden auf die neuen Namen
umbenannt statt geloescht.

Keine historischen Einzelbuchungen (Seeding Option A).

Aufruf lokal:    python scripts/seed_accounting_chart.py
Aufruf Railway:  railway ssh ... "/opt/venv/bin/python scripts/seed_accounting_chart.py"
"""

import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.accounting import (
    Account,
    AccountKind,
    Booking,
    BudgetEntry,
    FiscalYear,
    FiscalYearStatus,
)

# (code, name, kind, group_name) – Reihenfolge = sort_order
# Verschlankt 2026-07: nur Konten, die real bebucht werden.
# Feinere Unterteilung bei Bedarf via Kontenplan-Verwaltung (Admin).
CHART_OF_ACCOUNTS = [
    # Einnahmen
    ('3000', 'Mitgliederbeiträge', AccountKind.INCOME, 'Mitgliederbeiträge'),
    ('3100', 'Spenden und Sponsoring', AccountKind.INCOME, 'Übrige Einnahmen'),
    ('3310', 'Essensanteile von Mitgliedern', AccountKind.INCOME, 'Essen'),
    ('3315', 'Aufgerundete Essensanteile', AccountKind.INCOME, 'Essen'),
    ('3400', 'Merch-Zahlungen von Mitgliedern', AccountKind.INCOME, 'Merch'),
    ('3410', 'Aufgerundete Merchbestellungen', AccountKind.INCOME, 'Merch'),
    ('3500', 'Einnahmen aus Reisen', AccountKind.INCOME, 'Reisen'),
    ('3620', 'Sonstige Einnahmen (Bussen, Rückerstattungen)', AccountKind.INCOME, 'Übrige Einnahmen'),
    # Ausgaben
    ('4500', 'Reisen und Ausflüge', AccountKind.EXPENSE, 'Reisen'),
    ('6100', 'Essen mit Vereinskonto', AccountKind.EXPENSE, 'Essen'),
    ('6541', 'Generalversammlung', AccountKind.EXPENSE, 'Vereinsanlässe'),
    ('6542', 'Vorstandssitzungen', AccountKind.EXPENSE, 'Vereinsanlässe'),
    ('6570', 'IT, Telefon und Internet', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6650', 'Merch-Einkauf bei Lieferanten', AccountKind.EXPENSE, 'Merch'),
    ('6660', 'Marketing und Merch-Beitrag des Vereins', AccountKind.EXPENSE, 'Merch'),
    ('6700', 'Sonstiger Vereinsaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6710', 'Rückzahlungen an Mitglieder', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6940', 'Kontoführung und Kartengebühren', AccountKind.EXPENSE, 'Finanzergebnis'),
]

# Alt-Codes aus dem PDF-Vorlagen-Kontenplan, die es im neuen Plan nicht mehr
# gibt. Ohne Buchungen -> loeschen; mit Buchungen -> deaktivieren + Warnung.
LEGACY_CODES = [
    '3015', '3020', '3110', '3120', '3130', '3300', '3320', '3340',
    '3600', '3610',
    '4000', '4400', '5000', '6000', '6200', '6300', '6400', '6500',
    '6510', '6530', '6540', '6800', '6900',
]

# Budget-Werte in Rappen pro Konto-Code (aus Excel «Jahresabschluss 2025»,
# remappt auf den verschlankten Kontenplan: 6510 Telefon -> 6570 IT/Telefon).
BUDGETS = {
    2025: {
        '3000': 924000,
        '4500': 550000,
        '6541': 40000,
        '6542': 10000,
        '6570': 10000,   # ehem. 6510 Telefon
        '6660': 70000,
        '6940': 5000,
    },
    2026: {
        '3000': 948000,
        '3620': 10000,
        '4500': 930000,
        '6541': 40000,
        '6542': 40000,
        '6570': 25000,   # ehem. 6510 (5000) + 6570 (20000)
        '6660': 90000,
        '6940': 10000,
    },
}

FISCAL_YEARS = range(2021, 2027)
CURRENT_OPEN_YEAR = 2026


def seed_accounts():
    created, renamed = 0, 0
    for sort_order, (code, name, kind, group_name) in enumerate(CHART_OF_ACCOUNTS):
        account = Account.query.filter_by(code=code).first()
        if account is None:
            account = Account(
                code=code, name=name, kind=kind,
                group_name=group_name, is_active=True, sort_order=sort_order,
            )
            db.session.add(account)
            created += 1
        else:
            # Bestehende Konten (alter Seed) auf verschlankten Plan nachziehen.
            if (account.name, account.group_name) != (name, group_name):
                account.name = name
                account.group_name = group_name
                renamed += 1
            account.sort_order = sort_order
            account.is_active = True
    print(f"Konten: {created} angelegt, {renamed} umbenannt/nachgezogen")


def cleanup_legacy_accounts():
    """Nie bebuchte Konten aus der alten PDF-Vorlage entfernen."""
    deleted, deactivated = 0, 0
    for code in LEGACY_CODES:
        account = Account.query.filter_by(code=code).first()
        if account is None:
            continue
        has_bookings = Booking.query.filter_by(account_id=account.id).first() is not None
        if has_bookings:
            account.is_active = False
            deactivated += 1
            print(f"WARNUNG: Alt-Konto {code} ({account.name}) hat Buchungen -> nur deaktiviert")
        else:
            BudgetEntry.query.filter_by(account_id=account.id).delete()
            db.session.delete(account)
            deleted += 1
    print(f"Alt-Konten: {deleted} gelöscht, {deactivated} deaktiviert")


def seed_fiscal_years():
    created = 0
    for year in FISCAL_YEARS:
        fy = FiscalYear.query.filter_by(year=year).first()
        if fy is None:
            status = (
                FiscalYearStatus.OPEN
                if year >= CURRENT_OPEN_YEAR
                else FiscalYearStatus.CLOSED
            )
            fy = FiscalYear(
                year=year,
                start_date=date(year, 1, 1),
                end_date=date(year, 12, 31),
                status=status,
            )
            db.session.add(fy)
            created += 1
    print(f"Geschäftsjahre: {created} angelegt")


def seed_budgets():
    created = 0
    for year, entries in BUDGETS.items():
        fy = FiscalYear.query.filter_by(year=year).first()
        if fy is None:
            print(f"WARNUNG: Geschäftsjahr {year} fehlt, Budget übersprungen")
            continue
        for code, amount_rappen in entries.items():
            account = Account.query.filter_by(code=code).first()
            if account is None:
                print(f"WARNUNG: Konto {code} fehlt, Budget übersprungen")
                continue
            entry = BudgetEntry.query.filter_by(
                fiscal_year_id=fy.id, account_id=account.id
            ).first()
            if entry is None:
                db.session.add(BudgetEntry(
                    fiscal_year_id=fy.id,
                    account_id=account.id,
                    amount_rappen=amount_rappen,
                ))
                created += 1
    print(f"Budget-Einträge: {created} angelegt")


def main():
    app = create_app()
    with app.app_context():
        seed_accounts()
        db.session.flush()
        cleanup_legacy_accounts()
        db.session.flush()
        seed_fiscal_years()
        db.session.flush()
        seed_budgets()
        db.session.commit()
        print("Seed abgeschlossen.")


if __name__ == '__main__':
    main()

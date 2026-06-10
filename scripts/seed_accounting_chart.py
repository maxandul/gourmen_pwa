#!/usr/bin/env python3
"""Seed fuer das Buchhaltungsmodul (Phase 4).

Legt an (idempotent, mehrfach ausfuehrbar ohne Fehler):
- Kontenplan gemaess docs/capabilities/accounting.md Sektion 6
- FiscalYears 2021-2026 (2021-2025 closed, 2026 open)
- Budget-Werte 2025 und 2026 (aus vorlagen_buchhaltung/
  20260324_Erfolgsrechnung 2025 und Budget 2026.xlsx uebernommen;
  die Datei selbst wird nicht committet)

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
    BudgetEntry,
    FiscalYear,
    FiscalYearStatus,
)

# (code, name, kind, group_name) – Reihenfolge = sort_order
CHART_OF_ACCOUNTS = [
    # Einnahmen
    ('3000', 'Mitgliederbeiträge', AccountKind.INCOME, 'Mitgliederbeiträge'),
    ('3015', 'Freiwillige Beiträge von Mitgliedern', AccountKind.INCOME, 'Mitgliederbeiträge'),
    ('3020', 'Gönnerbeiträge', AccountKind.INCOME, 'Mitgliederbeiträge'),
    ('3100', 'Spenden von Privaten', AccountKind.INCOME, 'Erhaltene Zuwendungen'),
    ('3110', 'Legate und Vermächtnisse', AccountKind.INCOME, 'Erhaltene Zuwendungen'),
    ('3120', 'Subventionen / Spenden öffentlicher Hand', AccountKind.INCOME, 'Erhaltene Zuwendungen'),
    ('3130', 'Einnahmen Sammelaktionen', AccountKind.INCOME, 'Erhaltene Zuwendungen'),
    ('3300', 'Erlöse aus Materialverkäufen', AccountKind.INCOME, 'Aktivitäten und Leistungen'),
    ('3310', 'Einnahmen aus monatlichen Essen', AccountKind.INCOME, 'Aktivitäten und Leistungen'),
    ('3320', 'Erlöse aus Veranstaltungen', AccountKind.INCOME, 'Aktivitäten und Leistungen'),
    ('3340', 'Mieteinnahmen', AccountKind.INCOME, 'Aktivitäten und Leistungen'),
    ('3600', 'Inserate, Werbe- und Sponsoringeinnahmen', AccountKind.INCOME, 'Übrige Erlöse'),
    ('3610', 'Ertrag aus Liegenschaften', AccountKind.INCOME, 'Übrige Erlöse'),
    ('3620', 'Sonstige Erlöse (Bussen)', AccountKind.INCOME, 'Übrige Erlöse'),
    # Ausgaben
    ('4000', 'Waren und Materialaufwand', AccountKind.EXPENSE, 'Aufwand Aktivitäten'),
    ('4400', 'Aufwand für bezogene Dienstleistungen', AccountKind.EXPENSE, 'Aufwand Aktivitäten'),
    ('4500', 'Leistungen für Vereinszweck (Reisen / Ausflüge)', AccountKind.EXPENSE, 'Aufwand Aktivitäten'),
    ('5000', 'Lohnaufwand', AccountKind.EXPENSE, 'Personalaufwand'),
    ('6000', 'Raumaufwand (Mieten)', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6100', 'Ausgaben aus monatlichem Essen', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6200', 'Fahrzeug- und Transportaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6300', 'Sachversicherungen, Abgaben und Gebühren', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6400', 'Energie- und Entsorgungsaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6500', 'Büromaterial, Drucksachen, Fachliteratur', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6510', 'Telefon, Internet, Porti', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6530', 'Sekretariats-, Buchführungs- und Revisionsaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6540', 'Entschädigungen und Spesen Vorstand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6541', 'Aufwand Vereinsversammlung', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6542', 'Aufwand Vorstandssitzungen', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6570', 'Informatik- und Internetaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6660', 'Werbe- und Marketingaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6700', 'Sonstiger Vereinsaufwand', AccountKind.EXPENSE, 'Übriger Aufwand'),
    ('6800', 'Abschreibungen und Wertberichtigungen', AccountKind.EXPENSE, 'Abschreibungen'),
    ('6900', 'Zinsaufwendungen', AccountKind.EXPENSE, 'Finanzergebnis'),
    ('6940', 'Spesen und Gebühren (Kontoführung)', AccountKind.EXPENSE, 'Finanzergebnis'),
]

# Budget-Werte in Rappen pro Konto-Code (aus Excel «Jahresabschluss 2025»:
# Spalten Budget 2025 und Budget 2026; 6940 dort negativ ausgewiesen → Betrag).
BUDGETS = {
    2025: {
        '3000': 924000,
        '4500': 550000,
        '6510': 10000,
        '6541': 40000,
        '6542': 10000,
        '6660': 70000,
        '6940': 5000,
    },
    2026: {
        '3000': 948000,
        '3620': 10000,
        '4500': 930000,
        '6510': 5000,
        '6541': 40000,
        '6542': 40000,
        '6570': 20000,
        '6660': 90000,
        '6940': 10000,
    },
}

FISCAL_YEARS = range(2021, 2027)
CURRENT_OPEN_YEAR = 2026


def seed_accounts():
    created, updated = 0, 0
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
            # Namen/Gruppen nicht ueberschreiben (Admin darf editieren) –
            # nur sort_order nachziehen falls noch Default.
            if account.sort_order != sort_order:
                account.sort_order = sort_order
                updated += 1
    print(f"Konten: {created} angelegt, {updated} aktualisiert")


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
        seed_fiscal_years()
        db.session.flush()
        seed_budgets()
        db.session.commit()
        print("Seed abgeschlossen.")


if __name__ == '__main__':
    main()

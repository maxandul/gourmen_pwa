#!/usr/bin/env python3
"""Seed fuer das Buchhaltungsmodul (Phase 4 + 4b).

Legt an (idempotent, mehrfach ausfuehrbar ohne Fehler):
- Verschlankter Kontenplan gemaess docs/capabilities/accounting.md Sektion 6
- FiscalYears 2021-2026 inkl. membership_fee_rappen (2025/2026: CHF 840)
- Budget-Werte 2025 und 2026 (aus Erfolgsrechnung/Budget-Excel)
- Ist-Sammelbuchungen 2022-2025 aus den Erfolgsrechnungen (Sparkapital /
  Budget-vs-Ist fuer abgeschlossene Jahre). 2021 war laut Abschluss leer.
- Beitrags-Claims fuer das offene Jahr 2026 (neuer Workflow Offene Posten)
- Optional: lokale ZKB-CSVs unter vorlagen_buchhaltung/ als pending Import
  (nur wenn Datei vorhanden; Dedup via line_key)

2026-Einzelbuchungen werden NICHT geseedet — die kommen ueber den
ZKB-Import-Review (primaerer Buchungs-Workflow seit Phase 4b).

Quellen (lokal, gitignored):
- vorlagen_buchhaltung/20260324_Erfolgsrechnung 2025 und Budget 2026.xlsx
- vorlagen_buchhaltung/Vereinsfinanzen_2026.xlsx (Kostenstellen-Logik)
- vorlagen_buchhaltung/Kontoauszug 2025.csv / Kontoauszug 2026.csv

Aufruf lokal:    python scripts/seed_accounting_chart.py
Aufruf Railway:  railway ssh ... "/opt/venv/bin/python scripts/seed_accounting_chart.py"
"""

from __future__ import annotations

import os
import sys
from datetime import date
from io import BytesIO
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.accounting import (
    Account,
    AccountKind,
    Booking,
    BookingDirection,
    BudgetEntry,
    FiscalYear,
    FiscalYearStatus,
)
from backend.models.member import Funktion, Member, Role
from backend.services.accounting import AccountingService

# (code, name, kind, group_name) – Reihenfolge = sort_order
# Verschlankt 2026-07: nur Konten, die real bebucht werden.
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

# Alt-Codes aus dem PDF-Vorlagen-Kontenplan, die es im neuen Plan nicht mehr gibt.
LEGACY_CODES = [
    '3015', '3020', '3110', '3120', '3130', '3300', '3320', '3340',
    '3600', '3610',
    '4000', '4400', '5000', '6000', '6200', '6300', '6400', '6500',
    '6510', '6530', '6540', '6800', '6900',
]

# Budget in Rappen (Quelle: Erfolgsrechnung 2025 / Budget 2026, Sheet
# «Jahresabschluss 2025»; 6510 Telefon → 6570 IT/Telefon zusammengeführt).
BUDGETS = {
    2025: {
        '3000': 924000,
        '4500': 550000,
        '6541': 40000,
        '6542': 10000,
        '6570': 10000,   # ehem. 6510
        '6660': 70000,
        '6940': 5000,
    },
    2026: {
        '3000': 948000,  # Budget-Beschluss (nicht 11×840=9240)
        '3620': 10000,
        '4500': 930000,
        '6541': 40000,
        '6542': 40000,
        '6570': 25000,   # 6510 (50) + 6570 (200)
        '6660': 90000,
        '6940': 10000,
    },
}

# Jahresbeitrag pro Mitglied in Rappen (Vereinsfinanzen_2026.xlsx: 840 CHF).
MEMBERSHIP_FEES = {
    2022: 60000,
    2023: 60000,
    2024: 60000,
    2025: 84000,
    2026: 84000,
}

# Ist-Sammelbuchungen aus den Erfolgsrechnungen (CHF → werden in Rappen
# gewandelt). Richtung ergibt sich aus dem Kontenplan; 6940 steht in der
# Excel negativ (Finanzergebnis) → Betrag = abs(). 6800 Abschreibung −10.49
# (2025) ist faktisch eine Mehreinnahme → Konto 3620.
# Tuple: (ziel_code, betrag_chf) – betrag immer positiv.
IST_TOTALS = {
    2022: [
        ('3000', 6000.00),
        ('4500', 1000.00),
        ('6940', 37.00),
    ],
    2023: [
        ('3000', 6000.00),
        ('4500', 2931.30),
        ('6541', 200.00),
        ('6660', 507.89),
        ('6940', 46.00),
    ],
    2024: [
        ('3000', 6600.00),
        ('4500', 4063.75),
        ('6541', 350.00),
        ('6660', 693.00),
        ('6940', 31.50),
    ],
    2025: [
        ('3000', 9020.00),
        ('3310', 677.40),
        ('3620', 10.49),   # ehem. Abschreibung 6800 (−10.49)
        ('4500', 6940.50),
        ('6100', 700.00),
        ('6570', 19.90),   # ehem. 6510
        ('6541', 317.75),
        ('6542', 115.00),
        ('6940', 92.50),
    ],
}

FISCAL_YEARS = range(2021, 2027)
CURRENT_OPEN_YEAR = 2026

REPO_ROOT = Path(__file__).resolve().parent.parent
VORLAGEN_DIR = REPO_ROOT / 'vorlagen_buchhaltung'
# Nur offenes Jahr: pending-Zeilen in closed Jahren sind nicht verbuchbar.
OPTIONAL_CSV_IMPORTS = (
    'Kontoauszug 2026.csv',
)

SEED_PAYMENT_REF_PREFIX = 'SEED-IST-'


def _chf_to_rappen(amount_chf: float) -> int:
    return int(round(amount_chf * 100))


def _seed_actor() -> Member | None:
    """Schatzmeister oder Admin als created_by fuer Seed-Buchungen/Claims."""
    member = Member.query.filter_by(
        funktion=Funktion.SCHATZMEISTER, is_active=True,
    ).first()
    if member is None:
        member = Member.query.filter_by(role=Role.ADMIN, is_active=True).first()
    if member is None:
        member = Member.query.filter_by(is_active=True).first()
    return member


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
    created, updated_fees = 0, 0
    for year in FISCAL_YEARS:
        fy = FiscalYear.query.filter_by(year=year).first()
        fee = MEMBERSHIP_FEES.get(year)
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
                membership_fee_rappen=fee,
            )
            db.session.add(fy)
            created += 1
        elif fee is not None and fy.membership_fee_rappen != fee:
            fy.membership_fee_rappen = fee
            updated_fees += 1
    print(f"Geschäftsjahre: {created} angelegt, {updated_fees} Beiträge nachgezogen")


def seed_budgets():
    created, updated = 0, 0
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
            elif entry.amount_rappen != amount_rappen:
                entry.amount_rappen = amount_rappen
                updated += 1
    print(f"Budget-Einträge: {created} angelegt, {updated} aktualisiert")


def seed_historical_totals(actor: Member):
    """Eine Sammelbuchung pro Konto/Jahr aus den Erfolgsrechnungen (2022–2025).

    Idempotent über payment_ref = SEED-IST-{year}-{code}. Geschlossene Jahre
    werden direkt beschrieben (create_booking erlaubt nur offene Jahre).
    """
    created, skipped = 0, 0
    for year, rows in IST_TOTALS.items():
        fy = FiscalYear.query.filter_by(year=year).first()
        if fy is None:
            print(f"WARNUNG: Geschäftsjahr {year} fehlt, Ist-Buchungen übersprungen")
            continue
        for code, amount_chf in rows:
            account = Account.query.filter_by(code=code).first()
            if account is None:
                print(f"WARNUNG: Konto {code} fehlt, Ist {year} übersprungen")
                continue
            amount_rappen = _chf_to_rappen(amount_chf)
            if amount_rappen <= 0:
                continue
            payment_ref = f'{SEED_PAYMENT_REF_PREFIX}{year}-{code}'
            existing = Booking.query.filter_by(payment_ref=payment_ref).first()
            if existing is not None:
                skipped += 1
                continue
            direction = (
                BookingDirection.IN
                if account.kind == AccountKind.INCOME
                else BookingDirection.OUT
            )
            db.session.add(Booking(
                fiscal_year_id=fy.id,
                booking_date=date(year, 12, 31),
                description=f'Ist {year} (Seed aus Erfolgsrechnung)',
                amount_rappen=amount_rappen,
                direction=direction,
                account_id=account.id,
                payment_ref=payment_ref,
                created_by=actor.id,
            ))
            created += 1
    print(f"Ist-Sammelbuchungen: {created} angelegt, {skipped} bereits vorhanden")


def seed_contribution_claims(actor: Member):
    """Beitrags-Claims fuer das offene Jahr (Phase 4b Offene Posten)."""
    fy = FiscalYear.query.filter_by(year=CURRENT_OPEN_YEAR).first()
    if fy is None:
        print(f"WARNUNG: Offenes Jahr {CURRENT_OPEN_YEAR} fehlt, Claims übersprungen")
        return
    if not fy.membership_fee_rappen:
        print(f"WARNUNG: Jahr {fy.year} ohne membership_fee_rappen, Claims übersprungen")
        return
    created = AccountingService.create_claims_for_fiscal_year(fy.id, actor)
    print(f"Beitrags-Claims {fy.year}: {len(created)} angelegt")


def seed_optional_bank_imports(actor: Member):
    """Lokale ZKB-CSVs als pending Import einlesen (neuer Workflow).

    Auf Railway fehlen die gitignored Vorlagen typischerweise — dann no-op.
    Verbuchen bleibt Aufgabe des Schatzmeisters im Review-Screen.
    """
    from backend.services.bank_import import BankImportError, BankImportService

    present = [name for name in OPTIONAL_CSV_IMPORTS if (VORLAGEN_DIR / name).is_file()]
    if not present:
        print(
            "ZKB-CSV-Import: keine lokalen Vorlagen gefunden "
            f"(erwartet unter {VORLAGEN_DIR.name}/) – übersprungen. "
            "2026-Buchungen bitte via UI-Import nachziehen."
        )
        return

    for name in present:
        path = VORLAGEN_DIR / name
        try:
            with path.open('rb') as fh:
                data = fh.read()
            upload = BytesIO(data)
            upload.filename = name  # von BankImportService.import_statement gelesen
            statement = BankImportService.import_statement(upload, actor)
            print(
                f"ZKB-Import {name}: {statement.new_count} neu, "
                f"{statement.duplicate_count} Duplikate "
                f"({statement.pending_count} pending)"
            )
        except BankImportError as exc:
            print(f"WARNUNG: ZKB-Import {name} fehlgeschlagen: {exc}")


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
        db.session.flush()

        actor = _seed_actor()
        if actor is None:
            print(
                "WARNUNG: Kein aktives Mitglied gefunden – "
                "Ist-Buchungen, Claims und CSV-Import übersprungen."
            )
            db.session.commit()
            print("Seed abgeschlossen (ohne Buchungen/Claims).")
            return

        seed_historical_totals(actor)
        db.session.commit()

        seed_contribution_claims(actor)
        seed_optional_bank_imports(actor)
        print("Seed abgeschlossen.")
        print(
            "Hinweis: 2026-Einzelbuchungen entstehen über den ZKB-Import-Review, "
            "nicht als Seed-Sammelbuchungen."
        )


if __name__ == '__main__':
    main()

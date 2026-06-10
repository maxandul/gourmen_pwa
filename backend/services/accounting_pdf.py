"""AccountingPdfService – PDF-Erzeugung fuer Buchhaltung (Phase 4).

Revisorenbericht und Jahresabschluss mit reportlab (pure Python,
Railway-kompatibel). Spezifikation: docs/capabilities/accounting.md
Sektion 9.1 und 12. Saemtlicher PDF-Code lebt hier – nicht in Routes
oder im AccountingService.
"""

import logging
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

VEREIN_NAME = 'Verein Männliche Frohvollen (Gourmen)'

CONFIRMATION_TEXT = (
    'Der unterzeichnende Revisor bestätigt, dass die Buchhaltung des Vereins '
    'Männliche Frohvollen für das Geschäftsjahr {year} geprüft und für '
    'korrekt befunden wurde.'
)


def _chf(rappen: int) -> str:
    return f"CHF {(rappen or 0) / 100:,.2f}".replace(',', "'")


class AccountingPdfService:
    """Erzeugt Revisorenbericht und Jahresabschluss als PDF-Bytes."""

    @classmethod
    def generate_report(cls, fiscal_year, approval=None) -> bytes:
        """Erfolgsrechnung nach Kontengruppen als PDF.

        Mit `approval` (RevisionApproval) wird der Bestätigungsblock des
        Revisors angefuegt (Revisorenbericht); ohne entsteht der neutrale
        Jahresabschluss fuer Archiv/Export.
        """
        from backend.services.accounting import AccountingService

        summary = AccountingService.get_year_summary(fiscal_year.id)
        opening_balance = AccountingService.get_opening_balance(fiscal_year.id)
        groups = AccountingService.get_budget_grouped(fiscal_year.id)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=cls._title(fiscal_year, approval),
            author=VEREIN_NAME,
        )

        styles = getSampleStyleSheet()
        h1 = styles['Title']
        h2 = ParagraphStyle('h2', parent=styles['Heading2'], spaceBefore=10)
        body = styles['BodyText']
        small = ParagraphStyle('small', parent=body, fontSize=9, textColor=colors.grey)

        story = [
            Paragraph(VEREIN_NAME, h1),
            Paragraph(cls._title(fiscal_year, approval), h2),
            Paragraph(f"Erstellt am {date.today().strftime('%d.%m.%Y')}", small),
            Spacer(1, 6 * mm),
            Paragraph('Übersicht', h2),
            cls._summary_table(opening_balance, summary),
            Spacer(1, 4 * mm),
            Paragraph('Erfolgsrechnung nach Kontengruppen', h2),
            cls._groups_table(groups, summary),
        ]

        if approval is not None:
            story += cls._approval_block(fiscal_year, approval, h2, body)

        doc.build(story)
        payload = buffer.getvalue()
        buffer.close()
        logger.info(
            'PDF generiert: %s (%d Bytes, approval=%s)',
            cls._title(fiscal_year, approval), len(payload), approval is not None,
        )
        return payload

    # -- Bausteine ----------------------------------------------------------

    @staticmethod
    def _title(fiscal_year, approval) -> str:
        kind = 'Revisorenbericht' if approval is not None else 'Jahresabschluss'
        return f'{kind} {fiscal_year.year}'

    @staticmethod
    def _summary_table(opening_balance: int, summary: dict) -> Table:
        closing = opening_balance + summary['result_rappen']
        data = [
            ['Sparkapital zu Jahresbeginn', _chf(opening_balance)],
            ['Einnahmen', _chf(summary['income_rappen'])],
            ['Ausgaben', _chf(summary['expense_rappen'])],
            ['Jahresergebnis', _chf(summary['result_rappen'])],
            ['Sparkapital zu Jahresende', _chf(closing)],
        ]
        table = Table(data, colWidths=[100 * mm, 60 * mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 3), (-1, 3), 0.5, colors.black),
            ('FONTNAME', (0, 3), (-1, 4), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return table

    @staticmethod
    def _groups_table(groups: list[dict], summary: dict) -> Table:
        data = [['Kontengruppe', 'Konto', 'Betrag']]
        bold_rows = []
        for group in groups:
            for row in group['rows']:
                data.append([
                    '',
                    f"{row['account'].code} {row['account'].name}",
                    _chf(row['actual_rappen']),
                ])
            bold_rows.append(len(data))
            sign = '+' if group['kind'].value == 'income' else '−'
            data.append([
                f"Total {group['name']} ({sign})", '', _chf(group['actual_rappen']),
            ])
        bold_rows.append(len(data))
        data.append(['Jahresergebnis', '', _chf(summary['result_rappen'])])

        table = Table(data, colWidths=[60 * mm, 70 * mm, 35 * mm], repeatRows=1)
        style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        for row_idx in bold_rows:
            style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            style.append(('LINEABOVE', (0, row_idx), (-1, row_idx), 0.25, colors.grey))
        table.setStyle(TableStyle(style))
        return table

    @staticmethod
    def _approval_block(fiscal_year, approval, h2, body) -> list:
        reviewer_name = approval.reviewer.full_name if approval.reviewer else '–'
        return [
            Spacer(1, 8 * mm),
            Paragraph('Bestätigung der Revision', h2),
            Paragraph(CONFIRMATION_TEXT.format(year=fiscal_year.year), body),
            Spacer(1, 4 * mm),
            Paragraph(f'Revisor: {reviewer_name}', body),
            Paragraph(
                f"Bestätigt am: {approval.approved_at.strftime('%d.%m.%Y')}", body
            ),
        ]

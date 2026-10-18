"""Identify persisted settlement history without reinterpreting old payments."""
from backend.models.accounting import MemberClaim, ClaimType
from backend.models.participation import Participation


class BillBroStateService:
    @staticmethod
    def requires_correction(event):
        return (event.gesamtbetrag_rappen is not None or
                any(getattr(event, field) is not None for field in
                    ('betrag_sparsam_rappen', 'betrag_normal_rappen', 'betrag_allin_rappen')) or
                Participation.query.filter(Participation.event_id == event.id,
                    Participation.calculated_share_rappen.isnot(None)).first() is not None or
                MemberClaim.query.filter_by(event_id=event.id, claim_type=ClaimType.ESSENSANTEIL).first() is not None)

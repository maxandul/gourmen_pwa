"""Purpose-limited sensitive field views, separate from full admin editing."""
from flask_login import current_user
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService


class MemberSensitiveService:
    TRAVEL_FIELDS = (
        ('pass_nummer', 'Passnummer'),
        ('pass_ausgestellt', 'Pass ausgestellt'),
        ('pass_ablauf', 'Pass ablaeuft'),
        ('id_nummer', 'ID-Nummer'),
        ('id_ausgestellt', 'ID ausgestellt'),
        ('id_ablauf', 'ID ablaeuft'),
    )

    @staticmethod
    def can_read_travel(actor):
        return bool(actor and actor.is_active and
                    (actor.is_admin() or actor.has_funktion('REISEKOMMISSAR')))

    @classmethod
    def read_travel(cls, actor, target_id):
        # Both checks precede decryption. A fresh session alone grants no role.
        if (not cls.can_read_travel(actor) or current_user.get_id() != actor.get_id()
                or not SecurityService.check_step_up_access()):
            raise PermissionError('Reisedokumentzugriff nicht erlaubt')
        sensitive = MemberSensitive.query.filter_by(member_id=target_id).first()
        payload = SecurityService.read_member_sensitive(sensitive.payload_encrypted) if sensitive else {}
        return [(label, payload.get(key) or '') for key, label in cls.TRAVEL_FIELDS]

"""Personal display preferences, never evidence of a private payment."""
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData
from backend.extensions import db
from backend.models.accounting import MemberClaim, ClaimType, ClaimStatus


class ReminderError(ValueError):
    pass


class PrivateReminderService:
    @staticmethod
    def serializer():
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'],salt='private-reminder-v1')

    @staticmethod
    def query(actor):
        if not actor or not actor.is_active:
            raise ReminderError('Aktiver eigener Zugang erforderlich.')
        return MemberClaim.query.filter(MemberClaim.member_id==actor.id,
            MemberClaim.creditor_member_id.isnot(None),MemberClaim.claim_type==ClaimType.ESSENSANTEIL,
            MemberClaim.expected_rappen>0,MemberClaim.status!=ClaimStatus.ERLASSEN)

    @staticmethod
    def state(claim):
        return dict(amount=claim.expected_rappen,creditor=claim.creditor_member_id)

    @classmethod
    def token(cls,claim,actor):
        if claim.member_id!=actor.id:
            raise ReminderError('Nur die eigene Erinnerung kann geaendert werden.')
        return cls.serializer().dumps(dict(actor=actor.id,generation=actor.auth_generation,claim=claim.id,
            state=cls.state(claim),version=claim.private_reminder_version,hidden=not claim.private_reminder_hidden))

    @classmethod
    def rows(cls,actor,*,include_hidden=False,event_id=None):
        query=cls.query(actor)
        if not include_hidden:
            query=query.filter_by(private_reminder_hidden=False)
        if event_id is not None:
            query=query.filter_by(event_id=event_id)
        return [dict(claim=c,token=cls.token(c,actor)) for c in query.order_by(MemberClaim.created_at.desc(),MemberClaim.id.desc())]

    @classmethod
    def undo_row(cls,actor,claim_id):
        if not claim_id:
            return None
        claim=cls.query(actor).filter_by(id=claim_id,private_reminder_hidden=True).first()
        return dict(claim=claim,token=cls.token(claim,actor)) if claim else None

    @classmethod
    def toggle(cls,claim_id,actor,action,token):
        try:
            if action not in ('hide','show'):
                raise ReminderError('Unbekannte Anzeigeaktion.')
            hidden=action=='hide'
            try:
                payload=cls.serializer().loads(token,max_age=1800)
            except (BadData,TypeError):
                raise ReminderError('Anzeigeformular ungueltig oder abgelaufen. Neu laden.') from None
            if payload.get('actor')!=actor.id or payload.get('generation')!=actor.auth_generation or payload.get('claim')!=claim_id or payload.get('hidden') is not hidden:
                raise ReminderError('Anzeigeformular passt nicht zu diesem Zugang oder dieser Aktion.')
            claim=cls.query(actor).filter_by(id=claim_id).populate_existing().with_for_update().first()
            if not claim or payload['state']!=cls.state(claim):
                raise ReminderError('Eigener Betrag oder Empfaenger geaendert. Neu laden.')
            if claim.private_reminder_version==payload['version']+1 and claim.private_reminder_hidden==hidden:
                db.session.rollback(); return False
            if claim.private_reminder_version!=payload['version']:
                raise ReminderError('Anzeigezustand inzwischen geaendert. Neu laden.')
            claim.private_reminder_hidden=hidden
            claim.private_reminder_changed=False
            claim.private_reminder_version+=1
            db.session.commit()
            return True
        except ReminderError:
            db.session.rollback(); raise
        except Exception:
            db.session.rollback()
            raise ReminderError('Anzeige nicht gespeichert. Aktuellen Stand pruefen.') from None

    @staticmethod
    def copy_for_correction(old,new):
        """Copy only unchanged personal choices; never infer a private payment."""
        if new.creditor_member_id is None or old is None:
            return
        same=(old.creditor_member_id,old.expected_rappen)==(new.creditor_member_id,new.expected_rappen)
        new.private_reminder_hidden=bool(old.private_reminder_hidden) if same else False
        new.private_reminder_changed=bool(old.private_reminder_changed) if same else True
        new.private_reminder_version=0

    @staticmethod
    def before_sync(claim,amount,creditor):
        if claim.creditor_member_id is None and creditor is None:
            return
        if (claim.expected_rappen,claim.creditor_member_id)==(amount,creditor):
            return
        claim.private_reminder_hidden=False
        claim.private_reminder_changed=creditor is not None
        claim.private_reminder_version=(claim.private_reminder_version or 0)+1

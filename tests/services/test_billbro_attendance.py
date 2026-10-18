"""RSVP evidence, financial effects and GGL stay separate and atomic."""
from datetime import datetime
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim
from backend.models.billbro_correction import BillBroCorrection
from tests.services.test_billbro_correction import final_round, preview, confirm, url
from tests.services.test_billbro_invoice_correction import seed_guesses
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot


def correction_form(**updates):
    values = dict(invoice='100', total='100', paid_by='vereinskonto', reason='Actual attendance corrected')
    values.update(updates)
    return values


@pytest.mark.parametrize('rsvp', [True, False, None])
def test_organizer_attendance_preserves_original_answer_and_inputs(app, client, round_data, rsvp):
    with app.app_context():
        part = Participation.query.filter_by(member_id=round_data[0]).one()
        part.teilnahme = rsvp
        part.responded_at = datetime(2026, 1, 2) if rsvp is not None else None
        part.guess_bill_amount_rappen = 9900
        db.session.commit()
        old_answer = (part.teilnahme, part.responded_at)
    for endpoint, expected in [('mark_absent', False), ('mark_present', True)]:
        assert client.post(f'/billbro/{round_data[1]}/{endpoint}/{round_data[0]}').status_code == 302
        with app.app_context():
            part = Participation.query.filter_by(member_id=round_data[0]).one()
            assert (part.teilnahme, part.responded_at) == old_answer
            assert part.billbro_attending is expected
            assert part.esstyp == Esstyp.NORMAL and part.guess_bill_amount_rappen == 9900
            assert Participation.query.filter_by(billbro_attending=expected, member_id=round_data[0]).count() == 1
    response = client.get(f'/events/{round_data[1]}?tab=billbro')
    assert response.status_code == 200
    assert ('Keine Antwort' if rsvp is None else 'Zugesagt' if rsvp else 'Abgesagt') in response.text


def test_absence_correction_recomputes_claims_and_ggl_without_changing_rsvp(app, client, final_round):
    seed_guesses(app, final_round)
    with app.app_context():
        part = Participation.query.order_by(Participation.member_id).first()
        pid, mid = part.id, part.member_id
    before = snapshot(app, final_round[1])
    values = correction_form(**{f'attendance_{pid}': 'absent'})
    response = client.post(url(final_round), data=values)
    assert response.status_code == 200 and 'GGL: bisher' in response.text
    assert snapshot(app, final_round[1]) == before
    token = preview(client, final_round, values)
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        part = db.session.get(Participation, pid)
        assert part.teilnahme is True and not part.billbro_attending
        assert part.esstyp == Esstyp.NORMAL and part.guess_bill_amount_rappen == 10000
        assert part.calculated_share_rappen is None and part.points is None and part.rank is None
        claims = MemberClaim.query.all()
        assert len(claims) == 2 and all(c.expected_rappen == 5000 and c.member_id != mid for c in claims)
        assert [(p.rank, p.points) for p in Participation.query.filter_by(billbro_attending=True)] == [(1.5, 1.5), (1.5, 1.5)]
        history = BillBroCorrection.query.one()
        assert history.before_json['participations'][0]['teilnahme'] is True
        assert history.after_json['participations'][0]['teilnahme'] is True
        assert history.after_json['participations'][0]['billbro_attendance'] is False
    assert confirm(client, final_round, token).status_code == 302
    assert client.get(url(final_round)).status_code == 200


def new_member(app, active=True):
    with app.app_context():
        member = Member(vorname='New', nachname='Synthetic', email='new-attendee@example.com', is_active=active, passwort_hash='unused', password_changed_at=datetime(2026, 1, 1))
        db.session.add(member)
        db.session.commit()
        return member.id


def test_new_attendee_only_created_on_confirm_without_fabricated_rsvp(app, client, final_round):
    mid = new_member(app)
    values = correction_form(**{f'attendance_{-mid}': 'present', f'esstyp_{-mid}': 'NORMAL'})
    token = preview(client, final_round, values)
    with app.app_context():
        assert Participation.query.filter_by(member_id=mid).first() is None
    assert confirm(client, final_round, token).status_code == 302
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        part = Participation.query.filter_by(member_id=mid).one()
        assert part.teilnahme is None and part.responded_at is None and part.billbro_attending
        assert part.guess_bill_amount_rappen is None and part.points is None
        assert part.calculated_share_rappen == 2500
        assert sum(c.expected_rappen for c in MemberClaim.query.all()) == 10000
        assert BillBroCorrection.query.count() == 1
    response = client.get(f'/events/{final_round[1]}?tab=billbro')
    assert response.status_code == 200 and 'Keine Antwort' in response.text


@pytest.mark.parametrize('failure_target', [Participation, BillBroCorrection])
def test_new_attendee_insert_or_history_failure_rolls_back_everything(app, client, final_round, failure_target):
    mid = new_member(app)
    token = preview(client, final_round, correction_form(**{f'attendance_{-mid}': 'present', f'esstyp_{-mid}': 'NORMAL'}))
    before = snapshot(app, final_round[1])
    def fail(*args):
        raise OperationalError('synthetic', {}, Exception('synthetic'))
    sa_event.listen(failure_target, 'before_insert', fail)
    try:
        assert confirm(client, final_round, token).status_code == 400
    finally:
        sa_event.remove(failure_target, 'before_insert', fail)
    assert snapshot(app, final_round[1]) == before
    assert confirm(client, final_round, token).status_code == 302


def test_candidate_loses_eligibility_after_preview(app, client, final_round):
    mid = new_member(app)
    token = preview(client, final_round, correction_form(**{f'attendance_{-mid}': 'present', f'esstyp_{-mid}': 'NORMAL'}))
    with app.app_context():
        db.session.get(Member, mid).is_active = False
        db.session.commit()
    before = snapshot(app, final_round[1])
    assert confirm(client, final_round, token).status_code == 400
    assert snapshot(app, final_round[1]) == before


@pytest.mark.parametrize('value', ['unknown', ''])
def test_invalid_attendance_retained_without_writes(app, client, final_round, value):
    with app.app_context():
        pid = Participation.query.first().id
    before = snapshot(app, final_round[1])
    response = client.post(url(final_round), data=correction_form(**{f'attendance_{pid}': value}))
    assert response.status_code == 400 and 'ungültig' in response.text
    assert snapshot(app, final_round[1]) == before


def test_first_finalization_uses_actual_attendance(app, client, round_data):
    assert client.post(f'/billbro/{round_data[1]}/mark_absent/{round_data[0]}').status_code == 302
    assert client.post(f'/billbro/{round_data[1]}/set_total', data={'gesamtbetrag_manual': '100'}).status_code == 302
    with app.app_context():
        assert Participation.query.filter_by(member_id=round_data[0]).one().teilnahme is True
        assert [c.expected_rappen for c in MemberClaim.query.all()] == [5000, 5000]


@pytest.mark.parametrize('active', [True, False])
def test_pre_final_new_person_keeps_missing_response_and_checks_eligibility(app, client, round_data, active):
    mid = new_member(app, active)
    assert client.post(f'/billbro/{round_data[1]}/mark_present/{mid}').status_code == 302
    with app.app_context():
        part = Participation.query.filter_by(member_id=mid).first()
        if active:
            assert part.teilnahme is None and part.responded_at is None and part.billbro_attending
        else:
            assert part is None


def test_round_close_keeps_missing_and_original_rsvp(app, client, round_data):
    with app.app_context():
        part = Participation.query.order_by(Participation.member_id.desc()).first()
        pid = part.id
        part.teilnahme = None
        db.session.commit()
    assert client.post(f'/billbro/{round_data[1]}/toggle_status').status_code == 302
    with app.app_context():
        part = db.session.get(Participation, pid)
        assert part.teilnahme is None and part.billbro_attendance is False
        assert db.session.get(Event, round_data[1]).billbro_closed


@pytest.mark.parametrize('invalid', ['all_absent', 'absent_payer', 'unknown_member', 'missing_type'])
def test_invalid_correction_preserves_original_round(app, client, final_round, invalid):
    with app.app_context():
        parts = Participation.query.order_by(Participation.id).all()
        pid, mid = parts[0].id, parts[0].member_id
        ids = [p.id for p in parts]
    values = correction_form()
    if invalid == 'all_absent':
        values.update({f'attendance_{i}': 'absent' for i in ids})
    elif invalid == 'absent_payer':
        values.update(paid_by='mitglied', payer_member_id=str(mid))
        values[f'attendance_{pid}'] = 'absent'
    elif invalid == 'unknown_member':
        values['attendance_-9999'] = 'present'
    else:
        new_id = new_member(app)
        values[f'attendance_{-new_id}'] = 'present'
    before = snapshot(app, final_round[1])
    assert client.post(url(final_round), data=values).status_code == 400
    assert snapshot(app, final_round[1]) == before


def test_old_preview_without_attendance_rejected(app, client, final_round):
    from itsdangerous import URLSafeTimedSerializer
    from backend.services.billbro_correction import BillBroCorrectionService
    token = preview(client, final_round, correction_form(total='110'))
    with app.app_context():
        payload = BillBroCorrectionService.serializer().loads(token)
        payload['proposed'].pop('attendance')
        old = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='billbro-correction-v3').dumps(payload)
    before = snapshot(app, final_round[1])
    assert confirm(client, final_round, old).status_code == 400
    assert snapshot(app, final_round[1]) == before


@pytest.mark.parametrize('attending', [True, False])
def test_rating_write_eligibility_follows_actual_attendance(app, client, round_data, attending):
    from backend.models.rating import EventRating
    from tests.conftest import auth_id
    with app.app_context():
        part = Participation.query.order_by(Participation.member_id.desc()).first()
        mid = part.member_id
        part.teilnahme = not attending
        part.billbro_attendance = attending
        part.event.allow_ratings = True
        db.session.commit()
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, mid)
        state['_fresh'] = True
    response = client.post(f'/ratings/event/{round_data[1]}/rate', data={'food_rating': '4', 'drinks_rating': '4', 'service_rating': '4', 'comment': 'Synthetic'})
    assert response.status_code == 302
    with app.app_context():
        assert EventRating.query.filter_by(participant_id=mid).count() == int(attending)



def test_pre_final_attendance_failure_keeps_rsvp_and_all_game_values(app, client, round_data):
    seed_guesses(app, round_data)
    before = snapshot(app, round_data[1])
    def fail(*args):
        raise OperationalError('synthetic', {}, Exception('synthetic'))
    sa_event.listen(Participation, 'before_update', fail)
    try:
        assert client.post(f'/billbro/{round_data[1]}/mark_absent/{round_data[0]}').status_code == 302
    finally:
        sa_event.remove(Participation, 'before_update', fail)
    assert snapshot(app, round_data[1]) == before
    assert client.post(f'/billbro/{round_data[1]}/mark_absent/{round_data[0]}').status_code == 302
    with app.app_context():
        assert not Participation.query.filter_by(member_id=round_data[0]).one().billbro_attending


def test_board_event_does_not_offer_or_accept_non_board_new_attendee(app, client, final_round):
    from backend.models.event import EventAudience
    mid = new_member(app)
    with app.app_context():
        db.session.get(Event, final_round[1]).audience = EventAudience.BOARD
        db.session.commit()
    response = client.get(url(final_round))
    assert response.status_code == 200 and f'attendance_{-mid}' not in response.text
    before = snapshot(app, final_round[1])
    assert client.post(url(final_round), data=correction_form(**{f'attendance_{-mid}': 'present', f'esstyp_{-mid}': 'NORMAL'})).status_code == 400
    assert snapshot(app, final_round[1]) == before

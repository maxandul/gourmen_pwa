from types import SimpleNamespace
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.participation import Participation
from backend.models.billbro_correction import BillBroCorrection
from backend.services.ggl_rules import GGLService
from tests.services.test_billbro_correction import final_round, preview, confirm, url
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot


def test_pure_ggl_zero_difference_and_fractional_ties():
    parts = [SimpleNamespace(id=i, member_id=i, teilnahme=True, guess_bill_amount_rappen=g) for i,g in [(3,11000),(1,10000),(2,9000)]]
    values = GGLService.project_points(parts, 10000)
    assert values[1] == dict(diff_amount_rappen=0, rank=1, points=3)
    assert values[2] == values[3] == dict(diff_amount_rappen=1000, rank=2.5, points=1.5)
    assert GGLService.project_points(list(reversed(parts)), 10000) == values


def seed_guesses(app, ids):
    with app.app_context():
        parts = Participation.query.order_by(Participation.member_id).all()
        for part, guess in zip(parts, [10000,11000,9000]): part.guess_bill_amount_rappen=guess
        db.session.flush()
        GGLService.calculate_event_points(ids[1])


def form(**updates):
    values = dict(invoice='105', total='120', paid_by='vereinskonto', reason='Correct restaurant invoice')
    values.update(updates); return values


def test_invoice_preview_and_confirm_preserve_fractional_results(app, client, final_round):
    seed_guesses(app, final_round)
    before = snapshot(app, final_round[1])
    response = client.post(url(final_round), data=form())
    assert response.status_code == 200 and 'GGL: bisher → neu' in response.text and '1.5' in response.text
    assert snapshot(app, final_round[1]) == before
    token = preview(client, final_round, form())
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        db.session.expire_all()
        event = db.session.get(Event, final_round[1]); parts = Participation.query.order_by(Participation.member_id).all()
        assert (event.rechnungsbetrag_rappen,event.gesamtbetrag_rappen,event.trinkgeld_rappen) == (10500,12000,1500)
        assert [(p.rank,p.points) for p in parts] == [(1.5,2.5),(1.5,2.5),(3,1)]
        assert [p.guess_bill_amount_rappen for p in parts] == [10000,11000,9000]
        history = BillBroCorrection.query.one()
        assert history.before_json['participations'][0]['rank'] == 1
        assert history.after_json['participations'][0]['rank'] == 1.5
    response = client.get(url(final_round))
    assert response.status_code == 200 and 'Nachher: GGL' in response.text and 'Rang 1.5' in response.text
    response = client.get(f'/events/{final_round[1]}?tab=billbro')
    assert response.status_code == 200 and 'col-rank">1.5</td>' in response.text


@pytest.mark.parametrize('invoice',['NaN','-1','0','99.999','121'])
def test_invalid_invoice_keeps_original_state(app, client, final_round, invoice):
    before = snapshot(app, final_round[1])
    assert client.post(url(final_round), data=form(invoice=invoice)).status_code == 400
    assert snapshot(app, final_round[1]) == before


def test_invoice_only_change_accepted_and_history_failure_rolls_back_ggl(app, client, final_round):
    seed_guesses(app, final_round)
    token = preview(client, final_round, form(invoice='95',total='100'))
    before = snapshot(app, final_round[1])
    def fail(*args): raise OperationalError('synthetic', {}, Exception('synthetic'))
    sa_event.listen(BillBroCorrection,'before_insert',fail)
    try: assert confirm(client, final_round, token).status_code == 400
    finally: sa_event.remove(BillBroCorrection,'before_insert',fail)
    assert snapshot(app, final_round[1]) == before
    assert confirm(client, final_round, token).status_code == 302


def test_non_ggl_invoice_does_not_invent_game_points(app, client, final_round):
    with app.app_context():
        db.session.get(Event, final_round[1]).event_typ = EventType.AUSFLUG; db.session.commit()
    token = preview(client, final_round, form())
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context(): assert all(p.rank is None and p.points is None for p in Participation.query.all())


def test_first_invoice_uses_same_exact_match_ranking(app, client, round_data):
    with app.app_context():
        parts=Participation.query.order_by(Participation.member_id).all()
        for part,guess in zip(parts,[10000,9000,11000]): part.guess_bill_amount_rappen=guess
        db.session.commit()
    response=client.post(f'/billbro/{round_data[1]}/enter_bill',data={'rechnungsbetrag':'100'})
    assert response.status_code==302
    with app.app_context():
        assert [(p.rank,p.points) for p in Participation.query.order_by(Participation.member_id)]==[(1,3),(2.5,1.5),(2.5,1.5)]


def test_missing_guess_and_absence_do_not_get_points():
    parts = [SimpleNamespace(id=1,member_id=1,teilnahme=True,guess_bill_amount_rappen=None),
             SimpleNamespace(id=2,member_id=2,teilnahme=False,guess_bill_amount_rappen=10000),
             SimpleNamespace(id=3,member_id=3,teilnahme=True,guess_bill_amount_rappen=10000)]
    projected = GGLService.project_points(parts,10000)
    assert projected[1] == projected[2] == dict(diff_amount_rappen=None,rank=None,points=None)
    assert projected[3] == dict(diff_amount_rappen=0,rank=1,points=1)


def test_old_b1_preview_cannot_be_confirmed(app,client,final_round):
    from itsdangerous import URLSafeTimedSerializer
    from backend.services.billbro_correction import BillBroCorrectionService
    token = preview(client,final_round,form())
    with app.app_context():
        payload = BillBroCorrectionService.serializer().loads(token)
        payload['proposed'].pop('invoice')
        old_token = URLSafeTimedSerializer(app.config['SECRET_KEY'],salt='billbro-correction-v1').dumps(payload)
    assert confirm(client,final_round,old_token).status_code == 400
    with app.app_context(): assert BillBroCorrection.query.count() == 0

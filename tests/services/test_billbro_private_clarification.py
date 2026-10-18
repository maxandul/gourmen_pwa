"""Private zero counters are not evidence that nobody paid outside the app."""
import pytest
from backend.extensions import db
from backend.models.accounting import MemberClaim
from backend.models.billbro_correction import BillBroCorrection
from backend.services.billbro_correction import BillBroCorrectionService
from tests.services.test_billbro_correction import final_round, preview, confirm, url
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot


@pytest.fixture
def private_round(app, client, final_round):
    token = preview(client, final_round, dict(total='100', paid_by='mitglied', payer_member_id=str(final_round[0]), reason='Synthetic private payer'))
    assert confirm(client, final_round, token).status_code == 302
    return final_round


def values(ids, **updates):
    result = dict(total='120', paid_by='mitglied', payer_member_id=str(ids[0]), reason='Synthetic correction',
                  private_unpaid_confirmed='yes', private_unpaid_note='Synthetic discussion: nobody has paid')
    result.update(updates)
    return result


@pytest.mark.parametrize('updates', [
    {'private_unpaid_confirmed': ''}, {'private_unpaid_confirmed': 'no'},
    {'private_unpaid_confirmed': 'true'}, {'private_unpaid_note': ''},
    {'private_unpaid_note': '   '}, {'private_unpaid_note': 'x' * 1001},
])
def test_zero_counter_without_explicit_valid_clarification_cannot_write(app, client, private_round, updates):
    before = snapshot(app, private_round[1])
    response = client.post(url(private_round), data=values(private_round, **updates))
    assert response.status_code == 400 and 'Private Zahlungen sind der App unbekannt' in response.text
    assert snapshot(app, private_round[1]) == before


def test_signed_clarification_preserved_even_if_unsigned_fields_replaced(app, client, private_round):
    note = 'Synthetic <discussion>: no payments'
    token = preview(client, private_round, values(private_round, private_unpaid_note=note))
    response = client.post(url(private_round), data=dict(action='confirm', preview_token=token,
        private_unpaid_confirmed='no', private_unpaid_note='Unsigned replacement'))
    assert response.status_code == 302
    after = snapshot(app, private_round[1])
    assert confirm(client, private_round, token).status_code == 302
    assert snapshot(app, private_round[1]) == after
    with app.app_context():
        history = BillBroCorrection.query.order_by(BillBroCorrection.id.desc()).first()
        assert history.after_json['private_unpaid_clarification']['note'] == note
        assert BillBroCorrection.query.count() == 2
        assert all(c.paid_rappen == 0 for c in MemberClaim.query.all())
    response = client.get(url(private_round))
    assert response.status_code == 200 and '&lt;discussion&gt;' in response.text
    assert 'Erklärung, kein Banknachweis' in response.text and 'Unsigned replacement' not in response.text


@pytest.mark.parametrize('after_preview', [False, True])
def test_statement_never_overrides_recorded_payment(app, client, private_round, after_preview):
    token = preview(client, private_round, values(private_round)) if after_preview else None
    with app.app_context():
        MemberClaim.query.first().register_payment(100)
        db.session.commit()
    before = snapshot(app, private_round[1])
    response = confirm(client, private_round, token) if after_preview else client.post(url(private_round), data=values(private_round))
    assert response.status_code == 400
    assert snapshot(app, private_round[1]) == before


def test_old_token_without_clarification_contract_rejected(app, client, private_round):
    from itsdangerous import URLSafeTimedSerializer
    token = preview(client, private_round, values(private_round))
    with app.app_context():
        payload = BillBroCorrectionService.serializer().loads(token)
        payload['proposed'].pop('private_unpaid_confirmed')
        payload['proposed'].pop('private_unpaid_note')
        old = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='billbro-correction-v4').dumps(payload)
    before = snapshot(app, private_round[1])
    assert confirm(client, private_round, old).status_code == 400
    assert snapshot(app, private_round[1]) == before

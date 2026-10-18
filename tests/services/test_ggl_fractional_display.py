"""Fractional event results survive season aggregation and personal views."""
import pytest
from flask import template_rendered
from backend.extensions import db
from backend.models.participation import Participation
from backend.services.ggl_rules import GGLService
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.mark.parametrize('invoice,expected_points,expected_ranks', [
    (10000, [3, 1.5, 1.5], [1, 2, 2]),
    (10500, [2.5, 2.5, 1], [1, 1, 3]),
])
def test_fractional_totals_ties_and_original_personal_page(
        app, client, round_data, invoice, expected_points, expected_ranks):
    with app.app_context():
        parts = Participation.query.order_by(Participation.member_id).all()
        member_ids = [p.member_id for p in parts]
        for part, guess in zip(parts, [10000, 11000, 9000]):
            part.guess_bill_amount_rappen = guess
        parts[0].event.rechnungsbetrag_rappen = invoice
        db.session.flush()
        GGLService.calculate_event_points(round_data[1])
        ranking = {row['member_id']: row for row in GGLService.get_season_ranking(2026)}
        for mid, points, rank in zip(member_ids, expected_points, expected_ranks):
            context = GGLService.get_member_performance_view_context(mid, 2026)
            assert context['user_points'] == points
            assert context['rank'] == ranking[mid]['rank'] == rank
        last = GGLService.get_member_performance_view_context(member_ids[-1], 2026)
        if invoice == 10000:
            assert last['show_equal_above'] and not last['show_gap_above']
        else:
            assert last['gap_above_points'] == 1.5
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, member_ids[-1])
        state['_fresh'] = True
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    template_rendered.connect(capture, app)
    try:
        response = client.get('/ggl/?tab=performance&season=2026')
    finally:
        template_rendered.disconnect(capture, app)
    assert response.status_code == 200
    assert contexts[-1]['current_stats']['rank'] == expected_ranks[-1]
    assert contexts[-1]['performance_context']['user_points'] == expected_points[-1]
    assert f'>{expected_ranks[-1]}</span>' in response.text

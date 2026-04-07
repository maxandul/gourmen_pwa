"""Aggregierte Statistiken für vergangene Monatsessen (Events-Index Tab Statistiken)."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

from sqlalchemy import and_, or_

from backend.models.event import Event, EventType
from backend.models.member import Member
from backend.models.participation import Participation, Esstyp
from backend.models.rating import EventRating

_SHORT_MONTHS_DE = (
    'Jan', 'Feb', 'Mrz', 'Apr', 'Mai', 'Jun',
    'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez',
)


def _member_eligible_for_event(member: Member, event: Event) -> bool:
    if not member.is_active:
        return False
    if member.beitritt and event.datum.date() < member.beitritt:
        return False
    return True


def _event_restaurant_label(event: Event) -> str:
    return (event.restaurant or event.place_name or '').strip() or '—'


def _homepage_for_restaurant_label(past_ms: list[Event], label: str) -> str | None:
    """Neuestes Event mit gleichem Restaurant-Label: Website bevorzugt `place_website`, sonst `website`."""
    matching = [e for e in past_ms if _event_restaurant_label(e) == label]
    matching.sort(key=lambda e: e.datum, reverse=True)
    for e in matching:
        u = (e.place_website or e.website or '').strip()
        if u:
            return u
    return None


def _meta_for_restaurant_label(past_ms: list[Event], label: str) -> tuple[str | None, str | None]:
    """Nimmt das neueste Event je Restaurant-Label und liefert Küche + Adresse für Suche/Anzeige."""
    matching = [e for e in past_ms if _event_restaurant_label(e) == label]
    matching.sort(key=lambda e: e.datum, reverse=True)
    if not matching:
        return None, None
    ev = matching[0]
    cuisine = (ev.kueche or '').strip() or None
    address = (ev.place_address or '').strip() or None
    return cuisine, address


def get_landing_extras(now: datetime) -> dict[str, Any]:
    """Letztes besuchtes Restaurant (Monatsessen) und Datum des nächsten Monatsessens für die Landingpage."""
    last_ev = (
        Event.query.filter(
            Event.published.is_(True),
            Event.event_typ == EventType.MONATSESSEN,
            Event.datum < now,
            or_(
                and_(Event.restaurant.isnot(None), Event.restaurant != ''),
                and_(Event.place_name.isnot(None), Event.place_name != ''),
            ),
        )
        .order_by(Event.datum.desc())
        .first()
    )
    last_restaurant = _event_restaurant_label(last_ev) if last_ev else None

    next_ms = (
        Event.query.filter(
            Event.published.is_(True),
            Event.event_typ == EventType.MONATSESSEN,
            Event.datum >= now,
        )
        .order_by(Event.datum.asc())
        .first()
    )
    next_essen_date = None
    next_essen_restaurant = None
    if next_ms:
        month_idx = max(1, min(12, next_ms.datum.month)) - 1
        month_short = _SHORT_MONTHS_DE[month_idx]
        next_essen_date = f"{next_ms.datum.day:02d}. {month_short} {next_ms.datum.year % 100:02d}"
        next_essen_restaurant = (next_ms.restaurant or next_ms.place_name or '').strip() or 'TBD'

    return {
        'last_restaurant': last_restaurant,
        'next_essen_date': next_essen_date,
        'next_essen_restaurant': next_essen_restaurant,
    }


def get_landing_restaurant_table(
    now: datetime,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Öffentliche Landing: Monatsessen-Restaurants mit mindestens einer Bewertung,
    sortiert nach Ø Gesamtbewertung absteigend. Paginierung ab 1.
    """
    past_ms: list[Event] = (
        Event.query.filter(
            Event.published.is_(True),
            Event.event_typ == EventType.MONATSESSEN,
            Event.datum < now,
        )
        .order_by(Event.datum.asc())
        .all()
    )
    if not past_ms:
        return [], 0, 1, 1

    event_ids = [e.id for e in past_ms]
    ratings_rows: list[EventRating] = EventRating.query.filter(
        EventRating.event_id.in_(event_ids)
    ).all()
    event_to_restaurant_label: dict[int, str] = {
        ev.id: _event_restaurant_label(ev) for ev in past_ms
    }
    restaurant_rating_vals: dict[str, list[float]] = defaultdict(list)
    for row in ratings_rows:
        eid = row.event_id
        label = event_to_restaurant_label.get(eid, '—')
        restaurant_rating_vals[label].append(float(row.average_rating))

    rows_full: list[dict[str, Any]] = []
    for label, ovs in restaurant_rating_vals.items():
        if not ovs:
            continue
        cuisine, address = _meta_for_restaurant_label(past_ms, label)
        rows_full.append(
            {
                'restaurant': label,
                'overall_avg': round(mean(ovs), 1),
                'homepage': _homepage_for_restaurant_label(past_ms, label),
                'kueche': cuisine,
                'adresse': address,
            }
        )
    rows_full.sort(key=lambda x: (-x['overall_avg'], x['restaurant']))

    total = len(rows_full)
    total_pages = max(1, (total + per_page - 1) // per_page) if total > 0 else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_rows = rows_full[start : start + per_page]
    return page_rows, total, total_pages, page


def _organizer_spirit_rufname(member: Member | None) -> str:
    if member is None:
        return '—'
    return member.display_spirit_rufname


def get_monatsessen_statistics(
    *,
    now: datetime,
    season_year: int | None,
    organizer_id: int | None,
    current_member_id: int,
) -> dict[str, Any] | None:
    """
    Liefert Kontext für Tab Statistiken (nur Monatsessen, Filter Jahr/Organisator).
    Rückgabe None, wenn keine vergangenen Monatsessen im Filter.
    """
    q = (
        Event.query.filter(
            Event.published.is_(True),
            Event.event_typ == EventType.MONATSESSEN,
            Event.datum < now,
        )
        .order_by(Event.datum.asc())
    )
    if season_year is not None:
        q = q.filter(Event.season == season_year)
    if organizer_id is not None:
        q = q.filter(Event.organisator_id == organizer_id)

    past_ms: list[Event] = q.all()
    if not past_ms:
        return None

    event_ids = [e.id for e in past_ms]
    parts: list[Participation] = (
        Participation.query.filter(Participation.event_id.in_(event_ids)).all()
    )
    part_map: dict[tuple[int, int], Participation] = {
        (p.event_id, p.member_id): p for p in parts
    }

    ratings_rows: list[EventRating] = EventRating.query.filter(
        EventRating.event_id.in_(event_ids)
    ).all()
    event_to_restaurant_label: dict[int, str] = {
        ev.id: _event_restaurant_label(ev) for ev in past_ms
    }
    ratings_by_event: dict[int, list[float]] = defaultdict(list)
    restaurant_rating_vals: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {'food': [], 'drinks': [], 'service': [], 'overall': []}
    )
    for row in ratings_rows:
        eid = row.event_id
        ratings_by_event[eid].append(float(row.average_rating))
        label = event_to_restaurant_label.get(eid, '—')
        b = restaurant_rating_vals[label]
        b['food'].append(float(row.food_rating))
        b['drinks'].append(float(row.drinks_rating))
        b['service'].append(float(row.service_rating))
        b['overall'].append(float(row.average_rating))

    active_members: list[Member] = Member.query.filter_by(is_active=True).all()
    member_by_id = {m.id: m for m in active_members}

    # Ø Teilnahmequote je Monatsessen (Mittel der Event-Quoten)
    event_participation_rates: list[float] = []
    for ev in past_ms:
        eligible = [m for m in active_members if _member_eligible_for_event(m, ev)]
        if not eligible:
            continue
        confirmed = 0
        for m in eligible:
            p = part_map.get((ev.id, m.id))
            if p and p.teilnahme:
                confirmed += 1
        event_participation_rates.append(100.0 * confirmed / len(eligible))
    avg_ms_participation_pct = (
        mean(event_participation_rates) if event_participation_rates else 0.0
    )

    # Ø Kosten pro Person (alle erfassten Anteile, teilnahme=True)
    share_rappen_values = [
        p.calculated_share_rappen
        for p in parts
        if p.teilnahme and p.calculated_share_rappen is not None
    ]
    avg_share_chf = (
        mean(share_rappen_values) / 100.0 if share_rappen_values else None
    )

    # Ø Trinkgeld %
    tip_pcts: list[float] = []
    for ev in past_ms:
        if (
            ev.rechnungsbetrag_rappen
            and ev.rechnungsbetrag_rappen > 0
            and ev.trinkgeld_rappen is not None
        ):
            tip_pcts.append(100.0 * ev.trinkgeld_rappen / ev.rechnungsbetrag_rappen)
    avg_tip_pct = mean(tip_pcts) if tip_pcts else None

    current_member = member_by_id.get(current_member_id)
    eligible_for_user = (
        [e for e in past_ms if current_member and _member_eligible_for_event(current_member, e)]
        if current_member
        else []
    )
    user_confirmed = 0
    for e in eligible_for_user:
        p = part_map.get((e.id, current_member_id))
        if p and p.teilnahme:
            user_confirmed += 1
    user_participation_pct = (
        100.0 * user_confirmed / len(eligible_for_user) if eligible_for_user else 0.0
    )

    esstyp_counts = {Esstyp.ALLIN: 0, Esstyp.NORMAL: 0, Esstyp.SPARSAM: 0}
    user_share_rappen: list[int] = []
    for e in past_ms:
        p = part_map.get((e.id, current_member_id))
        if not p or not p.teilnahme:
            continue
        if p.esstyp is not None and p.esstyp in esstyp_counts:
            esstyp_counts[p.esstyp] += 1
        if p.calculated_share_rappen is not None:
            user_share_rappen.append(p.calculated_share_rappen)
    user_avg_pay_chf = (
        mean(user_share_rappen) / 100.0 if user_share_rappen else None
    )

    kuechen = Counter()
    for ev in past_ms:
        k = (ev.kueche or '').strip()
        if k:
            kuechen[k] += 1
    top_kueche = kuechen.most_common(1)[0][0] if kuechen else None

    # Rekorde: Ø-Anteil pro Event
    def _event_avg_share_rappen(ev: Event) -> float | None:
        vals = [
            p.calculated_share_rappen
            for p in part_map.values()
            if p.event_id == ev.id
            and p.teilnahme
            and p.calculated_share_rappen is not None
        ]
        if not vals:
            return None
        return float(mean(vals))

    event_avgs: list[tuple[Event, float]] = []
    for ev in past_ms:
        a = _event_avg_share_rappen(ev)
        if a is not None:
            event_avgs.append((ev, a))

    expensive = min(event_avgs, key=lambda t: -t[1]) if event_avgs else None
    cheapest = min(event_avgs, key=lambda t: t[1]) if event_avgs else None

    max_tip_event: Event | None = None
    max_tip_rappen = 0
    for ev in past_ms:
        if ev.trinkgeld_rappen is None:
            continue
        if ev.trinkgeld_rappen > max_tip_rappen:
            max_tip_rappen = ev.trinkgeld_rappen
            max_tip_event = ev
    if max_tip_rappen <= 0:
        max_tip_event = None

    event_overall_avgs: list[tuple[Event, float]] = []
    for ev in past_ms:
        xs = ratings_by_event.get(ev.id)
        if not xs:
            continue
        event_overall_avgs.append((ev, float(mean(xs))))

    record_best_rated: dict[str, Any] | None = None
    record_worst_rated: dict[str, Any] | None = None
    if len(event_overall_avgs) >= 2:
        best_ev, best_avg = max(event_overall_avgs, key=lambda t: t[1])
        worst_ev, worst_avg = min(event_overall_avgs, key=lambda t: t[1])
        record_best_rated = {
            'restaurant': _event_restaurant_label(best_ev),
            'overall_avg': round(best_avg, 1),
        }
        record_worst_rated = {
            'restaurant': _event_restaurant_label(worst_ev),
            'overall_avg': round(worst_avg, 1),
        }

    # Charts: Teilnahmequote je Member
    member_chart: list[dict[str, Any]] = []
    for m in active_members:
        el = [e for e in past_ms if _member_eligible_for_event(m, e)]
        if not el:
            continue
        att = sum(
            1
            for e in el
            if (part_map.get((e.id, m.id)) and part_map[(e.id, m.id)].teilnahme)
        )
        pct = 100.0 * att / len(el)
        member_chart.append(
            {
                'id': m.id,
                'label': m.display_name_with_spirit,
                'rate': round(pct, 1),
            }
        )
    member_chart.sort(key=lambda x: x['rate'], reverse=True)

    # Ø Kosten je Organisator (Mittel der Event-Durchschnittsanteile)
    org_avgs: dict[int, list[float]] = defaultdict(list)
    for ev, avg_r in event_avgs:
        org_avgs[ev.organisator_id].append(avg_r / 100.0)
    organizer_chart: list[dict[str, Any]] = []
    for oid, chfs in org_avgs.items():
        om = member_by_id.get(oid)
        organizer_chart.append(
            {
                'id': oid,
                'label': om.display_name_with_spirit if om else f'#{oid}',
                'avg_chf': round(mean(chfs), 2),
            }
        )
    organizer_chart.sort(key=lambda x: x['avg_chf'], reverse=True)

    # Restaurant-Tabelle (alle mit mind. einer Bewertung; Sortierung/Top 10 im Client)
    restaurant_ratings_rows: list[dict[str, Any]] = []
    for label, b in restaurant_rating_vals.items():
        if not b['overall']:
            continue
        restaurant_ratings_rows.append(
            {
                'restaurant': label,
                'overall_avg': round(mean(b['overall']), 2),
                'food_avg': round(mean(b['food']), 2),
                'drinks_avg': round(mean(b['drinks']), 2),
                'service_avg': round(mean(b['service']), 2),
                'count': len(b['overall']),
            }
        )
    restaurant_ratings_rows.sort(key=lambda x: (-x['overall_avg'], x['restaurant']))

    # Ø Gesamtbewertung je Organisator (Mittel der Event-Durchschnitte, nur Events mit Ratings)
    org_event_overall: dict[int, list[float]] = defaultdict(list)
    for ev in past_ms:
        xs = ratings_by_event.get(ev.id)
        if not xs:
            continue
        org_event_overall[ev.organisator_id].append(float(mean(xs)))
    organizer_rating_chart: list[dict[str, Any]] = []
    for oid, ev_avgs in org_event_overall.items():
        om = member_by_id.get(oid)
        organizer_rating_chart.append(
            {
                'label': om.display_name_with_spirit if om else f'#{oid}',
                'avg': round(mean(ev_avgs), 2),
            }
        )
    organizer_rating_chart.sort(key=lambda x: -x['avg'])

    # Küchen: alle Küchen als absolute Häufigkeit (keine Top-N-Kürzung)
    kitchen_labels: list[str] = []
    kitchen_values: list[int] = []
    if kuechen:
        for name, cnt in kuechen.most_common():
            kitchen_labels.append(name)
            kitchen_values.append(cnt)

    charts_payload = {
        'memberParticipation': {
            'labels': [x['label'] for x in member_chart],
            'values': [x['rate'] for x in member_chart],
        },
        'organizerCost': {
            'labels': [x['label'] for x in organizer_chart],
            'values': [x['avg_chf'] for x in organizer_chart],
        },
        'organizerRatings': {
            'labels': [x['label'] for x in organizer_rating_chart],
            'values': [x['avg'] for x in organizer_rating_chart],
        },
        'restaurantRatings': restaurant_ratings_rows,
        'kitchens': {'labels': kitchen_labels, 'values': kitchen_values},
    }

    return {
        'count_past_monatsessen': len(past_ms),
        'avg_ms_participation_pct': int(round(avg_ms_participation_pct)),
        'avg_share_chf': int(round(avg_share_chf)) if avg_share_chf is not None else None,
        'avg_tip_pct': round(avg_tip_pct, 1) if avg_tip_pct is not None else None,
        'user_confirmed': user_confirmed,
        'user_eligible_count': len(eligible_for_user),
        'user_participation_pct': int(round(user_participation_pct)),
        'user_esstyp_allin': esstyp_counts[Esstyp.ALLIN],
        'user_esstyp_normal': esstyp_counts[Esstyp.NORMAL],
        'user_esstyp_sparsam': esstyp_counts[Esstyp.SPARSAM],
        'user_avg_pay_chf': int(round(user_avg_pay_chf)) if user_avg_pay_chf is not None else None,
        'top_kueche': top_kueche,
        'record_expensive': (
            {
                'avg_chf': round(expensive[1] / 100.0, 2),
                'restaurant': _event_restaurant_label(expensive[0]),
                'organizer': _organizer_spirit_rufname(
                    member_by_id.get(expensive[0].organisator_id)
                ),
            }
            if expensive
            else None
        ),
        'record_cheapest': (
            {
                'avg_chf': round(cheapest[1] / 100.0, 2),
                'restaurant': _event_restaurant_label(cheapest[0]),
                'organizer': _organizer_spirit_rufname(
                    member_by_id.get(cheapest[0].organisator_id)
                ),
            }
            if cheapest
            else None
        ),
        'record_max_tip': (
            {
                'chf': round(max_tip_rappen / 100.0, 2),
                'restaurant': _event_restaurant_label(max_tip_event),
                'overall_avg': (
                    round(mean(ratings_by_event[max_tip_event.id]), 1)
                    if ratings_by_event.get(max_tip_event.id)
                    else None
                ),
            }
            if max_tip_event
            else None
        ),
        'record_best_rated': record_best_rated,
        'record_worst_rated': record_worst_rated,
        'charts_json': charts_payload,
    }

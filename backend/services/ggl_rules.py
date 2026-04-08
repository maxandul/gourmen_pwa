from collections import defaultdict
from datetime import datetime

from markupsafe import Markup, escape
from sqlalchemy.orm import joinedload

from backend.models.participation import Participation
from backend.models.event import Event
from backend.models.member import Member
from backend.extensions import db

class GGLService:
    """GGL (Gourmen Guessing League) service for points calculation and ranking"""
    
    @staticmethod
    def calculate_event_points(event_id):
        """Calculate points for all participants in an event"""
        # Get all participations with valid guesses
        participations = Participation.query.filter_by(
            event_id=event_id,
            teilnahme=True
        ).filter(
            Participation.guess_bill_amount_rappen.isnot(None)
        ).all()
        
        if not participations:
            return []
        
        # Sort by difference amount (ascending - best guess first)
        sorted_participations = sorted(
            participations, 
            key=lambda p: p.diff_amount_rappen or float('inf')
        )
        
        # Calculate fractional ranking
        rankings = GGLService._calculate_fractional_ranking(sorted_participations)
        
        # Calculate points (N - rank + 1)
        n_participants = len(sorted_participations)
        for participation, rank in rankings.items():
            points = n_participants - rank + 1
            participation.rank = rank
            participation.points = points
        
        # Update database
        db.session.commit()
        
        return sorted_participations
    
    @staticmethod
    def _calculate_fractional_ranking(participations):
        """Calculate fractional ranking for participants with same difference"""
        rankings = {}
        current_rank = 1
        i = 0
        
        while i < len(participations):
            # Find all participants with same difference
            current_diff = participations[i].diff_amount_rappen
            same_diff_indices = [i]
            
            j = i + 1
            while j < len(participations) and participations[j].diff_amount_rappen == current_diff:
                same_diff_indices.append(j)
                j += 1
            
            # Calculate average rank for this group
            if len(same_diff_indices) == 1:
                # Single participant
                rankings[participations[i]] = current_rank
            else:
                # Multiple participants with same difference
                avg_rank = sum(range(current_rank, current_rank + len(same_diff_indices))) / len(same_diff_indices)
                for idx in same_diff_indices:
                    rankings[participations[idx]] = avg_rank
            
            current_rank += len(same_diff_indices)
            i = j
        
        return rankings
    
    @staticmethod
    def get_season_ranking(season_year):
        """Saison-Rangliste (Tab Tabelle): Sortierung nach Gesamtpunkten, bei Gleichstand nach ØPkt (beides absteigend)."""
        # Get all events in the season
        events = Event.query.filter_by(season=season_year).all()
        
        # Collect all participations with valid guesses
        member_points = defaultdict(list)
        member_diffs = defaultdict(list)
        member_participation_count = defaultdict(int)
        
        for event in events:
            participations = Participation.query.filter_by(
                event_id=event.id,
                teilnahme=True
            ).filter(
                Participation.guess_bill_amount_rappen.isnot(None)
            ).all()
            
            for participation in participations:
                if participation.points is not None:
                    member_points[participation.member_id].append(participation.points)
                    member_participation_count[participation.member_id] += 1
                if participation.diff_amount_rappen is not None:
                    member_diffs[participation.member_id].append(participation.diff_amount_rappen)
        
        # Alle aktiven Spieler aufführen (auch ohne Teilnahme = 0 Punkte / 0 Events)
        active_members = Member.query.filter_by(is_active=True).all()
        season_stats = []
        for member in active_members:
            member_id = member.id
            points_list = member_points.get(member_id, [])
            total_points = sum(points_list)
            participation_count = member_participation_count.get(member_id, 0)
            avg_points = total_points / participation_count if participation_count > 0 else 0

            # Calculate average difference
            diffs_list = member_diffs.get(member_id, [])
            total_diff = sum(diffs_list)
            avg_diff_rappen = total_diff / len(diffs_list) if len(diffs_list) > 0 else 0

            season_stats.append({
                'member_id': member_id,
                'total_points': total_points,
                'participation_count': participation_count,
                'avg_points': avg_points,
                'avg_diff_rappen': avg_diff_rappen,
                'events_ranked': len(points_list)
            })
        
        # Sort by total points (descending), then by average points (descending)
        season_stats.sort(key=lambda x: (x['total_points'], x['avg_points']), reverse=True)
        
        # Tie-aware Ranking: gleiche (Punkte, ØPkt) => gleicher Rang
        current_rank = 1
        prev_key = None
        for i, stats in enumerate(season_stats):
            key = (stats['total_points'], stats['avg_points'])
            if prev_key is None:
                current_rank = 1
            elif key != prev_key:
                current_rank = i + 1
            stats['rank'] = current_rank
            prev_key = key
        
        return season_stats

    @staticmethod
    def _ggl_season_table_sort_key(row: dict) -> tuple:
        """Sortierschlüssel wie in get_season_ranking: Gesamtpunkte, dann ØPkt (absteigend)."""
        return (row['total_points'], row['avg_points'])

    @staticmethod
    def _ggl_leading_tie_group(ranking: list) -> list:
        """Alle Tabellenzeilen mit gleichem Schlüssel wie Platz 1 (echte Punktgleichheit inkl. Tie-Break)."""
        if not ranking:
            return []
        top_key = GGLService._ggl_season_table_sort_key(ranking[0])
        return [r for r in ranking if GGLService._ggl_season_table_sort_key(r) == top_key]

    @staticmethod
    def _ggl_next_rank_block_from_index(ranking: list, start: int) -> list:
        """Ab Index start: zusammenhängender Block gleicher (Punkte, ØPkt)."""
        if start >= len(ranking):
            return []
        nk = GGLService._ggl_season_table_sort_key(ranking[start])
        block = []
        for i in range(start, len(ranking)):
            if GGLService._ggl_season_table_sort_key(ranking[i]) == nk:
                block.append(ranking[i])
            else:
                break
        return block
    
    @staticmethod
    def get_member_season_stats(member_id, season_year):
        """Get season statistics for a specific member"""
        # Get all events in the season where member participated
        participations = db.session.query(Participation).join(Event).filter(
            Participation.member_id == member_id,
            Participation.teilnahme == True,
            Participation.guess_bill_amount_rappen.isnot(None),
            Event.season == season_year
        ).all()
        
        if not participations:
            total_events_in_season = Event.query.filter(
                Event.season == season_year,
                Event.published == True
            ).count()
            return {
                'member_id': member_id,
                'season': season_year,
                'total_points': 0,
                'participation_count': 0,
                'avg_points': 0,
                'avg_diff_rappen': 0,
                'events_ranked': 0,
                'total_events_in_season': total_events_in_season
            }
        
        # Calculate statistics
        total_points = sum(p.points for p in participations if p.points is not None)
        participation_count = len(participations)
        with_points = [p for p in participations if p.points is not None]
        avg_points = total_points / len(with_points) if with_points else 0

        # Ø Differenz nur über Schätzungen mit ausgewerteter Differenz (nicht Saison-Event-Anzahl)
        with_diff = [p for p in participations if p.diff_amount_rappen is not None]
        avg_diff = (
            sum(p.diff_amount_rappen for p in with_diff) / len(with_diff) if with_diff else 0
        )
        
        # Get total number of events in the season
        total_events_in_season = Event.query.filter(
            Event.season == season_year,
            Event.published == True
        ).count()
        
        return {
            'member_id': member_id,
            'season': season_year,
            'total_points': total_points,
            'participation_count': participation_count,
            'avg_points': avg_points,
            'avg_diff_rappen': avg_diff,
            'events_ranked': len([p for p in participations if p.points is not None]),
            'total_events_in_season': total_events_in_season
        }
    
    @staticmethod
    def get_current_season():
        """Get current season year"""
        return datetime.utcnow().year
    
    @staticmethod
    def get_available_seasons():
        """Get list of available seasons"""
        seasons = db.session.query(Event.season).distinct().order_by(Event.season.desc()).all()
        return [season[0] for season in seasons]
    
    @staticmethod
    def get_season_progression_data(season_year):
        """Get season progression data for chart visualization"""
        # Get all events in the season, ordered by date
        all_events = Event.query.filter_by(season=season_year).order_by(Event.datum).all()
        
        if not all_events:
            return {
                'events': [],
                'members': [],
                'progression_data': {}
            }
        
        # Filter events that have points awarded
        events_with_points = []
        for event in all_events:
            participations = Participation.query.filter_by(
                event_id=event.id,
                teilnahme=True
            ).filter(
                Participation.guess_bill_amount_rappen.isnot(None)
            ).all()
            
            valid_participations = [p for p in participations if p.points is not None]
            if valid_participations:
                events_with_points.append(event)
        
        if not events_with_points:
            return {
                'events': [],
                'members': [],
                'progression_data': {}
            }
        
        # Get all members who participated in at least one event with points
        member_ids = set()
        for event in events_with_points:
            participations = Participation.query.filter_by(
                event_id=event.id,
                teilnahme=True
            ).filter(
                Participation.guess_bill_amount_rappen.isnot(None)
            ).all()
            
            for participation in participations:
                if participation.points is not None:
                    member_ids.add(participation.member_id)
        
        # Get member details
        members = Member.query.filter(Member.id.in_(member_ids)).all()
        
        # Build progression data
        progression_data = {}
        for member in members:
            progression_data[member.id] = {
                'member': member,
                'cumulative_points': [],
                'cumulative_signed_diff_rappen': [],
                'cumulative_abs_diff_rappen': [],
                'ranks': []
            }
        
        # Calculate cumulative points and ranks for each event with points
        for event in events_with_points:
            # Get participations for this event
            participations = Participation.query.filter_by(
                event_id=event.id,
                teilnahme=True
            ).filter(
                Participation.guess_bill_amount_rappen.isnot(None)
            ).all()
            
            # Filter participations with points
            valid_participations = [p for p in participations if p.points is not None]
            
            # Sort by points (descending) to calculate ranks
            sorted_participations = sorted(valid_participations, key=lambda p: p.points, reverse=True)
            
            # Calculate ranks
            ranks = {}
            current_rank = 1
            for i, participation in enumerate(sorted_participations):
                if i > 0 and participation.points < sorted_participations[i-1].points:
                    current_rank = i + 1
                ranks[participation.member_id] = current_rank
            
            # Update progression data
            for member_id in member_ids:
                if member_id in ranks:
                    # Member participated in this event
                    participation = next(p for p in valid_participations if p.member_id == member_id)
                    current_points = participation.points
                    previous_total = progression_data[member_id]['cumulative_points'][-1] if progression_data[member_id]['cumulative_points'] else 0
                    # Handle None values from previous events
                    if previous_total is None:
                        previous_total = 0
                    new_total = previous_total + current_points

                    prev_diff = (
                        progression_data[member_id]['cumulative_signed_diff_rappen'][-1]
                        if progression_data[member_id]['cumulative_signed_diff_rappen']
                        else 0
                    )
                    if prev_diff is None:
                        prev_diff = 0
                    if (
                        event.rechnungsbetrag_rappen is not None
                        and participation.guess_bill_amount_rappen is not None
                    ):
                        event_signed = (
                            participation.guess_bill_amount_rappen
                            - event.rechnungsbetrag_rappen
                        )
                    else:
                        event_signed = 0
                    new_diff = prev_diff + event_signed
                    prev_abs_diff = (
                        progression_data[member_id]['cumulative_abs_diff_rappen'][-1]
                        if progression_data[member_id]['cumulative_abs_diff_rappen']
                        else 0
                    )
                    if prev_abs_diff is None:
                        prev_abs_diff = 0
                    new_abs_diff = prev_abs_diff + abs(event_signed)
                    
                    progression_data[member_id]['cumulative_points'].append(new_total)
                    progression_data[member_id]['cumulative_signed_diff_rappen'].append(new_diff)
                    progression_data[member_id]['cumulative_abs_diff_rappen'].append(new_abs_diff)
                    progression_data[member_id]['ranks'].append(ranks[member_id])
                else:
                    # Member didn't participate in this event - keep previous total
                    previous_total = progression_data[member_id]['cumulative_points'][-1] if progression_data[member_id]['cumulative_points'] else 0
                    if previous_total is None:
                        previous_total = 0
                    prev_diff = (
                        progression_data[member_id]['cumulative_signed_diff_rappen'][-1]
                        if progression_data[member_id]['cumulative_signed_diff_rappen']
                        else 0
                    )
                    if prev_diff is None:
                        prev_diff = 0
                    prev_abs_diff = (
                        progression_data[member_id]['cumulative_abs_diff_rappen'][-1]
                        if progression_data[member_id]['cumulative_abs_diff_rappen']
                        else 0
                    )
                    if prev_abs_diff is None:
                        prev_abs_diff = 0
                    
                    progression_data[member_id]['cumulative_points'].append(previous_total)
                    progression_data[member_id]['cumulative_signed_diff_rappen'].append(prev_diff)
                    progression_data[member_id]['cumulative_abs_diff_rappen'].append(prev_abs_diff)
                    progression_data[member_id]['ranks'].append(None)
        
        # Convert members to serializable format
        serializable_members = []
        for member in members:
            serializable_members.append({
                'id': member.id,
                'display_name': member.display_name,
                'spirit_animal': member.spirit_animal
            })
        
        # Convert progression data to serializable format
        serializable_progression_data = {}
        for member_id, data in progression_data.items():
            serializable_progression_data[member_id] = {
                'member': {
                    'id': data['member'].id,
                    'display_name': data['member'].display_name,
                    'spirit_animal': data['member'].spirit_animal
                },
                'cumulative_points': data['cumulative_points'],
                'cumulative_signed_diff_rappen': data['cumulative_signed_diff_rappen'],
                'cumulative_abs_diff_rappen': data['cumulative_abs_diff_rappen'],
                'ranks': data['ranks']
            }
        
        return {
            'events': events_with_points,
            'members': serializable_members,
            'progression_data': serializable_progression_data
        }

    @staticmethod
    def _format_signed_chf_rappen(rappen: int) -> str:
        """Format signed Rappen as CHF with sign (e.g. +12.50 CHF / −3.40 CHF)."""
        if rappen is None:
            return ''
        sign = '−' if rappen < 0 else '+'
        body = f'{abs(rappen) / 100:.2f}'
        return f'{sign}{body} CHF'

    @staticmethod
    def _insight_val(val) -> Markup:
        """Hervorhebung für Kennzahlen im Insight-Panel (CSS: .metrics-insight-panel__value)."""
        return Markup(
            '<span class="metrics-insight-panel__value">'
            f'{escape(str(val))}'
            '</span>'
        )

    @staticmethod
    def _insight_abstand_line(prefix: str, name_phrase: str, n: int) -> Markup:
        """prefix: „Zum nächsten Rang“ oder „Zur Spitze“; name_phrase ohne HTML."""
        v = GGLService._insight_val
        if n == 1:
            return (
                Markup(prefix)
                + Markup(' (')
                + escape(name_phrase)
                + Markup(') fehlt dir ')
                + v(1)
                + Markup(' Punkt.')
            )
        return (
            Markup(prefix)
            + Markup(' (')
            + escape(name_phrase)
            + Markup(') fehlen dir ')
            + v(n)
            + Markup(' Punkte.')
        )

    @staticmethod
    def _insight_section(title: str, items: list[Markup]) -> Markup:
        """Überschrift + Fliesstext-Zeilen für das Performance-Insight-Panel."""
        if not items:
            return Markup('')
        out = (
            Markup('<section class="metrics-insight-panel__section">')
            + Markup('<h3 class="metrics-insight-panel__heading">')
            + escape(title)
            + Markup('</h3>')
        )
        for it in items:
            out += (
                Markup('<p class="metrics-insight-panel__item">')
                + it
                + Markup('</p>')
            )
        out += Markup('</section>')
        return out

    @staticmethod
    def _names_phrase(labels: list[str]) -> str:
        if not labels:
            return ''
        if len(labels) == 1:
            return labels[0]
        return ', '.join(labels[:-1]) + ' und ' + labels[-1]

    @staticmethod
    def _season_abs_diff_rows(season_year: int) -> list[Participation]:
        """Alle Saison-Teilnahmen mit gültiger Schätzung und Rechnungsbetrag."""
        return (
            db.session.query(Participation)
            .options(joinedload(Participation.event))
            .join(Event)
            .filter(
                Event.season == season_year,
                Participation.teilnahme.is_(True),
                Participation.guess_bill_amount_rappen.isnot(None),
                Event.rechnungsbetrag_rappen.isnot(None),
            )
            .all()
        )

    @staticmethod
    def _abs_diff_rappen(p: Participation) -> int | None:
        ev = p.event
        if ev is None or ev.rechnungsbetrag_rappen is None:
            return None
        if p.guess_bill_amount_rappen is None:
            return None
        return abs(p.guess_bill_amount_rappen - ev.rechnungsbetrag_rappen)

    @staticmethod
    def get_member_performance_view_context(member_id: int, season_year: int) -> dict:
        """
        Kontext für die persönliche Performance-Ansicht (Rang, Abstände, Schätzungen).
        Nutzt dieselbe Sortierung wie get_season_ranking / Tab Tabelle: Punkte ↓, bei Gleichstand ØPkt ↓.
        """
        ranking = GGLService.get_season_ranking(season_year)
        leading = GGLService._ggl_leading_tie_group(ranking)
        leading_ids = {r['member_id'] for r in leading}

        member_stats = GGLService.get_member_season_stats(member_id, season_year)

        participations = (
            db.session.query(Participation)
            .options(joinedload(Participation.event))
            .join(Event)
            .filter(
                Participation.member_id == member_id,
                Participation.teilnahme.is_(True),
                Participation.guess_bill_amount_rappen.isnot(None),
                Event.season == season_year,
            )
            .all()
        )

        if member_stats is None:
            user_points = 0
            user_idx = None
        else:
            user_points = int(member_stats['total_points'] or 0)
            user_idx = next(
                (i for i, row in enumerate(ranking) if row['member_id'] == member_id),
                None,
            )

        max_points = ranking[0]['total_points'] if ranking else None
        in_leader_group = (
            member_stats is not None
            and (user_points or 0) > 0
            and member_id in leading_ids
        )

        member_ids = {row['member_id'] for row in ranking}
        members_by_id = {}
        if member_ids:
            for m in Member.query.filter(Member.id.in_(member_ids)).all():
                members_by_id[m.id] = m

        def _label(mid: int) -> str:
            m = members_by_id.get(mid)
            return m.display_spirit_rufname if m else '—'

        def _spitze_peer_labels() -> list[str]:
            return [_label(r['member_id']) for r in leading]

        ctx = {
            'has_participation': member_stats is not None,
            'user_points': user_points,
            'rank': user_idx + 1 if user_idx is not None else None,
            'rank_total': len(ranking),
            'show_gap_above': False,
            'gap_above_points': None,
            'above_label': None,
            'show_equal_above': False,
            'equal_above_label': None,
            'show_gap_leader': False,
            'gap_leader_points': None,
            'leader_peer_labels': [],
            'show_lead_next_tier': False,
            'lead_next_tier_points': None,
            'next_tier_peer_labels': [],
            'best_signed_rappen': None,
            'worst_signed_rappen': None,
            'avg_signed_rappen': None,
            'best_diff_display': None,
            'worst_diff_display': None,
            'insight_paragraphs': [],
        }

        if not ranking:
            pass
        elif in_leader_group:
            k = len(leading)
            if k < len(ranking):
                nblock = GGLService._ggl_next_rank_block_from_index(ranking, k)
                if nblock:
                    gap_pts = leading[0]['total_points'] - nblock[0]['total_points']
                    if gap_pts > 0:
                        ctx['show_lead_next_tier'] = True
                        ctx['lead_next_tier_points'] = gap_pts
                        ctx['next_tier_peer_labels'] = [
                            _label(r['member_id']) for r in nblock
                        ]
        elif user_idx is not None and user_idx > 0:
            above_row = ranking[user_idx - 1]
            gap_a = above_row['total_points'] - user_points
            if gap_a > 0:
                ctx['show_gap_above'] = True
                ctx['gap_above_points'] = gap_a
                ctx['above_label'] = _label(above_row['member_id'])
            elif gap_a == 0:
                ctx['show_equal_above'] = True
                ctx['equal_above_label'] = _label(above_row['member_id'])
            if max_points is not None and user_points < max_points and user_idx != 1:
                ctx['show_gap_leader'] = True
                ctx['gap_leader_points'] = max_points - user_points
                ctx['leader_peer_labels'] = _spitze_peer_labels()
        else:
            if user_idx is None and max_points is not None and ranking:
                ctx['show_gap_leader'] = True
                ctx['gap_leader_points'] = max_points - user_points
                ctx['leader_peer_labels'] = _spitze_peer_labels()

        signed_pairs = []
        for p in participations:
            ev = p.event
            if ev is None or ev.rechnungsbetrag_rappen is None:
                continue
            s = p.guess_bill_amount_rappen - ev.rechnungsbetrag_rappen
            signed_pairs.append(s)

        if signed_pairs:
            by_abs = [(abs(s), s) for s in signed_pairs]
            _, best_s = min(by_abs, key=lambda x: x[0])
            _, worst_s = max(by_abs, key=lambda x: x[0])
            ctx['best_signed_rappen'] = best_s
            ctx['worst_signed_rappen'] = worst_s
            avg_sr = sum(signed_pairs) / len(signed_pairs)
            ctx['avg_signed_rappen'] = avg_sr
            ctx['best_diff_display'] = GGLService._format_signed_chf_rappen(best_s)
            ctx['worst_diff_display'] = GGLService._format_signed_chf_rappen(worst_s)

        ctx['insight_paragraphs'] = GGLService._build_performance_insight_paragraphs(
            ctx=ctx,
            member_stats=member_stats,
            participations=participations,
            season_year=season_year,
        )

        return ctx

    @staticmethod
    def _build_performance_insight_paragraphs(
        *,
        ctx: dict,
        member_stats,
        participations: list,
        season_year: int,
    ) -> list[Markup]:
        paragraphs: list[Markup] = []
        if member_stats is None:
            return paragraphs

        v = GGLService._insight_val

        # — Abstände —
        bits: list[Markup] = []
        if ctx.get('show_equal_above') and ctx.get('equal_above_label'):
            bits.append(
                Markup('Du bist gleichauf mit ')
                + v(ctx['equal_above_label'])
                + Markup('.')
            )
        if ctx.get('show_gap_above') and ctx.get('above_label') and ctx.get('gap_above_points'):
            bits.append(
                GGLService._insight_abstand_line(
                    'Zum nächsten Rang',
                    ctx['above_label'],
                    ctx['gap_above_points'],
                )
            )
        if ctx.get('show_gap_leader') and ctx.get('leader_peer_labels'):
            bits.append(
                GGLService._insight_abstand_line(
                    'Zur Spitze',
                    GGLService._names_phrase(ctx['leader_peer_labels']),
                    ctx['gap_leader_points'],
                )
            )
        if ctx.get('show_lead_next_tier') and ctx.get('next_tier_peer_labels'):
            bits.append(
                GGLService._insight_abstand_line(
                    'Zum nächsten Rang',
                    GGLService._names_phrase(ctx['next_tier_peer_labels']),
                    ctx['lead_next_tier_points'],
                )
            )
        if bits:
            paragraphs.append(
                GGLService._insight_section('Abstände', bits)
            )

        # — Schätz-Differenzen (beste / schlechteste Schätzung) —
        signed_pairs: list[int] = []
        for p in participations:
            ev = p.event
            if ev is None or ev.rechnungsbetrag_rappen is None:
                continue
            signed_pairs.append(p.guess_bill_amount_rappen - ev.rechnungsbetrag_rappen)

        if signed_pairs:
            by_abs = [(abs(s), s) for s in signed_pairs]
            _, best_s = min(by_abs, key=lambda x: x[0])
            _, worst_s = max(by_abs, key=lambda x: x[0])

            best_disp = GGLService._format_signed_chf_rappen(best_s)
            worst_disp = GGLService._format_signed_chf_rappen(worst_s)

            best_abs_r = abs(best_s)
            worst_abs_r = abs(worst_s)

            season_rows = GGLService._season_abs_diff_rows(season_year)
            all_abs_r = []
            for p in season_rows:
                ad = GGLService._abs_diff_rappen(p)
                if ad is not None:
                    all_abs_r.append(ad)
            all_abs_r.sort()

            def _rank_small(val: int) -> int:
                return 1 + sum(1 for x in all_abs_r if x < val)

            def _rank_large(val: int) -> int:
                return 1 + sum(1 for x in all_abs_r if x > val)

            n_all = len(all_abs_r)
            rb = _rank_small(best_abs_r) if n_all else None
            rw = _rank_large(worst_abs_r) if n_all else None

            if rb is not None and rb <= 3:
                if rb == 1:
                    best_tail = 'Damit hast du bisher die beste Schätzung — Nice!'
                elif rb == 2:
                    best_tail = 'Damit hast du bisher die zweitbeste Schätzung — Nice!'
                else:
                    best_tail = 'Damit hast du bisher die drittbeste Schätzung — Nice!'
            elif rb is not None and n_all:
                best_tail = f'Rang {rb} von {n_all}.'
            else:
                best_tail = ''

            if rw is not None and rw <= 3:
                if rw == 1:
                    worst_tail = 'Das ist bisher die schlechteste Schätzung — Buuh!'
                elif rw == 2:
                    worst_tail = 'Das ist bisher die zweitschlechteste Schätzung — Buuh!'
                else:
                    worst_tail = 'Das ist bisher die drittschlechteste Schätzung — Buuh!'
            elif rw is not None and n_all:
                worst_tail = (
                    f'Rang {rw} von {n_all} vom schlechtesten her '
                    f'(alle Schätzungen der Saison).'
                )
            else:
                worst_tail = ''

            guess_items: list[Markup] = [
                Markup('Deine beste Schätzung: ')
                + v(best_disp)
                + (Markup('. ') + escape(best_tail) if best_tail else Markup('.')),
                Markup('Deine schlechteste Schätzung: ')
                + v(worst_disp)
                + (Markup('. ') + escape(worst_tail) if worst_tail else Markup('.')),
            ]

            paragraphs.append(
                GGLService._insight_section('Schätz-Differenzen', guess_items)
            )

        # — Abschnitt Teilnahme —
        guessed_event_ids = {p.event_id for p in participations}
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        member_id = member_stats.get('member_id') if isinstance(member_stats, dict) else None
        # Nur bereits stattgefundene Events (wie in der laufenden Saison erwartet), nicht alle erfassten Termine.
        pub_events = (
            Event.query.filter(
                Event.season == season_year,
                Event.published == True,  # noqa: E712
                Event.datum < now,
            )
            .order_by(Event.datum)
            .all()
        )
        occurred_ids = {e.id for e in pub_events}
        y_possible = len(pub_events)
        x_guess = len(guessed_event_ids & occurred_ids)

        # "Aufholjagd"-Events: angesetzte (publizierte) Events von heute bis Saisonende,
        # exklusive bereits explizit abgemeldeter Teilnahmen (teilnahme=False).
        upcoming_events = (
            Event.query.filter(
                Event.season == season_year,
                Event.published == True,  # noqa: E712
                Event.datum >= today_start,
            )
            .order_by(Event.datum)
            .all()
        )
        remaining = 0
        if upcoming_events and member_id is not None:
            upcoming_ids = [e.id for e in upcoming_events]
            parts = Participation.query.filter(
                Participation.member_id == member_id,
                Participation.event_id.in_(upcoming_ids),
            ).all()
            parts_by_event_id = {p.event_id: p for p in parts}
            remaining = sum(
                1
                for e in upcoming_events
                if not (
                    parts_by_event_id.get(e.id) is not None
                    and parts_by_event_id[e.id].teilnahme is False
                )
            )

        if y_possible > 0:
            teil_items: list[Markup] = [
                Markup('Du hast an ')
                + v(x_guess)
                + Markup(' von ')
                + v(y_possible)
                + Markup(' Events dieser Saison mitgeschätzt.')
            ]
            if remaining == 1:
                teil_items.append(
                    Markup('Dir bleibt noch ')
                    + v(1)
                    + Markup(' Event für deine Aufholjagd.')
                )
            else:
                teil_items.append(
                    Markup('Dir bleiben noch ')
                    + v(remaining)
                    + Markup(' Events für deine Aufholjagd.')
                )
            paragraphs.append(
                GGLService._insight_section('Teilnahme an Events', teil_items)
            )

        return paragraphs

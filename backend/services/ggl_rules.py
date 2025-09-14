from collections import defaultdict
from backend.models.participation import Participation
from backend.models.event import Event
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
        """Get season ranking for a specific year"""
        # Get all events in the season
        events = Event.query.filter_by(season=season_year).all()
        
        # Collect all participations with valid guesses
        member_points = defaultdict(list)
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
        
        # Calculate season statistics
        season_stats = []
        for member_id, points_list in member_points.items():
            total_points = sum(points_list)
            participation_count = member_participation_count[member_id]
            avg_points = total_points / participation_count if participation_count > 0 else 0
            
            season_stats.append({
                'member_id': member_id,
                'total_points': total_points,
                'participation_count': participation_count,
                'avg_points': avg_points,
                'events_ranked': len(points_list)
            })
        
        # Sort by total points (descending), then by average points (descending)
        season_stats.sort(key=lambda x: (x['total_points'], x['avg_points']), reverse=True)
        
        # Add ranking position
        for i, stats in enumerate(season_stats):
            stats['rank'] = i + 1
        
        return season_stats
    
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
            return None
        
        # Calculate statistics
        total_points = sum(p.points for p in participations if p.points is not None)
        participation_count = len(participations)
        avg_points = total_points / participation_count if participation_count > 0 else 0
        
        # Calculate average difference
        total_diff = sum(p.diff_amount_rappen for p in participations if p.diff_amount_rappen is not None)
        avg_diff = total_diff / participation_count if participation_count > 0 else 0
        
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
        from datetime import datetime
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
        from backend.models.member import Member
        members = Member.query.filter(Member.id.in_(member_ids)).all()
        
        # Build progression data
        progression_data = {}
        for member in members:
            progression_data[member.id] = {
                'member': member,
                'cumulative_points': [],
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
                    current_points = next(p.points for p in valid_participations if p.member_id == member_id)
                    previous_total = progression_data[member_id]['cumulative_points'][-1] if progression_data[member_id]['cumulative_points'] else 0
                    # Handle None values from previous events
                    if previous_total is None:
                        previous_total = 0
                    new_total = previous_total + current_points
                    
                    progression_data[member_id]['cumulative_points'].append(new_total)
                    progression_data[member_id]['ranks'].append(ranks[member_id])
                else:
                    # Member didn't participate in this event - keep previous total
                    previous_total = progression_data[member_id]['cumulative_points'][-1] if progression_data[member_id]['cumulative_points'] else 0
                    if previous_total is None:
                        previous_total = 0
                    
                    progression_data[member_id]['cumulative_points'].append(previous_total)
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
                'ranks': data['ranks']
            }
        
        return {
            'events': events_with_points,
            'members': serializable_members,
            'progression_data': serializable_progression_data
        } 
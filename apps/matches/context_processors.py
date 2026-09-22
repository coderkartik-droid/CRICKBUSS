from .models import Match

def live_matches_processor(request):
    """
    Supplies live match counts and ticker matches to all templates.
    """
    try:
        live_matches = Match.objects.filter(
            status=Match.Status.LIVE
        ).select_related('team1', 'team2', 'venue').order_by('start_datetime')[:5]

        live_count = Match.objects.filter(status=Match.Status.LIVE).count()

        return {
            'header_live_matches': live_matches,
            'header_live_count': live_count,
        }
    except Exception:
        return {
            'header_live_matches': [],
            'header_live_count': 0,
        }

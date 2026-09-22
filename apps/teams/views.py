from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Team

class TeamListView(ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    paginate_by = 18

    def get_queryset(self):
        qs = Team.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category and category in Team.TeamType.values:
            qs = qs.filter(team_type=category)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(short_name__icontains=query) | Q(country__icontains=query))
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Team.TeamType.choices
        context['active_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object

        # Fetch players belonging to this team
        context['squad_players'] = team.players.filter(is_active=True).order_by('role', 'name')

        # Fetch recent and upcoming matches involving this team
        from apps.matches.models import Match
        context['recent_matches'] = Match.objects.filter(
            Q(team1=team) | Q(team2=team),
            status=Match.Status.COMPLETED
        ).select_related('team1', 'team2', 'venue').order_by('-start_datetime')[:5]

        context['upcoming_matches'] = Match.objects.filter(
            Q(team1=team) | Q(team2=team),
            status=Match.Status.UPCOMING
        ).select_related('team1', 'team2', 'venue').order_by('start_datetime')[:5]

        return context

import json
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Player, BattingStat, BowlingStat

class PlayerListView(ListView):
    model = Player
    template_name = 'players/player_list.html'
    context_object_name = 'players'
    paginate_by = 24

    def get_queryset(self):
        qs = Player.objects.filter(is_active=True).select_related('primary_team')
        role = self.request.GET.get('role')
        if role and role in Player.Role.values:
            qs = qs.filter(role=role)
        country = self.request.GET.get('country')
        if country:
            qs = qs.filter(primary_team__slug=country)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(nickname__icontains=query))
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Player.Role.choices
        context['active_role'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('q', '')
        from apps.teams.models import Team
        context['teams'] = Team.objects.filter(team_type=Team.TeamType.INTERNATIONAL, is_active=True).order_by('name')
        return context


class PlayerDetailView(DetailView):
    model = Player
    template_name = 'players/player_detail.html'
    context_object_name = 'player'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.object

        batting_stats = player.batting_stats.all().order_by('format')
        bowling_stats = player.bowling_stats.all().order_by('format')

        context['batting_stats'] = batting_stats
        context['bowling_stats'] = bowling_stats

        # Chart.js Career Graph data preparation
        formats = [b.format for b in batting_stats]
        runs = [b.runs for b in batting_stats]
        averages = [float(b.batting_average) for b in batting_stats]

        context['career_chart_json'] = json.dumps({
            'labels': formats,
            'runs': runs,
            'averages': averages,
        })

        # Related news articles
        from apps.news.models import NewsArticle
        context['player_news'] = NewsArticle.objects.filter(
            Q(title__icontains=player.name) | Q(content__icontains=player.name),
            is_published=True
        ).order_by('-published_at')[:4]

        return context

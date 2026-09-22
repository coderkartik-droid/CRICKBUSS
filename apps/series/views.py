from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Series, PointsTableEntry

class SeriesListView(ListView):
    model = Series
    template_name = 'series/series_list.html'
    context_object_name = 'series_list'
    paginate_by = 12

    def get_queryset(self):
        qs = Series.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category and category in Series.Category.values:
            qs = qs.filter(category=category)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(short_name__icontains=query) | Q(host_country__icontains=query))
        return qs.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Series.Category.choices
        context['active_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class SeriesDetailView(DetailView):
    model = Series
    template_name = 'series/series_detail.html'
    context_object_name = 'series'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.object

        from apps.matches.models import Match
        matches = series.matches.select_related('team1', 'team2', 'venue').order_by('start_datetime')
        context['all_matches'] = matches
        context['completed_matches'] = matches.filter(status=Match.Status.COMPLETED)
        context['upcoming_matches'] = matches.filter(status=Match.Status.UPCOMING)
        context['live_matches'] = matches.filter(status=Match.Status.LIVE)

        context['points_table'] = series.points_table.select_related('team').order_by('position')
        context['participating_teams'] = series.participating_teams.prefetch_related('players').all()

        active_tab = self.request.GET.get('tab', 'schedule')
        context['active_tab'] = active_tab
        return context

from django.views.generic import ListView
from .models import RankingEntry

class RankingsView(ListView):
    model = RankingEntry
    template_name = 'rankings/rankings.html'
    context_object_name = 'rankings'

    def get_queryset(self):
        gender = self.request.GET.get('gender', RankingEntry.Gender.MEN)
        fmt = self.request.GET.get('format', RankingEntry.Format.TEST)
        category = self.request.GET.get('category', RankingEntry.Category.BATTERS)

        return RankingEntry.objects.filter(
            gender=gender,
            cricket_format=fmt,
            category=category
        ).select_related('player', 'team').order_by('rank')[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genders'] = RankingEntry.Gender.choices
        context['formats'] = RankingEntry.Format.choices
        context['categories'] = RankingEntry.Category.choices

        context['current_gender'] = self.request.GET.get('gender', RankingEntry.Gender.MEN)
        context['current_format'] = self.request.GET.get('format', RankingEntry.Format.TEST)
        context['current_category'] = self.request.GET.get('category', RankingEntry.Category.BATTERS)
        return context

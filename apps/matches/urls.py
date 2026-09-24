from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    # Home Page
    path('', views.HomePageView.as_view(), name='home'),

    # Matches Section
    path('matches/', views.MatchListView.as_view(), name='match_list'),
    path('matches/<slug:slug>/', views.MatchDetailView.as_view(), name='match_detail'),
    path('matches/<slug:slug>/scorer/', views.LiveScorerPanelView.as_view(), name='match_scorer'),
    path('matches/<slug:slug>/scorer/playing-xi/', views.AssignPlayingXIView.as_view(), name='assign_playing_xi'),
    path('matches/<slug:slug>/scorer/action/', views.LiveScorerActionView.as_view(), name='match_scorer_action'),
    path('matches/<slug:slug>/live-json/', views.MatchLiveScoreJsonView.as_view(), name='match_live_json'),
    path('matches/<slug:slug>/graphs-json/', views.MatchGraphsDataJsonView.as_view(), name='match_graphs_json'),

    # Search & Newsletter
    path('search/suggest/', views.SearchSuggestJsonView.as_view(), name='search_suggest'),
    path('search/', views.GlobalSearchView.as_view(), name='global_search'),
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'matches', views.MatchViewSet, basename='api_match')
router.register(r'teams', views.TeamViewSet, basename='api_team')
router.register(r'players', views.PlayerViewSet, basename='api_player')
router.register(r'series', views.SeriesViewSet, basename='api_series')
router.register(r'news', views.NewsViewSet, basename='api_news')
router.register(r'videos', views.VideoViewSet, basename='api_video')

urlpatterns = [
    # Auth Endpoints
    path('auth/register/', views.APIRegisterView.as_view(), name='api_register'),
    path('auth/login/', views.APILoginView.as_view(), name='api_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/profile/', views.APIUserProfileView.as_view(), name='api_profile'),

    # Specific Endpoints
    path('matches/live/', views.LiveMatchesAPIView.as_view(), name='api_live'),
    path('matches/live/now/', views.LiveMatchesAPIView.as_view(), name='api_live_now'),
    path('rankings/', views.RankingListAPIView.as_view(), name='api_rankings'),
    path('search/', views.APIGlobalSearchView.as_view(), name='api_search'),

    # ViewSet Routers
    path('', include(router.urls)),
]

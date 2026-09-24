from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('', views.PlayerListView.as_view(), name='player_list'),
    path('register/', views.PlayerRegisterView.as_view(), name='player_register'),
    path('<slug:slug>/', views.PlayerDetailView.as_view(), name='player_detail'),
]

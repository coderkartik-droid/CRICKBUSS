from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='team_list'),
    path('<slug:slug>/', views.TeamDetailView.as_view(), name='team_detail'),
]

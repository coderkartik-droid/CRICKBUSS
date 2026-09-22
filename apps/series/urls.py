from django.urls import path
from . import views

app_name = 'series'

urlpatterns = [
    path('', views.SeriesListView.as_view(), name='series_list'),
    path('<slug:slug>/', views.SeriesDetailView.as_view(), name='series_detail'),
]

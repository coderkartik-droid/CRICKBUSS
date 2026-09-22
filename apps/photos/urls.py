from django.urls import path
from . import views

app_name = 'photos'

urlpatterns = [
    path('', views.PhotoAlbumListView.as_view(), name='album_list'),
    path('<slug:slug>/', views.PhotoAlbumDetailView.as_view(), name='album_detail'),
]

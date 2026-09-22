from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.VideoListView.as_view(), name='video_list'),
    path('<slug:slug>/', views.VideoDetailView.as_view(), name='video_detail'),
    path('<slug:slug>/like/', views.ToggleVideoLikeView.as_view(), name='toggle_like'),
    path('<slug:slug>/bookmark/', views.ToggleVideoBookmarkView.as_view(), name='toggle_bookmark'),
]

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.NewsListView.as_view(), name='news_list'),
    path('<slug:slug>/', views.NewsDetailView.as_view(), name='article_detail'),
    path('<slug:slug>/comment/', views.CommentCreateView.as_view(), name='add_comment'),
    path('<slug:slug>/like/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('<slug:slug>/bookmark/', views.ToggleBookmarkView.as_view(), name='toggle_bookmark'),
]

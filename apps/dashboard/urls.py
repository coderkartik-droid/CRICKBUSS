from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('super-admin/', views.SuperAdminDashboardView.as_view(), name='super_admin'),
    path('scorer/', views.ScorerDashboardView.as_view(), name='scorer'),
    path('admin-portal/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('managed-users/', views.ManagedUsersView.as_view(), name='managed_users'),
    path('assign-scorers/', views.AssignScorersView.as_view(), name='assign_scorers'),
    path('local/<slug:entity>/', views.LocalManagementView.as_view(), name='local_management'),
    path('website-settings/', views.WebsiteSettingsView.as_view(), name='website_settings'),
    path('saved/', views.SavedItemsView.as_view(), name='saved_items'),
    path('notifications/', views.NotificationSettingsView.as_view(), name='notifications'),
    path('my-comments/', views.UserCommentsListView.as_view(), name='my_comments'),
    path('save-match/<uuid:match_id>/', views.ToggleSaveMatchView.as_view(), name='toggle_save_match'),
]

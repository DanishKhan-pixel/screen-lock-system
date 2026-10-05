from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("reports/", views.reports, name="reports"),
    path("reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("users/", views.users, name="users"),
    path("profile/", views.profile, name="profile"),
    path("profile/update/", views.update_profile, name="update_profile"),
    path("settings/", views.settings_page, name="settings"),
    path("api/status/", views.api_status, name="api_status"),
    path("api/reports/", views.api_reports, name="api_reports"),
    path("api/me/", views.api_me, name="api_me"),
]

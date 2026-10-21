from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("reports/", views.reports, name="reports"),
    path("reports/create/", views.create_report, name="create_report"),
    path("reports/export/csv/", views.export_reports_csv, name="export_reports_csv"),
    path("reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("reports/<int:pk>/edit/", views.edit_report, name="edit_report"),
    path("reports/<int:pk>/delete/", views.delete_report, name="delete_report"),
    path("users/", views.users, name="users"),
    path("profile/", views.profile, name="profile"),
    path("profile/update/", views.update_profile, name="update_profile"),
    path("settings/", views.settings_page, name="settings"),
    path("api/status/", views.api_status, name="api_status"),
    path("api/reports/", views.api_reports, name="api_reports"),
    path("api/reports/<int:pk>/", views.api_report_detail, name="api_report_detail"),
    path("api/me/", views.api_me, name="api_me"),
]

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("accounts/login/", views.AppLoginView.as_view(), name="login"),
    path("accounts/logout/", views.AppLogoutView.as_view(), name="logout"),
    path("lock/", views.lock_screen, name="lock_screen"),
    path("lock/activate/", views.activate_lock, name="activate_lock"),
]

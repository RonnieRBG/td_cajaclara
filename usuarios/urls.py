from django.urls import path

from .views import LoginView, LogoutView, PerfilView, RefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("perfil/", PerfilView.as_view(), name="auth-perfil"),
]

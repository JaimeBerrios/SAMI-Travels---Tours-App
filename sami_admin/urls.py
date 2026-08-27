from django.urls import path

from . import views


app_name = "sami_admin"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("usuarios/", views.user_list, name="user-list"),
    path("usuarios/nuevo/", views.user_create, name="user-create"),
    path("", views.dashboard, name="dashboard"),
]

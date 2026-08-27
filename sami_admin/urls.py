from django.urls import path

from . import views


app_name = "sami_admin"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("usuarios/", views.user_list, name="user-list"),
    path("usuarios/nuevo/", views.user_create, name="user-create"),
    path("usuarios/<int:user_id>/editar/", views.user_update, name="user-update"),
    path(
        "usuarios/<int:user_id>/desactivar/",
        views.user_deactivate,
        name="user-deactivate",
    ),
    path("", views.dashboard, name="dashboard"),
]

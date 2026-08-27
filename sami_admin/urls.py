from django.urls import path

from . import views


app_name = "sami_admin"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cambiar-password/", views.change_password, name="change-password"),
    path("cotizaciones/", views.quotation_list, name="quotation-list"),
    path("cotizaciones/nueva/", views.quotation_create, name="quotation-create"),
    path(
        "cotizaciones/<int:quotation_id>/editar/",
        views.quotation_update,
        name="quotation-update",
    ),
    path(
        "cotizaciones/<int:quotation_id>/vista-previa/",
        views.quotation_preview,
        name="quotation-preview",
    ),
    path(
        "cotizaciones/<int:quotation_id>/pdf/",
        views.quotation_pdf,
        name="quotation-pdf",
    ),
    path(
        "cotizaciones/<int:quotation_id>/eliminar/",
        views.quotation_delete,
        name="quotation-delete",
    ),
    path("usuarios/", views.user_list, name="user-list"),
    path("usuarios/nuevo/", views.user_create, name="user-create"),
    path("usuarios/<int:user_id>/editar/", views.user_update, name="user-update"),
    path(
        "usuarios/<int:user_id>/desactivar/",
        views.user_deactivate,
        name="user-deactivate",
    ),
    path(
        "usuarios/<int:user_id>/eliminar/",
        views.user_deactivate,
        name="user-delete",
    ),
    path("", views.dashboard, name="dashboard"),
]

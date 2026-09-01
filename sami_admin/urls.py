from django.urls import path

from . import views


app_name = "sami_admin"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cambiar-password/", views.change_password, name="change-password"),
    path("cotizaciones/", views.quotation_list, name="quotation-list"),
    path("cotizaciones/nueva/", views.quotation_create, name="quotation-create"),
    path("solicitudes/", views.request_list, name="request-list"),
    path("campanas/", views.campaign_list, name="campaign-list"),
    path("campanas/nueva/", views.campaign_create, name="campaign-create"),
    path(
        "campanas/<int:campaign_id>/editar/",
        views.campaign_update,
        name="campaign-update",
    ),
    path(
        "campanas/<int:campaign_id>/estado/",
        views.campaign_toggle,
        name="campaign-toggle",
    ),
    path(
        "campanas/<int:campaign_id>/duplicar/",
        views.campaign_duplicate,
        name="campaign-duplicate",
    ),
    path(
        "campanas/<int:campaign_id>/eliminar/",
        views.campaign_archive,
        name="campaign-archive",
    ),
    path(
        "campanas/<int:campaign_id>/restaurar/",
        views.campaign_restore,
        name="campaign-restore",
    ),
    path(
        "campanas/<int:campaign_id>/eliminar-definitivamente/",
        views.campaign_delete,
        name="campaign-delete",
    ),
    path(
        "solicitudes/<int:request_id>/",
        views.request_detail,
        name="request-detail",
    ),
    path(
        "solicitudes/<int:request_id>/convertir/",
        views.request_convert,
        name="request-convert",
    ),
    path("api/departamentos/", views.departments_json, name="departments-json"),
    path("api/aeropuertos/", views.airports_json, name="airports-json"),
    path("api/lugares-turisticos/", views.tourist_places_json, name="tourist-places-json"),
    path("api/tours/", views.tours_json, name="tours-json"),
    path("catalogo/<str:catalog>/", views.catalog_list, name="catalog-list"),
    path("catalogo/<str:catalog>/nuevo/", views.catalog_create, name="catalog-create"),
    path(
        "catalogo/<str:catalog>/<int:item_id>/editar/",
        views.catalog_update,
        name="catalog-update",
    ),
    path(
        "catalogo/<str:catalog>/<int:item_id>/eliminar/",
        views.catalog_delete,
        name="catalog-delete",
    ),
    path(
        "catalogo/<str:catalog>/<int:item_id>/estado/",
        views.catalog_toggle,
        name="catalog-toggle",
    ),
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
        views.user_delete,
        name="user-delete",
    ),
    path("", views.dashboard, name="dashboard"),
]

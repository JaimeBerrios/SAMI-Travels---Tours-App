from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.portal_publico, name="portal-publico"),
    path(
        "agencia-de-viajes-san-miguel/",
        views.agencia_san_miguel,
        name="agencia-san-miguel",
    ),
    path("politica-de-privacidad/", views.privacy_policy, name="privacy-policy"),
    path("destinos/<slug:slug>/", views.destination_detail, name="destination-detail"),
    path("tours/<slug:slug>/", views.tour_detail, name="tour-detail"),
]

from django.conf import settings
from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path(
        "",
        views.mantenimiento if settings.MAINTENANCE_MODE else views.portal_publico,
        name="portal-publico",
    ),
    path("mantenimiento/", views.mantenimiento, name="mantenimiento"),
    path("panel-interno/", views.panel_interno, name="panel-interno"),
    path(
        "cotizaciones/<int:cotizacion_id>/pdf/",
        views.cotizacion_pdf,
        name="cotizacion-pdf",
    ),
]

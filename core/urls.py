from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.portal_publico, name="portal-publico"),
    path("panel-interno/", views.panel_interno, name="panel-interno"),
]

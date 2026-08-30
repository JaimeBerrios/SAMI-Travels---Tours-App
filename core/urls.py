from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.portal_publico, name="portal-publico"),
    path("politica-de-privacidad/", views.privacy_policy, name="privacy-policy"),
]

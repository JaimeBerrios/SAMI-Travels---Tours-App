from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.portal_publico, name="portal-publico"),
    path("politica-de-privacidad/", views.privacy_policy, name="privacy-policy"),
    path("campanas/<int:campaign_id>/clic/", views.campaign_click, name="campaign-click"),
    path("destinos/<slug:slug>/", views.destination_detail, name="destination-detail"),
    path("tours/<slug:slug>/", views.tour_detail, name="tour-detail"),
]

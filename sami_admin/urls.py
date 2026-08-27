from django.urls import path

from . import views


app_name = "sami_admin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]

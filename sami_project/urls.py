"""URL configuration for sami_project."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Return a simple response to confirm that the service is running."""
    return JsonResponse({"status": "ok", "service": "sami_project"})


urlpatterns = [
    path("", health_check, name="health-check"),
    path("admin/", admin.site.urls),
]

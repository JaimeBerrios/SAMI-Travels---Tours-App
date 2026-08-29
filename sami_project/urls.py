"""URL configuration for sami_project."""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


ROBOTS_TXT = """User-agent: *
Disallow: /sami-admin/
Disallow: /admin/
Allow: /
"""


def robots_txt(request):
    return HttpResponse(ROBOTS_TXT, content_type="text/plain; charset=utf-8")


urlpatterns = [
    path("robots.txt", robots_txt, name="robots-txt"),
    path("admin/", admin.site.urls),
    path("sami-admin/", include("sami_admin.urls")),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls")),
]

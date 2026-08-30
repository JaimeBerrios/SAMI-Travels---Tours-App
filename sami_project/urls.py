"""URL configuration for sami_project."""

from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path

from core.sitemaps import PublicSitemap


ROBOTS_TXT = """User-agent: *
Disallow: /sami-admin/
Allow: /
Sitemap: https://samitravelstours.com/sitemap.xml
"""


def robots_txt(request):
    return HttpResponse(ROBOTS_TXT, content_type="text/plain; charset=utf-8")


urlpatterns = [
    path("robots.txt", robots_txt, name="robots-txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"public": PublicSitemap}},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("sami-admin/", include("sami_admin.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

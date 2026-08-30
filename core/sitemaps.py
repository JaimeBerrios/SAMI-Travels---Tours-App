from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from sami_admin.models import LugarTuristico, Tour


class PublicSitemap(Sitemap):
    """Index only canonical, publicly discoverable pages."""

    protocol = "https"
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        destinations = LugarTuristico.objects.filter(
            activo=True,
            departamento__activo=True,
            departamento__pais__activo=True,
        )
        tours = Tour.objects.filter(
            activo=True,
            lugar_turistico__activo=True,
        )
        return [
            ("page", "core:portal-publico"),
            ("page", "core:privacy-policy"),
            *(("destination", item) for item in destinations),
            *(("tour", item) for item in tours),
        ]

    def priority(self, item):
        kind, value = item
        if kind == "page" and value == "core:portal-publico":
            return 1.0
        return 0.7 if kind in {"destination", "tour"} else 0.3

    def changefreq(self, item):
        kind, value = item
        if kind == "page" and value == "core:portal-publico":
            return "weekly"
        return "weekly" if kind in {"destination", "tour"} else "yearly"

    def location(self, item):
        kind, value = item
        if kind == "destination":
            return reverse("core:destination-detail", args=[value.slug])
        if kind == "tour":
            return reverse("core:tour-detail", args=[value.slug])
        return reverse(value)

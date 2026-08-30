from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PublicSitemap(Sitemap):
    """Index only canonical, publicly discoverable pages."""

    protocol = "https"
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["core:portal-publico", "core:privacy-policy"]

    def priority(self, item):
        return 1.0 if item == "core:portal-publico" else 0.3

    def changefreq(self, item):
        return "weekly" if item == "core:portal-publico" else "yearly"

    def location(self, item):
        return reverse(item)

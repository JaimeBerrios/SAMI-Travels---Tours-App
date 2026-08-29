from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .models import SolicitudContacto


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    }
)
class BasicProductionViewsTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_public_portal_responds(self):
        response = self.client.get(reverse("core:portal-publico"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/portal_publico.html")
        self.assertNotIn("X-Robots-Tag", response)
        self.assertNotContains(response, reverse("sami_admin:dashboard"))
        self.assertNotContains(response, "SAMI Admin")

    def test_robots_txt_only_allows_the_public_site(self):
        response = self.client.get(reverse("robots-txt"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(
            response.content.decode(),
            "User-agent: *\n"
            "Disallow: /sami-admin/\n"
            "Disallow: /admin/\n"
            "Allow: /\n",
        )

    def test_admin_route_responds(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_sami_admin_login_has_meta_and_http_robots_protection(self):
        response = self.client.get(reverse("sami_admin:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">',
            html=True,
        )
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_sami_admin_dashboard_has_meta_and_http_robots_protection(self):
        user = get_user_model().objects.create_user(
            username="seo-admin",
            password="test-password",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("sami_admin:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">',
            html=True,
        )
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_internal_panel_requires_staff(self):
        response = self.client.get(reverse("core:panel-interno"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_public_form_persists_the_complete_contact_request(self):
        response = self.client.post(
            reverse("core:portal-publico"),
            {
                "nombre": "María López",
                "contacto": "maria@example.com",
                "servicio": "vuelo y tour",
                "destino": "Madrid",
                "detalles": "Dos adultos, salida en diciembre.",
            },
        )

        self.assertRedirects(response, reverse("core:portal-publico"))
        solicitud = SolicitudContacto.objects.get()
        self.assertEqual(solicitud.nombre, "María López")
        self.assertEqual(solicitud.contacto, "maria@example.com")
        self.assertEqual(solicitud.destino, "Madrid")
        self.assertEqual(solicitud.detalles, "Dos adultos, salida en diciembre.")

    def test_public_form_rejects_incomplete_requests(self):
        response = self.client.post(
            reverse("core:portal-publico"),
            {"nombre": "María", "servicio": "vuelo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SolicitudContacto.objects.exists())

    def test_public_form_rejects_honeypot_submissions(self):
        response = self.client.post(
            reverse("core:portal-publico"),
            {
                "nombre": "Robot",
                "contacto": "robot@example.com",
                "servicio": "vuelo",
                "website": "https://spam.example",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SolicitudContacto.objects.exists())

    @override_settings(PUBLIC_FORM_RATE_LIMIT=1)
    def test_public_form_rate_limits_repeated_attempts(self):
        payload = {
            "nombre": "María López",
            "contacto": "maria@example.com",
            "servicio": "vuelo",
        }
        self.client.post(reverse("core:portal-publico"), payload)
        response = self.client.post(reverse("core:portal-publico"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SolicitudContacto.objects.count(), 1)

    def test_security_headers_are_present(self):
        response = self.client.get(reverse("core:portal-publico"))

        self.assertIn("default-src 'self'", response["Content-Security-Policy"])
        self.assertEqual(
            response["Permissions-Policy"],
            "camera=(), microphone=(), geolocation=(), payment=()",
        )

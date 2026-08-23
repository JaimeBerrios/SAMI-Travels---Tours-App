import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse


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
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = get_user_model().objects.create_user(
            username="pdf-test-staff",
            email="staff@example.com",
            password="test-password-not-for-production",
            is_staff=True,
        )

    def test_public_portal_responds(self):
        response = self.client.get(reverse("core:portal-publico"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/portal_publico.html")

    def test_admin_route_responds(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_internal_panel_requires_staff(self):
        response = self.client.get(reverse("core:panel-interno"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    @patch("core.views.generate_pdf", return_value=b"%PDF-1.7 test document")
    def test_staff_can_generate_and_download_quote_pdf(self, generate_pdf_mock):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("core:cotizacion-pdf", kwargs={"cotizacion_id": 1})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="cotizacion-1.pdf"',
        )
        self.assertTrue(response.content.startswith(b"%PDF"))
        generate_pdf_mock.assert_called_once()
        rendered_html, base_url = generate_pdf_mock.call_args.args
        self.assertIn("Sami Travels & Tours", rendered_html)
        self.assertIn("Cliente de ejemplo", rendered_html)
        self.assertIn("Cotización de viaje", rendered_html)
        self.assertNotIn("�", rendered_html)
        self.assertEqual(base_url, "http://testserver/")


class BootstrapAdminCommandTests(TestCase):
    def test_disabled_bootstrap_does_nothing(self):
        with patch.dict(os.environ, {"DJANGO_BOOTSTRAP_ADMIN": "false"}):
            call_command("bootstrap_admin")

        self.assertFalse(get_user_model().objects.exists())

    def test_enabled_bootstrap_creates_admin_only_once(self):
        environment = {
            "DJANGO_BOOTSTRAP_ADMIN": "true",
            "DJANGO_ADMIN_USERNAME": "temporary-admin",
            "DJANGO_ADMIN_EMAIL": "admin@example.com",
            "DJANGO_ADMIN_PASSWORD": "initial-test-password",
        }
        output = StringIO()

        with patch.dict(os.environ, environment, clear=False):
            call_command("bootstrap_admin", stdout=output)

        user = get_user_model().objects.get(username="temporary-admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("initial-test-password"))

        environment["DJANGO_ADMIN_PASSWORD"] = "must-not-replace-password"
        with patch.dict(os.environ, environment, clear=False):
            call_command("bootstrap_admin", stdout=output)

        user.refresh_from_db()
        self.assertEqual(
            get_user_model().objects.filter(username="temporary-admin").count(),
            1,
        )
        self.assertTrue(user.check_password("initial-test-password"))

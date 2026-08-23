from unittest.mock import patch

from django.contrib.auth import get_user_model
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

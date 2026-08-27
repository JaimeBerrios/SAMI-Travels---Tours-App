from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from .decorators import staff_required


class StaffRequiredTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/sami-admin/")
        self.protected_view = staff_required(lambda request: None)

    def test_anonymous_user_is_sent_to_sami_admin_login(self):
        self.request.user = SimpleNamespace(is_authenticated=False)

        response = self.protected_view(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "/sami-admin/login/?next=/sami-admin/",
        )

    def test_authenticated_non_staff_user_gets_permission_denied(self):
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=False,
        )

        with self.assertRaises(PermissionDenied):
            self.protected_view(self.request)


class SamiAdminUrlTests(SimpleTestCase):
    def test_dashboard_url(self):
        self.assertEqual(reverse("sami_admin:dashboard"), "/sami-admin/")
        self.assertEqual(
            resolve("/sami-admin/").view_name,
            "sami_admin:dashboard",
        )

    def test_authentication_urls(self):
        self.assertEqual(reverse("sami_admin:login"), "/sami-admin/login/")
        self.assertEqual(reverse("sami_admin:logout"), "/sami-admin/logout/")

from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from .decorators import staff_required
from .views import dashboard


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

    def test_login_redirect_uses_dashboard_name(self):
        self.assertEqual(settings.LOGIN_REDIRECT_URL, "sami_admin:dashboard")


class DashboardTests(SimpleTestCase):
    def test_staff_user_can_render_dashboard_without_database_queries(self):
        request = RequestFactory().get("/sami-admin/")
        request.user = get_user_model()(
            username="admin",
            first_name="SAMI",
            is_active=True,
            is_staff=True,
        )

        response = dashboard(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenido, SAMI")

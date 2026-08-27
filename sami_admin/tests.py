from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from .decorators import staff_required, superuser_required
from .forms import StaffUserCreationForm
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


class SuperuserRequiredTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/sami-admin/usuarios/")
        self.protected_view = superuser_required(lambda request: "allowed")

    def test_staff_adviser_gets_permission_denied(self):
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )

        with self.assertRaises(PermissionDenied):
            self.protected_view(self.request)

    def test_active_superuser_is_allowed(self):
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

        self.assertEqual(self.protected_view(self.request), "allowed")


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

    def test_user_management_urls(self):
        self.assertEqual(reverse("sami_admin:user-list"), "/sami-admin/usuarios/")
        self.assertEqual(
            reverse("sami_admin:user-create"),
            "/sami-admin/usuarios/nuevo/",
        )

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


class StaffUserCreationFormTests(SimpleTestCase):
    def test_save_forces_limited_staff_permissions(self):
        user = get_user_model()(is_staff=False, is_superuser=True, is_active=False)
        form = StaffUserCreationForm()

        with patch(
            "django.contrib.auth.forms.UserCreationForm.save",
            return_value=user,
        ):
            saved_user = form.save(commit=False)

        self.assertTrue(saved_user.is_active)
        self.assertTrue(saved_user.is_staff)
        self.assertFalse(saved_user.is_superuser)

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from .decorators import staff_required, superuser_required
from .forms import ROLE_ADMIN, ROLE_SUPERUSER, StaffUserCreationForm
from .models import Cotizacion
from .views import (
    assign_user_role,
    can_view_all_quotes,
    dashboard,
    quotation_delete,
    quotations_for,
    user_deactivate,
)


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
        self.assertEqual(
            reverse("sami_admin:change-password"),
            "/sami-admin/cambiar-password/",
        )

    def test_quotation_urls(self):
        self.assertEqual(
            reverse("sami_admin:quotation-list"),
            "/sami-admin/cotizaciones/",
        )
        self.assertEqual(
            reverse("sami_admin:quotation-create"),
            "/sami-admin/cotizaciones/nueva/",
        )
        self.assertEqual(
            reverse("sami_admin:quotation-update", args=[9]),
            "/sami-admin/cotizaciones/9/editar/",
        )
        self.assertEqual(
            reverse("sami_admin:quotation-delete", args=[9]),
            "/sami-admin/cotizaciones/9/eliminar/",
        )

    def test_user_management_urls(self):
        self.assertEqual(reverse("sami_admin:user-list"), "/sami-admin/usuarios/")
        self.assertEqual(
            reverse("sami_admin:user-create"),
            "/sami-admin/usuarios/nuevo/",
        )
        self.assertEqual(
            reverse("sami_admin:user-update", args=[7]),
            "/sami-admin/usuarios/7/editar/",
        )
        self.assertEqual(
            reverse("sami_admin:user-deactivate", args=[7]),
            "/sami-admin/usuarios/7/desactivar/",
        )
        self.assertEqual(
            reverse("sami_admin:user-delete", args=[7]),
            "/sami-admin/usuarios/7/eliminar/",
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


class RoleAssignmentTests(SimpleTestCase):
    @patch("sami_admin.views.Group.objects")
    def test_administrator_role_uses_group_without_superuser_access(self, group_manager):
        user = MagicMock()
        user.is_active = False
        administrator_group = object()
        group_manager.filter.return_value = []
        group_manager.get_or_create.return_value = (administrator_group, True)

        assign_user_role(user, ROLE_ADMIN)

        self.assertFalse(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        group_manager.get_or_create.assert_called_once_with(name="Administrador")
        user.groups.add.assert_called_once_with(administrator_group)

    @patch("sami_admin.views.Group.objects")
    def test_superuser_role_does_not_add_a_limited_group(self, group_manager):
        user = MagicMock()
        group_manager.filter.return_value = []

        assign_user_role(user, ROLE_SUPERUSER)

        self.assertTrue(user.is_superuser)
        group_manager.get_or_create.assert_not_called()
        user.groups.add.assert_not_called()


class UserDeactivateTests(SimpleTestCase):
    def test_deactivation_rejects_get_requests(self):
        request = RequestFactory().get("/sami-admin/usuarios/7/desactivar/")

        response = user_deactivate(request, user_id=7)

        self.assertEqual(response.status_code, 405)


class QuotationPermissionTests(SimpleTestCase):
    def test_superuser_can_view_all_quotes(self):
        user = SimpleNamespace(is_superuser=True)
        self.assertTrue(can_view_all_quotes(user))

    def test_administrator_can_view_all_quotes(self):
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = True
        user = SimpleNamespace(is_superuser=False, groups=groups)

        self.assertTrue(can_view_all_quotes(user))
        groups.filter.assert_called_once_with(name="Administrador")

    @patch("sami_admin.views.Cotizacion.objects")
    def test_adviser_queryset_is_limited_to_owner(self, quotation_manager):
        queryset = quotation_manager.select_related.return_value
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = False
        adviser = SimpleNamespace(is_superuser=False, groups=groups)

        quotations_for(adviser)

        queryset.filter.assert_called_once_with(asesor=adviser)

    def test_quotation_delete_rejects_get_requests(self):
        request = RequestFactory().get("/sami-admin/cotizaciones/9/eliminar/")

        response = quotation_delete(request, quotation_id=9)

        self.assertEqual(response.status_code, 405)


class CotizacionModelTests(SimpleTestCase):
    def test_string_representation(self):
        quotation = Cotizacion(pk=12, cliente_nombre="María López")
        self.assertEqual(str(quotation), "Cotización #12 - María López")

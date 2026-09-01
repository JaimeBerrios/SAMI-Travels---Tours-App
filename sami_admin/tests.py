from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from PIL import Image

from core.models import SolicitudContacto

from .decorators import administrator_required, staff_required
from .forms import (
    ROLE_ADMIN, ROLE_CHOICES, CampanaPromocionalForm, CotizacionForm, LugarTuristicoForm,
    StaffUserCreationForm,
)
from .models import (
    AEROLINEAS_CHOICES, CampanaPromocional, Cotizacion, Departamento, HistorialCotizacion,
    LugarTuristico, Pais, Tour,
)
from .views import (
    assign_user_role,
    can_view_all_quotes,
    dashboard,
    generate_quotation_pdf,
    quotation_delete,
    quotation_pdf,
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


class AdministratorRequiredTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/sami-admin/usuarios/")
        self.protected_view = administrator_required(lambda request: "allowed")

    def test_administrator_group_is_allowed(self):
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = True
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=False,
            groups=groups,
        )
        self.assertEqual(self.protected_view(self.request), "allowed")

    def test_adviser_is_denied(self):
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = False
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=False,
            groups=groups,
        )
        with self.assertRaises(PermissionDenied):
            self.protected_view(self.request)


class CampaignManagementTests(TestCase):
    def setUp(self):
        self.administrator = get_user_model().objects.create_user(
            username="admin-campanas",
            password="password-seguro-123",
            is_staff=True,
        )
        administrator_group, _ = Group.objects.get_or_create(name="Administrador")
        self.administrator.groups.add(administrator_group)

    @staticmethod
    def image_upload(name, size):
        output = BytesIO()
        Image.new("RGB", size, "#173F6B").save(output, format="JPEG", quality=80)
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/jpeg")

    @staticmethod
    def animated_gif_upload(name, size):
        output = BytesIO()
        frames = [Image.new("P", size, color) for color in (1, 2)]
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=200,
            loop=0,
        )
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/gif")

    @staticmethod
    def video_upload(name, content_type="video/mp4"):
        if name.endswith(".webm"):
            content = b"\x1a\x45\xdf\xa3" + (b"\x00" * 64)
        else:
            content = b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 64)
        return SimpleUploadedFile(name, content, content_type=content_type)

    def test_campaign_form_shows_dimensions_and_optimizes_both_images(self):
        form = CampanaPromocionalForm(
            data={
                "nombre": "Black Friday",
                "etiqueta": "Oferta especial",
                "titulo": "Hasta 25 % de descuento",
                "descripcion": "Promoción para destinos seleccionados.",
                "texto_alternativo": "Familia viajando",
                "texto_boton": "Cotizar ahora",
                "tipo_enlace": CampanaPromocional.TipoEnlace.COTIZADOR,
                "color_superposicion": "#D71920",
                "opacidad_superposicion": 42,
                "fecha_inicio": (timezone.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
                "fecha_fin": (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
                "prioridad": 20,
                "activo": True,
                "mostrar_avion": True,
            },
            files={
                "imagen_escritorio": self.image_upload("desktop.jpg", (1920, 800)),
                "imagen_movil": self.image_upload("mobile.jpg", (1080, 1350)),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["imagen_escritorio"].name.endswith(".webp"))
        self.assertTrue(form.cleaned_data["imagen_movil"].name.endswith(".webp"))
        self.assertEqual(form.cleaned_data["color_superposicion"], "#D71920")
        self.assertEqual(form.cleaned_data["opacidad_superposicion"], 42)

    def test_campaign_form_rejects_an_incorrect_image_ratio(self):
        form = CampanaPromocionalForm(
            data={
                "nombre": "Navidad",
                "titulo": "Viaja en Navidad",
                "descripcion": "Oferta navideña.",
                "texto_alternativo": "Destino navideño",
                "texto_boton": "Cotizar",
                "tipo_enlace": CampanaPromocional.TipoEnlace.COTIZADOR,
                "color_superposicion": "#06152B",
                "opacidad_superposicion": 55,
                "fecha_inicio": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "prioridad": 10,
                "activo": True,
            },
            files={
                "imagen_escritorio": self.image_upload("square.jpg", (800, 800)),
                "imagen_movil": self.image_upload("mobile.jpg", (1080, 1350)),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("imagen_escritorio", form.errors)

    def test_campaign_form_accepts_responsive_videos_with_static_fallbacks(self):
        form = CampanaPromocionalForm(
            data={
                "nombre": "Video de verano",
                "etiqueta": "Promoción especial",
                "titulo": "Descubre el verano",
                "descripcion": "Promoción con video corto.",
                "texto_alternativo": "Playa al atardecer",
                "tipo_multimedia": CampanaPromocional.TipoMultimedia.VIDEO,
                "texto_boton": "Cotizar",
                "tipo_enlace": CampanaPromocional.TipoEnlace.COTIZADOR,
                "color_superposicion": "#06152B",
                "opacidad_superposicion": 55,
                "fecha_inicio": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "prioridad": 10,
                "orden": 2,
                "activo": True,
            },
            files={
                "imagen_escritorio": self.image_upload("desktop.jpg", (1920, 800)),
                "imagen_movil": self.image_upload("mobile.jpg", (1080, 1350)),
                "multimedia_escritorio": self.video_upload("desktop.mp4"),
                "multimedia_movil": self.video_upload("mobile.webm", "video/webm"),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["tipo_multimedia"],
            CampanaPromocional.TipoMultimedia.VIDEO,
        )
        self.assertEqual(form.cleaned_data["orden"], 2)

    def test_campaign_form_accepts_responsive_animated_gifs(self):
        common_data = {
            "nombre": "GIF promocional",
            "etiqueta": "Promoción especial",
            "titulo": "Oferta animada",
            "descripcion": "Promoción con animación.",
            "texto_alternativo": "Promoción animada",
            "tipo_multimedia": CampanaPromocional.TipoMultimedia.GIF,
            "texto_boton": "Cotizar",
            "tipo_enlace": CampanaPromocional.TipoEnlace.COTIZADOR,
            "color_superposicion": "#06152B",
            "opacidad_superposicion": 55,
            "fecha_inicio": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "prioridad": 10,
            "activo": True,
        }
        form = CampanaPromocionalForm(
            data=common_data,
            files={
                "imagen_escritorio": self.image_upload("desktop.jpg", (1920, 800)),
                "imagen_movil": self.image_upload("mobile.jpg", (1080, 1350)),
                "multimedia_escritorio": self.animated_gif_upload("desktop.gif", (1920, 800)),
                "multimedia_movil": self.animated_gif_upload("mobile.gif", (1080, 1350)),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_campaign_can_be_duplicated_archived_restored_and_deleted(self):
        campaign = CampanaPromocional.objects.create(
            nombre="Campaña reutilizable",
            titulo="Viaja ahora",
            descripcion="Campaña de prueba.",
            imagen_escritorio="campanas/escritorio/reutilizable.webp",
            imagen_movil="campanas/movil/reutilizable.webp",
            texto_alternativo="Destino",
            fecha_inicio=timezone.now(),
            activo=True,
        )
        self.client.force_login(self.administrator)

        duplicate_response = self.client.post(
            reverse("sami_admin:campaign-duplicate", args=[campaign.pk])
        )
        duplicate = CampanaPromocional.objects.exclude(pk=campaign.pk).get()
        self.assertRedirects(
            duplicate_response,
            reverse("sami_admin:campaign-update", args=[duplicate.pk]),
        )
        self.assertFalse(duplicate.activo)
        self.assertEqual(duplicate.imagen_escritorio.name, campaign.imagen_escritorio.name)

        archive_response = self.client.post(
            reverse("sami_admin:campaign-archive", args=[campaign.pk])
        )
        self.assertRedirects(
            archive_response,
            f'{reverse("sami_admin:campaign-list")}?estado=papelera',
        )
        campaign.refresh_from_db()
        self.assertFalse(campaign.activo)
        self.assertIsNotNone(campaign.archivada_en)

        self.client.post(reverse("sami_admin:campaign-restore", args=[campaign.pk]))
        campaign.refresh_from_db()
        self.assertIsNone(campaign.archivada_en)
        self.assertFalse(campaign.activo)

        self.client.post(reverse("sami_admin:campaign-archive", args=[campaign.pk]))
        delete_response = self.client.post(
            reverse("sami_admin:campaign-delete", args=[campaign.pk])
        )
        self.assertRedirects(
            delete_response,
            f'{reverse("sami_admin:campaign-list")}?estado=papelera',
        )
        self.assertFalse(CampanaPromocional.objects.filter(pk=campaign.pk).exists())

    def test_campaign_list_can_filter_the_trash_and_search(self):
        visible = CampanaPromocional.objects.create(
            nombre="Verano Caribe",
            titulo="Viaja al Caribe",
            descripcion="Oferta vigente.",
            imagen_escritorio="campanas/escritorio/caribe.webp",
            imagen_movil="campanas/movil/caribe.webp",
            texto_alternativo="Caribe",
            fecha_inicio=timezone.now(),
        )
        archived = CampanaPromocional.objects.create(
            nombre="Invierno archivado",
            titulo="Oferta anterior",
            descripcion="Campaña archivada.",
            imagen_escritorio="campanas/escritorio/invierno.webp",
            imagen_movil="campanas/movil/invierno.webp",
            texto_alternativo="Invierno",
            fecha_inicio=timezone.now(),
            archivada_en=timezone.now(),
            activo=False,
        )
        older_archived = CampanaPromocional.objects.create(
            nombre="Promoción anterior",
            titulo="Viajes del año pasado",
            descripcion="Material para consultar en el historial.",
            imagen_escritorio="campanas/escritorio/anterior.webp",
            imagen_movil="campanas/movil/anterior.webp",
            texto_alternativo="Viaje anterior",
            fecha_inicio=timezone.now() - timedelta(days=90),
            archivada_en=timezone.now() - timedelta(days=2),
            activo=False,
        )
        self.client.force_login(self.administrator)

        response = self.client.get(
            reverse("sami_admin:campaign-list"), {"q": "Caribe"}
        )
        self.assertContains(response, visible.nombre)
        self.assertNotContains(response, "Invierno archivado")
        trash = self.client.get(
            reverse("sami_admin:campaign-list"), {"estado": "papelera"}
        )
        self.assertContains(trash, "Invierno archivado")
        self.assertContains(trash, "Promoción anterior")
        self.assertNotContains(trash, visible.nombre)
        self.assertContains(trash, "Campañas eliminadas recientemente")
        self.assertContains(trash, "Eliminada el", count=2)
        self.assertEqual(trash.context["campaign_counts"], {"active": 1, "trash": 2})
        self.assertEqual(
            [campaign.pk for campaign in trash.context["campaigns"]],
            [archived.pk, older_archived.pk],
        )

        partial_search = self.client.get(
            reverse("sami_admin:campaign-list"),
            {"estado": "papelera", "q": "historial"},
        )
        self.assertContains(partial_search, older_archived.nombre)
        self.assertNotContains(partial_search, archived.nombre)

    def test_campaign_files_are_cleaned_only_after_the_last_reference(self):
        campaign = CampanaPromocional.objects.create(
            nombre="Campaña original",
            titulo="Oferta",
            descripcion="Campaña con archivos compartidos.",
            imagen_escritorio="campanas/escritorio/compartida.webp",
            imagen_movil="campanas/movil/compartida.webp",
            texto_alternativo="Destino",
            fecha_inicio=timezone.now(),
        )
        duplicate = CampanaPromocional.objects.create(
            nombre="Campaña duplicada",
            titulo=campaign.titulo,
            descripcion=campaign.descripcion,
            imagen_escritorio=campaign.imagen_escritorio.name,
            imagen_movil=campaign.imagen_movil.name,
            texto_alternativo=campaign.texto_alternativo,
            fecha_inicio=timezone.now(),
        )
        storage = campaign.imagen_escritorio.storage

        with patch.object(storage, "exists", return_value=True), patch.object(
            storage, "delete"
        ) as delete_file:
            campaign.delete()
            delete_file.assert_not_called()
            duplicate.delete()
            self.assertEqual(delete_file.call_count, 2)

    def test_replacing_campaign_image_cleans_the_unreferenced_previous_file(self):
        campaign = CampanaPromocional.objects.create(
            nombre="Campaña editable",
            titulo="Oferta",
            descripcion="Campaña con imagen reemplazable.",
            imagen_escritorio="campanas/escritorio/anterior.webp",
            imagen_movil="campanas/movil/mobile.webp",
            texto_alternativo="Destino",
            fecha_inicio=timezone.now(),
        )
        storage = campaign.imagen_escritorio.storage

        with patch.object(storage, "exists", return_value=True), patch.object(
            storage, "delete"
        ) as delete_file:
            campaign.imagen_escritorio = "campanas/escritorio/nueva.webp"
            campaign.save()

        delete_file.assert_called_once_with("campanas/escritorio/anterior.webp")

    def test_only_administrators_can_manage_campaigns(self):
        adviser = get_user_model().objects.create_user(
            username="asesor-campanas", password="password", is_staff=True
        )
        self.client.force_login(adviser)
        self.assertEqual(
            self.client.get(reverse("sami_admin:campaign-list")).status_code, 403
        )

        self.client.force_login(self.administrator)
        response = self.client.get(reverse("sami_admin:campaign-create"))
        self.assertContains(response, "1920 × 800 px")
        self.assertContains(response, "1080 × 1350 px")
        self.assertContains(response, "Destino del botón")
        self.assertContains(response, "Color de superposición")
        self.assertContains(response, "overlay-opacity-output")
        self.assertContains(response, 'id="campaign-link-test"')
        self.assertContains(response, "Probar enlace actual")
        self.assertContains(response, "GIF animado")
        self.assertContains(response, "Peso estimado")
        self.assertContains(response, "máximo 15 segundos")

        place_response = self.client.get(
            reverse("sami_admin:catalog-create", args=["lugares"])
        )
        self.assertContains(place_response, "1600 × 1200 px")

    def test_campaign_mutations_reject_advisers(self):
        adviser = get_user_model().objects.create_user(
            username="asesor-sin-permisos", password="password", is_staff=True
        )
        campaign = CampanaPromocional.objects.create(
            nombre="Campaña protegida",
            titulo="Oferta protegida",
            descripcion="Solo administradores.",
            imagen_escritorio="campanas/escritorio/protegida.webp",
            imagen_movil="campanas/movil/protegida.webp",
            texto_alternativo="Destino",
            fecha_inicio=timezone.now(),
        )
        self.client.force_login(adviser)

        for url_name in (
            "campaign-toggle",
            "campaign-duplicate",
            "campaign-archive",
            "campaign-restore",
            "campaign-delete",
        ):
            response = self.client.post(
                reverse(f"sami_admin:{url_name}", args=[campaign.pk])
            )
            self.assertEqual(response.status_code, 403)

    def test_campaign_list_exposes_the_saved_link_for_verification(self):
        campaign = CampanaPromocional.objects.create(
            nombre="Oferta externa",
            titulo="Promoción especial",
            descripcion="Consulta todos los detalles.",
            imagen_escritorio="campanas/escritorio/oferta.webp",
            imagen_movil="campanas/movil/oferta.webp",
            texto_alternativo="Promoción de viajes",
            texto_boton="Conocer promoción",
            tipo_enlace=CampanaPromocional.TipoEnlace.PERSONALIZADO,
            url_personalizada="https://example.com/oferta",
            fecha_inicio=timezone.now(),
        )
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("sami_admin:campaign-list"))

        self.assertContains(response, campaign.url_personalizada)
        self.assertContains(response, "Probar enlace")
        self.assertContains(response, "Visible ahora")

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
        self.assertEqual(
            reverse("sami_admin:quotation-preview", args=[9]),
            "/sami-admin/cotizaciones/9/vista-previa/",
        )
        self.assertEqual(
            reverse("sami_admin:quotation-pdf", args=[9]),
            "/sami-admin/cotizaciones/9/pdf/",
        )
        self.assertEqual(
            reverse("sami_admin:airports-json"),
            "/sami-admin/api/aeropuertos/",
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


@override_settings(ADMIN_LOGIN_RATE_LIMIT=2)
class LoginRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            password="valid-password-123",
            is_staff=True,
        )

    def test_repeated_invalid_logins_are_rate_limited(self):
        url = reverse("sami_admin:login")
        payload = {"username": "staff@example.com", "password": "incorrecta"}

        self.client.post(url, payload)
        self.client.post(url, payload)
        response = self.client.post(url, payload)

        self.assertContains(response, "Demasiados intentos de acceso")


class DashboardTests(TestCase):
    @patch("sami_admin.views.Cotizacion.objects")
    def test_dashboard_renders_grouped_quotation_analytics(self, quotation_manager):
        queryset = quotation_manager.select_related.return_value
        queryset.filter.return_value = queryset
        grouped_query = queryset.values.return_value
        grouped_query.annotate.return_value = [
            {"estado": Cotizacion.Estado.PENDIENTE, "total": 5},
            {"estado": Cotizacion.Estado.APROBADA, "total": 3},
            {"estado": Cotizacion.Estado.RECHAZADA, "total": 1},
        ]
        request = RequestFactory().get("/sami-admin/")
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = True
        request.user = SimpleNamespace(
            pk=None,
            username="admin",
            first_name="SAMI",
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            groups=groups,
            get_full_name=lambda: "SAMI",
        )

        response = dashboard(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenido, SAMI")
        self.assertContains(response, "chart.js@4.4.7")
        self.assertContains(
            response,
            '<script id="quotation-approved-data" type="application/json">3</script>',
            html=True,
        )
        self.assertContains(
            response,
            '<script id="quotation-pending-data" type="application/json">5</script>',
            html=True,
        )
        self.assertContains(
            response,
            '<script id="quotation-rejected-data" type="application/json">1</script>',
            html=True,
        )
        queryset.filter.assert_any_call(archivada=False)
        queryset.values.assert_called_once_with("estado")
        grouped_query.annotate.assert_called_once()


class PublicRequestWorkflowTests(TestCase):
    def setUp(self):
        self.adviser = get_user_model().objects.create_user(
            username="asesor-solicitudes",
            password="password-123",
            is_staff=True,
        )
        self.adviser.groups.add(Group.objects.create(name="Asesor"))
        self.client.force_login(self.adviser)
        self.request_record = SolicitudContacto.objects.create(
            nombre="Cliente del portal",
            contacto="cliente@example.com",
            correo="cliente@example.com",
            servicio=SolicitudContacto.Servicio.VUELO,
            origen="San Salvador",
            destino="Madrid",
            adultos=2,
        )

    def test_staff_can_open_request_inbox(self):
        response = self.client.get(reverse("sami_admin:request-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente del portal")

    def test_request_can_be_converted_to_quotation(self):
        response = self.client.post(
            reverse("sami_admin:request-convert", args=[self.request_record.pk])
        )

        self.request_record.refresh_from_db()
        self.assertEqual(self.request_record.estado, SolicitudContacto.Estado.CONVERTIDA)
        self.assertIsNotNone(self.request_record.cotizacion_id)
        quotation = self.request_record.cotizacion
        self.assertEqual(quotation.asesor, self.adviser)
        self.assertEqual(quotation.cliente_correo, "cliente@example.com")
        self.assertEqual(quotation.tipo_cotizacion, Cotizacion.TipoCotizacion.VUELOS)
        self.assertRedirects(
            response,
            reverse("sami_admin:quotation-update", args=[quotation.pk]),
        )

    def test_private_flight_request_converts_with_special_details(self):
        self.request_record.servicio = SolicitudContacto.Servicio.VUELO_PRIVADO
        self.request_record.motivo_vuelo_privado = "negocios"
        self.request_record.equipaje_estimado = "4 maletas"
        self.request_record.preferencia_aeronave = "Jet mediano"
        self.request_record.save()

        self.client.post(
            reverse("sami_admin:request-convert", args=[self.request_record.pk])
        )

        self.request_record.refresh_from_db()
        quotation = self.request_record.cotizacion
        self.assertEqual(quotation.tipo_cotizacion, Cotizacion.TipoCotizacion.VUELOS)
        self.assertIn("Vuelo privado", quotation.notas_importantes)
        self.assertIn("4 maletas", quotation.notas_importantes)
        self.assertIn("Jet mediano", quotation.notas_importantes)


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
    def test_only_administrator_and_adviser_roles_are_available(self, group_manager):
        user = MagicMock()
        administrator_group = object()
        group_manager.filter.return_value = []
        group_manager.get_or_create.return_value = (administrator_group, True)

        assign_user_role(user, ROLE_ADMIN)

        self.assertFalse(user.is_superuser)
        self.assertEqual(
            ROLE_CHOICES,
            (("administrador", "Administrador"), ("asesor", "Asesor")),
        )


class UserDeactivateTests(SimpleTestCase):
    def test_deactivation_rejects_get_requests(self):
        request = RequestFactory().get("/sami-admin/usuarios/7/desactivar/")

        response = user_deactivate(request, user_id=7)

        self.assertEqual(response.status_code, 405)


class AdministratorUserManagementTests(TestCase):
    def setUp(self):
        administrator_group, _ = Group.objects.get_or_create(name="Administrador")
        self.administrator = get_user_model().objects.create_user(
            username="administrador",
            email="admin@example.com",
            password="password-123",
            is_staff=True,
        )
        self.administrator.groups.add(administrator_group)
        self.adviser = get_user_model().objects.create_user(
            username="asesor-eliminable",
            email="asesor@example.com",
            password="password-123",
            is_staff=True,
        )
        self.adviser.groups.add(Group.objects.create(name="Asesor"))
        self.client.force_login(self.administrator)

    def test_administrator_can_open_user_management_and_sees_menu_link(self):
        response = self.client.get(reverse("sami_admin:user-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo usuario")
        self.assertContains(response, reverse("sami_admin:user-list"))
        self.assertNotContains(response, "Superusuario")

    def test_administrator_can_delete_an_adviser_access(self):
        response = self.client.post(
            reverse("sami_admin:user-delete", args=[self.adviser.pk])
        )
        self.assertRedirects(response, reverse("sami_admin:user-list"))
        self.assertFalse(
            get_user_model().objects.filter(pk=self.adviser.pk).exists()
        )

    def test_administrator_cannot_delete_own_access(self):
        self.client.post(
            reverse("sami_admin:user-delete", args=[self.administrator.pk])
        )
        self.administrator.refresh_from_db()
        self.assertTrue(self.administrator.is_active)


class QuotationPermissionTests(SimpleTestCase):
    def test_administrator_can_view_all_quotes(self):
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = True
        user = SimpleNamespace(groups=groups)

        self.assertTrue(can_view_all_quotes(user))
        groups.filter.assert_called_once_with(name="Administrador")

    @patch("sami_admin.views.Cotizacion.objects")
    def test_adviser_queryset_is_limited_to_owner(self, quotation_manager):
        queryset = quotation_manager.select_related.return_value
        groups = MagicMock()
        groups.filter.return_value.exists.return_value = False
        adviser = SimpleNamespace(groups=groups)

        quotations_for(adviser)

        queryset.filter.return_value.filter.assert_called_once_with(asesor=adviser)

    def test_quotation_delete_rejects_get_requests(self):
        request = RequestFactory().get("/sami-admin/cotizaciones/9/eliminar/")

        response = quotation_delete(request, quotation_id=9)

        self.assertEqual(response.status_code, 405)


class CotizacionModelTests(TestCase):
    def test_string_representation(self):
        quotation = Cotizacion(pk=12, cliente_nombre="María López")
        self.assertEqual(str(quotation), "Cotización #12 - María López")

    def test_tour_form_clears_internal_flight_data(self):
        pais = Pais.objects.create(nombre="Guatemala")
        departamento = Departamento.objects.create(pais=pais, nombre="Sacatepéquez")
        lugar = LugarTuristico.objects.create(
            departamento=departamento,
            nombre="Antigua Guatemala",
            imagen="lugares_turisticos/antigua.jpg",
            descripcion_historica="Ciudad colonial.",
        )
        form = CotizacionForm(
            data={
                "cliente_nombre": "Ana Pérez",
                "cliente_correo": "ana@example.com",
                "tipo_cotizacion": Cotizacion.TipoCotizacion.TOURS,
                "destino": "Antigua Guatemala",
                "pais": pais.pk,
                "departamento": departamento.pk,
                "lugar_turistico": lugar.pk,
                "duracion_tour": "1 Día",
                "incluye": "Guía",
                "itinerario_resumido": "Recorrido por el centro histórico.",
                "aerolinea": "avianca",
                "precio_estimado": "500.00",
                "estado": Cotizacion.Estado.PENDIENTE,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["aerolinea"])

    def test_airline_field_uses_the_managed_dropdown_choices(self):
        field = Cotizacion._meta.get_field("aerolinea")
        form = CotizacionForm()

        self.assertEqual(list(field.choices), AEROLINEAS_CHOICES)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertEqual(form.fields["aerolinea"].widget.input_type, "select")
        self.assertEqual(
            form.fields["aerolinea"].widget.attrs["aria-describedby"],
            "id_aerolinea_helptext",
        )


class DestinationCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="asesor-catalogo",
            password="password-seguro-123",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.pais = Pais.objects.create(nombre="El Salvador")
        self.departamento = Departamento.objects.create(
            pais=self.pais,
            nombre="La Libertad",
        )
        self.lugar = LugarTuristico.objects.create(
            departamento=self.departamento,
            nombre="El Tunco",
            imagen="lugares_turisticos/el-tunco.jpg",
            descripcion_historica="Destino costero emblemático.",
        )
        self.tour = Tour.objects.create(
            lugar_turistico=self.lugar,
            nombre_comercial="Aventura costera",
            duracion="1 Día",
            incluye="Transporte y guía",
            itinerario="Playa y atardecer",
            precio_base=125,
        )

    def test_department_and_place_endpoints_filter_the_catalog(self):
        response = self.client.get(
            reverse("sami_admin:departments-json"), {"pais": self.pais.pk}
        )
        self.assertEqual(response.json()["results"], [
            {"id": self.departamento.pk, "nombre": "La Libertad"}
        ])

        response = self.client.get(
            reverse("sami_admin:tourist-places-json"),
            {"departamento": self.departamento.pk},
        )
        self.assertEqual(response.json()["results"], [
            {"id": self.lugar.pk, "nombre": "El Tunco"}
        ])

        response = self.client.get(
            reverse("sami_admin:tours-json"), {"lugar": self.lugar.pk}
        )
        self.assertEqual(response.json()["results"][0]["nombre"], "Aventura costera")
        self.assertEqual(response.json()["results"][0]["precio_base"], "125.00")

    def test_airport_endpoint_filters_mock_gds_results(self):
        response = self.client.get(
            reverse("sami_admin:airports-json"), {"q": "san salvador"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [
            {"iata": "SAL", "ciudad": "San Salvador", "pais": "El Salvador"}
        ])

    def test_airport_endpoint_is_accent_insensitive_and_requires_two_characters(self):
        response = self.client.get(
            reverse("sami_admin:airports-json"), {"q": "mexico"}
        )
        self.assertEqual(
            [airport["iata"] for airport in response.json()["results"]],
            ["MEX", "CUN", "GDL"],
        )

        response = self.client.get(reverse("sami_admin:airports-json"), {"q": "m"})
        self.assertEqual(response.json()["results"], [])

    def test_airport_endpoint_requires_staff_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("sami_admin:airports-json"), {"q": "sal"})

        self.assertRedirects(
            response,
            "/sami-admin/login/?next=/sami-admin/api/aeropuertos/%3Fq%3Dsal",
        )

    def test_quotation_form_loads_flatpickr_and_airport_autosuggest(self):
        response = self.client.get(reverse("sami_admin:quotation-create"))

        self.assertContains(response, "flatpickr@4.6.13")
        self.assertContains(response, 'id="flight-date-range"')
        self.assertContains(response, 'name="origen"')
        self.assertContains(response, 'id="origin-airport-results"')
        self.assertContains(response, 'id="destination-airport-results"')
        self.assertContains(response, reverse("sami_admin:airports-json"))
        self.assertContains(response, "window.setTimeout(search, 300)")

    def test_edit_form_initializes_the_full_location_hierarchy(self):
        quotation = Cotizacion(
            lugar_turistico=self.lugar,
            asesor=self.user,
            cliente_nombre="Cliente",
        )
        form = CotizacionForm(instance=quotation)
        self.assertEqual(form.fields["pais"].initial, self.pais.pk)
        self.assertEqual(form.fields["departamento"].initial, self.departamento.pk)
        self.assertIn(self.lugar, form.fields["lugar_turistico"].queryset)

    def test_catalog_is_available_to_staff(self):
        response = self.client.get(
            reverse("sami_admin:catalog-list", args=["lugares"])
        )
        self.assertContains(response, "El Tunco")
        self.assertContains(response, "Catálogo de Destinos")

    def test_adviser_can_read_but_cannot_mutate_catalog(self):
        response = self.client.get(
            reverse("sami_admin:catalog-create", args=["paises"])
        )
        self.assertEqual(response.status_code, 403)

    def test_administrator_can_deactivate_catalog_items(self):
        administrator_group, _ = Group.objects.get_or_create(name="Administrador")
        self.user.groups.add(administrator_group)
        response = self.client.post(
            reverse("sami_admin:catalog-toggle", args=["lugares", self.lugar.pk])
        )
        self.assertRedirects(
            response, reverse("sami_admin:catalog-list", args=["lugares"])
        )
        self.lugar.refresh_from_db()
        self.assertFalse(self.lugar.activo)

    def test_invalid_image_upload_is_rejected(self):
        form = LugarTuristicoForm(
            data={
                "departamento": self.departamento.pk,
                "nombre": "Archivo inválido",
                "descripcion_historica": "Texto",
                "activo": True,
            },
            files={
                "imagen": SimpleUploadedFile(
                    "falsa.jpg", b"esto no es una imagen", content_type="image/jpeg"
                )
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("imagen", form.errors)

    def test_quotation_freezes_catalog_and_tour_content(self):
        form = CotizacionForm(data={
            "cliente_nombre": "Cliente SAMI",
            "cliente_correo": "cliente@example.com",
            "tipo_cotizacion": Cotizacion.TipoCotizacion.TOURS,
            "destino": "Texto reemplazado",
            "pais": self.pais.pk,
            "departamento": self.departamento.pk,
            "lugar_turistico": self.lugar.pk,
            "tour": self.tour.pk,
            "duracion_tour": "1 Día",
            "incluye": "Transporte y guía",
            "itinerario_resumido": "Playa y atardecer",
            "precio_estimado": "125.00",
            "estado": Cotizacion.Estado.PENDIENTE,
        })
        self.assertTrue(form.is_valid(), form.errors)
        quotation = form.save(commit=False)
        self.assertEqual(quotation.destino, "El Tunco")
        self.assertEqual(quotation.nombre_tour_cotizado, "Aventura costera")
        self.assertEqual(quotation.descripcion_historica_cotizada, self.lugar.descripcion_historica)
        quotation.asesor = self.user
        quotation.save()
        original_history = quotation.descripcion_historica_cotizada
        self.lugar.descripcion_historica = "Reseña nueva que no debe alterar documentos previos."
        self.lugar.save(update_fields=["descripcion_historica"])
        edit_form = CotizacionForm(data=form.data, instance=quotation)
        self.assertTrue(edit_form.is_valid(), edit_form.errors)
        edited = edit_form.save()
        self.assertEqual(edited.descripcion_historica_cotizada, original_history)


class QuotationAuditTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="asesor-auditoria", password="password-123", is_staff=True
        )
        self.client.force_login(self.user)

    def test_delete_action_archives_and_keeps_history(self):
        quotation = Cotizacion.objects.create(
            asesor=self.user,
            cliente_nombre="Cliente",
            cliente_correo="cliente@example.com",
            tipo_cotizacion=Cotizacion.TipoCotizacion.VUELOS,
            destino="Miami",
            precio_estimado=500,
        )
        self.client.post(reverse("sami_admin:quotation-delete", args=[quotation.pk]))
        quotation.refresh_from_db()
        self.assertTrue(quotation.archivada)
        self.assertTrue(
            HistorialCotizacion.objects.filter(
                cotizacion=quotation, accion="archivada", usuario=self.user
            ).exists()
        )


class QuotationPdfTests(SimpleTestCase):
    def test_tour_document_renders_destination_experience(self):
        quotation = SimpleNamespace(
            id=31,
            cliente_nombre="Lucía Ramos",
            cliente_correo="lucia@example.com",
            tipo_cotizacion=Cotizacion.TipoCotizacion.TOURS,
            destino="El Tunco",
            lugar_turistico=SimpleNamespace(
                nombre="El Tunco",
                imagen=SimpleNamespace(url="/media/lugares_turisticos/el-tunco.jpg"),
                descripcion_historica="Historia del destino costero.",
            ),
            nombre_destino_documento="El Tunco",
            ubicacion_destino_cotizada="La Libertad, El Salvador",
            descripcion_destino_documento="Historia del destino costero.",
            imagen_destino_documento="/media/lugares_turisticos/el-tunco.jpg",
            duracion_tour="1 Día",
            punto_encuentro="Hotel principal",
            incluye="Transporte y guía",
            no_incluye="Propinas",
            itinerario_resumido="Salida, recorrido y regreso.",
            fecha_creacion=None,
            precio_estimado=150,
            asesor=SimpleNamespace(get_full_name=lambda: "Asesor SAMI"),
        )
        html = get_template("sami_admin/cotizacion_documento.html").render(
            {"cotizacion": quotation, "preview": False, "contact_email": "info@example.com"}
        )
        self.assertIn("Historia del destino costero", html)
        self.assertIn("Transporte y guía", html)
        self.assertIn("Itinerario resumido", html)
        self.assertIn("/media/lugares_turisticos/el-tunco.jpg", html)

    def test_flight_document_shows_itinerary_but_never_airline(self):
        quotation = SimpleNamespace(
            id=21,
            cliente_nombre="Carlos Rivera",
            cliente_correo="carlos@example.com",
            tipo_cotizacion=Cotizacion.TipoCotizacion.VUELOS_TOURS,
            destino="Guadalajara",
            ruta_vuelo="San Salvador a Guadalajara",
            cantidad_adultos=2,
            cantidad_ninos=1,
            fecha_ida=None,
            hora_salida_ida=None,
            hora_llegada_ida=None,
            escala_ida="1 escala de 2 horas",
            fecha_vuelta=None,
            hora_salida_vuelta=None,
            hora_llegada_vuelta=None,
            escala_vuelta="Vuelo directo",
            aerolinea="AEROLINEA-CONFIDENCIAL-XYZ",
            equipaje_incluido="Una maleta de 23 kg",
            notas_importantes="Presentarse tres horas antes",
            fecha_creacion=None,
            precio_estimado=1200,
            asesor=SimpleNamespace(
                get_full_name=lambda: "Asesor SAMI",
                username="USUARIO-PRIVADO-ASESOR",
            ),
        )

        html = get_template("sami_admin/cotizacion_documento.html").render(
            {
                "cotizacion": quotation,
                "preview": True,
                "contact_email": "contacto@example.com",
            }
        )

        self.assertIn("Itinerario aéreo", html)
        self.assertIn("San Salvador a Guadalajara", html)
        self.assertIn("Una maleta de 23 kg", html)
        self.assertNotIn("AEROLINEA-CONFIDENCIAL-XYZ", html)
        self.assertNotIn("USUARIO-PRIVADO-ASESOR", html)

    def test_document_has_svg_social_links_and_omits_internal_status(self):
        quotation = SimpleNamespace(
            id=18,
            cliente_nombre="Ana Pérez",
            cliente_correo="ana@example.com",
            destino="Roatán, Honduras",
            fecha_creacion=None,
            precio_estimado=850,
            asesor=SimpleNamespace(
                get_full_name=lambda: "Asesor SAMI",
                username="asesor",
            ),
        )

        html = get_template("sami_admin/cotizacion_documento.html").render(
            {
                "cotizacion": quotation,
                "preview": True,
                "contact_email": "contacto@example.com",
            }
        )

        self.assertGreaterEqual(html.count("<svg"), 8)
        self.assertIn("Descargar PDF", html)
        self.assertIn("Editar Cotización", html)
        self.assertIn("instagram.com/sami.travelstours", html)
        self.assertIn("facebook.com/samitravelstours", html)
        self.assertIn("@page { size: Letter; margin: 0; }", html)
        self.assertIn("print-color-adjust: exact", html)
        self.assertIn("position: absolute; bottom: 0", html)
        self.assertNotIn("Estado", html)
        self.assertNotIn("Pendiente", html)

    def test_pdf_generator_uses_html_and_base_url(self):
        html_class = MagicMock()
        html_class.return_value.write_pdf.return_value = b"pdf-content"

        with patch.dict(
            "sys.modules",
            {"weasyprint": SimpleNamespace(HTML=html_class)},
        ):
            result = generate_quotation_pdf(
                "<html></html>",
                "https://example.com/",
            )

        self.assertEqual(result, b"pdf-content")
        html_class.assert_called_once_with(
            string="<html></html>",
            base_url="https://example.com/",
        )

    @patch("sami_admin.views.generate_quotation_pdf", return_value=b"pdf-content")
    @patch("sami_admin.views.HistorialCotizacion.objects.create")
    @patch("sami_admin.views.render_to_string", return_value="<html></html>")
    @patch("sami_admin.views.get_object_or_404")
    @patch("sami_admin.views.quotations_for")
    def test_download_uses_strict_filename(
        self,
        quotations_for_mock,
        get_object_mock,
        render_mock,
        history_mock,
        generate_mock,
    ):
        quotation = SimpleNamespace(pk=42)
        get_object_mock.return_value = quotation
        request = RequestFactory().get("/sami-admin/cotizaciones/42/pdf/")
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
        )

        response = quotation_pdf(request, quotation_id=42)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="Cotizacion_SAMI_42.pdf"',
        )
        generate_mock.assert_called_once_with(
            "<html></html>",
            base_url="http://testserver/",
        )

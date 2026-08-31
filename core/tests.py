from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from sami_admin.models import (
    CampanaPromocional, Departamento, LugarTuristico, Pais, Tour,
)

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

    def test_removed_san_miguel_landing_returns_not_found(self):
        response = self.client.get("/agencia-de-viajes-san-miguel/")

        self.assertEqual(response.status_code, 404)

    def test_current_campaign_replaces_the_default_hero_and_keeps_plane(self):
        campaign = CampanaPromocional.objects.create(
            nombre="Black Friday",
            etiqueta="Oferta limitada",
            titulo="Viaja con descuento",
            descripcion="Promoción especial para destinos seleccionados.",
            imagen_escritorio="campanas/escritorio/black-friday.webp",
            imagen_movil="campanas/movil/black-friday.webp",
            texto_alternativo="Viajeros durante Black Friday",
            texto_boton="Ver oferta",
            tipo_enlace=CampanaPromocional.TipoEnlace.PERSONALIZADO,
            url_personalizada="https://example.com/black-friday",
            fecha_inicio=timezone.now() - timedelta(hours=1),
            fecha_fin=timezone.now() + timedelta(days=1),
            mostrar_avion=True,
        )

        response = self.client.get(reverse("core:portal-publico"))

        self.assertContains(response, campaign.titulo)
        self.assertContains(response, campaign.imagen_escritorio.url)
        self.assertContains(response, campaign.imagen_movil.url)
        self.assertContains(response, 'href="https://example.com/black-friday"')
        self.assertContains(response, ">Ver oferta</a>")
        self.assertContains(response, 'id="flight-animation-toggle"')
        self.assertContains(response, 'id="quick-quote"')
        self.assertContains(response, 'id="btn-quick-quote"')
        self.assertNotContains(
            response, "Tu próximo destino está más cerca de lo que imaginas."
        )

    def test_expired_campaign_falls_back_to_the_corporate_hero(self):
        CampanaPromocional.objects.create(
            nombre="Navidad pasada",
            titulo="Oferta finalizada",
            descripcion="Esta campaña ya no debe aparecer.",
            imagen_escritorio="campanas/escritorio/navidad.webp",
            imagen_movil="campanas/movil/navidad.webp",
            texto_alternativo="Promoción navideña",
            fecha_inicio=timezone.now() - timedelta(days=2),
            fecha_fin=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(reverse("core:portal-publico"))

        self.assertNotContains(response, "Oferta finalizada")
        self.assertContains(
            response, "Tu agencia de viajes en El Salvador para descubrir el mundo"
        )

    def test_robots_txt_only_allows_the_public_site(self):
        response = self.client.get(reverse("robots-txt"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(
            response.content.decode(),
            "User-agent: *\n"
            "Disallow: /sami-admin/\n"
            "Allow: /\n"
            "Sitemap: https://samitravelstours.com/sitemap.xml\n",
        )

    def test_public_portal_contains_seo_and_conversion_markup(self):
        response = self.client.get(reverse("core:portal-publico"))

        self.assertContains(
            response,
            "Agencia de viajes en El Salvador | SAMI Travels & Tours",
        )
        self.assertContains(response, "Asesoría de viajes para San Miguel")
        self.assertContains(response, "https://www.googletagmanager.com/gtag/js?id=G-N92HCL999R")
        self.assertContains(response, "gtag('config', 'G-N92HCL999R');")
        self.assertContains(
            response,
            '<link rel="canonical" href="https://samitravelstours.com/">',
            html=True,
        )
        self.assertContains(response, 'property="og:type" content="website"')
        self.assertContains(response, 'name="twitter:card" content="summary_large_image"')
        self.assertContains(response, '"@type": "TravelAgency"')
        self.assertContains(response, 'id="btn-cta-whatsapp"')
        self.assertContains(response, 'data-track-action="whatsapp_click"')
        self.assertContains(response, 'id="form-public-quote"')
        self.assertContains(response, 'id="quick-quote"')
        self.assertContains(response, 'data-quick-service="vuelo"')
        self.assertContains(response, 'data-quick-service="tour"')
        self.assertContains(response, 'data-quick-service="vuelo y tour"')
        self.assertContains(response, 'data-trip-type="roundtrip"')
        self.assertContains(response, 'data-trip-type="oneway"')
        self.assertContains(response, 'id="quick-adults"')
        self.assertContains(response, 'id="quick-children"')
        self.assertContains(response, 'id="popular-routes-title"')
        self.assertContains(response, 'id="trip-explorer"')
        self.assertContains(response, 'event: "quick_quote_continue"')
        self.assertContains(response, 'id="btn-submit-quote"')
        self.assertContains(response, 'id="link-social-facebook"')
        self.assertContains(response, 'id="link-social-instagram"')
        self.assertContains(response, 'data-tour-id="tours-personalizados"')
        self.assertContains(response, 'data-tour-name="Tours personalizados"')
        self.assertContains(response, 'id="cookie-consent"')
        self.assertContains(response, 'analytics_storage: "denied"')
        self.assertContains(response, 'ad_storage: "denied"')
        self.assertContains(response, 'id="btn-cookie-preferences"')

    def test_privacy_policy_is_public_and_has_its_own_metadata(self):
        response = self.client.get(reverse("core:privacy-policy"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/privacy_policy.html")
        self.assertContains(response, "Política de Privacidad")
        self.assertContains(response, "Google Analytics 4")
        self.assertContains(response, "Meta Pixel")
        self.assertContains(
            response,
            '<link rel="canonical" href="https://samitravelstours.com/politica-de-privacidad/">',
            html=True,
        )

    def test_sitemap_only_indexes_the_public_portal(self):
        response = self.client.get(
            reverse("django.contrib.sitemaps.views.sitemap"),
            HTTP_HOST="samitravelstours.com",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        content = response.content.decode()
        self.assertIn("https://samitravelstours.com/", content)
        self.assertIn(
            "https://samitravelstours.com/politica-de-privacidad/",
            content,
        )
        self.assertNotIn("/sami-admin/", content)

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
        self.assertNotContains(response, "G-N92HCL999R")
        self.assertNotContains(response, "googletagmanager.com")

    def test_public_form_persists_the_complete_contact_request(self):
        response = self.client.post(
            reverse("core:portal-publico"),
            {
                "nombre": "María López",
                "correo": "maria@example.com",
                "servicio": "vuelo y tour",
                "destino": "Madrid",
                "detalles": "Dos adultos, salida en diciembre.",
            },
        )

        self.assertRedirects(response, reverse("core:portal-publico"))
        solicitud = SolicitudContacto.objects.get()
        self.assertEqual(solicitud.nombre, "María López")
        self.assertEqual(solicitud.correo, "maria@example.com")
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
                "correo": "robot@example.com",
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
            "correo": "maria@example.com",
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

    def test_public_catalog_pages_and_quote_prefill(self):
        country = Pais.objects.create(nombre="El Salvador")
        department = Departamento.objects.create(
            pais=country,
            nombre="La Libertad",
        )
        place = LugarTuristico.objects.create(
            departamento=department,
            nombre="El Tunco",
            imagen="lugares_turisticos/el-tunco.jpg",
            descripcion_historica="Destino de playa reconocido por sus olas.",
            mejor_epoca="Noviembre a abril",
            duracion_recomendada="3 a 5 días",
            aeropuerto_principal="Aeropuerto Internacional de El Salvador",
            actividades_destacadas="Surf\nAtardeceres en la playa",
            requisitos_viaje="Confirma documentos vigentes antes de viajar.",
            destacado=True,
        )
        tour = Tour.objects.create(
            lugar_turistico=place,
            nombre_comercial="Atardecer en El Tunco",
            duracion="6 horas",
            incluye="Transporte y guía",
            itinerario="Recorrido por la costa",
            precio_base=75,
            destacado=True,
        )

        destination_response = self.client.get(
            reverse("core:destination-detail", args=[place.slug])
        )
        tour_response = self.client.get(
            reverse("core:tour-detail", args=[tour.slug])
        )
        portal_response = self.client.get(
            reverse("core:portal-publico"), {"tour": tour.pk}
        )

        self.assertContains(destination_response, "El Tunco")
        self.assertContains(destination_response, "Noviembre a abril")
        self.assertContains(destination_response, "Surf")
        self.assertContains(destination_response, '"@type":"TouristDestination"')
        self.assertContains(tour_response, "Atardecer en El Tunco")
        self.assertContains(tour_response, '"@type":"TouristTrip"')
        self.assertContains(portal_response, "Atardecer en El Tunco")
        self.assertContains(portal_response, 'value="tour" selected')

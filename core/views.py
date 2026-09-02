from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from sami_admin.models import CampanaPromocional, LugarTuristico, Tour

from .forms import SolicitudContactoForm
from .models import SolicitudContacto


def _normalize_location_search(value):
    from unicodedata import combining, normalize

    return "".join(
        character
        for character in normalize("NFKD", value.strip().casefold())
        if not combining(character)
    )


def travel_locations_json(request):
    """Return selectable airports or catalog destinations for the public quote."""
    query = _normalize_location_search(request.GET.get("q", ""))
    service = request.GET.get("service", "vuelo")
    if query and len(query) < 2:
        return JsonResponse({"results": []})

    if service == SolicitudContacto.Servicio.TOUR:
        places = LugarTuristico.objects.filter(
            activo=True,
            departamento__activo=True,
            departamento__pais__activo=True,
        ).select_related("departamento__pais")
        if query:
            places = [
                place
                for place in places
                if query in _normalize_location_search(place.nombre)
                or query in _normalize_location_search(place.departamento.nombre)
                or query in _normalize_location_search(
                    place.departamento.pais.nombre
                )
            ][:8]
        else:
            places = places.order_by("-destacado", "nombre")
        results = [
            {
                "id": f"place-{place.pk}",
                "kind": "place",
                "place_id": place.pk,
                "value": place.nombre,
                "primary": place.nombre,
                "secondary": (
                    f"{place.departamento.nombre} · {place.departamento.pais.nombre}"
                ),
            }
            for place in places[:8]
        ]
        return JsonResponse({"results": results})

    # Imported lazily to keep the existing shared mock-GDS catalog in one place.
    from sami_admin.views import AIRPORTS

    airports = AIRPORTS
    if query:
        airports = tuple(
            airport
            for airport in AIRPORTS
            if query in _normalize_location_search(airport["iata"])
            or query in _normalize_location_search(airport["ciudad"])
            or query in _normalize_location_search(airport["pais"])
        )
    results = [
        {
            "id": f"airport-{airport['iata']}",
            "kind": "airport",
            "value": (
                f"({airport['iata']}) {airport['ciudad']}, {airport['pais']}"
            ),
            "primary": f"{airport['ciudad']} ({airport['iata']})",
            "secondary": airport["pais"],
        }
        for airport in airports[:8]
    ]
    return JsonResponse({"results": results})


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",", 1)[0].strip() or request.META.get(
        "REMOTE_ADDR", "unknown"
    )


def portal_publico(request):
    """Display the public portal and receive provisional quote requests."""
    initial = {}
    if request.method == "GET":
        if request.GET.get("tour", "").isdigit():
            selected_tour = Tour.objects.filter(
                pk=request.GET["tour"], activo=True
            ).select_related("lugar_turistico").first()
            if selected_tour:
                initial.update(
                    {
                        "servicio": SolicitudContacto.Servicio.TOUR,
                        "tour": selected_tour,
                        "lugar_turistico": selected_tour.lugar_turistico,
                        "destino": selected_tour.lugar_turistico.nombre,
                    }
                )
        elif request.GET.get("lugar", "").isdigit():
            selected_place = LugarTuristico.objects.filter(
                pk=request.GET["lugar"], activo=True
            ).first()
            if selected_place:
                initial.update(
                    {
                        "servicio": SolicitudContacto.Servicio.TOUR,
                        "lugar_turistico": selected_place,
                        "destino": selected_place.nombre,
                    }
                )
    form = SolicitudContactoForm(request.POST or None, initial=initial)
    if request.method == "POST":
        rate_key = f"public-form:{_client_ip(request)}"
        attempts = cache.get(rate_key, 0)
        if attempts >= settings.PUBLIC_FORM_RATE_LIMIT:
            messages.error(
                request,
                "Has enviado varias solicitudes. Inténtalo de nuevo más tarde.",
            )
        elif form.is_valid():
            cache.set(rate_key, attempts + 1, settings.PUBLIC_FORM_RATE_WINDOW)
            solicitud = form.save()
            attributed_campaign = request.session.pop("attributed_campaign", None)
            if attributed_campaign:
                CampanaPromocional.objects.filter(
                    pk=attributed_campaign, archivada_en__isnull=True
                ).update(conversiones=F("conversiones") + 1)
            messages.success(
                request,
                f"¡Gracias, {solicitud.nombre}! Tu solicitud fue registrada. "
                "Un asesor se pondrá en contacto contigo muy pronto.",
            )
            return redirect("core:portal-publico")
        else:
            cache.set(rate_key, attempts + 1, settings.PUBLIC_FORM_RATE_WINDOW)
            messages.error(
                request,
                "Revisa los datos del formulario e inténtalo nuevamente.",
            )

    destinations = LugarTuristico.objects.filter(
        activo=True,
        departamento__activo=True,
        departamento__pais__activo=True,
    ).select_related("departamento__pais")
    featured_destinations = destinations.filter(destacado=True)[:6]
    if not featured_destinations:
        featured_destinations = destinations[:6]
    tours = Tour.objects.filter(
        activo=True,
        lugar_turistico__activo=True,
        lugar_turistico__departamento__activo=True,
        lugar_turistico__departamento__pais__activo=True,
    ).select_related("lugar_turistico__departamento__pais")
    featured_tours = tours.filter(destacado=True)[:6]
    if not featured_tours:
        featured_tours = tours[:6]
    now = timezone.now()
    campaign = CampanaPromocional.objects.filter(
        archivada_en__isnull=True,
        activo=True,
        fecha_inicio__lte=now,
    ).filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)).select_related(
        "lugar_turistico", "tour"
    ).order_by("-prioridad", "orden", "-fecha_inicio", "-id").first()
    campaign_url = ""
    if campaign:
        viewed_campaigns = request.session.get("viewed_campaigns", [])
        if campaign.pk not in viewed_campaigns:
            CampanaPromocional.objects.filter(pk=campaign.pk).update(
                impresiones=F("impresiones") + 1
            )
            request.session["viewed_campaigns"] = (viewed_campaigns + [campaign.pk])[-20:]
        request.session["attributed_campaign"] = campaign.pk
        campaign_url = reverse("core:campaign-click", args=[campaign.pk])
    return render(
        request,
        "core/portal_publico.html",
        {
            "form": form,
            "featured_destinations": featured_destinations,
            "featured_tours": featured_tours,
            "campaign": campaign,
            "campaign_url": campaign_url,
        },
    )


def destination_detail(request, slug):
    destination = get_object_or_404(
        LugarTuristico.objects.select_related("departamento__pais"),
        slug=slug,
        activo=True,
        departamento__activo=True,
        departamento__pais__activo=True,
    )
    tours = destination.tours.filter(activo=True)
    return render(
        request,
        "core/destination_detail.html",
        {"destination": destination, "tours": tours},
    )


def tour_detail(request, slug):
    tour = get_object_or_404(
        Tour.objects.select_related("lugar_turistico__departamento__pais"),
        slug=slug,
        activo=True,
        lugar_turistico__activo=True,
        lugar_turistico__departamento__activo=True,
        lugar_turistico__departamento__pais__activo=True,
    )
    return render(request, "core/tour_detail.html", {"tour": tour})


def privacy_policy(request):
    """Display the public privacy and cookie policy."""
    return render(
        request,
        "core/privacy_policy.html",
        {"contact_email": settings.CONTACT_EMAIL},
    )


def campaign_click(request, campaign_id):
    campaign = get_object_or_404(
        CampanaPromocional, pk=campaign_id, archivada_en__isnull=True
    )
    CampanaPromocional.objects.filter(pk=campaign.pk).update(clics=F("clics") + 1)
    return redirect(campaign.get_target_url())

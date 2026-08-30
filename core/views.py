from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from sami_admin.models import CampanaPromocional, LugarTuristico, Tour

from .forms import SolicitudContactoForm
from .models import SolicitudContacto


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
        activo=True,
        fecha_inicio__lte=now,
    ).filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)).select_related(
        "lugar_turistico", "tour"
    ).order_by("-prioridad", "-fecha_inicio", "-id").first()
    campaign_url = campaign.get_target_url() if campaign else ""
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

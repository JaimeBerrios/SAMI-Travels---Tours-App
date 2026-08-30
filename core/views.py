from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render

from .forms import SolicitudContactoForm


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",", 1)[0].strip() or request.META.get(
        "REMOTE_ADDR", "unknown"
    )


def portal_publico(request):
    """Display the public portal and receive provisional quote requests."""
    form = SolicitudContactoForm(request.POST or None)
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

    return render(request, "core/portal_publico.html", {"form": form})


def privacy_policy(request):
    """Display the public privacy and cookie policy."""
    return render(
        request,
        "core/privacy_policy.html",
        {"contact_email": settings.CONTACT_EMAIL},
    )

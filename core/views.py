from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.shortcuts import redirect, render

from .models import SolicitudContacto


def portal_publico(request):
    """Display the public portal and receive provisional quote requests."""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        contacto = request.POST.get("contacto", "").strip()
        servicio = request.POST.get("servicio", "").strip()
        destino = request.POST.get("destino", "").strip()
        detalles = request.POST.get("detalles", "").strip()

        servicios_validos = {value for value, _ in SolicitudContacto.Servicio.choices}
        if nombre and contacto and servicio in servicios_validos:
            solicitud = SolicitudContacto.objects.create(
                nombre=nombre,
                contacto=contacto,
                servicio=servicio,
                destino=destino,
                detalles=detalles,
            )
            messages.success(
                request,
                f"¡Gracias, {solicitud.nombre}! Tu solicitud fue registrada. "
                "Un asesor se pondrá en contacto contigo muy pronto.",
            )
            return redirect("core:portal-publico")

        messages.error(
            request,
            "Completa tu nombre, contacto y selecciona un servicio válido.",
        )

    return render(request, "core/portal_publico.html")


def mantenimiento(request):
    """Display the maintenance page without replacing the public portal."""
    return render(
        request,
        "core/mantenimiento.html",
        {"contact_email": settings.CONTACT_EMAIL},
        status=503,
    )


@staff_member_required(login_url="admin:login")
def panel_interno(request):
    """Keep the former staff URL as an alias for the SAMI Admin dashboard."""
    return redirect("sami_admin:dashboard")

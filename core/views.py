from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render


def portal_publico(request):
    """Display the public portal and receive provisional quote requests."""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        servicio = request.POST.get("servicio", "viaje").strip()

        if nombre:
            messages.success(
                request,
                f"¡Gracias, {nombre}! Recibimos tu solicitud de {servicio}. "
                "Uno de nuestros agentes se pondrá en contacto contigo.",
            )
            return redirect("core:portal-publico")

        messages.error(request, "Por favor, indícanos tu nombre para continuar.")

    return render(request, "core/portal_publico.html")


@staff_member_required(login_url="admin:login")
def panel_interno(request):
    """Display the provisional workspace for agency staff."""
    context = {
        "resumen": {
            "pendientes": 0,
            "en_proceso": 0,
            "completadas": 0,
        },
        "cotizaciones": [],
    }
    return render(request, "core/panel_interno.html", context)

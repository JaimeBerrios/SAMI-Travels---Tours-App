from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone


def generate_pdf(html, base_url):
    """Render HTML as PDF, loading WeasyPrint only for PDF requests."""
    from weasyprint import HTML

    return HTML(string=html, base_url=base_url).write_pdf()


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


@staff_member_required(login_url="admin:login")
def cotizacion_pdf(request, cotizacion_id):
    """Genera una cotización PDF; sustituir los datos de ejemplo por un modelo."""
    cotizacion = {
        "id": cotizacion_id,
        "cliente": "Cliente de ejemplo",
        "destino": "Roatán, Honduras",
        "fecha_salida": "15 de diciembre de 2026",
        "viajeros": 2,
        "subtotal": "750.00",
        "impuestos": "97.50",
        "total": "847.50",
    }
    html = render_to_string(
        "core/cotizacion_pdf.html",
        {"cotizacion": cotizacion, "fecha_emision": timezone.localdate()},
        request=request,
    )
    pdf = generate_pdf(html, request.build_absolute_uri("/"))

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="cotizacion-{cotizacion_id}.pdf"'
    )
    return response

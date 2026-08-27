from django.db.models import Count
from django.shortcuts import render

from core.models import Cliente, Destino, PaqueteTuristico, Reserva

from .decorators import staff_required


@staff_required
def dashboard(request):
    """Show a live operational summary for agency staff."""
    reservas_por_estado = dict(
        Reserva.objects.values_list("estado")
        .annotate(total=Count("id"))
        .order_by()
    )

    context = {
        "stats": {
            "clientes": Cliente.objects.filter(activo=True).count(),
            "reservas": Reserva.objects.count(),
            "pendientes": reservas_por_estado.get(Reserva.Estado.SOLICITADA, 0),
            "paquetes": PaqueteTuristico.objects.filter(activo=True).count(),
            "destinos": Destino.objects.filter(activo=True).count(),
        },
        "reservas_recientes": Reserva.objects.select_related(
            "cliente", "paquete", "destino"
        )[:5],
    }
    return render(request, "sami_admin/dashboard.html", context)

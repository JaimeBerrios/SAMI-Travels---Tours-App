def administrative_permissions(request):
    from core.models import SolicitudContacto

    user = request.user
    can_manage_users = False
    if user.is_authenticated and user.is_active and user.is_staff:
        can_manage_users = user.groups.filter(name="Administrador").exists()
    pending_requests = 0
    if user.is_authenticated and user.is_active and user.is_staff:
        pending_requests = SolicitudContacto.objects.exclude(
            estado__in=(
                SolicitudContacto.Estado.CONVERTIDA,
                SolicitudContacto.Estado.DESCARTADA,
            )
        ).count()
    return {
        "can_manage_users": can_manage_users,
        "solicitudes_pendientes_global": pending_requests,
    }

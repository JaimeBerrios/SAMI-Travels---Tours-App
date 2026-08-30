from .models import Cotizacion


def can_view_all_quotes(user):
    """Return whether a staff member can access agency-wide quotations."""
    return user.groups.filter(name="Administrador").exists()


def quotations_for(user):
    """Return only the quotations visible to a given staff member."""
    queryset = Cotizacion.objects.select_related(
        "asesor", "lugar_turistico__departamento__pais", "tour"
    ).filter(archivada=False)
    if not can_view_all_quotes(user):
        queryset = queryset.filter(asesor=user)
    return queryset

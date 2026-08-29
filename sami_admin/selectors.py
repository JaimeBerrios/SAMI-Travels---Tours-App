from .models import Cotizacion


def can_view_all_quotes(user):
    """Return whether a staff member can access agency-wide quotations."""
    return user.is_superuser or user.groups.filter(name="Administrador").exists()


def quotations_for(user):
    """Return only the quotations visible to a given staff member."""
    queryset = Cotizacion.objects.select_related("asesor")
    if not can_view_all_quotes(user):
        queryset = queryset.filter(asesor=user)
    return queryset

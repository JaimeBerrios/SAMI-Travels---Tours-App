from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Allow active staff users and return 403 for authenticated non-staff users."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied(
                "No tienes permisos para acceder al panel administrativo."
            )

        return view_func(request, *args, **kwargs)

    return wrapped_view

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import staff_required, superuser_required
from .forms import SamiAdminAuthenticationForm, StaffUserCreationForm


def login_view(request):
    """Authenticate staff against Django's configured authentication backends."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("sami_admin:dashboard")

    form = SamiAdminAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(
        request,
        "sami_admin/login.html",
        {
            "form": form,
            "next": request.GET.get("next", ""),
        },
    )


@require_POST
def logout_view(request):
    logout(request)
    return redirect(reverse("sami_admin:login"))


@staff_required
def dashboard(request):
    """Render the main workspace without requiring operational data tables."""
    return render(request, "sami_admin/dashboard.html")


@superuser_required
def user_list(request):
    """List staff accounts; access is exclusive to superusers."""
    users = get_user_model().objects.filter(is_staff=True).order_by(
        "-is_superuser", "first_name", "last_name", "username"
    )
    return render(request, "sami_admin/user_list.html", {"users": users})


@superuser_required
def user_create(request):
    """Create a limited staff account without superuser privileges."""
    form = StaffUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(
            request,
            f"El usuario {user.username} fue creado como asesor.",
        )
        return redirect("sami_admin:user-list")

    return render(request, "sami_admin/user_form.html", {"form": form})

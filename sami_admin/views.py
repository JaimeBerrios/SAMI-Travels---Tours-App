from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import staff_required, superuser_required
from .forms import (
    MANAGED_GROUPS,
    ROLE_SUPERUSER,
    SamiAdminAuthenticationForm,
    StaffUserCreationForm,
    StaffUserUpdateForm,
    get_user_role,
)


def assign_user_role(user, role):
    """Persist one of SAMI's managed roles without removing unrelated groups."""
    user.is_staff = True
    user.is_superuser = role == ROLE_SUPERUSER
    user.save()

    user.groups.remove(*Group.objects.filter(name__in=MANAGED_GROUPS.values()))
    group_name = MANAGED_GROUPS.get(role)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)


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
    """List current and deactivated staff accounts for auditability."""
    users = list(
        get_user_model()
        .objects.filter(is_staff=True)
        .prefetch_related("groups")
        .order_by("-is_active", "-is_superuser", "first_name", "username")
    )
    for user in users:
        user.sami_role = get_user_role(user)
    return render(request, "sami_admin/user_list.html", {"users": users})


@superuser_required
def user_create(request):
    """Create a limited staff account without superuser privileges."""
    form = StaffUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            assign_user_role(user, form.cleaned_data["role"])
        messages.success(
            request,
            f"El usuario {user.username} fue creado correctamente.",
        )
        return redirect("sami_admin:user-list")

    return render(
        request,
        "sami_admin/user_form.html",
        {"form": form, "form_title": "Crear usuario", "is_editing": False},
    )


@superuser_required
def user_update(request, user_id):
    """Update identity and role fields for a staff account."""
    user = get_object_or_404(get_user_model(), pk=user_id, is_staff=True)
    form = StaffUserUpdateForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        new_role = form.cleaned_data["role"]
        active_superusers = get_user_model().objects.filter(
            is_superuser=True, is_active=True
        )
        if (
            user.is_superuser
            and new_role != ROLE_SUPERUSER
            and active_superusers.count() <= 1
        ):
            form.add_error(
                "role",
                "Debe permanecer al menos un superusuario activo.",
            )
        else:
            with transaction.atomic():
                user = form.save(commit=False)
                assign_user_role(user, new_role)
            messages.success(request, f"El usuario {user.username} fue actualizado.")
            return redirect("sami_admin:user-list")

    return render(
        request,
        "sami_admin/user_form.html",
        {"form": form, "form_title": "Editar usuario", "is_editing": True},
    )


@require_POST
@superuser_required
def user_deactivate(request, user_id):
    """Soft-delete a staff account while retaining its historical relations."""
    user = get_object_or_404(get_user_model(), pk=user_id, is_staff=True)
    if user.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
    elif (
        user.is_superuser
        and get_user_model().objects.filter(
            is_superuser=True, is_active=True
        ).count()
        <= 1
    ):
        messages.error(request, "Debe permanecer al menos un superusuario activo.")
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"El usuario {user.username} fue desactivado.")
    return redirect("sami_admin:user-list")

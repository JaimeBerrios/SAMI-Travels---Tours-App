from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Prefetch
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import (
    administrator_required,
    catalog_manager_required,
    staff_required,
    superuser_required,
)
from .forms import (
    MANAGED_GROUPS,
    ROLE_ADMIN,
    CotizacionForm,
    DepartamentoForm,
    LugarTuristicoForm,
    PaisForm,
    TourForm,
    SamiAdminAuthenticationForm,
    StaffUserCreationForm,
    StaffUserUpdateForm,
    apply_error_attributes,
    get_user_role,
)
from .models import Cotizacion, Departamento, HistorialCotizacion, LugarTuristico, Pais, Tour
from .selectors import can_view_all_quotes, quotations_for
from .services import generate_quotation_pdf


def assign_user_role(user, role):
    """Persist one of SAMI's managed roles without removing unrelated groups."""
    user.is_staff = True
    user.is_superuser = False
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
    if request.method == "POST":
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        client_ip = forwarded.split(",", 1)[0].strip() or request.META.get(
            "REMOTE_ADDR", "unknown"
        )
        rate_key = f"admin-login:{client_ip}"
        attempts = cache.get(rate_key, 0)
        if attempts >= settings.ADMIN_LOGIN_RATE_LIMIT:
            form.add_error(
                None,
                "Demasiados intentos de acceso. Inténtalo de nuevo más tarde.",
            )
        elif form.is_valid():
            cache.delete(rate_key)
            login(request, form.get_user())
            next_url = request.POST.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            cache.set(rate_key, attempts + 1, settings.ADMIN_LOGIN_RATE_WINDOW)

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
    """Render the main workspace with a compact quotation status summary."""
    quotations = quotations_for(request.user)
    counts_by_status = {
        row["estado"]: row["total"]
        for row in quotations.values("estado").annotate(total=Count("id"))
    }
    total_cotizaciones = quotations.count()
    total_clientes = (
        quotations.order_by()
        .values_list("cliente_correo", flat=True)
        .distinct()
        .count()
    )
    total_accesos = 1
    if request.user.pk:
        total_accesos = (
            get_user_model().objects.filter(is_staff=True, is_active=True).count()
        )
    return render(
        request,
        "sami_admin/dashboard.html",
        {
            "cotizaciones_pendientes": counts_by_status.get(
                Cotizacion.Estado.PENDIENTE, 0
            ),
            "cotizaciones_aprobadas": counts_by_status.get(
                Cotizacion.Estado.APROBADA, 0
            ),
            "cotizaciones_rechazadas": counts_by_status.get(
                Cotizacion.Estado.RECHAZADA, 0
            ),
            "total_cotizaciones": total_cotizaciones,
            "total_clientes": total_clientes,
            "total_accesos": total_accesos,
            "ultimas_cotizaciones": quotations[:5],
        },
    )


@staff_required
def quotation_list(request):
    can_view_all = can_view_all_quotes(request.user)
    quotations = quotations_for(request.user)
    return render(
        request,
        "sami_admin/cotizacion_list.html",
        {
            "cotizaciones": quotations,
            "can_view_all": can_view_all,
        },
    )


@staff_required
def quotation_create(request):
    form = CotizacionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quotation = form.save(commit=False)
        quotation.asesor = request.user
        quotation.save()
        form.save_destinations(quotation)
        HistorialCotizacion.objects.create(
            cotizacion=quotation,
            usuario=request.user,
            accion="creada",
            estado=quotation.estado,
            datos={"tipo": quotation.tipo_cotizacion, "precio": str(quotation.precio_estimado)},
        )
        messages.success(request, "La cotización fue creada correctamente.")
        return redirect("sami_admin:quotation-list")
    return render(
        request,
        "sami_admin/cotizacion_form.html",
        {"form": form, "form_title": "Nueva cotización"},
    )


@staff_required
def departments_json(request):
    pais_id = request.GET.get("pais", "")
    departments = Departamento.objects.none()
    if pais_id.isdigit():
        departments = Departamento.objects.filter(
            pais_id=pais_id, activo=True, pais__activo=True
        )
    departments = departments.values(
        "id", "nombre"
    )
    return JsonResponse({"results": list(departments)})


@staff_required
def tourist_places_json(request):
    departamento_id = request.GET.get("departamento", "")
    places = LugarTuristico.objects.none()
    if departamento_id.isdigit():
        places = LugarTuristico.objects.filter(
            departamento_id=departamento_id,
            activo=True,
            departamento__activo=True,
            departamento__pais__activo=True,
        )
    places = places.values("id", "nombre")
    return JsonResponse({"results": list(places)})


@staff_required
def tours_json(request):
    lugar_id = request.GET.get("lugar", "")
    tours = Tour.objects.none()
    if lugar_id.isdigit():
        tours = Tour.objects.filter(
            lugar_turistico_id=lugar_id,
            activo=True,
            lugar_turistico__activo=True,
            lugar_turistico__departamento__activo=True,
            lugar_turistico__departamento__pais__activo=True,
        )
    results = [
        {
            "id": tour.pk,
            "nombre": tour.nombre_comercial,
            "duracion": tour.duracion,
            "punto_encuentro": tour.punto_encuentro,
            "incluye": tour.incluye,
            "no_incluye": tour.no_incluye,
            "itinerario": tour.itinerario,
            "recomendaciones": tour.recomendaciones,
            "que_llevar": tour.que_llevar,
            "restricciones": tour.restricciones,
            "politica_cancelacion": tour.politica_cancelacion,
            "precio_base": str(tour.precio_base),
        }
        for tour in tours
    ]
    return JsonResponse({"results": results})


CATALOG_CONFIG = {
    "paises": {
        "model": Pais,
        "form": PaisForm,
        "title": "Países",
        "singular": "país",
    },
    "departamentos": {
        "model": Departamento,
        "form": DepartamentoForm,
        "title": "Departamentos",
        "singular": "departamento",
    },
    "lugares": {
        "model": LugarTuristico,
        "form": LugarTuristicoForm,
        "title": "Lugares turísticos",
        "singular": "lugar turístico",
    },
    "tours": {
        "model": Tour,
        "form": TourForm,
        "title": "Tours y paquetes",
        "singular": "tour",
    },
}


def _catalog_home(catalog):
    """Return the unified destination view for geographic catalog actions."""
    return "paises" if catalog in {"paises", "departamentos", "lugares"} else catalog


def _catalog_config(catalog):
    try:
        return CATALOG_CONFIG[catalog]
    except KeyError as exc:
        raise Http404("Catálogo no encontrado") from exc


@staff_required
def catalog_list(request, catalog):
    config = _catalog_config(catalog)
    status = request.GET.get("estado", "todos" if catalog == "paises" else "activos")
    hierarchy = []
    if catalog == "paises":
        child_status = Q()
        if status in {"activos", "inactivos"}:
            child_status = Q(activo=status == "activos")
        lugar_qs = LugarTuristico.objects.filter(child_status).order_by("nombre")
        departamento_qs = Departamento.objects.filter(child_status).order_by("nombre").prefetch_related(
            Prefetch("lugares_turisticos", queryset=lugar_qs)
        )
        country_qs = Pais.objects.all()
        if status in {"activos", "inactivos"}:
            country_qs = country_qs.filter(
                activo=status == "activos"
            )
        country_qs = country_qs.prefetch_related(Prefetch("departamentos", queryset=departamento_qs))
        query = request.GET.get("q", "").strip().lower()
        for pais in country_qs:
            departamentos = list(pais.departamentos.all())
            if query and not (
                query in pais.nombre.lower()
                or any(query in departamento.nombre.lower() for departamento in departamentos)
                or any(query in lugar.nombre.lower() for departamento in departamentos for lugar in departamento.lugares_turisticos.all())
            ):
                continue
            hierarchy.append(pais)
    items = config["model"].objects.all()
    if catalog == "departamentos":
        items = items.select_related("pais").annotate(total_lugares=Count("lugares_turisticos"))
    elif catalog == "paises":
        items = items.annotate(total_departamentos=Count("departamentos"))
    elif catalog == "lugares":
        items = items.select_related("departamento__pais").annotate(total_tours=Count("tours"))
    elif catalog == "tours":
        items = items.select_related("lugar_turistico__departamento__pais")
    query = request.GET.get("q", "").strip()
    if query:
        if catalog == "paises":
            items = items.filter(nombre__icontains=query)
        elif catalog == "departamentos":
            items = items.filter(Q(nombre__icontains=query) | Q(pais__nombre__icontains=query))
        elif catalog == "lugares":
            items = items.filter(
                Q(nombre__icontains=query) | Q(departamento__nombre__icontains=query)
                | Q(departamento__pais__nombre__icontains=query)
            )
        else:
            items = items.filter(
                Q(nombre_comercial__icontains=query) | Q(lugar_turistico__nombre__icontains=query)
            )
    if status in {"activos", "inactivos"}:
        items = items.filter(activo=status == "activos")
    if catalog == "tours":
        items = items.order_by("lugar_turistico__nombre", "nombre_comercial")
    elif catalog == "lugares":
        items = items.order_by("departamento__pais__nombre", "departamento__nombre", "nombre")
    elif catalog == "departamentos":
        items = items.order_by("pais__nombre", "nombre")
    else:
        items = items.order_by("nombre")
    page = Paginator(items, 15).get_page(request.GET.get("page"))
    can_manage_catalog = request.user.is_superuser or request.user.groups.filter(
        name="Administrador"
    ).exists()
    return render(
        request,
        "sami_admin/catalogo_list.html",
        {"items": page, "page_obj": page, "catalog": catalog, "query": query,
         "status": status, "can_manage_catalog": can_manage_catalog,
         "hierarchy": hierarchy, **config},
    )


@catalog_manager_required
def catalog_create(request, catalog):
    config = _catalog_config(catalog)
    initial = {}
    if request.method == "GET":
        if catalog == "departamentos" and request.GET.get("pais", "").isdigit():
            initial["pais"] = request.GET["pais"]
        if catalog == "lugares" and request.GET.get("departamento", "").isdigit():
            initial["departamento"] = request.GET["departamento"]
    form = config["form"](request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.creado_por = request.user
        item.actualizado_por = request.user
        item.save()
        messages.success(request, f"El {config['singular']} fue creado correctamente.")
        return redirect("sami_admin:catalog-list", catalog=_catalog_home(catalog))
    return render(
        request,
        "sami_admin/catalogo_form.html",
        {"form": form, "catalog": catalog, "catalog_home": _catalog_home(catalog), "form_title": f"Nuevo {config['singular']}"},
    )


@catalog_manager_required
def catalog_update(request, catalog, item_id):
    config = _catalog_config(catalog)
    item = get_object_or_404(config["model"], pk=item_id)
    form = config["form"](request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.actualizado_por = request.user
        item.save()
        messages.success(request, f"El {config['singular']} fue actualizado.")
        return redirect("sami_admin:catalog-list", catalog=_catalog_home(catalog))
    return render(
        request,
        "sami_admin/catalogo_form.html",
        {"form": form, "catalog": catalog, "catalog_home": _catalog_home(catalog), "form_title": f"Editar {config['singular']}"},
    )


@require_POST
@superuser_required
def catalog_delete(request, catalog, item_id):
    config = _catalog_config(catalog)
    item = get_object_or_404(config["model"], pk=item_id)
    try:
        item.delete()
        messages.success(request, f"El {config['singular']} fue eliminado.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar porque tiene elementos relacionados.")
    return redirect("sami_admin:catalog-list", catalog=catalog)


@require_POST
@catalog_manager_required
def catalog_toggle(request, catalog, item_id):
    config = _catalog_config(catalog)
    item = get_object_or_404(config["model"], pk=item_id)
    item.activo = not item.activo
    item.actualizado_por = request.user
    item.save(update_fields=["activo", "actualizado_por", "actualizado_en"])
    action = "activado" if item.activo else "desactivado"
    messages.success(request, f"El {config['singular']} fue {action}.")
    return redirect("sami_admin:catalog-list", catalog=catalog)


@staff_required
def quotation_update(request, quotation_id):
    quotation = get_object_or_404(quotations_for(request.user), pk=quotation_id)
    form = CotizacionForm(request.POST or None, instance=quotation)
    if request.method == "POST" and form.is_valid():
        quotation = form.save()
        form.save_destinations(quotation)
        HistorialCotizacion.objects.create(
            cotizacion=quotation,
            usuario=request.user,
            accion="actualizada",
            estado=quotation.estado,
            datos={"tipo": quotation.tipo_cotizacion, "precio": str(quotation.precio_estimado)},
        )
        messages.success(request, "La cotización fue actualizada.")
        return redirect("sami_admin:quotation-list")
    return render(
        request,
        "sami_admin/cotizacion_form.html",
        {
            "form": form,
            "form_title": "Editar cotización",
            "historial": quotation.historial.select_related("usuario")[:12],
        },
    )


@staff_required
def quotation_preview(request, quotation_id):
    quotation = get_object_or_404(quotations_for(request.user), pk=quotation_id)
    return render(
        request,
        "sami_admin/cotizacion_documento.html",
        {
            "cotizacion": quotation,
            "preview": True,
            "contact_email": settings.CONTACT_EMAIL,
        },
    )


@staff_required
def quotation_pdf(request, quotation_id):
    quotation = get_object_or_404(quotations_for(request.user), pk=quotation_id)
    html = render_to_string(
        "sami_admin/cotizacion_documento.html",
        {
            "cotizacion": quotation,
            "preview": False,
            "contact_email": settings.CONTACT_EMAIL,
        },
        request=request,
    )
    base_url = request.build_absolute_uri("/")
    pdf = generate_quotation_pdf(html, base_url=base_url)
    HistorialCotizacion.objects.create(
        cotizacion=quotation,
        usuario=request.user,
        accion="pdf_generado",
        estado=getattr(quotation, "estado", ""),
    )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Cotizacion_SAMI_{quotation.pk}.pdf"'
    )
    return response


@require_POST
@staff_required
def quotation_delete(request, quotation_id):
    quotation = get_object_or_404(quotations_for(request.user), pk=quotation_id)
    quotation.archivada = True
    quotation.save(update_fields=["archivada"])
    HistorialCotizacion.objects.create(
        cotizacion=quotation,
        usuario=request.user,
        accion="archivada",
        estado=quotation.estado,
    )
    messages.success(request, "La cotización fue archivada y conserva su historial.")
    return redirect("sami_admin:quotation-list")


@staff_required
def change_password(request):
    """Let every authenticated staff role update its own password."""
    form = PasswordChangeForm(request.user, request.POST or None)
    input_class = (
        "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
        "text-brand-navy shadow-sm outline-none transition "
        "focus:border-brand-red focus:ring-4 focus:ring-brand-red/10"
    )
    for field in form.fields.values():
        field.widget.attrs["class"] = input_class
    apply_error_attributes(form)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Tu contraseña fue actualizada correctamente.")
        return redirect("sami_admin:dashboard")

    return render(
        request,
        "sami_admin/change_password.html",
        {"form": form},
    )


@administrator_required
def user_list(request):
    """List current and deactivated staff accounts for auditability."""
    users = list(
        get_user_model()
        .objects.filter(is_staff=True, is_superuser=False)
        .prefetch_related("groups")
        .order_by("-is_active", "-is_superuser", "first_name", "username")
    )
    for user in users:
        user.sami_role = get_user_role(user)
    return render(request, "sami_admin/user_list.html", {"users": users})


@administrator_required
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


@administrator_required
def user_update(request, user_id):
    """Update identity and role fields for a staff account."""
    user = get_object_or_404(
        get_user_model(), pk=user_id, is_staff=True, is_superuser=False
    )
    form = StaffUserUpdateForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        new_role = form.cleaned_data["role"]
        active_administrators = get_user_model().objects.filter(
            is_active=True,
            is_staff=True,
            is_superuser=False,
            groups__name=MANAGED_GROUPS[ROLE_ADMIN],
        ).distinct()
        if (
            user.groups.filter(name=MANAGED_GROUPS[ROLE_ADMIN]).exists()
            and new_role != ROLE_ADMIN
            and active_administrators.count() <= 1
        ):
            form.add_error(
                "role",
                "Debe permanecer al menos un administrador activo.",
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
@administrator_required
def user_deactivate(request, user_id):
    """Soft-delete a staff account while retaining its historical relations."""
    user = get_object_or_404(
        get_user_model(), pk=user_id, is_staff=True, is_superuser=False
    )
    if user.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
    elif (
        user.groups.filter(name=MANAGED_GROUPS[ROLE_ADMIN]).exists()
        and get_user_model().objects.filter(
            is_superuser=False,
            is_staff=True,
            is_active=True,
            groups__name=MANAGED_GROUPS[ROLE_ADMIN],
        ).distinct().count()
        <= 1
    ):
        messages.error(request, "Debe permanecer al menos un administrador activo.")
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(
            request,
            f"El usuario {user.username} fue eliminado del acceso al panel.",
        )
    return redirect("sami_admin:user-list")


@require_POST
@administrator_required
def user_delete(request, user_id):
    """Delete unused accounts; preserve referenced accounts by revoking access."""
    user = get_object_or_404(
        get_user_model(), pk=user_id, is_staff=True, is_superuser=False
    )
    if user.pk == request.user.pk:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect("sami_admin:user-list")

    is_administrator = user.groups.filter(
        name=MANAGED_GROUPS[ROLE_ADMIN]
    ).exists()
    active_administrators = get_user_model().objects.filter(
        is_superuser=False,
        is_staff=True,
        is_active=True,
        groups__name=MANAGED_GROUPS[ROLE_ADMIN],
    ).distinct()
    if is_administrator and active_administrators.count() <= 1:
        messages.error(request, "Debe permanecer al menos un administrador activo.")
        return redirect("sami_admin:user-list")

    username = user.username
    try:
        user.delete()
        messages.success(request, f"El usuario {username} fue eliminado.")
    except ProtectedError:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.warning(
            request,
            f"El acceso de {username} fue eliminado. La cuenta se conservó porque tiene historial relacionado.",
        )
    return redirect("sami_admin:user-list")

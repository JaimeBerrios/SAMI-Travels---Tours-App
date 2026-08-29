from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Cotizacion, Departamento, LugarTuristico, Pais


ROLE_SUPERUSER = "superuser"
ROLE_ADMIN = "administrador"
ROLE_ADVISER = "asesor"
ROLE_CHOICES = (
    (ROLE_SUPERUSER, "Superusuario"),
    (ROLE_ADMIN, "Administrador"),
    (ROLE_ADVISER, "Asesor"),
)
MANAGED_GROUPS = {
    ROLE_ADMIN: "Administrador",
    ROLE_ADVISER: "Asesor",
}


def apply_error_attributes(form):
    """Expose bound field errors visually and to assistive technologies."""
    if not form.is_bound:
        return
    for field_name in form.errors:
        if field_name not in form.fields:
            continue
        field = form.fields[field_name]
        current_class = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (
            f"{current_class} border-rose-500 focus:border-rose-500 "
            "focus:ring-rose-500/20"
        ).strip()
        field.widget.attrs["aria-invalid"] = "true"
        described_by = field.widget.attrs.get("aria-describedby", "").split()
        error_id = f"id_{field_name}_error"
        if error_id not in described_by:
            described_by.append(error_id)
        field.widget.attrs["aria-describedby"] = " ".join(described_by)


def get_user_role(user):
    if user.is_superuser:
        return ROLE_SUPERUSER
    group_names = {group.name for group in user.groups.all()}
    if MANAGED_GROUPS[ROLE_ADMIN] in group_names:
        return ROLE_ADMIN
    return ROLE_ADVISER


class StaffUserFieldsMixin:
    role = forms.ChoiceField(label="Rol", choices=ROLE_CHOICES)

    def apply_tailwind_classes(self):
        self.fields["email"].required = True
        input_class = (
            "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
            "text-brand-navy shadow-sm outline-none transition "
            "placeholder:text-slate-400 focus:border-brand-red "
            "focus:ring-4 focus:ring-brand-red/10"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = input_class
        apply_error_attributes(self)


class SamiAdminAuthenticationForm(AuthenticationForm):
    """Authenticate only active members of the SAMI administrative team."""

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Nombre de usuario",
                "class": (
                    "block w-full rounded-xl border border-slate-300 bg-white "
                    "py-3 pl-11 pr-4 text-brand-navy shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-rose-500 "
                    "focus:ring-2 focus:ring-rose-500"
                ),
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Tu contraseña",
                "class": (
                    "block w-full rounded-xl border border-slate-300 bg-white "
                    "py-3 pl-11 pr-12 text-brand-navy shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-rose-500 "
                    "focus:ring-2 focus:ring-rose-500"
                ),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_error_attributes(self)

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "Esta cuenta no tiene acceso al panel administrativo.",
                code="not_staff",
            )


class StaffUserCreationForm(StaffUserFieldsMixin, UserCreationForm):
    """Create a staff account with a role selected by a superuser."""

    role = forms.ChoiceField(label="Rol", choices=ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Usuario",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


class StaffUserUpdateForm(StaffUserFieldsMixin, forms.ModelForm):
    """Edit identity fields and the SAMI role of an existing staff account."""

    role = forms.ChoiceField(label="Rol", choices=ROLE_CHOICES)

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "role")
        labels = StaffUserCreationForm.Meta.labels

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()
        if self.instance and self.instance.pk:
            self.fields["role"].initial = get_user_role(self.instance)


class CotizacionForm(forms.ModelForm):
    pais = forms.ModelChoiceField(
        label="País",
        queryset=Pais.objects.all(),
        required=False,
        empty_label="Selecciona un país",
    )
    departamento = forms.ModelChoiceField(
        label="Departamento",
        queryset=Departamento.objects.none(),
        required=False,
        empty_label="Selecciona un departamento",
    )
    FLIGHT_FIELDS = (
        "ruta_vuelo",
        "cantidad_adultos",
        "cantidad_ninos",
        "fecha_ida",
        "hora_salida_ida",
        "hora_llegada_ida",
        "escala_ida",
        "fecha_vuelta",
        "hora_salida_vuelta",
        "hora_llegada_vuelta",
        "escala_vuelta",
        "aerolinea",
        "equipaje_incluido",
        "notas_importantes",
    )

    class Meta:
        model = Cotizacion
        fields = (
            "cliente_nombre",
            "cliente_correo",
            "tipo_cotizacion",
            "destino",
            "pais",
            "departamento",
            "lugar_turistico",
            "duracion_tour",
            "punto_encuentro",
            "incluye",
            "no_incluye",
            "itinerario_resumido",
            "ruta_vuelo",
            "cantidad_adultos",
            "cantidad_ninos",
            "fecha_ida",
            "hora_salida_ida",
            "hora_llegada_ida",
            "escala_ida",
            "fecha_vuelta",
            "hora_salida_vuelta",
            "hora_llegada_vuelta",
            "escala_vuelta",
            "aerolinea",
            "equipaje_incluido",
            "notas_importantes",
            "precio_estimado",
            "estado",
        )
        labels = {
            "cliente_nombre": "Nombre del cliente",
            "cliente_correo": "Correo del cliente",
            "tipo_cotizacion": "Tipo de cotización",
            "lugar_turistico": "Lugar turístico",
            "duracion_tour": "Duración del tour",
            "punto_encuentro": "Punto de encuentro",
            "no_incluye": "No incluye",
            "itinerario_resumido": "Itinerario resumido",
            "ruta_vuelo": "Ruta del vuelo",
            "cantidad_ninos": "Cantidad de niños",
            "escala_ida": "Escala de ida",
            "escala_vuelta": "Escala de vuelta",
            "aerolinea": "Aerolínea (uso interno)",
            "equipaje_incluido": "Equipaje incluido",
            "notas_importantes": "Notas importantes para el cliente",
            "precio_estimado": "Precio estimado (USD)",
        }
        help_texts = {
            "tipo_cotizacion": "Los campos de vuelo se mostrar\u00e1n seg\u00fan esta selecci\u00f3n.",
            "aerolinea": "Dato interno: nunca se muestra en el documento del cliente.",
            "equipaje_incluido": "Detalla peso, piezas y tipo de equipaje incluidos.",
            "notas_importantes": "Estas notas s\u00ed ser\u00e1n visibles para el cliente.",
        }
        widgets = {
            "cliente_nombre": forms.TextInput(attrs={"placeholder": "Nombre completo"}),
            "cliente_correo": forms.EmailInput(
                attrs={"placeholder": "cliente@correo.com"}
            ),
            "destino": forms.TextInput(attrs={"placeholder": "Destino del viaje"}),
            "duracion_tour": forms.TextInput(
                attrs={"placeholder": "Ej. 3 Días / 2 Noches"}
            ),
            "punto_encuentro": forms.TextInput(
                attrs={"placeholder": "Ej. Recepción del hotel a las 8:00 a. m."}
            ),
            "incluye": forms.Textarea(attrs={"rows": 4}),
            "no_incluye": forms.Textarea(attrs={"rows": 4}),
            "itinerario_resumido": forms.Textarea(attrs={"rows": 5}),
            "ruta_vuelo": forms.TextInput(
                attrs={"placeholder": "Ej. San Salvador a Guadalajara"}
            ),
            "cantidad_adultos": forms.NumberInput(attrs={"min": "0"}),
            "cantidad_ninos": forms.NumberInput(attrs={"min": "0"}),
            "fecha_ida": forms.DateInput(attrs={"type": "date"}),
            "hora_salida_ida": forms.TimeInput(attrs={"type": "time"}),
            "hora_llegada_ida": forms.TimeInput(attrs={"type": "time"}),
            "escala_ida": forms.TextInput(
                attrs={"placeholder": "Ej. 1 escala de 2 h 30 min"}
            ),
            "fecha_vuelta": forms.DateInput(attrs={"type": "date"}),
            "hora_salida_vuelta": forms.TimeInput(attrs={"type": "time"}),
            "hora_llegada_vuelta": forms.TimeInput(attrs={"type": "time"}),
            "escala_vuelta": forms.TextInput(
                attrs={"placeholder": "Ej. Vuelo directo"}
            ),
            "equipaje_incluido": forms.Textarea(attrs={"rows": 3}),
            "notas_importantes": forms.Textarea(attrs={"rows": 3}),
            "precio_estimado": forms.NumberInput(
                attrs={"min": "0", "step": "0.01", "placeholder": "0.00"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pais_id = self.data.get("pais") if self.is_bound else None
        departamento_id = self.data.get("departamento") if self.is_bound else None
        if self.instance and self.instance.lugar_turistico_id:
            lugar = self.instance.lugar_turistico
            pais_id = pais_id or lugar.departamento.pais_id
            departamento_id = departamento_id or lugar.departamento_id
            self.fields["pais"].initial = pais_id
            self.fields["departamento"].initial = departamento_id
        if pais_id:
            self.fields["departamento"].queryset = Departamento.objects.filter(
                pais_id=pais_id
            )
        self.fields["lugar_turistico"].queryset = LugarTuristico.objects.none()
        if departamento_id:
            self.fields["lugar_turistico"].queryset = LugarTuristico.objects.filter(
                departamento_id=departamento_id
            )
        input_class = (
            "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
            "text-brand-navy shadow-sm outline-none transition "
            "placeholder:text-slate-400 focus:border-brand-red "
            "focus:ring-4 focus:ring-brand-red/10"
        )
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = input_class
            if field.help_text:
                field.widget.attrs["aria-describedby"] = f"id_{field_name}_helptext"
        apply_error_attributes(self)

    def clean(self):
        cleaned_data = super().clean()
        lugar = cleaned_data.get("lugar_turistico")
        departamento = cleaned_data.get("departamento")
        if lugar and departamento and lugar.departamento_id != departamento.pk:
            self.add_error("lugar_turistico", "El lugar no pertenece al departamento seleccionado.")
        if cleaned_data.get("tipo_cotizacion") == Cotizacion.TipoCotizacion.TOURS:
            for field_name in self.FLIGHT_FIELDS:
                cleaned_data[field_name] = None
        return cleaned_data


class CatalogFormMixin:
    def apply_tailwind_classes(self):
        input_class = (
            "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
            "text-brand-navy shadow-sm outline-none transition focus:border-brand-red "
            "focus:ring-4 focus:ring-brand-red/10"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = input_class
        apply_error_attributes(self)


class PaisForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = Pais
        fields = ("nombre",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()


class DepartamentoForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ("pais", "nombre")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()


class LugarTuristicoForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = LugarTuristico
        fields = ("departamento", "nombre", "imagen", "descripcion_historica")
        widgets = {"descripcion_historica": forms.Textarea(attrs={"rows": 7})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()

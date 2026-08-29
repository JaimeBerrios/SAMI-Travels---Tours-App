from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Cotizacion


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


class SamiAdminAuthenticationForm(AuthenticationForm):
    """Authenticate only active members of the SAMI administrative team."""

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Tu usuario de Django",
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
                    "py-3 pl-11 pr-4 text-brand-navy shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-rose-500 "
                    "focus:ring-2 focus:ring-rose-500"
                ),
            }
        ),
    )

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
        if self.is_bound:
            for field_name in self.errors:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs["aria-invalid"] = "true"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("tipo_cotizacion") == Cotizacion.TipoCotizacion.TOURS:
            for field_name in self.FLIGHT_FIELDS:
                cleaned_data[field_name] = None
        return cleaned_data

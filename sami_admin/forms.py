from io import BytesIO
import json
from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.files.base import ContentFile
from django.db.models import Q
from PIL import Image, ImageOps, UnidentifiedImageError

from core.models import SolicitudContacto

from .models import (
    CampanaPromocional, Cotizacion, CotizacionDestino, Departamento,
    LugarTuristico, Pais, Tour,
)


ROLE_ADMIN = "administrador"
ROLE_ADVISER = "asesor"
ROLE_CHOICES = (
    (ROLE_ADMIN, "Administrador"),
    (ROLE_ADVISER, "Asesor"),
)
MANAGED_GROUPS = {
    ROLE_ADMIN: "Administrador",
    ROLE_ADVISER: "Asesor",
}


class SolicitudGestionForm(forms.ModelForm):
    class Meta:
        model = SolicitudContacto
        fields = (
            "correo", "telefono", "estado", "asignada_a", "notas_internas"
        )
        widgets = {"notas_internas": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asignada_a"].queryset = get_user_model().objects.filter(
            is_active=True,
            is_staff=True,
        ).order_by("first_name", "username")
        input_class = (
            "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
            "text-brand-navy shadow-sm outline-none transition focus:border-brand-red "
            "focus:ring-4 focus:ring-brand-red/10"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = input_class
        apply_error_attributes(self)


class CampanaPromocionalForm(forms.ModelForm):
    IMAGE_SPECS = {
        "imagen_escritorio": ((1920, 800), "escritorio"),
        "imagen_movil": ((1080, 1350), "móvil"),
    }
    MULTIMEDIA_LIMITS = {
        "multimedia_escritorio": {"gif": 5 * 1024 * 1024, "video": 12 * 1024 * 1024},
        "multimedia_movil": {"gif": 4 * 1024 * 1024, "video": 8 * 1024 * 1024},
    }

    class Meta:
        model = CampanaPromocional
        fields = (
            "nombre", "etiqueta", "titulo", "descripcion",
            "imagen_escritorio", "imagen_movil", "tipo_multimedia",
            "multimedia_escritorio", "multimedia_movil", "color_superposicion",
            "opacidad_superposicion", "texto_alternativo",
            "texto_boton", "tipo_enlace", "lugar_turistico", "tour",
            "url_personalizada", "fecha_inicio", "fecha_fin", "prioridad", "orden",
            "activo", "mostrar_avion",
        )
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "tipo_multimedia": forms.RadioSelect,
            "color_superposicion": forms.TextInput(attrs={"type": "color"}),
            "opacidad_superposicion": forms.NumberInput(
                attrs={"type": "range", "min": 0, "max": 100, "step": 1}
            ),
            "fecha_inicio": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "fecha_fin": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lugar_turistico"].queryset = LugarTuristico.objects.filter(
            activo=True,
            departamento__activo=True,
            departamento__pais__activo=True,
        )
        self.fields["tour"].queryset = Tour.objects.filter(
            activo=True,
            lugar_turistico__activo=True,
        )
        input_class = (
            "block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 "
            "text-brand-navy shadow-sm outline-none transition focus:border-brand-red "
            "focus:ring-4 focus:ring-brand-red/10"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = input_class
        for name in ("activo", "mostrar_avion"):
            self.fields[name].widget.attrs["class"] = "size-5 accent-rose-600"
        for name in ("imagen_escritorio", "imagen_movil"):
            self.fields[name].widget.attrs["accept"] = "image/jpeg,image/png,image/webp"
        for name in ("multimedia_escritorio", "multimedia_movil"):
            self.fields[name].widget.attrs["accept"] = "image/gif,video/mp4,video/webm"
        self.fields["multimedia_escritorio"].label = "GIF o video para computadora"
        self.fields["multimedia_movil"].label = "GIF o video para celular"
        self.fields["tipo_multimedia"].widget.attrs["class"] = "space-y-2"
        self.fields["tipo_multimedia"].required = False
        self.fields["tipo_multimedia"].initial = CampanaPromocional.TipoMultimedia.IMAGEN
        self.fields["orden"].required = False
        self.fields["orden"].initial = 0
        self.fields["color_superposicion"].widget.attrs["class"] = (
            "h-12 w-full cursor-pointer rounded-xl border border-slate-300 bg-white p-1"
        )
        self.fields["url_personalizada"].widget.attrs["placeholder"] = (
            "https://ejemplo.com/promocion"
        )
        for name in ("fecha_inicio", "fecha_fin"):
            self.fields[name].widget.format = "%Y-%m-%dT%H:%M"
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
        apply_error_attributes(self)

    def _clean_campaign_image(self, field_name):
        image = self.cleaned_data.get(field_name)
        uploaded = self.files.get(field_name)
        if not image or not uploaded:
            return image
        if image.size > 1536 * 1024:
            raise forms.ValidationError("La imagen no puede superar 1.5 MB.")
        target, label = self.IMAGE_SPECS[field_name]
        try:
            image.seek(0)
            with Image.open(image) as source:
                source.load()
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Usa una imagen JPG, PNG o WebP.")
                ratio = source.width / source.height
                target_ratio = target[0] / target[1]
                if abs(ratio - target_ratio) / target_ratio > 0.10:
                    raise forms.ValidationError(
                        f"La proporción no corresponde a la imagen de {label}. "
                        f"Utiliza {target[0]} × {target[1]} px."
                    )
                source = ImageOps.fit(
                    source.convert("RGB"), target, method=Image.Resampling.LANCZOS
                )
                output = BytesIO()
                source.save(output, format="WEBP", quality=84, method=6)
        except forms.ValidationError:
            raise
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("El archivo no es una imagen válida.")
        filename = f"{Path(uploaded.name).stem}.webp"
        return ContentFile(output.getvalue(), name=filename)

    def clean_imagen_escritorio(self):
        return self._clean_campaign_image("imagen_escritorio")

    def clean_imagen_movil(self):
        return self._clean_campaign_image("imagen_movil")

    def _clean_campaign_multimedia(self, field_name):
        media = self.cleaned_data.get(field_name)
        uploaded = self.files.get(field_name)
        if not media or not uploaded:
            return media
        media_type = self.data.get(
            "tipo_multimedia", CampanaPromocional.TipoMultimedia.IMAGEN
        )
        if media_type not in {
            CampanaPromocional.TipoMultimedia.GIF,
            CampanaPromocional.TipoMultimedia.VIDEO,
        }:
            raise forms.ValidationError(
                "Selecciona GIF animado o Video antes de adjuntar este archivo."
            )
        limit = self.MULTIMEDIA_LIMITS[field_name][media_type]
        if media.size > limit:
            raise forms.ValidationError(
                f"El archivo no puede superar {limit // (1024 * 1024)} MB."
            )
        suffix = Path(uploaded.name).suffix.lower()
        uploaded.seek(0)
        signature = uploaded.read(16)
        uploaded.seek(0)
        if media_type == CampanaPromocional.TipoMultimedia.GIF:
            if suffix != ".gif" or not signature.startswith((b"GIF87a", b"GIF89a")):
                raise forms.ValidationError("Selecciona un archivo GIF válido.")
            try:
                with Image.open(uploaded) as source:
                    if source.format != "GIF" or getattr(source, "n_frames", 1) < 2:
                        raise forms.ValidationError("El GIF debe contener animación.")
                    target, label = self.IMAGE_SPECS[
                        field_name.replace("multimedia", "imagen")
                    ]
                    ratio = source.width / source.height
                    target_ratio = target[0] / target[1]
                    if abs(ratio - target_ratio) / target_ratio > 0.10:
                        raise forms.ValidationError(
                            f"La proporción no corresponde al formato de {label}. "
                            f"Utiliza una proporción cercana a {target[0]} × {target[1]}."
                        )
            except forms.ValidationError:
                raise
            except (UnidentifiedImageError, OSError):
                raise forms.ValidationError("El archivo GIF no es válido.")
            finally:
                uploaded.seek(0)
            return media
        valid_mp4 = suffix == ".mp4" and b"ftyp" in signature[4:12]
        valid_webm = suffix == ".webm" and signature.startswith(b"\x1a\x45\xdf\xa3")
        if not (valid_mp4 or valid_webm):
            raise forms.ValidationError("Usa un video MP4 o WebM válido.")
        return media

    def clean_multimedia_escritorio(self):
        return self._clean_campaign_multimedia("multimedia_escritorio")

    def clean_multimedia_movil(self):
        return self._clean_campaign_multimedia("multimedia_movil")

    def clean(self):
        cleaned = super().clean()
        cleaned["tipo_multimedia"] = (
            cleaned.get("tipo_multimedia")
            or CampanaPromocional.TipoMultimedia.IMAGEN
        )
        cleaned["orden"] = cleaned.get("orden") or 0
        start = cleaned.get("fecha_inicio")
        end = cleaned.get("fecha_fin")
        if start and end and end <= start:
            self.add_error("fecha_fin", "Debe ser posterior al inicio de la campaña.")
        media_type = cleaned.get("tipo_multimedia")
        if media_type in {
            CampanaPromocional.TipoMultimedia.GIF,
            CampanaPromocional.TipoMultimedia.VIDEO,
        }:
            for field_name in ("multimedia_escritorio", "multimedia_movil"):
                if not cleaned.get(field_name) and field_name not in self.errors:
                    self.add_error(
                        field_name,
                        "Adjunta una versión para computadora y otra para celular.",
                    )
                    continue
                media = cleaned.get(field_name)
                if not media or field_name in self.errors:
                    continue
                suffix = Path(media.name).suffix.lower()
                if media_type == CampanaPromocional.TipoMultimedia.GIF and suffix != ".gif":
                    self.add_error(field_name, "El archivo guardado no es GIF; reemplázalo.")
                elif media_type == CampanaPromocional.TipoMultimedia.VIDEO and suffix not in {
                    ".mp4",
                    ".webm",
                }:
                    self.add_error(
                        field_name, "El archivo guardado no es MP4 o WebM; reemplázalo."
                    )
        link_type = cleaned.get("tipo_enlace")
        requirements = {
            CampanaPromocional.TipoEnlace.DESTINO: ("lugar_turistico", "Selecciona el destino de la campaña."),
            CampanaPromocional.TipoEnlace.TOUR: ("tour", "Selecciona el tour de la campaña."),
            CampanaPromocional.TipoEnlace.PERSONALIZADO: ("url_personalizada", "Escribe la dirección del enlace."),
        }
        if link_type in requirements:
            field, error = requirements[link_type]
            if not cleaned.get(field):
                self.add_error(field, error)
        return cleaned


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
    """Create a staff account with an administrator or adviser role."""

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
    destinos_json = forms.CharField(required=False, widget=forms.HiddenInput())
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
    tour = forms.ModelChoiceField(
        label="Tour o paquete",
        queryset=Tour.objects.none(),
        required=False,
        empty_label="Selecciona un tour (opcional)",
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
            "tour",
            "destinos_json",
            "duracion_tour",
            "punto_encuentro",
            "incluye",
            "no_incluye",
            "itinerario_resumido",
            "recomendaciones_tour",
            "que_llevar_tour",
            "restricciones_tour",
            "politica_cancelacion",
            "notas_tour",
            "vigencia_cotizacion",
            "edades_ninos",
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
            "recomendaciones_tour": "Recomendaciones al viajero",
            "que_llevar_tour": "Qué llevar",
            "restricciones_tour": "Restricciones",
            "politica_cancelacion": "Política de cancelación",
            "notas_tour": "Notas importantes del tour",
            "vigencia_cotizacion": "Vigencia de la cotización",
            "edades_ninos": "Edades de los niños",
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
            "recomendaciones_tour": forms.Textarea(attrs={"rows": 3}),
            "que_llevar_tour": forms.Textarea(attrs={"rows": 3}),
            "restricciones_tour": forms.Textarea(attrs={"rows": 3}),
            "politica_cancelacion": forms.Textarea(attrs={"rows": 3}),
            "notas_tour": forms.Textarea(attrs={"rows": 3}),
            "vigencia_cotizacion": forms.DateInput(attrs={"type": "date"}),
            "edades_ninos": forms.TextInput(attrs={"placeholder": "Ej. 5, 11"}),
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
        self._original_lugar_id = self.instance.lugar_turistico_id
        self._original_tour_id = self.instance.tour_id
        pais_id = self.data.get("pais") if self.is_bound else None
        departamento_id = self.data.get("departamento") if self.is_bound else None
        lugar_id = self.data.get("lugar_turistico") if self.is_bound else None
        if self.instance and self.instance.lugar_turistico_id:
            lugar = self.instance.lugar_turistico
            pais_id = pais_id or lugar.departamento.pais_id
            departamento_id = departamento_id or lugar.departamento_id
            lugar_id = lugar_id or lugar.pk
            self.fields["pais"].initial = pais_id
            self.fields["departamento"].initial = departamento_id
        if not self.is_bound and self.instance and self.instance.pk:
            self.fields["destinos_json"].initial = json.dumps([
                {
                    "pais": destino.lugar_turistico.departamento.pais_id,
                    "departamento": destino.lugar_turistico.departamento_id,
                    "lugar": destino.lugar_turistico_id,
                    "tour": destino.tour_id,
                    "fecha": destino.fecha_visita.isoformat(),
                    "precio": str(destino.precio_manual or ""),
                    "notas": destino.notas,
                }
                for destino in self.instance.destinos.all()
            ])
        country_filter = Q(activo=True)
        if not self.is_bound and pais_id:
            country_filter |= Q(pk=pais_id)
        self.fields["pais"].queryset = Pais.objects.filter(country_filter)
        if pais_id:
            department_filter = Q(activo=True, pais__activo=True)
            if not self.is_bound and departamento_id:
                department_filter |= Q(pk=departamento_id)
            self.fields["departamento"].queryset = Departamento.objects.filter(
                department_filter, pais_id=pais_id
            )
        self.fields["lugar_turistico"].queryset = LugarTuristico.objects.none()
        if departamento_id:
            place_filter = Q(
                activo=True,
                departamento__activo=True,
                departamento__pais__activo=True,
            )
            if not self.is_bound and lugar_id:
                place_filter |= Q(pk=lugar_id)
            self.fields["lugar_turistico"].queryset = LugarTuristico.objects.filter(
                place_filter,
                departamento_id=departamento_id,
            )
        self.fields["tour"].queryset = Tour.objects.none()
        if lugar_id:
            tour_filter = Q(
                activo=True,
                lugar_turistico__activo=True,
                lugar_turistico__departamento__activo=True,
                lugar_turistico__departamento__pais__activo=True,
            )
            if not self.is_bound and self.instance and self.instance.tour_id:
                tour_filter |= Q(pk=self.instance.tour_id)
            self.fields["tour"].queryset = Tour.objects.filter(
                tour_filter,
                lugar_turistico_id=lugar_id,
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
        tour = cleaned_data.get("tour")
        if lugar and departamento and lugar.departamento_id != departamento.pk:
            self.add_error("lugar_turistico", "El lugar no pertenece al departamento seleccionado.")
        if tour and lugar and tour.lugar_turistico_id != lugar.pk:
            self.add_error("tour", "El tour no pertenece al lugar seleccionado.")
        tipo = cleaned_data.get("tipo_cotizacion")
        legacy_lugar = cleaned_data.get("lugar_turistico")
        legacy_tour = cleaned_data.get("tour")
        destinos = []
        raw_destinos = cleaned_data.get("destinos_json") or "[]"
        try:
            parsed_destinos = json.loads(raw_destinos)
            if not isinstance(parsed_destinos, list):
                raise ValueError
        except (TypeError, ValueError, json.JSONDecodeError):
            self.add_error("destinos_json", "El itinerario de destinos no es válido.")
            parsed_destinos = []
        for index, item in enumerate(parsed_destinos):
            if not isinstance(item, dict):
                self.add_error("destinos_json", f"La parada {index + 1} no es válida.")
                continue
            try:
                lugar = LugarTuristico.objects.select_related(
                    "departamento__pais"
                ).get(pk=int(item.get("lugar")), activo=True)
            except (TypeError, ValueError, LugarTuristico.DoesNotExist):
                self.add_error("destinos_json", f"Selecciona un lugar válido para la parada {index + 1}.")
                continue
            tour = None
            if item.get("tour") not in (None, "", 0, "0"):
                try:
                    tour = Tour.objects.get(
                        pk=int(item["tour"]),
                        lugar_turistico=lugar,
                        activo=True,
                    )
                except (TypeError, ValueError, Tour.DoesNotExist):
                    self.add_error("destinos_json", f"El tour de la parada {index + 1} no es válido.")
                    continue
            try:
                fecha_visita = date.fromisoformat(str(item.get("fecha", "")))
            except (TypeError, ValueError):
                self.add_error("destinos_json", f"Indica una fecha para la parada {index + 1}.")
                continue
            precio = item.get("precio")
            if precio in (None, ""):
                precio = None
            else:
                try:
                    precio = Decimal(str(precio))
                    if precio < 0:
                        raise ValueError
                except (TypeError, ValueError, InvalidOperation):
                    self.add_error("destinos_json", f"El precio de la parada {index + 1} no es válido.")
                    continue
            destinos.append({
                "lugar": lugar,
                "tour": tour,
                "fecha": fecha_visita,
                "precio": precio,
                "notas": str(item.get("notas", ""))[:2000],
                "duracion": str(item.get("duracion") or (tour.duracion if tour else "") or cleaned_data.get("duracion_tour") or ""),
                "punto_encuentro": str(item.get("punto_encuentro") or (tour.punto_encuentro if tour else "") or cleaned_data.get("punto_encuentro") or ""),
                "incluye": str(item.get("incluye") or (tour.incluye if tour else "") or cleaned_data.get("incluye") or ""),
                "no_incluye": str(item.get("no_incluye") or (tour.no_incluye if tour else "") or cleaned_data.get("no_incluye") or ""),
                "itinerario": str(item.get("itinerario") or (tour.itinerario if tour else "") or cleaned_data.get("itinerario_resumido") or ""),
                "recomendaciones": str(item.get("recomendaciones") or (tour.recomendaciones if tour else "") or cleaned_data.get("recomendaciones_tour") or ""),
                "que_llevar": str(item.get("que_llevar") or (tour.que_llevar if tour else "") or cleaned_data.get("que_llevar_tour") or ""),
                "restricciones": str(item.get("restricciones") or (tour.restricciones if tour else "") or cleaned_data.get("restricciones_tour") or ""),
                "politica_cancelacion": str(item.get("politica_cancelacion") or (tour.politica_cancelacion if tour else "") or cleaned_data.get("politica_cancelacion") or ""),
            })
        # Compatibilidad con cotizaciones de tour creadas antes del itinerario
        # múltiple: si el formulario legado trae un lugar, se convierte en una
        # primera parada para no invalidar ni perder esos registros.
        if not destinos and legacy_lugar and tipo in (
            Cotizacion.TipoCotizacion.TOURS,
            Cotizacion.TipoCotizacion.VUELOS_TOURS,
        ):
            destinos.append({
                "lugar": legacy_lugar,
                "tour": legacy_tour,
                "fecha": date.today(),
                "precio": None,
                "notas": str(cleaned_data.get("notas_tour") or "")[:2000],
                "duracion": str(cleaned_data.get("duracion_tour") or ""),
                "punto_encuentro": str(cleaned_data.get("punto_encuentro") or ""),
                "incluye": str(cleaned_data.get("incluye") or ""),
                "no_incluye": str(cleaned_data.get("no_incluye") or ""),
                "itinerario": str(cleaned_data.get("itinerario_resumido") or ""),
                "recomendaciones": str(cleaned_data.get("recomendaciones_tour") or ""),
                "que_llevar": str(cleaned_data.get("que_llevar_tour") or ""),
                "restricciones": str(cleaned_data.get("restricciones_tour") or ""),
                "politica_cancelacion": str(cleaned_data.get("politica_cancelacion") or ""),
            })
        cleaned_data["destinos"] = destinos
        if destinos:
            first_destination = destinos[0]
            cleaned_data["lugar_turistico"] = first_destination["lugar"]
            cleaned_data["tour"] = first_destination["tour"]
            for field_name, destination_key in {
                "duracion_tour": "duracion",
                "punto_encuentro": "punto_encuentro",
                "incluye": "incluye",
                "no_incluye": "no_incluye",
                "itinerario_resumido": "itinerario",
                "recomendaciones_tour": "recomendaciones",
                "que_llevar_tour": "que_llevar",
                "restricciones_tour": "restricciones",
                "politica_cancelacion": "politica_cancelacion",
            }.items():
                if not cleaned_data.get(field_name):
                    cleaned_data[field_name] = first_destination[destination_key]
        includes_tour = tipo in (
            Cotizacion.TipoCotizacion.TOURS,
            Cotizacion.TipoCotizacion.VUELOS_TOURS,
        )
        includes_flight = tipo in (
            Cotizacion.TipoCotizacion.VUELOS,
            Cotizacion.TipoCotizacion.VUELOS_TOURS,
        )
        if tour:
            defaults = {
                "duracion_tour": tour.duracion,
                "punto_encuentro": tour.punto_encuentro,
                "incluye": tour.incluye,
                "no_incluye": tour.no_incluye,
                "itinerario_resumido": tour.itinerario,
                "recomendaciones_tour": tour.recomendaciones,
                "que_llevar_tour": tour.que_llevar,
                "restricciones_tour": tour.restricciones,
                "politica_cancelacion": tour.politica_cancelacion,
            }
            for name, value in defaults.items():
                if name not in self.data:
                    cleaned_data[name] = value
        if includes_tour:
            required_tour_fields = {
                "lugar_turistico": "Selecciona un lugar turístico para la propuesta.",
                "duracion_tour": "Indica la duración del tour.",
                "incluye": "Detalla qué incluye el tour.",
                "itinerario_resumido": "Agrega el itinerario resumido.",
            }
            for name, message in required_tour_fields.items():
                if name == "lugar_turistico" and destinos:
                    continue
                if not cleaned_data.get(name):
                    self.add_error(name, message)
            if not destinos:
                self.add_error("destinos_json", "Agrega al menos un destino al itinerario.")
        else:
            for name in (
                "lugar_turistico", "tour", "duracion_tour", "punto_encuentro",
                "incluye", "no_incluye", "itinerario_resumido",
                "recomendaciones_tour", "que_llevar_tour", "restricciones_tour",
                "politica_cancelacion", "notas_tour", "vigencia_cotizacion",
            ):
                cleaned_data[name] = None
            cleaned_data["destinos"] = []
        if includes_flight:
            for name, message in {
                "ruta_vuelo": "Indica la ruta del vuelo.",
                "cantidad_adultos": "Indica la cantidad de adultos.",
                "fecha_ida": "Indica la fecha de ida.",
            }.items():
                if cleaned_data.get(name) in (None, ""):
                    self.add_error(name, message)
            if cleaned_data.get("cantidad_adultos") is not None and cleaned_data["cantidad_adultos"] < 1:
                self.add_error("cantidad_adultos", "Debe viajar al menos un adulto.")
        if tipo == Cotizacion.TipoCotizacion.TOURS:
            for field_name in self.FLIGHT_FIELDS:
                cleaned_data[field_name] = None
        return cleaned_data

    def save(self, commit=True):
        quotation = super().save(commit=False)
        lugar = self.cleaned_data.get("lugar_turistico")
        if lugar:
            quotation.destino = lugar.nombre
            if not quotation.pk or lugar.pk != self._original_lugar_id:
                quotation.nombre_destino_cotizado = lugar.nombre
                quotation.ubicacion_destino_cotizada = (
                    f"{lugar.departamento.nombre}, {lugar.departamento.pais.nombre}"
                )
                quotation.descripcion_historica_cotizada = lugar.descripcion_historica
                quotation.imagen_destino_cotizada = lugar.imagen.name if lugar.imagen else ""
            selected_tour = self.cleaned_data.get("tour")
            if not quotation.pk or getattr(selected_tour, "pk", None) != self._original_tour_id:
                quotation.nombre_tour_cotizado = (
                    selected_tour.nombre_comercial if selected_tour else ""
                )
        else:
            quotation.nombre_destino_cotizado = ""
            quotation.ubicacion_destino_cotizada = ""
            quotation.descripcion_historica_cotizada = ""
            quotation.imagen_destino_cotizada = ""
            quotation.nombre_tour_cotizado = ""
        if commit:
            quotation.save()
            self.save_m2m()
        return quotation

    def save_destinations(self, quotation):
        CotizacionDestino.objects.filter(cotizacion=quotation).delete()
        destinations = self.cleaned_data.get("destinos", [])
        for order, item in enumerate(destinations, start=1):
            lugar = item["lugar"]
            tour = item["tour"]
            destination = CotizacionDestino.objects.create(
                cotizacion=quotation,
                lugar_turistico=lugar,
                tour=tour,
                fecha_visita=item["fecha"],
                orden=order,
                precio_manual=item["precio"],
                notas=item["notas"],
                nombre_destino=lugar.nombre,
                ubicacion_destino=f"{lugar.departamento.nombre}, {lugar.departamento.pais.nombre}",
                descripcion_historica=lugar.descripcion_historica,
                imagen_destino=lugar.imagen.name if lugar.imagen else "",
                nombre_tour=tour.nombre_comercial if tour else "",
                duracion_tour=item["duracion"],
                punto_encuentro=item["punto_encuentro"],
                incluye=item["incluye"],
                no_incluye=item["no_incluye"],
                itinerario=item["itinerario"],
                recomendaciones=item["recomendaciones"],
                que_llevar=item["que_llevar"],
                restricciones=item["restricciones"],
                politica_cancelacion=item["politica_cancelacion"],
            )
        first = destinations[0] if destinations else None
        if first:
            quotation.lugar_turistico = first["lugar"]
            quotation.tour = first["tour"]
            quotation.destino = first["lugar"].nombre
            quotation.nombre_destino_cotizado = first["lugar"].nombre
            quotation.ubicacion_destino_cotizada = (
                f"{first['lugar'].departamento.nombre}, {first['lugar'].departamento.pais.nombre}"
            )
            quotation.descripcion_historica_cotizada = first["lugar"].descripcion_historica
            quotation.imagen_destino_cotizada = first["lugar"].imagen.name if first["lugar"].imagen else ""
            quotation.nombre_tour_cotizado = first["tour"].nombre_comercial if first["tour"] else ""
            quotation.duracion_tour = first["duracion"]
            quotation.punto_encuentro = first["punto_encuentro"]
            quotation.incluye = first["incluye"]
            quotation.no_incluye = first["no_incluye"]
            quotation.itinerario_resumido = first["itinerario"]
            quotation.recomendaciones_tour = first["recomendaciones"]
            quotation.que_llevar_tour = first["que_llevar"]
            quotation.restricciones_tour = first["restricciones"]
            quotation.politica_cancelacion = first["politica_cancelacion"]
        quotation.save(update_fields=[
            "lugar_turistico", "tour", "destino", "nombre_destino_cotizado",
            "ubicacion_destino_cotizada", "descripcion_historica_cotizada",
            "imagen_destino_cotizada", "nombre_tour_cotizado", "duracion_tour",
            "punto_encuentro", "incluye", "no_incluye", "itinerario_resumido",
            "recomendaciones_tour", "que_llevar_tour", "restricciones_tour",
            "politica_cancelacion",
        ])


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
        fields = ("nombre", "activo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()


class DepartamentoForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ("pais", "nombre", "activo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Pais.objects.filter(activo=True)
        if self.instance and self.instance.pais_id:
            queryset = Pais.objects.filter(Q(activo=True) | Q(pk=self.instance.pais_id))
        self.fields["pais"].queryset = queryset
        self.apply_tailwind_classes()


class LugarTuristicoForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = LugarTuristico
        fields = (
            "departamento", "nombre", "imagen", "resumen_publico",
            "descripcion_historica", "mejor_epoca", "duracion_recomendada",
            "aeropuerto_principal", "actividades_destacadas", "requisitos_viaje",
            "destacado", "activo",
        )
        widgets = {
            "descripcion_historica": forms.Textarea(attrs={"rows": 7}),
            "actividades_destacadas": forms.Textarea(attrs={"rows": 5}),
            "requisitos_viaje": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Departamento.objects.filter(activo=True, pais__activo=True)
        if self.instance and self.instance.departamento_id:
            queryset = Departamento.objects.filter(
                Q(activo=True, pais__activo=True) | Q(pk=self.instance.departamento_id)
            )
        self.fields["departamento"].queryset = queryset
        self.apply_tailwind_classes()
        self.fields["imagen"].widget.attrs["accept"] = "image/jpeg,image/png,image/webp"

    def clean_imagen(self):
        image = self.cleaned_data.get("imagen")
        uploaded = self.files.get("imagen")
        if not image or not uploaded:
            return image
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La imagen no puede superar 5 MB.")
        try:
            image.seek(0)
            with Image.open(image) as source:
                source.load()
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Usa una imagen JPG, PNG o WebP.")
                source.thumbnail((1600, 1200))
                if source.mode not in {"RGB", "L"}:
                    background = Image.new("RGB", source.size, "white")
                    if "A" in source.getbands():
                        background.paste(source, mask=source.getchannel("A"))
                    else:
                        background.paste(source)
                    source = background
                elif source.mode == "L":
                    source = source.convert("RGB")
                output = BytesIO()
                source.save(output, format="JPEG", quality=82, optimize=True)
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("El archivo no es una imagen válida.")
        filename = f"{Path(uploaded.name).stem}.jpg"
        return ContentFile(output.getvalue(), name=filename)


class TourForm(CatalogFormMixin, forms.ModelForm):
    class Meta:
        model = Tour
        fields = (
            "lugar_turistico", "nombre_comercial", "duracion", "punto_encuentro",
            "incluye", "no_incluye", "itinerario", "recomendaciones", "que_llevar",
            "restricciones", "politica_cancelacion", "precio_base", "destacado",
            "en_promocion", "activo",
        )
        widgets = {
            name: forms.Textarea(attrs={"rows": 4})
            for name in (
                "incluye", "no_incluye", "itinerario", "recomendaciones",
                "que_llevar", "restricciones", "politica_cancelacion",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = LugarTuristico.objects.filter(
            activo=True, departamento__activo=True, departamento__pais__activo=True
        )
        if self.instance and self.instance.lugar_turistico_id:
            queryset = LugarTuristico.objects.filter(
                Q(
                    activo=True,
                    departamento__activo=True,
                    departamento__pais__activo=True,
                )
                | Q(pk=self.instance.lugar_turistico_id)
            )
        self.fields["lugar_turistico"].queryset = queryset
        self.apply_tailwind_classes()

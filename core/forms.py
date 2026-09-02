from django import forms
from django.utils import timezone
from django.utils.translation import get_language

from sami_admin.models import LugarTuristico, Tour

from .models import SolicitudContacto
from .phone import COUNTRY_CODES, normalize_international_phone


class SolicitudContactoForm(forms.ModelForm):
    """Validate public leads and expose a honeypot for simple bots."""

    TRIP_ROUNDTRIP = "roundtrip"
    TRIP_ONEWAY = "oneway"

    website = forms.CharField(required=False)
    codigo_pais = forms.CharField(
        label="Código de país",
        initial="+503",
        required=False,
        max_length=5,
    )
    tipo_trayecto = forms.ChoiceField(
        choices=(
            (TRIP_ROUNDTRIP, "Ida y vuelta"),
            (TRIP_ONEWAY, "Solo ida"),
        ),
        initial=TRIP_ROUNDTRIP,
        required=False,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = SolicitudContacto
        fields = (
            "nombre",
            "correo",
            "telefono",
            "servicio",
            "origen",
            "destino",
            "fecha_ida",
            "fecha_regreso",
            "hora_salida_preferida",
            "adultos",
            "ninos",
            "edades_ninos",
            "motivo_vuelo_privado",
            "equipaje_estimado",
            "preferencia_aeronave",
            "presupuesto",
            "lugar_turistico",
            "tour",
            "detalles",
        )
        widgets = {
            "fecha_ida": forms.DateInput(attrs={"type": "date"}),
            "fecha_regreso": forms.DateInput(attrs={"type": "date"}),
            "hora_salida_preferida": forms.TimeInput(attrs={"type": "time"}),
            "detalles": forms.Textarea(attrs={"rows": 4}),
        }

    @staticmethod
    def _message(spanish, english):
        return english if (get_language() or "es").startswith("en") else spanish

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (get_language() or "es").startswith("en"):
            self.fields["tipo_trayecto"].choices = (
                (self.TRIP_ROUNDTRIP, "Round trip"),
                (self.TRIP_ONEWAY, "One way"),
            )
            self.fields["motivo_vuelo_privado"].choices = (
                ("", "---------"),
                (SolicitudContacto.MotivoVueloPrivado.NEGOCIOS, "Business"),
                (SolicitudContacto.MotivoVueloPrivado.TURISMO, "Tourism"),
                (SolicitudContacto.MotivoVueloPrivado.GRUPO, "Group travel"),
                (SolicitudContacto.MotivoVueloPrivado.EMERGENCIA, "Urgent need"),
                (SolicitudContacto.MotivoVueloPrivado.OTRO, "Other"),
            )
        self.country_codes = COUNTRY_CODES
        minimum_date = timezone.localdate().isoformat()
        self.fields["fecha_ida"].widget.attrs["min"] = minimum_date
        self.fields["fecha_regreso"].widget.attrs["min"] = minimum_date
        if (
            self.instance.pk
            and self.instance.fecha_ida
            and not self.instance.fecha_regreso
            and not self.is_bound
        ):
            self.fields["tipo_trayecto"].initial = self.TRIP_ONEWAY
        self.fields["correo"].required = True
        self.fields["adultos"].required = False
        self.fields["adultos"].initial = 1
        self.fields["ninos"].required = False
        self.fields["ninos"].initial = 0
        self.fields["lugar_turistico"].queryset = LugarTuristico.objects.filter(
            activo=True,
            departamento__activo=True,
            departamento__pais__activo=True,
        ).select_related("departamento__pais")
        self.fields["tour"].queryset = Tour.objects.filter(
            activo=True,
            lugar_turistico__activo=True,
            lugar_turistico__departamento__activo=True,
            lugar_turistico__departamento__pais__activo=True,
        ).select_related("lugar_turistico")

    def clean(self):
        cleaned = super().clean()
        cleaned["adultos"] = cleaned.get("adultos") or 1
        cleaned["ninos"] = cleaned.get("ninos") or 0
        fecha_ida = cleaned.get("fecha_ida")
        fecha_regreso = cleaned.get("fecha_regreso")
        tipo_trayecto = cleaned.get("tipo_trayecto") or self.TRIP_ROUNDTRIP
        tipo_trayecto_enviado = bool(self.data.get("tipo_trayecto"))
        servicio = cleaned.get("servicio")
        includes_flight = servicio in (
            SolicitudContacto.Servicio.VUELO,
            SolicitudContacto.Servicio.VUELO_PRIVADO,
            SolicitudContacto.Servicio.VUELO_TOUR,
        )
        if includes_flight and tipo_trayecto == self.TRIP_ONEWAY:
            fecha_regreso = None
            cleaned["fecha_regreso"] = None
        today = timezone.localdate()
        if fecha_ida and fecha_ida < today:
            self.add_error(
                "fecha_ida",
                self._message(
                    "La fecha de ida no puede estar en el pasado.",
                    "The departure date cannot be in the past.",
                ),
            )
        if fecha_regreso and fecha_regreso < today:
            self.add_error(
                "fecha_regreso",
                self._message(
                    "La fecha de regreso no puede estar en el pasado.",
                    "The return date cannot be in the past.",
                ),
            )
        if fecha_ida and fecha_regreso and fecha_regreso < fecha_ida:
            self.add_error(
                "fecha_regreso",
                self._message(
                    "La fecha de regreso no puede ser anterior a la fecha de ida.",
                    "The return date cannot be before the departure date.",
                ),
            )
        if (
            includes_flight
            and tipo_trayecto_enviado
            and tipo_trayecto != self.TRIP_ONEWAY
            and fecha_ida
            and not fecha_regreso
        ):
            self.add_error(
                "fecha_regreso",
                self._message(
                    "Selecciona la fecha de vuelta o cambia el trayecto a Solo ida.",
                    "Select a return date or change the trip to One way.",
                ),
            )
        tour = cleaned.get("tour")
        lugar = cleaned.get("lugar_turistico")
        if tour and lugar and tour.lugar_turistico_id != lugar.pk:
            self.add_error(
                "tour",
                self._message(
                    "El tour no pertenece al destino seleccionado.",
                    "The tour does not belong to the selected destination.",
                ),
            )
        if tour and not lugar:
            cleaned["lugar_turistico"] = tour.lugar_turistico
        if cleaned.get("servicio") != SolicitudContacto.Servicio.VUELO_PRIVADO:
            cleaned["hora_salida_preferida"] = None
            cleaned["motivo_vuelo_privado"] = ""
            cleaned["equipaje_estimado"] = ""
            cleaned["preferencia_aeronave"] = ""
        phone = (cleaned.get("telefono") or "").strip()
        country_code = (cleaned.get("codigo_pais") or "").strip()
        if phone:
            try:
                cleaned["telefono"] = normalize_international_phone(
                    country_code, phone
                )
            except ValueError as exc:
                english = (get_language() or "es").startswith("en")
                if str(exc) == "invalid_country_code":
                    message = (
                        "Select a valid country code."
                        if english else "Selecciona un código de país válido."
                    )
                    self.add_error("codigo_pais", message)
                else:
                    message = (
                        "Enter a valid international phone number."
                        if english else "Ingresa un número telefónico internacional válido."
                    )
                    self.add_error("telefono", message)
        return cleaned

    def save(self, commit=True):
        solicitud = super().save(commit=False)
        solicitud.contacto = solicitud.correo or solicitud.telefono
        if solicitud.lugar_turistico_id and not solicitud.destino:
            solicitud.destino = solicitud.lugar_turistico.nombre_localizado
        if commit:
            solicitud.save()
        return solicitud

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError(
                self._message("Solicitud no válida.", "Invalid request.")
            )
        return value

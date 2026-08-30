from django import forms

from sami_admin.models import LugarTuristico, Tour

from .models import SolicitudContacto


class SolicitudContactoForm(forms.ModelForm):
    """Validate public leads and expose a honeypot for simple bots."""

    website = forms.CharField(required=False)

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
            "adultos",
            "ninos",
            "edades_ninos",
            "presupuesto",
            "lugar_turistico",
            "tour",
            "detalles",
        )
        widgets = {
            "fecha_ida": forms.DateInput(attrs={"type": "date"}),
            "fecha_regreso": forms.DateInput(attrs={"type": "date"}),
            "detalles": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if fecha_ida and fecha_regreso and fecha_regreso < fecha_ida:
            self.add_error(
                "fecha_regreso",
                "La fecha de regreso no puede ser anterior a la fecha de ida.",
            )
        tour = cleaned.get("tour")
        lugar = cleaned.get("lugar_turistico")
        if tour and lugar and tour.lugar_turistico_id != lugar.pk:
            self.add_error("tour", "El tour no pertenece al destino seleccionado.")
        if tour and not lugar:
            cleaned["lugar_turistico"] = tour.lugar_turistico
        return cleaned

    def save(self, commit=True):
        solicitud = super().save(commit=False)
        solicitud.contacto = solicitud.correo or solicitud.telefono
        if solicitud.lugar_turistico_id and not solicitud.destino:
            solicitud.destino = solicitud.lugar_turistico.nombre
        if commit:
            solicitud.save()
        return solicitud

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Solicitud no válida.")
        return value

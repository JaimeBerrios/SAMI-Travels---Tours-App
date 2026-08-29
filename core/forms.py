from django import forms

from .models import SolicitudContacto


class SolicitudContactoForm(forms.ModelForm):
    """Validate public leads and expose a honeypot for simple bots."""

    website = forms.CharField(required=False)

    class Meta:
        model = SolicitudContacto
        fields = ("nombre", "contacto", "servicio", "destino", "detalles")

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Solicitud no válida.")
        return value

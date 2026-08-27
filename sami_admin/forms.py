from django import forms
from django.contrib.auth.forms import AuthenticationForm


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
                    "px-4 py-3 text-brand-navy shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-brand-red "
                    "focus:ring-4 focus:ring-brand-red/10"
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
                    "px-4 py-3 text-brand-navy shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-brand-red "
                    "focus:ring-4 focus:ring-brand-red/10"
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

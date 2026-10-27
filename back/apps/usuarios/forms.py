"""Formularios MVT del módulo de usuarios."""

from django import forms

from .services import crear_cuenta, validar_cuenta_libre, validar_password


class RegistroForm(forms.Form):
    """Alta de un votante por el sitio MVT (entregable A6)."""

    documento = forms.CharField(
        max_length=20,
        label='Documento',
        widget=forms.TextInput(attrs={'maxlength': 20}),
    )
    nombres = forms.CharField(max_length=100, label='Nombres')
    apellidos = forms.CharField(max_length=100, label='Apellidos')
    correo = forms.EmailField(label='Correo')
    password = forms.CharField(
        label='Contraseña',
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean(self):
        cleaned = super().clean()
        duplicados = validar_cuenta_libre(
            cleaned.get('documento'),
            cleaned.get('correo'),
        )
        for campo, mensaje in duplicados.items():
            self.add_error(campo, mensaje)

        password = cleaned.get('password') or ''
        if password != cleaned.get('password_confirm'):
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        else:
            for mensaje in validar_password(password):
                self.add_error('password', mensaje)

        return cleaned

    def crear(self):
        """Crea la cuenta con rol Votante y devuelve ``(user, perfil)``."""
        return crear_cuenta(
            documento=self.cleaned_data['documento'],
            nombres=self.cleaned_data['nombres'],
            apellidos=self.cleaned_data['apellidos'],
            correo=self.cleaned_data['correo'],
            password=self.cleaned_data['password'],
        )

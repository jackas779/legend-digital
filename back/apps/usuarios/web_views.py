"""Registro de cuentas y cambio de contraseña desde el sitio MVT (A6, A9)."""

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .forms import RegistroForm


def registro(request):
    """Alta de un votante: crea la cuenta y deja la sesión iniciada."""
    if request.user.is_authenticated:
        return redirect('inicio')

    form = RegistroForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            user, perfil = form.crear()
        except ValidationError as exc:
            for campo, mensajes in getattr(exc, 'message_dict', {}).items():
                for mensaje in mensajes:
                    form.add_error(campo, mensaje)
        else:
            login(request, user)
            messages.success(
                request,
                f'Cuenta creada para {perfil.nombres} {perfil.apellidos}. Ya puedes votar.',
            )
            return redirect('inicio')

    return render(request, 'usuarios/registro.html', {'form': form})


def cambiar_password(request):
    """Cambio de contraseña del usuario en sesión (entregable A9)."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        # La sesión no se pierde al cambiar la clave (A9).
        update_session_auth_hash(request, form.user)
        messages.success(request, 'Contraseña actualizada.')
        return redirect('inicio')

    return render(request, 'usuarios/cambiar_password.html', {'form': form})

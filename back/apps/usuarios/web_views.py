"""Registro de cuentas desde el sitio MVT (entregable A6)."""

from django.contrib import messages
from django.contrib.auth import login
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

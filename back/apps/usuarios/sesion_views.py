"""Login y logout por sesión (entregables A1, A7 y A8)."""

from django.contrib import messages
from django.contrib.auth import login as login_sesion
from django.contrib.auth import views as vistas_auth
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import SesionForm

DIAS_RECORDARME = 7


def _destino_seguro(request):
    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return None


def _destino_por_rol(user):
    """V6: cada rol aterriza donde le corresponde."""
    if user.is_superuser:
        return reverse('admin:index')

    perfil = getattr(user, 'perfil_usuario', None)
    rol = getattr(perfil, 'rol', None)
    nombre_rol = getattr(rol, 'nombre', '')

    return {
        'Administrador': reverse('admin:index'),
        'Organizador': reverse('gestion:ediciones'),
        'Auditor': reverse('resultados_indice'),
    }.get(nombre_rol, reverse('inicio'))


def acceder(request):
    """Inicia sesión con correo, usuario o documento.

    Aplica el backend propio (bloqueo de intentos y estado de la cuenta) y
    permite "recordarme" para extender la sesión a 7 días.
    """
    if request.user.is_authenticated:
        return redirect('inicio')

    form = SesionForm(request=request, data=request.POST or None)
    destino = _destino_seguro(request)

    if request.method == 'POST' and form.is_valid():
        login_sesion(request, form.obtener_usuario())
        if form.cleaned_data.get('recordarme'):
            request.session.set_expiry(DIAS_RECORDARME * 24 * 60 * 60)
        messages.success(
            request,
            f'Bienvenido, {request.user.get_full_name() or request.user.username}.',
        )
        if destino:
            return HttpResponseRedirect(destino)
        return HttpResponseRedirect(_destino_por_rol(request.user))

    return render(
        request,
        'registration/login.html',
        {'form': form, 'next': destino or ''},
    )


cerrar_sesion = vistas_auth.LogoutView.as_view()


def _ruta_local(dato, request):
    """Devuelve el next solo si es una ruta del mismo host."""
    if dato and url_has_allowed_host_and_scheme(
        dato, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return dato
    return None

"""Autenticación centralizada.

La usan tanto la API (JWT) como el login por sesión del sitio (MVT), para que
las reglas de bloqueo, estado de la cuenta e identificadores sean idénticas.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.utils import timezone

from .models import Usuario

User = get_user_model()

MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


def buscar_usuario(identificador):
    """Busca por correo, nombre de usuario o documento, en ese orden."""
    identificador = (identificador or '').strip()
    if not identificador:
        return None

    user = User.objects.filter(email__iexact=identificador).first()
    if user is not None:
        return user

    user = User.objects.filter(username__iexact=identificador).first()
    if user is not None:
        return user

    perfil = Usuario.objects.select_related('user').filter(documento=identificador).first()
    return perfil.user if perfil else None


def autenticar(identificador, password):
    """Devuelve ``(user, error)``. ``error`` es ``None`` si la autenticación pasa."""
    if not (identificador or '').strip() or not password:
        return None, 'Correo/usuario y contraseña son obligatorios.'

    user = buscar_usuario(identificador)
    if user is None:
        return None, 'Credenciales inválidas.'

    perfil = getattr(user, 'perfil_usuario', None)

    error = _verificar_bloqueo(perfil)
    if error:
        return None, error

    error = _verificar_estado(perfil)
    if error:
        return None, error

    if not user.check_password(password):
        _registrar_fallo(perfil)
        return None, 'Credenciales inválidas.'

    if not user.is_active:
        return None, 'Usuario inactivo.'

    _limpiar_intentos(perfil)
    return user, None


def _verificar_bloqueo(perfil):
    if perfil is None or perfil.bloqueado_hasta is None:
        return None
    ahora = timezone.now()
    if perfil.bloqueado_hasta <= ahora:
        return None
    minutos = max(1, int((perfil.bloqueado_hasta - ahora).total_seconds() // 60) + 1)
    return f'Cuenta bloqueada por intentos fallidos. Intenta de nuevo en {minutos} minuto(s).'


def _verificar_estado(perfil):
    if perfil is None:
        return None
    if perfil.estado == 'SUSPENDIDO':
        return 'Usuario suspendido. Contacta al administrador.'
    if perfil.estado == 'INACTIVO':
        return 'Usuario inactivo.'
    return None


def _registrar_fallo(perfil):
    if perfil is None:
        return
    perfil.intentos_fallidos += 1
    campos = ['intentos_fallidos']
    if perfil.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
        perfil.bloqueado_hasta = timezone.now() + timedelta(minutes=MINUTOS_BLOQUEO)
        perfil.intentos_fallidos = 0
        campos.append('bloqueado_hasta')
    perfil.save(update_fields=campos)


def _limpiar_intentos(perfil):
    if perfil is None:
        return
    if perfil.intentos_fallidos or perfil.bloqueado_hasta:
        perfil.intentos_fallidos = 0
        perfil.bloqueado_hasta = None
        perfil.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])


class UsuariosBackend(BaseBackend):
    """Backend de Django que acepta correo, usuario o documento."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identificador = username or kwargs.get('identificador') or kwargs.get('correo')
        user, _error = autenticar(identificador, password)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

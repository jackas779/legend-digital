"""Servicio de cuenta: un solo camino para crear usuarios (web y API).

Garantiza que las reglas de duplicados y la política de contraseñas se
apliquen por igual en el registro de la API y en el del sitio MVT.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Role, Usuario

User = get_user_model()

ROL_VOTANTE = 'Votante'


def generar_username(correo, documento):
    base = (correo.split('@')[0] or documento or 'usuario')[:30]
    username = base
    contador = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{contador}'
        contador += 1
    return username


def validar_cuenta_libre(documento, correo, user_id=None):
    """Devuelve ``{campo: mensaje}`` si el correo o documento ya están en uso."""
    errores = {}
    if correo and User.objects.filter(email__iexact=correo).exclude(id=user_id).exists():
        errores['correo'] = 'Este correo ya está registrado.'
    if documento and Usuario.objects.filter(documento=documento).exclude(user_id=user_id).exists():
        errores['documento'] = 'Este documento ya está registrado.'
    return errores


def validar_password(password, user=None):
    """Valida la política de contraseñas y devuelve la lista de mensajes."""
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return list(exc.messages)
    return []


def crear_cuenta(*, documento, nombres, apellidos, correo, password, rol=None):
    """Crea ``User`` + ``Usuario`` (Votante por defecto).

    Lanza ``ValidationError`` con ``{campo: [mensajes]}`` si hay duplicados o
    la contraseña no cumple la política.
    """
    errores = validar_cuenta_libre(documento, correo)
    errores_password = validar_password(password, user=User(username=correo.split('@')[0]))
    if errores_password:
        errores['password'] = errores_password

    if errores:
        raise ValidationError(errores)

    user = User.objects.create_user(
        username=generar_username(correo, documento),
        email=correo,
        password=password,
        first_name=nombres,
        last_name=apellidos,
    )

    if rol is None:
        rol, _ = Role.objects.get_or_create(
            nombre=ROL_VOTANTE,
            defaults={'descripcion': 'Usuario común: elige una opción y vota'},
        )

    perfil = Usuario.objects.create(
        user=user,
        documento=documento,
        nombres=nombres,
        apellidos=apellidos,
        correo=correo,
        rol=rol,
    )
    return user, perfil

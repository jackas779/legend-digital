"""Roles y permisos del MVP (entregables P1, P3, P4 y P5).

La autorización usa los modelos Role/Permission/RolPermiso del proyecto, no
los grupos de Django. Un código sigue el formato ``modulo.accion``: las
acciones ``ver/crear/editar/eliminar`` aplican a la gestión CRUD; códigos
como ``resultados.ver`` o ``padron.ver`` solo conceden lectura.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from rest_framework.permissions import BasePermission

MODULOS_CRUD = ('ediciones', 'categorias', 'votaciones', 'opciones', 'usuarios')


def catalogo():
    """Catálogo del P1: {modulo: [(codigo, descripcion), ...]}."""
    catalogo = {}
    for modulo in MODULOS_CRUD:
        catalogo[modulo] = [
            (f'{modulo}.ver', f'Consultar {modulo}'),
            (f'{modulo}.crear', f'Crear {modulo}'),
            (f'{modulo}.editar', f'Editar {modulo}'),
            (f'{modulo}.eliminar', f'Eliminar {modulo}'),
        ]
    return catalogo


# Códigos fuera del CRUD: lectura y el flujo de discrepancias.
#  - discrepancias.reportar: registrar hallazgos y verificar su resolución
#    (confirmar o reabrir). Es del auditor.
#  - discrepancias.resolver: resolver o descartar. Es del organizador; si su
#    rol no lo tiene, la discrepancia pasa al administrador.
#  - resultados.ver: resultados en vivo (antes del cierre). El votante no lo
#    tiene: verlos podría influir en quien todavía no vota.
#  - inscripciones.gestionar: inscribir votantes a una edición por lista.
CODIGOS_ESPECIALES = {
    'resultados.ver': 'Consultar resultados en vivo',
    'inscripciones.gestionar': 'Inscribir votantes a una edición',
    'padron.ver': 'Consultar padrón',
    'auditoria.ver': 'Consultar auditoría',
    'discrepancias.ver': 'Consultar discrepancias',
    'discrepancias.reportar': 'Reportar y verificar discrepancias',
    'discrepancias.resolver': 'Resolver discrepancias',
}


def codigos_del_catalogo():
    """Todos los códigos del catálogo, más la aplanación por rol."""
    return [
        codigo
        for modulo in catalogo().values()
        for codigo, _ in modulo
    ] + list(CODIGOS_ESPECIALES)


# Asignación por rol (tabla del plan, bloque 3).
PERMISOS_POR_ROL = {
    'Administrador': [
        f'{modulo}.{accion}'
        for modulo in MODULOS_CRUD
        for accion in ('ver', 'crear', 'editar', 'eliminar')
    ] + [
        'auditoria.ver',
        'discrepancias.ver',
        'discrepancias.resolver',
        'resultados.ver',
        'inscripciones.gestionar',
    ],
    'Organizador': [
        f'{modulo}.{accion}'
        for modulo in MODULOS_CRUD[:-1]
        for accion in ('ver', 'crear', 'editar', 'eliminar')
    ] + [
        'resultados.ver',
        'padron.ver',
        'discrepancias.ver',
        'discrepancias.resolver',
        'inscripciones.gestionar',
    ],
    'Votante': [],
    'Auditor': [
        'resultados.ver',
        'padron.ver',
        'auditoria.ver',
        'discrepancias.ver',
        'discrepancias.reportar',
    ],
}


def sincronizar_catalogo(crear_roles=False):
    """Crea los códigos que falten y asigna a cada rol los de PERMISOS_POR_ROL.

    Solo agrega, nunca quita: respeta lo que un administrador haya ajustado
    a mano (por ejemplo, quitarle ``discrepancias.resolver`` al organizador).
    Con ``crear_roles=False`` (el caso de ``migrate``) solo toca roles que ya
    existen. Devuelve (códigos creados, asignaciones creadas).
    """
    from django.db import transaction

    from back.apps.usuarios.models import Permission, Role

    creados = asignados = 0
    with transaction.atomic():
        descripciones = {
            codigo: descripcion
            for definiciones in catalogo().values()
            for codigo, descripcion in definiciones
        }
        descripciones.update(CODIGOS_ESPECIALES)
        for codigo, descripcion in descripciones.items():
            _, nuevo = Permission.objects.get_or_create(
                codigo=codigo,
                defaults={'modulo': codigo.split('.')[0], 'descripcion': descripcion},
            )
            creados += nuevo

        for nombre_rol, codigos in PERMISOS_POR_ROL.items():
            if crear_roles:
                rol, _ = Role.objects.get_or_create(nombre=nombre_rol)
            else:
                rol = Role.objects.filter(nombre=nombre_rol).first()
                if rol is None:
                    continue
            for codigo in codigos:
                _, nuevo = RolPermiso.objects.get_or_create(
                    rol=rol, permiso=Permission.objects.get(codigo=codigo)
                )
                asignados += nuevo
    return creados, asignados


def permisos_del_usuario(user):
    """Lista de códigos asignados al rol del usuario ([] si no hay perfil)."""
    perfil = getattr(user, 'perfil_usuario', None)
    if perfil is None or perfil.rol is None:
        return []
    return list(
        RolPermiso.objects.filter(rol=perfil.rol).values_list(
            'permiso__codigo', flat=True
        )
    )


def tiene_permiso(user, codigo) -> bool:
    """P3: el superusuario siempre puede; se resuelve por su rol."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return codigo in permisos_del_usuario(user)


ROL_ADMINISTRADOR = 'Administrador'
ROL_VOTANTE = 'Votante'


def es_administrador(user) -> bool:
    """Superusuario o perfil con rol Administrador."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None) == ROL_ADMINISTRADOR


def puede_asignar_rol(user, rol) -> bool:
    """Quién puede dar un rol a una cuenta.

    - Votante (o sin rol): cualquiera; es el alta pública.
    - Cualquier otro rol (Administrador, Organizador, Auditor...): solo un
      administrador, para evitar la escalada de privilegios.
    """
    nombre = getattr(rol, 'nombre', None)
    if nombre in (None, ROL_VOTANTE):
        return True
    return es_administrador(user)


def sin_permiso(request, codigo):
    """Página 403 legible: qué permiso falta, quién lo asigna y cómo volver."""
    from django.template.loader import render_to_string
    from django.utils.http import url_has_allowed_host_and_scheme

    anterior = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(anterior, allowed_hosts={request.get_host()}):
        anterior = ''
    descripcion = CODIGOS_ESPECIALES.get(codigo) or dict(
        par for definiciones in catalogo().values() for par in definiciones
    ).get(codigo, codigo)
    return HttpResponseForbidden(render_to_string(
        '403.html',
        {'codigo': codigo, 'descripcion': descripcion, 'anterior': anterior},
        request=request,
    ))


def requiere_permiso(codigo):
    """P4: decorador para vistas MVT.

    Anónimo: redirección al login con ``next``. Autenticado sin permiso: 403
    con una página que dice qué permiso falta y cómo volver.
    """

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not tiene_permiso(request.user, codigo):
                return sin_permiso(request, codigo)
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


class TienePermiso(BasePermission):
    """P5: permiso DRF genérico.

    La vista declara el código requerido en ``permiso_requerido``. La lectura
    (GET/HEAD/OPTIONS) solo exige sesión; la escritura exige el permiso, tal
    como pide el entregable.
    """

    def has_permission(self, request, view) -> bool:
        codigo = getattr(view, 'permiso_requerido', None)
        if codigo is None:
            return bool(request.user and request.user.is_authenticated)
        if request.method in ('GET', 'HEAD', 'OPTIONS') and not codigo.endswith('.ver'):
            return bool(request.user and request.user.is_authenticated)
        return tiene_permiso(request.user, codigo)


# Import al final para evitar la importación circular con los modelos.
from back.apps.usuarios.models import RolPermiso  # noqa: E402


class AdminPermisosMixin:
    """P6: el panel usa los permisos del proyecto, no los grupos de Django.

    Cada ModelAdmin declara sus códigos; un código ``None`` desactiva la
    acción en el panel para ese módulo (además del superusuario, que siempre
    puede).
    """

    codigo_ver: str | None = None
    codigo_crear: str | None = None
    codigo_editar: str | None = None
    codigo_eliminar: str | None = None

    def _puede(self, request, codigo):
        if codigo is None:
            return False
        user = request.user
        if user.is_superuser:
            return True
        return tiene_permiso(user, codigo)

    def has_module_permission(self, request):
        return self._puede(request, self.codigo_ver)

    def has_view_permission(self, request, obj=None):
        return self._puede(request, self.codigo_ver)

    def has_add_permission(self, request, obj=None):
        return self._puede(request, self.codigo_crear)

    def has_change_permission(self, request, obj=None):
        return self._puede(request, self.codigo_editar)

    def has_delete_permission(self, request, obj=None):
        return self._puede(request, self.codigo_eliminar)


class AdminSoloLecturaMixin(AdminPermisosMixin):
    """Para la urna y el padrón: consultar con su código, nunca escribir."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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


def codigos_del_catalogo():
    """Todos los códigos del catálogo, más la aplanación por rol."""
    return [
        codigo
        for modulo in catalogo().values()
        for codigo, _ in modulo
    ] + ['resultados.ver', 'padron.ver', 'auditoria.ver']


# Asignación por rol (tabla del plan, bloque 3).
PERMISOS_POR_ROL = {
    'Administrador': [
        f'{modulo}.{accion}'
        for modulo in MODULOS_CRUD
        for accion in ('ver', 'crear', 'editar', 'eliminar')
    ] + ['auditoria.ver'],
    'Organizador': [
        f'{modulo}.{accion}'
        for modulo in MODULOS_CRUD[:-1]
        for accion in ('ver', 'crear', 'editar', 'eliminar')
    ] + ['resultados.ver', 'padron.ver'],
    'Votante': ['resultados.ver'],
    'Auditor': ['resultados.ver', 'padron.ver', 'auditoria.ver'],
}


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


def requiere_permiso(codigo):
    """P4: decorador para vistas MVT.

    Anónimo: redirección al login con ``next``. Autenticado sin permiso: 403.
    """

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not tiene_permiso(request.user, codigo):
                return HttpResponseForbidden('No tienes permiso para esta sección.')
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

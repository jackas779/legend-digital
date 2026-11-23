from django.contrib import admin
from django.core.exceptions import PermissionDenied

from back.apps.usuarios.permisos import (
    ROL_ADMINISTRADOR,
    ROL_VOTANTE,
    AdminPermisosMixin,
    es_administrador,
    puede_asignar_rol,
)

from .models import Permission, Role, RolPermiso, SessionToken, Usuario


def _es_cuenta_admin(perfil):
    return getattr(getattr(perfil, 'rol', None), 'nombre', None) == ROL_ADMINISTRADOR


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'usuarios.ver'
    codigo_crear = 'usuarios.crear'
    codigo_editar = 'usuarios.editar'
    codigo_eliminar = 'usuarios.eliminar'
    list_display = ('documento', 'nombres', 'apellidos', 'correo', 'rol', 'estado')
    list_filter = ('rol', 'estado')
    search_fields = ('documento', 'nombres', 'apellidos', 'correo')

    # Solo un administrador cambia el rol de una cuenta o toca la de otro admin.
    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if obj is not None and not es_administrador(request.user):
            campos.append('rol')
        return campos

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'rol' and not es_administrador(request.user):
            kwargs['queryset'] = Role.objects.filter(nombre=ROL_VOTANTE)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj is not None and _es_cuenta_admin(obj) and not es_administrador(request.user):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and _es_cuenta_admin(obj) and not es_administrador(request.user):
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not puede_asignar_rol(request.user, obj.rol):
            raise PermissionDenied('Solo un administrador puede asignar ese rol.')
        super().save_model(request, obj, form, change)


@admin.register(Role)
class RoleAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'usuarios.ver'
    codigo_crear = 'usuarios.crear'
    codigo_editar = 'usuarios.editar'
    codigo_eliminar = 'usuarios.eliminar'
    list_display = ('nombre', 'descripcion')
    inlines = [RolPermisoInline]

    # Cambiar los permisos de un rol es otra vía para volverse administrador:
    # solo el administrador crea, edita o borra roles.
    def has_add_permission(self, request, obj=None):
        return es_administrador(request.user) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return es_administrador(request.user) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user) and super().has_delete_permission(request, obj)


@admin.register(Permission)
class PermissionAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'usuarios.ver'
    codigo_editar = 'usuarios.editar'
    list_display = ('codigo', 'modulo', 'descripcion')
    list_filter = ('modulo',)
    search_fields = ('codigo',)


@admin.register(SessionToken)
class SessionTokenAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'usuarios.ver'
    list_display = ('usuario', 'ip_origen', 'fecha_emision', 'fecha_expiracion', 'revocado')
    list_filter = ('revocado',)

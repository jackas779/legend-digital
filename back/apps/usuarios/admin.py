from django.contrib import admin

from back.apps.usuarios.permisos import AdminPermisosMixin

from .models import Permission, Role, RolPermiso, SessionToken, Usuario


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


@admin.register(Role)
class RoleAdmin(AdminPermisosMixin, admin.ModelAdmin):
    codigo_ver = 'usuarios.ver'
    codigo_crear = 'usuarios.crear'
    codigo_editar = 'usuarios.editar'
    codigo_eliminar = 'usuarios.eliminar'
    list_display = ('nombre', 'descripcion')
    inlines = [RolPermisoInline]


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

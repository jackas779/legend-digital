from django.contrib import admin

from .models import Permission, Role, RolPermiso, SessionToken, Usuario


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('documento', 'nombres', 'apellidos', 'correo', 'rol', 'estado')
    list_filter = ('rol', 'estado')
    search_fields = ('documento', 'nombres', 'apellidos', 'correo')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    inlines = [RolPermisoInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'modulo', 'descripcion')
    list_filter = ('modulo',)
    search_fields = ('codigo',)


@admin.register(SessionToken)
class SessionTokenAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ip_origen', 'fecha_emision', 'fecha_expiracion', 'revocado')
    list_filter = ('revocado',)

from django.contrib import admin

from .models import LogAuditoriaEvento


@admin.register(LogAuditoriaEvento)
class LogAuditoriaEventoAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'modulo', 'accion', 'usuario', 'ip_origen')
    list_filter = ('modulo', 'accion')
    search_fields = ('accion', 'modulo')
    readonly_fields = (
        'usuario',
        'modulo',
        'accion',
        'detalles_json',
        'ip_origen',
        'hash_trazabilidad',
        'timestamp',
    )

    def has_add_permission(self, request):
        return False

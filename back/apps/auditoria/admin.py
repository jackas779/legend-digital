from django.contrib import admin

from back.apps.usuarios.permisos import AdminSoloLecturaMixin

from .models import ConfirmacionAuditoria, Discrepancia, LogAuditoriaEvento


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


# Discrepancias y confirmaciones: solo consulta. Su flujo (reportar,
# resolver, confirmar, reabrir) pasa por /auditoria/ para que quede en el
# registro y respete quién puede hacer qué.
@admin.register(Discrepancia)
class DiscrepanciaAdmin(AdminSoloLecturaMixin, admin.ModelAdmin):
    codigo_ver = 'discrepancias.ver'
    list_display = ('fecha_reporte', 'tipo', 'edicion', 'votacion', 'estado', 'reportada_por')
    list_filter = ('estado', 'tipo', 'edicion')


@admin.register(ConfirmacionAuditoria)
class ConfirmacionAuditoriaAdmin(AdminSoloLecturaMixin, admin.ModelAdmin):
    codigo_ver = 'discrepancias.ver'
    list_display = ('fecha', 'edicion', 'votacion', 'estado_edicion', 'auditor')
    list_filter = ('edicion',)

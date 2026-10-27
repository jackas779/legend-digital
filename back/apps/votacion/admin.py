from django.contrib import admin

from .models import (
    ActaEscrutinio,
    CertificadoVotacion,
    PadronVotante,
    Voto,
)


@admin.register(PadronVotante)
class PadronVotanteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'votacion', 'ha_votado', 'fecha_emision')
    list_filter = ('ha_votado', 'votacion')
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    """La urna es de solo lectura: un voto no se edita ni se borra desde el panel."""

    list_display = ('id', 'opcion', 'votacion', 'fecha_registro')
    list_filter = ('opcion__votacion',)
    readonly_fields = ('id', 'opcion', 'votacion', 'fecha_registro', 'firma_criptografica')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CertificadoVotacion)
class CertificadoVotacionAdmin(admin.ModelAdmin):
    list_display = ('codigo_certificado', 'padron', 'fecha_generacion')
    search_fields = ('codigo_certificado',)


@admin.register(ActaEscrutinio)
class ActaEscrutinioAdmin(admin.ModelAdmin):
    list_display = ('votacion', 'fecha_cierre', 'total_votos_urna')
    list_filter = ('votacion',)

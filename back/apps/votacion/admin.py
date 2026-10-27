from django.contrib import admin

from back.apps.usuarios.permisos import AdminSoloLecturaMixin

from .models import (
    ActaEscrutinio,
    CertificadoVotacion,
    PadronVotante,
    Voto,
)


@admin.register(PadronVotante)
class PadronVotanteAdmin(AdminSoloLecturaMixin, admin.ModelAdmin):
    codigo_ver = 'padron.ver'
    list_display = ('usuario', 'votacion', 'ha_votado', 'fecha_emision')
    list_filter = ('ha_votado', 'votacion')
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Voto)
class VotoAdmin(AdminSoloLecturaMixin, admin.ModelAdmin):
    """La urna es de solo lectura: un voto no se edita ni se borra desde el panel."""

    codigo_ver = 'resultados.ver'
    list_display = ('id', 'opcion', 'votacion', 'fecha_registro')
    list_filter = ('opcion__votacion',)
    readonly_fields = ('id', 'opcion', 'votacion', 'fecha_registro', 'firma_criptografica')


@admin.register(CertificadoVotacion)
class CertificadoVotacionAdmin(admin.ModelAdmin):
    list_display = ('codigo_certificado', 'padron', 'fecha_generacion')
    search_fields = ('codigo_certificado',)


@admin.register(ActaEscrutinio)
class ActaEscrutinioAdmin(admin.ModelAdmin):
    list_display = ('votacion', 'fecha_cierre', 'total_votos_urna')
    list_filter = ('votacion',)

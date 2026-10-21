from django.conf import settings
from django.db import models


class LogAuditoriaEvento(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_auditoria')
    modulo = models.CharField(max_length=50)
    accion = models.CharField(max_length=100)
    detalles_json = models.JSONField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45)
    hash_trazabilidad = models.CharField(max_length=256)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'logs_auditoria_eventos'

    def __str__(self):
        return f'{self.modulo} - {self.accion}'

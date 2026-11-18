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


class Discrepancia(models.Model):
    """Hallazgo del auditor sobre una edición (o una votación de ella).

    El auditor observa y verifica, no decide: registra la discrepancia y
    puede confirmar o reabrir su resolución, pero no resolverla. La
    resuelve el organizador si tiene el permiso ``discrepancias.resolver``;
    si no lo tiene, pasa al administrador. Una discrepancia abierta no
    bloquea el cierre de la edición: la edición queda "finalizada con
    discrepancias pendientes" hasta que se resuelvan.
    """

    ABIERTA = 'ABIERTA'
    RESUELTA = 'RESUELTA'
    DESCARTADA = 'DESCARTADA'

    ESTADOS = [
        (ABIERTA, 'Abierta'),
        (RESUELTA, 'Resuelta'),
        (DESCARTADA, 'Descartada'),
    ]

    TIPOS = [
        ('PADRON_URNA', 'Votos en la urna no coinciden con los participantes del padrón'),
        ('FIRMA_INVALIDA', 'Firma de voto no verificable'),
        ('VOTO_FUERA_DE_HORARIO', 'Voto registrado fuera del horario permitido'),
        ('ABIERTA_CON_EDICION_CERRADA', 'Votación abierta con la edición cerrada'),
        ('ACTA_DESCUADRADA', 'El acta no coincide con la urna'),
        ('NO_INSCRITO', 'Votó alguien que no estaba inscrito a tiempo'),
        ('OTRA', 'Otra'),
    ]

    edicion = models.ForeignKey(
        'elecciones.Edicion',
        on_delete=models.PROTECT,
        related_name='discrepancias',
    )
    votacion = models.ForeignKey(
        'elecciones.Votacion',
        on_delete=models.PROTECT,
        related_name='discrepancias',
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=40, choices=TIPOS)
    descripcion = models.TextField()
    evidencia = models.JSONField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ABIERTA)

    reportada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='discrepancias_reportadas',
    )
    fecha_reporte = models.DateTimeField(auto_now_add=True)

    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='discrepancias_resueltas',
        null=True,
        blank=True,
    )
    resolucion = models.TextField(blank=True, default='')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    # Verificación del auditor sobre la resolución.
    confirmada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='discrepancias_confirmadas',
        null=True,
        blank=True,
    )
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    veces_reabierta = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'discrepancias'
        ordering = ['-fecha_reporte']
        verbose_name = 'discrepancia'
        verbose_name_plural = 'discrepancias'

    def __str__(self):
        return f'{self.get_tipo_display()} · {self.edicion}'

    @property
    def esta_abierta(self):
        return self.estado == self.ABIERTA

    @property
    def confirmada(self):
        return self.confirmada_por_id is not None


class ConfirmacionAuditoria(models.Model):
    """Constancia del auditor de que una edición o votación está en orden."""

    edicion = models.ForeignKey(
        'elecciones.Edicion',
        on_delete=models.PROTECT,
        related_name='confirmaciones',
    )
    votacion = models.ForeignKey(
        'elecciones.Votacion',
        on_delete=models.PROTECT,
        related_name='confirmaciones',
        null=True,
        blank=True,
    )
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='confirmaciones_auditoria',
    )
    estado_edicion = models.CharField(
        max_length=20,
        help_text='Estado de la edición en el momento de confirmar.',
    )
    observacion = models.TextField(blank=True, default='')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'confirmaciones_auditoria'
        ordering = ['-fecha']
        verbose_name = 'confirmación de auditoría'
        verbose_name_plural = 'confirmaciones de auditoría'

    def __str__(self):
        return f'Confirmación {self.edicion} · {self.fecha:%Y-%m-%d}'

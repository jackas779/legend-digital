import uuid

from django.db import models

from back.apps.elecciones.models import OpcionVotacion, Votacion
from back.apps.usuarios.models import Usuario


class PadronVotante(models.Model):
    """Habilitación y marca de participación de un usuario en una votación."""

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='padrones')
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='padron')
    ha_votado = models.BooleanField(default=False)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    hash_comprobante = models.CharField(max_length=256, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'padron_votantes'
        verbose_name = 'padrón de votante'
        verbose_name_plural = 'padrón de votantes'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'votacion'],
                name='uq_usuario_votacion',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} → {self.votacion}'


class CertificadoVotacion(models.Model):
    padron = models.OneToOneField(
        PadronVotante,
        on_delete=models.CASCADE,
        related_name='certificado',
    )
    codigo_certificado = models.CharField(max_length=100, unique=True)
    qr_verificacion_url = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificados_votacion'
        verbose_name = 'certificado de votación'
        verbose_name_plural = 'certificados de votación'

    def __str__(self):
        return self.codigo_certificado


class VotoUrna(models.Model):
    """Voto anónimo: no tiene ninguna referencia a la identidad del votante."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='votos_urna')
    opcion_votacion = models.ForeignKey(
        OpcionVotacion,
        on_delete=models.CASCADE,
        related_name='votos_urna',
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    firma_criptografica = models.CharField(max_length=256)

    class Meta:
        db_table = 'votos_urna'
        ordering = ['-fecha_registro']
        verbose_name = 'voto en urna'
        verbose_name_plural = 'votos en urna'

    def __str__(self):
        return f'Voto {self.id} en {self.votacion}'


class ActaEscrutinio(models.Model):
    votacion = models.OneToOneField(
        Votacion,
        on_delete=models.CASCADE,
        related_name='acta',
    )
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    total_padron_habilitado = models.PositiveIntegerField()
    total_participantes = models.PositiveIntegerField()
    total_votos_urna = models.PositiveIntegerField()
    archivo_pdf_url = models.URLField()
    hash_sello_bd = models.CharField(max_length=256)

    class Meta:
        db_table = 'actas_escrutinio'
        verbose_name = 'acta de escrutinio'
        verbose_name_plural = 'actas de escrutinio'

    def __str__(self):
        return f'Acta {self.votacion}'

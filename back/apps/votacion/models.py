import hashlib
import uuid

from django.conf import settings
from django.db import models

from back.apps.elecciones.models import Opcion, Votacion


class PadronVotante(models.Model):
    """Habilitación y marca de participación de un usuario en una votación.

    Para el MVP se apoya en el usuario de Django (``auth.User``) en lugar del
    perfil ``usuarios.Usuario``: así un superusuario creado con
    ``createsuperuser`` puede votar sin configurar roles adicionales.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='padrones',
    )
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


class Voto(models.Model):
    """Voto anónimo: no tiene ninguna referencia a la identidad del votante.

    La votación se deriva de la opción, de modo que no es posible registrar un
    voto en una votación usando una opción de otra.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opcion = models.ForeignKey(Opcion, on_delete=models.CASCADE, related_name='votos')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    firma_criptografica = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        db_table = 'votos'
        ordering = ['-fecha_registro']
        verbose_name = 'voto'
        verbose_name_plural = 'votos'

    def __str__(self):
        return f'Voto {self.id} → {self.opcion}'

    @property
    def votacion(self):
        return self.opcion.votacion

    def calcular_firma(self):
        contenido = f'{self.id}:{self.opcion_id}:{self.fecha_registro.isoformat()}'
        return hashlib.sha256(contenido.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.firma_criptografica:
            self.firma_criptografica = self.calcular_firma()
            super().save(update_fields=['firma_criptografica'])


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

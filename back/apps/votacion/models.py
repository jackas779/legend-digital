import hashlib
import uuid

from django.conf import settings
from django.db import models

from back.apps.elecciones.models import Opcion, Votacion


class PadronVotante(models.Model):
    """Habilitación y marca de participación de un usuario en una votación.

    Solo el rol ``Votante`` emite voto (el auditor, el organizador y el
    administrador son autoridades del proceso y no votan). Los registros
    de padrón corresponden por tanto a votantes con su perfil asignado.

    Unicidad (CP-02): un votante emite **un solo voto por categoría dentro
    de cada edición**, así su categoría tenga varias votaciones (subeventos).
    Para que la BD lo garantice sin consultas adicionales, el padrón guarda
    copias desnormalizadas de ``edicion`` y ``categoria`` tomadas de la
    votación; la constraint ``uq_usuario_categoria_edicion`` cierra el paso
    a un segundo voto en la misma categoría aunque dos requests entren en
    paralelo por votaciones distintas.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='padrones',
    )
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='padron')
    edicion = models.ForeignKey(
        'elecciones.Edicion',
        on_delete=models.CASCADE,
        related_name='padrones',
        null=True,
        blank=True,
        help_text='Copia desnormalizada de la edición de la votación.',
    )
    categoria = models.ForeignKey(
        'elecciones.Categoria',
        on_delete=models.CASCADE,
        related_name='padrones',
        null=True,
        blank=True,
        help_text='Copia desnormalizada de la categoría de la votación.',
    )
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
            models.UniqueConstraint(
                fields=['usuario', 'edicion', 'categoria'],
                name='uq_usuario_categoria_edicion',
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

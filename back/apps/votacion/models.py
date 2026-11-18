import hashlib
import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from back.apps.elecciones.models import Opcion, Votacion


def truncar_a_hora(momento):
    """Redondea hacia abajo a la hora: 10:47:12 → 10:00:00."""
    return momento.replace(minute=0, second=0, microsecond=0)


def hora_actual_redondeada():
    return truncar_a_hora(timezone.now())


def nuevo_comprobante():
    """Código del comprobante: aleatorio y sin relación con el voto."""
    return secrets.token_hex(32)


class PadronVotante(models.Model):
    """Habilitación y marca de participación de un usuario en una votación.

    Solo el rol ``Votante`` emite voto (el auditor, el organizador y el
    administrador son autoridades del proceso y no votan). Los registros
    de padrón corresponden por tanto a votantes con su perfil asignado.

    Unicidad (CP-02): un votante emite **un solo voto por categoría y ronda
    dentro de cada edición**. Las votaciones paralelas de una categoría
    (subeventos) comparten ese voto; una ronda nueva (segunda vuelta o
    final) es un voto nuevo. Para que la BD lo garantice, el padrón guarda
    copias desnormalizadas de ``edicion``, ``categoria`` y ``ronda`` de la
    votación, y la constraint ``uq_usuario_categoria_ronda`` cierra el paso
    aunque dos requests entren en paralelo por votaciones distintas.

    Secreto del voto: ``hash_comprobante`` es un código aleatorio propio del
    votante; no es la firma del voto, así que no permite llegar a la opción.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='padrones',
    )
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='padron')
    # Obligatorias: con NULL la constraint uq_usuario_categoria_edicion no
    # aplica (en SQL dos NULL no son iguales) y la regla quedaría sin efecto.
    edicion = models.ForeignKey(
        'elecciones.Edicion',
        on_delete=models.CASCADE,
        related_name='padrones',
        help_text='Copia desnormalizada de la edición de la votación.',
    )
    categoria = models.ForeignKey(
        'elecciones.Categoria',
        on_delete=models.CASCADE,
        related_name='padrones',
        help_text='Copia desnormalizada de la categoría de la votación.',
    )
    ronda = models.PositiveSmallIntegerField(
        default=1,
        help_text='Copia desnormalizada del número de ronda de la votación.',
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
                fields=['usuario', 'edicion', 'categoria', 'ronda'],
                name='uq_usuario_categoria_ronda',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} → {self.votacion}'

    def save(self, *args, **kwargs):
        # La copia desnormalizada siempre se toma de la votación: nadie puede
        # dejarla vacía ni apuntarla a otra edición, categoría o ronda.
        if self.votacion_id:
            votacion = self.votacion
            self.edicion_id = votacion.edicion_id
            self.categoria_id = votacion.categoria_id
            self.ronda = votacion.numero_ronda
            campos = kwargs.get('update_fields')
            if campos is not None:
                kwargs['update_fields'] = set(campos) | {'edicion', 'categoria', 'ronda'}
        super().save(*args, **kwargs)


class InscripcionEdicion(models.Model):
    """Inscripción de un votante a una edición.

    Las votaciones en modo "solo inscritos" admiten a quien se inscribió
    **antes** de que esa votación abriera. Inscribe el propio votante o el
    organizador por él.
    """

    VOTANTE = 'VOTANTE'
    ORGANIZADOR = 'ORGANIZADOR'
    ORIGENES = [(VOTANTE, 'El votante'), (ORGANIZADOR, 'El organizador')]

    edicion = models.ForeignKey(
        'elecciones.Edicion', on_delete=models.CASCADE, related_name='inscripciones'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inscripciones'
    )
    origen = models.CharField(max_length=20, choices=ORIGENES, default=VOTANTE)
    inscrito_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inscripciones_edicion'
        ordering = ['fecha_inscripcion']
        verbose_name = 'inscripción'
        verbose_name_plural = 'inscripciones'
        constraints = [
            models.UniqueConstraint(fields=['edicion', 'usuario'], name='uq_inscripcion_edicion'),
        ]

    def __str__(self):
        return f'{self.usuario} → {self.edicion}'


class Voto(models.Model):
    """Voto anónimo: no tiene ninguna referencia a la identidad del votante.

    La votación se deriva de la opción, de modo que no es posible registrar un
    voto en una votación usando una opción de otra.

    Secreto del voto: ``fecha_registro`` se guarda redondeada a la hora, para
    que no se pueda cruzar con el momento exacto en que votó cada persona.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opcion = models.ForeignKey(Opcion, on_delete=models.CASCADE, related_name='votos')
    fecha_registro = models.DateTimeField(default=hora_actual_redondeada, editable=False)
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
        self.fecha_registro = truncar_a_hora(self.fecha_registro or timezone.now())
        if not self.firma_criptografica:
            self.firma_criptografica = self.calcular_firma()
        super().save(*args, **kwargs)


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
    """Acta de una votación CERRADA: su generación la deja ESCRUTADA.

    ``hash_sello_bd`` sella el contenido de la urna al momento del
    escrutinio (firmas de los votos + totales); el auditor puede rehacerlo
    para detectar votos agregados o alterados después del acta.
    """

    votacion = models.OneToOneField(
        Votacion,
        on_delete=models.CASCADE,
        related_name='acta',
    )
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    total_padron_habilitado = models.PositiveIntegerField()
    total_participantes = models.PositiveIntegerField()
    total_votos_urna = models.PositiveIntegerField()
    archivo_pdf_url = models.URLField(blank=True, default='')
    hash_sello_bd = models.CharField(max_length=256)

    class Meta:
        db_table = 'actas_escrutinio'
        verbose_name = 'acta de escrutinio'
        verbose_name_plural = 'actas de escrutinio'

    def __str__(self):
        return f'Acta {self.votacion}'

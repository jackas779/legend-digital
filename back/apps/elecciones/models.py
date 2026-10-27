from django.db import models
from django.utils import timezone


class Edicion(models.Model):
    """Agrupa un proceso electoral completo (por ejemplo, Festival 2027)."""

    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PROGRAMADA', 'Programada'),
        ('ACTIVA', 'Activa'),
        ('CERRANDO', 'Cerrando'),
        ('FINALIZADA', 'Finalizada'),
    ]

    nombre = models.CharField(max_length=150)
    anio = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    creador = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='ediciones_gestionadas',
        null=True,
        blank=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ediciones'
        ordering = ['-anio', 'nombre']
        verbose_name = 'edición'
        verbose_name_plural = 'ediciones'
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'anio'],
                name='uq_edicion_nombre_anio',
            ),
        ]

    def __str__(self):
        # Evita "Festival 2027 2027" cuando el nombre ya incluye el año.
        if str(self.anio) in self.nombre:
            return self.nombre
        return f'{self.nombre} {self.anio}'.strip()

    @property
    def esta_activa(self):
        return self.estado == 'ACTIVA'


class Categoria(models.Model):
    """Temática reutilizable entre ediciones (Música, Deportes, etc.)."""

    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'categorias'
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Votacion(models.Model):
    """Votación concreta de una categoría dentro de una edición.

    Ejemplo: Festival 2027 → Música → "Canción favorita del público".
    """

    ESTADOS = Edicion.ESTADOS

    edicion = models.ForeignKey(Edicion, on_delete=models.CASCADE, related_name='votaciones')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='votaciones')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    mostrar_resultados_en_vivo = models.BooleanField(default=False)

    class Meta:
        db_table = 'votaciones'
        ordering = ['-fecha_apertura']
        verbose_name = 'votación'
        verbose_name_plural = 'votaciones'
        constraints = [
            models.UniqueConstraint(
                fields=['edicion', 'categoria', 'nombre'],
                name='uq_votacion_titulo',
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def titulo(self):
        return f'{self.nombre} · {self.edicion}'

    @property
    def esta_abierta(self):
        ahora = timezone.now()
        return (
            self.estado == 'ACTIVA'
            and self.fecha_apertura <= ahora <= self.fecha_cierre
        )

    @property
    def total_votos(self):
        return self.opciones.aggregate(total=models.Count('votos'))['total'] or 0


class Opcion(models.Model):
    """Alternativa que se puede votar dentro de una votación.

    Ejemplo: Canción A, Canción B, Canción C.
    """

    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='opciones')
    nombre = models.CharField(max_length=150)
    subtitulo = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Artista, lista o partido que acompaña a la opción.',
    )
    descripcion = models.TextField(blank=True, null=True)
    orden = models.PositiveIntegerField(help_text='Número de casilla en el tarjetón.')
    es_voto_blanco = models.BooleanField(default=False)
    foto_recurso = models.ForeignKey(
        'RecursoMultimedia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opciones',
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opciones'
        ordering = ['orden', 'nombre']
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'
        constraints = [
            models.UniqueConstraint(
                fields=['votacion', 'orden'],
                name='uq_votacion_casilla',
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def total_votos(self):
        return self.votos.count()


class Normativa(models.Model):
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='normativas')
    titulo = models.CharField(max_length=150)
    contenido_html = models.TextField(blank=True, null=True)
    archivo_pdf_url = models.URLField(blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'normativas'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return self.titulo


class RecursoMultimedia(models.Model):
    nombre_archivo = models.CharField(max_length=150)
    url_publica = models.URLField()
    tipo_mime = models.CharField(max_length=50)
    peso_bytes = models.PositiveIntegerField()
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recursos_multimedia'
        ordering = ['-fecha_subida']

    def __str__(self):
        return self.nombre_archivo

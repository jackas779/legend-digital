from django.db import models


class Edicion(models.Model):
    """Agrupa un proceso electoral completo (por ejemplo, Elecciones 2026)."""

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

    def __str__(self):
        return f'{self.nombre} {self.anio}'.strip()


class Categoria(models.Model):
    """Temática reutilizable de una votación (Alcaldía, Consejo, etc.)."""

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
    """Votación concreta de una categoría dentro de una edición."""

    ESTADOS = Edicion.ESTADOS

    edicion = models.ForeignKey(Edicion, on_delete=models.CASCADE, related_name='votaciones')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='votaciones')
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    mostrar_resultados_en_vivo = models.BooleanField(default=False)

    class Meta:
        db_table = 'votaciones'
        ordering = ['-fecha_apertura']
        verbose_name = 'votación'
        verbose_name_plural = 'votaciones'

    def __str__(self):
        return f'{self.categoria} · {self.edicion}'


class Opcion(models.Model):
    """Persona, lista o alternativa que puede participar en votaciones."""

    nombre = models.CharField(max_length=150)
    identificador_unico = models.CharField(max_length=100, unique=True)
    biografia = models.TextField(blank=True, null=True)
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
        ordering = ['nombre']
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'

    def __str__(self):
        return self.nombre


class OpcionVotacion(models.Model):
    """Casilla del tarjetón: una opción participando en una votación."""

    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='opciones')
    opcion = models.ForeignKey(Opcion, on_delete=models.CASCADE, related_name='participaciones')
    numero_casilla = models.PositiveIntegerField()
    es_voto_blanco = models.BooleanField(default=False)
    # Dato de presentación propio de la candidatura (la misma persona puede
    # presentarse con una lista distinta en otra votación).
    partido_lista = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = 'opciones_votacion'
        ordering = ['numero_casilla']
        verbose_name = 'opción de votación'
        verbose_name_plural = 'opciones de votación'
        constraints = [
            models.UniqueConstraint(
                fields=['votacion', 'numero_casilla'],
                name='uq_votacion_casilla',
            ),
            models.UniqueConstraint(
                fields=['votacion', 'opcion'],
                name='uq_votacion_opcion',
            ),
        ]

    def __str__(self):
        return f'{self.opcion} ({self.votacion})'


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

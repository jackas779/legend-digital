from django.db import models
from django.utils import timezone


class Edicion(models.Model):
    """Contenedor de un proceso electoral completo (por ejemplo, Festival 2027).

    La edición manda sobre todo lo que contiene: tiene un periodo
    (``fecha_inicio`` → ``fecha_fin``) y un ciclo de vida. Ninguna votación
    se abre ni recibe votos por fuera del estado y las fechas de su edición,
    y cuando la edición termina, todo lo de adentro termina con ella.

    Ciclo de vida (las transiciones viven en ``elecciones.ciclo``):

    - BORRADOR: se arma la estructura (categorías, votaciones, opciones).
    - PROGRAMADA: validada y a la espera de su fecha de inicio.
    - ACTIVA: automática al llegar ``fecha_inicio``; se vota.
    - CERRANDO: automática al llegar ``fecha_fin`` o por cierre anticipado;
      no entra ningún voto y se hace el escrutinio.
    - FINALIZADA: automática cuando todas sus votaciones están escrutadas o
      canceladas. Es definitiva: todo queda en solo lectura.
    """

    BORRADOR = 'BORRADOR'
    PROGRAMADA = 'PROGRAMADA'
    ACTIVA = 'ACTIVA'
    CERRANDO = 'CERRANDO'
    FINALIZADA = 'FINALIZADA'

    ESTADOS = [
        (BORRADOR, 'Borrador'),
        (PROGRAMADA, 'Programada'),
        (ACTIVA, 'Activa'),
        (CERRANDO, 'En escrutinio'),
        (FINALIZADA, 'Finalizada'),
    ]

    nombre = models.CharField(max_length=150)
    anio = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=BORRADOR)
    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Al llegar esta fecha una edición PROGRAMADA se activa sola.',
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Al llegar esta fecha la edición se cierra sola.',
    )
    cierre_anticipado = models.BooleanField(default=False)
    motivo_cierre = models.TextField(blank=True, default='')
    fecha_cierre_real = models.DateTimeField(null=True, blank=True)
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
        return self.estado == self.ACTIVA

    @property
    def admite_cambios_de_estructura(self):
        """Categorías, votaciones y opciones solo se agregan o quitan en BORRADOR."""
        return self.estado == self.BORRADOR

    @property
    def es_solo_lectura(self):
        return self.estado == self.FINALIZADA

    @property
    def no_lista(self):
        """Llegó su fecha de inicio y sigue en BORRADOR: no se abrirá sola."""
        return (
            self.estado == self.BORRADOR
            and self.fecha_inicio is not None
            and self.fecha_inicio <= timezone.now()
        )

    @property
    def en_periodo(self):
        """La fecha actual está dentro del periodo de la edición."""
        ahora = timezone.now()
        if self.fecha_inicio and ahora < self.fecha_inicio:
            return False
        if self.fecha_fin and ahora >= self.fecha_fin:
            return False
        return True

    @property
    def recibe_votos(self):
        """El cierre manda siempre: estado ACTIVA y dentro del periodo."""
        return self.estado == self.ACTIVA and self.en_periodo

    @property
    def num_discrepancias_pendientes(self):
        return self.discrepancias.filter(estado='ABIERTA').count()

    @property
    def finalizada_con_pendientes(self):
        """Se finalizó con discrepancias sin resolver (no bloquean el cierre)."""
        return self.estado == self.FINALIZADA and self.num_discrepancias_pendientes > 0


class Categoria(models.Model):
    """Temática del catálogo global, reutilizable entre ediciones.

    Una misma categoría (Música) puede estar en muchas ediciones; dentro de
    una edición aparece una sola vez aunque tenga varias votaciones. Si ya
    se usó en una edición finalizada no se borra ni se renombra: se archiva.
    """

    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    archivada = models.BooleanField(
        default=False,
        help_text='Archivada: no se ofrece a ediciones nuevas, pero se conserva su historial.',
    )

    class Meta:
        db_table = 'categorias'
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre

    @property
    def usada_en_edicion_finalizada(self):
        return self.votaciones.filter(edicion__estado=Edicion.FINALIZADA).exists()


class Votacion(models.Model):
    """Votación concreta de una categoría dentro de una edición.

    Ejemplo: Festival 2027 → Música → "Canción favorita del público".

    Tiene su propio ciclo de vida, siempre subordinado al de su edición:

    - BORRADOR: se está configurando.
    - LISTA: validada al programar la edición; espera su fecha de apertura.
    - ABIERTA: recibe votos (solo si la edición está ACTIVA).
    - CERRADA: ya no recibe votos y espera su acta.
    - ESCRUTADA: tiene su acta de escrutinio.
    - CANCELADA: la edición se cerró y la votación nunca llegó a abrirse.
    """

    BORRADOR = 'BORRADOR'
    LISTA = 'LISTA'
    ABIERTA = 'ABIERTA'
    CERRADA = 'CERRADA'
    ESCRUTADA = 'ESCRUTADA'
    CANCELADA = 'CANCELADA'

    ESTADOS = [
        (BORRADOR, 'Borrador'),
        (LISTA, 'Lista'),
        (ABIERTA, 'Abierta'),
        (CERRADA, 'Cerrada'),
        (ESCRUTADA, 'Escrutada'),
        (CANCELADA, 'Cancelada'),
    ]
    # Estados de los que no se vuelve: no se reabren ni se editan.
    ESTADOS_FINALES = (CERRADA, ESCRUTADA, CANCELADA)

    edicion = models.ForeignKey(Edicion, on_delete=models.CASCADE, related_name='votaciones')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='votaciones')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=BORRADOR)
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
        """Recibe votos ahora mismo.

        No basta el estado guardado: también se comprueban las fechas de la
        votación y el estado y periodo de la edición, por si el cambio
        automático todavía no se ha aplicado.
        """
        ahora = timezone.now()
        return (
            self.estado == self.ABIERTA
            and self.fecha_apertura <= ahora <= self.fecha_cierre
            and self.edicion.recibe_votos
        )

    @property
    def es_final(self):
        return self.estado in self.ESTADOS_FINALES

    @property
    def tiene_resultado_final(self):
        return self.estado in (self.CERRADA, self.ESCRUTADA)

    @property
    def num_opciones_validas(self):
        """Opciones que cuentan para validar: el voto en blanco no cuenta."""
        return self.opciones.filter(es_voto_blanco=False).count()

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

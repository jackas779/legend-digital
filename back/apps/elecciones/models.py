from django.conf import settings
from django.db import models


class CategoriaElectoral(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PROGRAMADA', 'Programada'),
        ('ACTIVA', 'Activa'),
        ('CERRANDO', 'Cerrando'),
        ('FINALIZADA', 'Finalizada'),
    ]

    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    mostrar_resultados_en_vivo = models.BooleanField(default=False)
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='categorias_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categorias_electorales'

    def __str__(self):
        return self.titulo


class Normativa(models.Model):
    categoria = models.ForeignKey(CategoriaElectoral, on_delete=models.CASCADE, related_name='normativas')
    titulo = models.CharField(max_length=150)
    contenido_html = models.TextField(blank=True, null=True)
    archivo_pdf_url = models.URLField(blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'normativas'

    def __str__(self):
        return self.titulo


class RecursoMultimedia(models.Model):
    nombre_archivo = models.CharField(max_length=150)
    url_publica = models.URLField()
    tipo_mime = models.CharField(max_length=50)
    peso_bytes = models.IntegerField()
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recursos_multimedia'

    def __str__(self):
        return self.nombre_archivo


class CandidatoOpcion(models.Model):
    categoria = models.ForeignKey(CategoriaElectoral, on_delete=models.CASCADE, related_name='candidatos')
    nombre_candidato = models.CharField(max_length=120)
    partido_lista = models.CharField(max_length=120, blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    orden_casilla = models.IntegerField()
    es_voto_blanco = models.BooleanField(default=False)
    foto_recurso = models.ForeignKey(RecursoMultimedia, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidatos')

    class Meta:
        db_table = 'candidatos_opciones'
        constraints = [
            models.UniqueConstraint(fields=['categoria', 'orden_casilla'], name='uq_categoria_casilla')
        ]

    def __str__(self):
        return self.nombre_candidato

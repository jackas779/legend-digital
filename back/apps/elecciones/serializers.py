from rest_framework import serializers

from .models import CategoriaElectoral, CandidatoOpcion, Normativa, RecursoMultimedia


class RecursoMultimediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoMultimedia
        fields = ['id', 'nombre_archivo', 'url_publica', 'tipo_mime', 'peso_bytes', 'fecha_subida']
        read_only_fields = ['id', 'fecha_subida']


class CategoriaElectoralSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaElectoral
        fields = [
            'id',
            'titulo',
            'descripcion',
            'fecha_apertura',
            'fecha_cierre',
            'estado',
            'mostrar_resultados_en_vivo',
            'creador',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'creador']


class NormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Normativa
        fields = ['id', 'categoria', 'titulo', 'contenido_html', 'archivo_pdf_url', 'fecha_publicacion']
        read_only_fields = ['id', 'categoria', 'fecha_publicacion']


class CandidatoOpcionSerializer(serializers.ModelSerializer):
    foto_recurso = RecursoMultimediaSerializer(read_only=True)

    class Meta:
        model = CandidatoOpcion
        fields = [
            'id',
            'categoria',
            'nombre_candidato',
            'partido_lista',
            'biografia',
            'orden_casilla',
            'es_voto_blanco',
            'foto_recurso',
        ]
        read_only_fields = ['id', 'categoria']

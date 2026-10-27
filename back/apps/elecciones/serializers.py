from rest_framework import serializers

from .models import (
    Categoria,
    Edicion,
    Normativa,
    Opcion,
    RecursoMultimedia,
    Votacion,
)


class RecursoMultimediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoMultimedia
        fields = ['id', 'nombre_archivo', 'url_publica', 'tipo_mime', 'peso_bytes', 'fecha_subida']
        read_only_fields = ['id', 'fecha_subida']


class EdicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicion
        fields = ['id', 'nombre', 'anio', 'estado', 'creador', 'fecha_creacion']
        read_only_fields = ['id', 'creador', 'fecha_creacion']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']
        read_only_fields = ['id']


class VotacionSerializer(serializers.ModelSerializer):
    edicion_nombre = serializers.CharField(source='edicion.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    titulo = serializers.ReadOnlyField()
    total_votos = serializers.ReadOnlyField()

    class Meta:
        model = Votacion
        fields = [
            'id',
            'edicion',
            'edicion_nombre',
            'categoria',
            'categoria_nombre',
            'nombre',
            'titulo',
            'descripcion',
            'fecha_apertura',
            'fecha_cierre',
            'estado',
            'mostrar_resultados_en_vivo',
            'total_votos',
        ]
        read_only_fields = ['id']


class OpcionSerializer(serializers.ModelSerializer):
    foto_recurso_detalle = RecursoMultimediaSerializer(source='foto_recurso', read_only=True)
    total_votos = serializers.ReadOnlyField()

    class Meta:
        model = Opcion
        fields = [
            'id',
            'votacion',
            'nombre',
            'subtitulo',
            'descripcion',
            'orden',
            'es_voto_blanco',
            'foto_recurso',
            'foto_recurso_detalle',
            'total_votos',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
        # La validación de casilla única se hace en validate() para devolver el
        # error sobre el campo 'orden' en lugar de non_field_errors.
        validators = []

    def validate(self, attrs):
        votacion = attrs.get('votacion', getattr(self.instance, 'votacion', None))
        orden = attrs.get('orden', getattr(self.instance, 'orden', None))

        if votacion is not None and orden is not None:
            existentes = Opcion.objects.filter(votacion=votacion, orden=orden)
            if self.instance is not None:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise serializers.ValidationError({
                    'orden': 'Ya existe una casilla con ese número en esta votación.'
                })

        return attrs


class NormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Normativa
        fields = ['id', 'votacion', 'titulo', 'contenido_html', 'archivo_pdf_url', 'fecha_publicacion']
        read_only_fields = ['id', 'votacion', 'fecha_publicacion']

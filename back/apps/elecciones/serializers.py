from rest_framework import serializers

from .models import (
    Categoria,
    Edicion,
    Normativa,
    Opcion,
    OpcionVotacion,
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
    titulo = serializers.SerializerMethodField()

    class Meta:
        model = Votacion
        fields = [
            'id',
            'edicion',
            'edicion_nombre',
            'categoria',
            'categoria_nombre',
            'titulo',
            'fecha_apertura',
            'fecha_cierre',
            'estado',
            'mostrar_resultados_en_vivo',
        ]
        read_only_fields = ['id']

    def get_titulo(self, obj):
        return f'{obj.categoria.nombre} · {obj.edicion.nombre}'


class OpcionSerializer(serializers.ModelSerializer):
    foto_recurso_detalle = RecursoMultimediaSerializer(source='foto_recurso', read_only=True)

    class Meta:
        model = Opcion
        fields = [
            'id',
            'nombre',
            'identificador_unico',
            'biografia',
            'foto_recurso',
            'foto_recurso_detalle',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']


class OpcionVotacionSerializer(serializers.ModelSerializer):
    opcion_detalle = OpcionSerializer(source='opcion', read_only=True)

    class Meta:
        model = OpcionVotacion
        fields = [
            'id',
            'votacion',
            'opcion',
            'opcion_detalle',
            'numero_casilla',
            'es_voto_blanco',
            'partido_lista',
        ]
        read_only_fields = ['id', 'votacion']

    def validate(self, attrs):
        votacion_id = self.context.get('votacion_id')
        if votacion_id is None:
            view = self.context.get('view')
            if view is not None:
                votacion_id = view.kwargs.get('votacion_id')

        if votacion_id is None:
            return attrs

        existentes = OpcionVotacion.objects.filter(votacion_id=votacion_id)
        if self.instance is not None:
            existentes = existentes.exclude(pk=self.instance.pk)

        numero_casilla = attrs.get('numero_casilla', getattr(self.instance, 'numero_casilla', None))
        opcion = attrs.get('opcion', getattr(self.instance, 'opcion', None))

        if numero_casilla is not None and existentes.filter(numero_casilla=numero_casilla).exists():
            raise serializers.ValidationError({
                'numero_casilla': 'Ya existe una casilla con ese número en esta votación.'
            })

        if opcion is not None and existentes.filter(opcion=opcion).exists():
            raise serializers.ValidationError({
                'opcion': 'Esta opción ya participa en la votación.'
            })

        return attrs


class NormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Normativa
        fields = ['id', 'votacion', 'titulo', 'contenido_html', 'archivo_pdf_url', 'fecha_publicacion']
        read_only_fields = ['id', 'votacion', 'fecha_publicacion']

from rest_framework import serializers

from .ciclo import errores_de_fechas_votacion
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
    """El estado es de solo lectura: cambia por ``elecciones.ciclo``.

    El periodo es obligatorio; después de programar, solo cambia el nombre.
    """

    fecha_inicio = serializers.DateTimeField()
    fecha_fin = serializers.DateTimeField()

    class Meta:
        model = Edicion
        fields = [
            'id',
            'nombre',
            'anio',
            'estado',
            'fecha_inicio',
            'fecha_fin',
            'cierre_anticipado',
            'motivo_cierre',
            'fecha_cierre_real',
            'creador',
            'fecha_creacion',
        ]
        read_only_fields = [
            'id',
            'estado',
            'cierre_anticipado',
            'motivo_cierre',
            'fecha_cierre_real',
            'creador',
            'fecha_creacion',
        ]

    def validate(self, attrs):
        instancia = self.instance
        if instancia is not None and instancia.estado != Edicion.BORRADOR:
            if instancia.estado != Edicion.PROGRAMADA:
                raise serializers.ValidationError(
                    f'La edición está {instancia.estado}: sus datos ya no se editan.'
                )
            fijos = [
                campo for campo in ('anio', 'fecha_inicio', 'fecha_fin')
                if campo in attrs and attrs[campo] != getattr(instancia, campo)
            ]
            if fijos:
                raise serializers.ValidationError(
                    {campo: 'Fijo desde que la edición se programó.' for campo in fijos}
                )

        inicio = attrs.get('fecha_inicio', getattr(instancia, 'fecha_inicio', None))
        fin = attrs.get('fecha_fin', getattr(instancia, 'fecha_fin', None))
        if inicio and fin and inicio >= fin:
            raise serializers.ValidationError({'fecha_fin': 'El fin debe ser posterior al inicio.'})
        return attrs


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'archivada']
        read_only_fields = ['id']

    def validate_nombre(self, nombre):
        instancia = self.instance
        if (
            instancia is not None
            and nombre != instancia.nombre
            and instancia.usada_en_edicion_finalizada
        ):
            raise serializers.ValidationError(
                'Se usó en una edición finalizada: el nombre no cambia para conservar el historial.'
            )
        return nombre


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
        read_only_fields = ['id', 'estado']

    def validate(self, attrs):
        instancia = self.instance
        edicion = attrs.get('edicion', getattr(instancia, 'edicion', None))

        if instancia is None:
            if edicion is not None and not edicion.admite_cambios_de_estructura:
                raise serializers.ValidationError(
                    {'edicion': 'Solo se crean votaciones en ediciones en BORRADOR.'}
                )
            categoria = attrs.get('categoria')
            if categoria is not None and categoria.archivada:
                raise serializers.ValidationError(
                    {'categoria': 'La categoría está archivada.'}
                )
        else:
            if instancia.es_final or instancia.edicion.es_solo_lectura:
                raise serializers.ValidationError(
                    f'La votación está {instancia.estado}: ya no se edita.'
                )
            if 'edicion' in attrs and attrs['edicion'] != instancia.edicion:
                raise serializers.ValidationError({'edicion': 'La edición de una votación no cambia.'})
            if not instancia.edicion.admite_cambios_de_estructura:
                fijos = [
                    campo for campo in ('categoria', 'fecha_apertura', 'fecha_cierre')
                    if campo in attrs and attrs[campo] != getattr(instancia, campo)
                ]
                if fijos:
                    raise serializers.ValidationError(
                        {campo: 'Fijo desde que la edición se programó.' for campo in fijos}
                    )

        errores = errores_de_fechas_votacion(
            edicion,
            attrs.get('fecha_apertura', getattr(instancia, 'fecha_apertura', None)),
            attrs.get('fecha_cierre', getattr(instancia, 'fecha_cierre', None)),
        )
        if errores:
            raise serializers.ValidationError({'fecha_cierre': errores})
        return attrs


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

        # Se agregan solo en BORRADOR; con la votación LISTA se corrigen
        # textos; abierta o terminada, nada.
        if votacion is not None:
            if self.instance is None and votacion.estado != Votacion.BORRADOR:
                raise serializers.ValidationError(
                    {'votacion': f'La votación está {votacion.estado}: no admite opciones nuevas.'}
                )
            if self.instance is not None:
                if votacion.estado not in (Votacion.BORRADOR, Votacion.LISTA):
                    raise serializers.ValidationError(
                        f'La votación está {votacion.estado}: sus opciones ya no se modifican.'
                    )
                if votacion.estado == Votacion.LISTA:
                    fijos = [
                        campo for campo in ('votacion', 'orden', 'es_voto_blanco')
                        if campo in attrs and attrs[campo] != getattr(self.instance, campo)
                    ]
                    if fijos:
                        raise serializers.ValidationError(
                            {campo: 'Fijo desde que la edición se programó.' for campo in fijos}
                        )

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

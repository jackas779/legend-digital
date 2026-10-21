from rest_framework import serializers

from .models import CategoriaElectoral


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

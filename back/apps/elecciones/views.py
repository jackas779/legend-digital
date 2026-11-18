from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from back.apps.usuarios.permisos import TienePermiso

from . import ciclo
from .models import Categoria, Edicion, Normativa, Opcion, RecursoMultimedia, Votacion
from .serializers import (
    CategoriaSerializer,
    EdicionSerializer,
    NormativaSerializer,
    OpcionSerializer,
    RecursoMultimediaSerializer,
    VotacionSerializer,
)


def health_view(request):
    return JsonResponse({'status': 'ok', 'module': 'elecciones'})


class EdicionListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'ediciones.crear'
    queryset = Edicion.objects.select_related('creador').all()
    serializer_class = EdicionSerializer

    def perform_create(self, serializer):
        # El perfil Usuario puede no existir (por ejemplo, un superusuario
        # creado con createsuperuser), por eso el creador es opcional.
        perfil = getattr(self.request.user, 'perfil_usuario', None)
        serializer.save(creador=perfil)


class EdicionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'ediciones.editar'
    queryset = Edicion.objects.select_related('creador').all()
    serializer_class = EdicionSerializer

    def perform_destroy(self, instance):
        # ED3: solo en BORRADOR o PROGRAMADA (nunca hubo votación).
        if instance.estado not in (Edicion.BORRADOR, Edicion.PROGRAMADA):
            raise ValidationError(
                f'La edición está {instance.estado}: su historial se conserva.'
            )
        instance.delete()


class TransicionEdicionView(APIView):
    """Acciones humanas del ciclo de vida de una edición.

    POST /ediciones/<id>/<accion>/ con accion en: programar, desprogramar,
    cerrar (cierre anticipado, exige ``motivo``) o escrutar. La activación,
    el cierre por fecha y la finalización son automáticos.
    """

    permission_classes = [TienePermiso]
    permiso_requerido = 'ediciones.editar'

    def post(self, request, pk, accion):
        edicion = get_object_or_404(Edicion, pk=pk)
        try:
            if accion == 'programar':
                ciclo.programar(edicion, request)
            elif accion == 'desprogramar':
                ciclo.desprogramar(edicion, request)
            elif accion == 'cerrar':
                ciclo.cerrar(
                    edicion, request, motivo=request.data.get('motivo', ''), anticipado=True
                )
            elif accion == 'escrutar':
                ciclo.escrutar_edicion(edicion, request)
            else:
                return Response({'detail': 'Acción desconocida.'}, status=status.HTTP_404_NOT_FOUND)
        except ciclo.TransicionInvalida as error:
            return Response(
                {'detail': str(error), 'errores': error.errores},
                status=status.HTTP_409_CONFLICT,
            )
        edicion.refresh_from_db()
        return Response(EdicionSerializer(edicion).data)


class TransicionVotacionView(APIView):
    """POST /votaciones/<id>/abrir/ (adelantar apertura) o /cerrar/."""

    permission_classes = [TienePermiso]
    permiso_requerido = 'votaciones.editar'

    def post(self, request, pk, accion):
        votacion = get_object_or_404(Votacion.objects.select_related('edicion'), pk=pk)
        try:
            if accion == 'abrir':
                ciclo.abrir_votacion(votacion, request)
            elif accion == 'cerrar':
                ciclo.cerrar_votacion(votacion, request)
            else:
                return Response({'detail': 'Acción desconocida.'}, status=status.HTTP_404_NOT_FOUND)
        except ciclo.TransicionInvalida as error:
            return Response({'detail': str(error)}, status=status.HTTP_409_CONFLICT)
        votacion.refresh_from_db()
        return Response(VotacionSerializer(votacion).data)


class CategoriaListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'categorias.crear'
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'categorias.editar'
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class VotacionListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'votaciones.crear'
    serializer_class = VotacionSerializer

    def get_queryset(self):
        queryset = Votacion.objects.select_related('edicion', 'categoria').all()
        edicion_id = self.request.query_params.get('edicion')
        categoria_id = self.request.query_params.get('categoria')

        if edicion_id:
            queryset = queryset.filter(edicion_id=edicion_id)
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        return queryset


class VotacionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'votaciones.editar'
    queryset = Votacion.objects.select_related('edicion', 'categoria').all()
    serializer_class = VotacionSerializer

    def perform_destroy(self, instance):
        # La estructura solo cambia con la edición en BORRADOR.
        if not instance.edicion.admite_cambios_de_estructura:
            raise ValidationError('Las votaciones solo se eliminan con la edición en BORRADOR.')
        if instance.total_votos:
            raise ValidationError('La votación ya registra votos.')
        instance.delete()


class NormativaListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'votaciones.editar'
    serializer_class = NormativaSerializer

    def get_queryset(self):
        return Normativa.objects.filter(votacion_id=self.kwargs['votacion_id']).order_by('-fecha_publicacion')

    def perform_create(self, serializer):
        serializer.save(votacion_id=self.kwargs['votacion_id'])


class OpcionListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'opciones.crear'
    serializer_class = OpcionSerializer

    def get_queryset(self):
        queryset = Opcion.objects.select_related('votacion', 'foto_recurso').all()
        votacion_id = self.request.query_params.get('votacion')
        if votacion_id:
            queryset = queryset.filter(votacion_id=votacion_id)
        return queryset


class OpcionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'opciones.editar'
    queryset = Opcion.objects.select_related('votacion', 'foto_recurso').all()
    serializer_class = OpcionSerializer

    def perform_destroy(self, instance):
        if instance.votacion.estado != Votacion.BORRADOR:
            raise ValidationError('Las opciones solo se eliminan con la votación en BORRADOR.')
        if instance.votos.exists():
            raise ValidationError('La opción ya registra votos.')
        instance.delete()


class RecursoMultimediaListCreateView(generics.ListCreateAPIView):
    permission_classes = [TienePermiso]
    permiso_requerido = 'votaciones.editar'
    queryset = RecursoMultimedia.objects.all()
    serializer_class = RecursoMultimediaSerializer


def _opcion_publica(opcion):
    """Diccionario compacto de una opción para el tarjetón del front."""
    return {
        'id': opcion.pk,
        'nombre': opcion.nombre,
        'subtitulo': opcion.subtitulo,
        'orden': opcion.orden,
        'es_voto_blanco': opcion.es_voto_blanco,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def categorias_publicas(request):
    """API GET obligatoria: categorías y opciones en un solo JSON.

    Con ``?edicion=<id>`` entrega las categorías de esa edición, cada una
    con sus votaciones y, dentro de cada votación, sus opciones (JSON).
    Sin parámetro recorre todas las votaciones existentes. Es pública
    (sin token) por diseño: muestra exactamente los mismos datos que el
    tarjetón MVT, que tampoco exige login.
    """
    edicion = None
    edicion_id = request.query_params.get('edicion')
    if edicion_id:
        edicion = get_object_or_404(Edicion, pk=edicion_id)

    categorias_qs = Categoria.objects.all().order_by('nombre')
    if edicion is not None:
        categorias_qs = categorias_qs.filter(votaciones__edicion=edicion)
    categorias_qs = categorias_qs.distinct().prefetch_related(
        models.Prefetch(
            'votaciones',
            # Con la edición marcada, la columna queda lista para la densidad.
            queryset=Votacion.objects.select_related('edicion').order_by('fecha_apertura'),
        )
    )

    data = []
    for categoria in categorias_qs:
        votaciones = []
        for votacion in categoria.votaciones.all():
            if edicion is not None and votacion.edicion_id != edicion.pk:
                continue
            votaciones.append({
                'id': votacion.pk,
                'nombre': votacion.nombre,
                'edicion': {'id': votacion.edicion_id, 'nombre': votacion.edicion.nombre},
                'descripcion': votacion.descripcion,
                'estado': votacion.estado,
                'abierta': votacion.esta_abierta,
                'fecha_apertura': votacion.fecha_apertura,
                'fecha_cierre': votacion.fecha_cierre,
                'mostrar_resultados_en_vivo': votacion.mostrar_resultados_en_vivo,
                'opciones': [_opcion_publica(op) for op in votacion.opciones.order_by('orden', 'nombre')],
            })
        if not edicion and not votaciones:
            # Sin edición de referencia solo listamos categorías con votaciones.
            continue
        data.append({
            'id': categoria.pk,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion,
            'votaciones': votaciones,
        })

    return Response({
        'edicion': (
            {'id': edicion.pk, 'nombre': edicion.nombre, 'anio': edicion.anio, 'estado': edicion.estado}
            if edicion is not None else None
        ),
        'categorias': data,
    })

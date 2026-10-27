from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = [IsAuthenticated]
    queryset = Edicion.objects.select_related('creador').all()
    serializer_class = EdicionSerializer

    def perform_create(self, serializer):
        # El perfil Usuario puede no existir (por ejemplo, un superusuario
        # creado con createsuperuser), por eso el creador es opcional.
        perfil = getattr(self.request.user, 'perfil_usuario', None)
        serializer.save(creador=perfil)


class EdicionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Edicion.objects.select_related('creador').all()
    serializer_class = EdicionSerializer


class CategoriaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class VotacionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    queryset = Votacion.objects.select_related('edicion', 'categoria').all()
    serializer_class = VotacionSerializer


class NormativaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NormativaSerializer

    def get_queryset(self):
        return Normativa.objects.filter(votacion_id=self.kwargs['votacion_id']).order_by('-fecha_publicacion')

    def perform_create(self, serializer):
        serializer.save(votacion_id=self.kwargs['votacion_id'])


class OpcionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OpcionSerializer

    def get_queryset(self):
        queryset = Opcion.objects.select_related('votacion', 'foto_recurso').all()
        votacion_id = self.request.query_params.get('votacion')
        if votacion_id:
            queryset = queryset.filter(votacion_id=votacion_id)
        return queryset


class OpcionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Opcion.objects.select_related('votacion', 'foto_recurso').all()
    serializer_class = OpcionSerializer


class RecursoMultimediaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = RecursoMultimedia.objects.all()
    serializer_class = RecursoMultimediaSerializer

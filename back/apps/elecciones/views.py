from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import CategoriaElectoral, CandidatoOpcion, Normativa
from .serializers import CategoriaElectoralSerializer, CandidatoOpcionSerializer, NormativaSerializer


def health_view(request):
    return JsonResponse({'status': 'ok', 'module': 'elecciones'})


class CategoriaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CategoriaElectoral.objects.all().order_by('-fecha_creacion')
    serializer_class = CategoriaElectoralSerializer

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CategoriaElectoral.objects.all()
    serializer_class = CategoriaElectoralSerializer


class NormativaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NormativaSerializer

    def get_queryset(self):
        return Normativa.objects.filter(categoria_id=self.kwargs['categoria_id']).order_by('-fecha_publicacion')

    def perform_create(self, serializer):
        serializer.save(categoria_id=self.kwargs['categoria_id'])


class CandidatoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CandidatoOpcionSerializer

    def get_queryset(self):
        return CandidatoOpcion.objects.filter(categoria_id=self.kwargs['categoria_id']).order_by('orden_casilla')

    def perform_create(self, serializer):
        serializer.save(categoria_id=self.kwargs['categoria_id'])

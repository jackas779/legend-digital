from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CategoriaElectoral
from .serializers import CategoriaElectoralSerializer


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

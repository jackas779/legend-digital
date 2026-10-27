from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny

from back.apps.elecciones.models import Opcion
from back.apps.elecciones.serializers import OpcionSerializer


def health_view(request):
    return JsonResponse({
        'status': 'ok',
        'module': 'votacion'
    })


class OpcionesVotacionView(generics.ListAPIView):
    """Tarjetón público: opciones de una votación, ordenadas por casilla."""

    serializer_class = OpcionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Opcion.objects.filter(
            votacion_id=self.kwargs['votacion_id']
        ).select_related('foto_recurso').order_by('orden')

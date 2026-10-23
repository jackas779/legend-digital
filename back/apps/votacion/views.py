
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny

from back.apps.elecciones.models import CandidatoOpcion
from back.apps.elecciones.serializers import CandidatoOpcionSerializer


def health_view(request):
    return JsonResponse({
        'status': 'ok',
        'module': 'votacion'
    })


class OpcionesVotacionView(generics.ListAPIView):
    serializer_class = CandidatoOpcionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        categoria_id = self.kwargs['categoria_id']

        return CandidatoOpcion.objects.filter(
            categoria_id=categoria_id
        ).order_by('orden_casilla')

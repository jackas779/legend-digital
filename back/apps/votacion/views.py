from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny

from back.apps.elecciones.models import OpcionVotacion
from back.apps.elecciones.serializers import OpcionVotacionSerializer


def health_view(request):
    return JsonResponse({
        'status': 'ok',
        'module': 'votacion'
    })


class OpcionesVotacionView(generics.ListAPIView):
    serializer_class = OpcionVotacionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        votacion_id = self.kwargs['votacion_id']

        return OpcionVotacion.objects.filter(
            votacion_id=votacion_id
        ).select_related('opcion', 'opcion__foto_recurso').order_by('numero_casilla')

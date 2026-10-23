
from django.urls import path

from .views import health_view, OpcionesVotacionView

urlpatterns = [
    path('health/', health_view, name='votacion-health'),
    path(
        'categorias/<int:categoria_id>/opciones/',
        OpcionesVotacionView.as_view(),
        name='votacion-opciones',
    ),
]

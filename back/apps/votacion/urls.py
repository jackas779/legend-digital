from django.urls import path

from .views import OpcionesVotacionView, health_view

urlpatterns = [
    path('health/', health_view, name='votacion-health'),
    path(
        'votaciones/<int:votacion_id>/opciones/',
        OpcionesVotacionView.as_view(),
        name='votacion-opciones',
    ),
]

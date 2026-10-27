from django.urls import path

from . import web_views

urlpatterns = [
    path('', web_views.inicio, name='inicio'),
    path('ediciones/<int:pk>/', web_views.edicion_detalle, name='edicion-detalle'),
    path('votaciones/<int:pk>/', web_views.tarjeton, name='tarjeton'),
    path('votaciones/<int:pk>/votar/', web_views.votar, name='votar'),
    path('votaciones/<int:pk>/resultados/', web_views.resultados, name='resultados'),
]

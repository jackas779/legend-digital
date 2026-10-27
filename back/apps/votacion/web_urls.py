from django.urls import path

from . import web_views

urlpatterns = [
    path('', web_views.inicio, name='inicio'),
    path('ediciones/<int:pk>/', web_views.edicion_detalle, name='edicion-detalle'),
    path('votaciones/<int:pk>/', web_views.tarjeton, name='tarjeton'),
    path('votaciones/<int:pk>/votar/', web_views.votar, name='votar'),
    path('votaciones/<int:pk>/resultados/', web_views.resultados, name='resultados'),
    path('comprobante/<str:hash_comprobante>/', web_views.comprobante, name='comprobante'),
    path('mis-votos/', web_views.mis_votos, name='mis_votos'),
    path('resultados/', web_views.resultados_indice, name='resultados_indice'),
    path(
        'resultados/edicion/<int:edicion_id>/',
        web_views.resultados_consolidado,
        name='resultados_consolidado',
    ),
]

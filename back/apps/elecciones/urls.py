from django.urls import path, re_path

from .views import (
    CategoriaDetailView,
    CategoriaListCreateView,
    EdicionDetailView,
    EdicionListCreateView,
    NormativaListCreateView,
    OpcionDetailView,
    OpcionListCreateView,
    RecursoMultimediaListCreateView,
    TransicionEdicionView,
    TransicionVotacionView,
    VotacionDetailView,
    VotacionListCreateView,
    health_view,
)

urlpatterns = [
    path('health/', health_view, name='elecciones-health'),

    path('ediciones/', EdicionListCreateView.as_view(), name='ediciones-list'),
    path('ediciones/<int:pk>/', EdicionDetailView.as_view(), name='ediciones-detail'),
    re_path(
        r'^ediciones/(?P<pk>\d+)/(?P<accion>programar|desprogramar|cerrar|escrutar)/$',
        TransicionEdicionView.as_view(),
        name='ediciones-transicion',
    ),

    path('categorias/', CategoriaListCreateView.as_view(), name='categorias-list'),
    path('categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categorias-detail'),

    path('votaciones/', VotacionListCreateView.as_view(), name='votaciones-list'),
    path('votaciones/<int:pk>/', VotacionDetailView.as_view(), name='votaciones-detail'),
    re_path(
        r'^votaciones/(?P<pk>\d+)/(?P<accion>abrir|cerrar)/$',
        TransicionVotacionView.as_view(),
        name='votaciones-transicion',
    ),

    path('votaciones/<int:votacion_id>/normativas/', NormativaListCreateView.as_view(), name='normativas-list'),

    path('opciones/', OpcionListCreateView.as_view(), name='opciones-list'),
    path('opciones/<int:pk>/', OpcionDetailView.as_view(), name='opciones-detail'),

    path('multimedia/', RecursoMultimediaListCreateView.as_view(), name='multimedia-list'),
]

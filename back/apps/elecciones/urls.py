from django.urls import path

from .views import (
    CategoriaDetailView,
    CategoriaListCreateView,
    EdicionDetailView,
    EdicionListCreateView,
    NormativaListCreateView,
    OpcionDetailView,
    OpcionListCreateView,
    OpcionVotacionListCreateView,
    RecursoMultimediaListCreateView,
    VotacionDetailView,
    VotacionListCreateView,
    health_view,
)

urlpatterns = [
    path('health/', health_view, name='elecciones-health'),

    path('ediciones/', EdicionListCreateView.as_view(), name='ediciones-list'),
    path('ediciones/<int:pk>/', EdicionDetailView.as_view(), name='ediciones-detail'),

    path('categorias/', CategoriaListCreateView.as_view(), name='categorias-list'),
    path('categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categorias-detail'),

    path('votaciones/', VotacionListCreateView.as_view(), name='votaciones-list'),
    path('votaciones/<int:pk>/', VotacionDetailView.as_view(), name='votaciones-detail'),

    path('votaciones/<int:votacion_id>/normativas/', NormativaListCreateView.as_view(), name='normativas-list'),
    path('votaciones/<int:votacion_id>/opciones/', OpcionVotacionListCreateView.as_view(), name='opciones-votacion-list'),

    path('opciones/', OpcionListCreateView.as_view(), name='opciones-list'),
    path('opciones/<int:pk>/', OpcionDetailView.as_view(), name='opciones-detail'),

    path('multimedia/', RecursoMultimediaListCreateView.as_view(), name='multimedia-list'),
]

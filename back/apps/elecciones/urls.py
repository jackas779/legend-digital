from django.urls import path

from .views import (
    CandidatoListCreateView,
    CategoriaDetailView,
    CategoriaListCreateView,
    NormativaListCreateView,
    health_view,
)

urlpatterns = [
    path('health/', health_view, name='elecciones-health'),
    path('categorias/', CategoriaListCreateView.as_view(), name='categorias-list'),
    path('categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categorias-detail'),
    path('categorias/<int:categoria_id>/normativas/', NormativaListCreateView.as_view(), name='normativas-list'),
    path('categorias/<int:categoria_id>/candidatos/', CandidatoListCreateView.as_view(), name='candidatos-list'),
]

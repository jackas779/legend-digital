from django.urls import path

from .views import CategoriaDetailView, CategoriaListCreateView, health_view

urlpatterns = [
    path('health/', health_view, name='elecciones-health'),
    path('categorias/', CategoriaListCreateView.as_view(), name='categorias-list'),
    path('categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categorias-detail'),
]

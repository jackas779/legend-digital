"""Rutas MVT de gestión de ediciones y categorías (ED1-ED4, CA1-CA3)."""

from django.urls import path

from . import gestion_views

app_name = 'gestion'

urlpatterns = [
    path('ediciones/', gestion_views.edicion_lista, name='ediciones'),
    path('ediciones/nueva/', gestion_views.edicion_crear, name='edicion_crear'),
    path(
        'ediciones/<int:edicion_id>/editar/',
        gestion_views.edicion_editar,
        name='edicion_editar',
    ),
    path(
        'ediciones/<int:edicion_id>/eliminar/',
        gestion_views.edicion_eliminar,
        name='edicion_eliminar',
    ),
    path(
        'ediciones/<int:edicion_id>/publicar/',
        gestion_views.edicion_publicar,
        name='edicion_publicar',
    ),
    path(
        'ediciones/<int:edicion_id>/finalizar/',
        gestion_views.edicion_finalizar,
        name='edicion_finalizar',
    ),
    path('categorias/', gestion_views.categoria_lista, name='categorias'),
    path('categorias/nueva/', gestion_views.categoria_crear, name='categoria_crear'),
    path(
        'categorias/<int:categoria_id>/editar/',
        gestion_views.categoria_editar,
        name='categoria_editar',
    ),
    path(
        'categorias/<int:categoria_id>/eliminar/',
        gestion_views.categoria_eliminar,
        name='categoria_eliminar',
    ),
]

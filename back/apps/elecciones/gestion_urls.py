"""Rutas MVT de gestión de ediciones y categorías (ED1-ED4, CA1-CA3)."""

from django.urls import path

from . import gestion_views

app_name = 'gestion'

urlpatterns = [
    path('ediciones/', gestion_views.edicion_lista, name='ediciones'),
    path('ediciones/nueva/', gestion_views.edicion_crear, name='edicion_crear'),
    path(
        'ediciones/<int:edicion_id>/',
        gestion_views.edicion_gestionar,
        name='edicion_gestionar',
    ),
    path(
        'ediciones/<int:edicion_id>/categorias/<int:categoria_id>/quitar/',
        gestion_views.edicion_quitar_categoria,
        name='edicion_quitar_categoria',
    ),
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
    # Ciclo de vida: la activación, el cierre por fecha y la finalización
    # son automáticos; aquí solo están las acciones humanas.
    path(
        'ediciones/<int:edicion_id>/programar/',
        gestion_views.edicion_programar,
        name='edicion_programar',
    ),
    path(
        'ediciones/<int:edicion_id>/desprogramar/',
        gestion_views.edicion_desprogramar,
        name='edicion_desprogramar',
    ),
    path(
        'ediciones/<int:edicion_id>/cerrar/',
        gestion_views.edicion_cerrar,
        name='edicion_cerrar',
    ),
    path(
        'ediciones/<int:edicion_id>/escrutar/',
        gestion_views.edicion_escrutar,
        name='edicion_escrutar',
    ),
    path(
        'ediciones/<int:edicion_id>/inscritos/',
        gestion_views.inscritos,
        name='inscritos',
    ),
    path(
        'ediciones/<int:edicion_id>/inscritos/<int:inscripcion_id>/retirar/',
        gestion_views.inscrito_retirar,
        name='inscrito_retirar',
    ),
    # Rondas: siguiente ronda, preparación tras repetición y empates.
    path(
        'votaciones/<int:votacion_id>/ronda-siguiente/',
        gestion_views.ronda_siguiente_crear,
        name='ronda_siguiente',
    ),
    path(
        'votaciones/<int:votacion_id>/ronda/eliminar/',
        gestion_views.ronda_eliminar,
        name='ronda_eliminar',
    ),
    path(
        'votaciones/<int:votacion_id>/ronda/preparar/',
        gestion_views.ronda_preparar,
        name='ronda_preparar',
    ),
    path(
        'votaciones/<int:votacion_id>/empate/',
        gestion_views.empate_resolver,
        name='empate_resolver',
    ),
    # Normativas (reglas) de cada votación.
    path(
        'votaciones/<int:votacion_id>/normativas/',
        gestion_views.normativa_lista,
        name='normativa_lista',
    ),
    path(
        'votaciones/<int:votacion_id>/normativas/nueva/',
        gestion_views.normativa_form,
        name='normativa_crear',
    ),
    path(
        'votaciones/<int:votacion_id>/normativas/<int:normativa_id>/editar/',
        gestion_views.normativa_form,
        name='normativa_editar',
    ),
    path(
        'votaciones/<int:votacion_id>/normativas/<int:normativa_id>/eliminar/',
        gestion_views.normativa_eliminar,
        name='normativa_eliminar',
    ),
    path('categorias/', gestion_views.categoria_lista, name='categorias'),
    path('categorias/nueva/', gestion_views.categoria_crear, name='categoria_crear'),
    path(
        'categorias/<int:categoria_id>/editar/',
        gestion_views.categoria_editar,
        name='categoria_editar',
    ),
    path(
        'categorias/<int:categoria_id>/archivar/',
        gestion_views.categoria_archivar,
        name='categoria_archivar',
    ),
    path(
        'categorias/<int:categoria_id>/eliminar/',
        gestion_views.categoria_eliminar,
        name='categoria_eliminar',
    ),
    path('votaciones/', gestion_views.votacion_lista, name='votaciones'),
    path('votaciones/nueva/', gestion_views.votacion_crear, name='votacion_crear'),
    path(
        'votaciones/<int:votacion_id>/editar/',
        gestion_views.votacion_editar,
        name='votacion_editar',
    ),
    path(
        'votaciones/<int:votacion_id>/abrir/',
        gestion_views.votacion_abrir,
        name='votacion_abrir',
    ),
    path(
        'votaciones/<int:votacion_id>/cerrar/',
        gestion_views.votacion_cerrar,
        name='votacion_cerrar',
    ),
    path(
        'votaciones/<int:votacion_id>/opciones/',
        gestion_views.opcion_lista,
        name='opcion_lista',
    ),
    path(
        'votaciones/<int:votacion_id>/opciones/nueva/',
        gestion_views.opcion_crear,
        name='opcion_crear',
    ),
    path(
        'votaciones/<int:votacion_id>/opciones/<int:opcion_id>/editar/',
        gestion_views.opcion_editar,
        name='opcion_editar',
    ),
    path(
        'votaciones/<int:votacion_id>/opciones/<int:opcion_id>/eliminar/',
        gestion_views.opcion_eliminar,
        name='opcion_eliminar',
    ),
]

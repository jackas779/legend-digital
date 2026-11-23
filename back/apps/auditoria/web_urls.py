from django.urls import path, re_path

from . import log_views, verificacion_views

urlpatterns = [
    path('', log_views.lista, name='auditoria_lista'),
    path('ediciones/', verificacion_views.ediciones, name='auditoria_ediciones'),
    path('ediciones/<int:edicion_id>/', verificacion_views.edicion, name='auditoria_edicion'),
    path(
        'ediciones/<int:edicion_id>/reportar/',
        verificacion_views.reportar,
        name='auditoria_reportar',
    ),
    path(
        'ediciones/<int:edicion_id>/confirmar/',
        verificacion_views.confirmar_edicion,
        name='auditoria_confirmar_edicion',
    ),
    path('discrepancias/', verificacion_views.discrepancia_lista, name='discrepancias'),
    path(
        'discrepancias/<int:discrepancia_id>/',
        verificacion_views.discrepancia_detalle,
        name='auditoria_discrepancia',
    ),
    re_path(
        r'^discrepancias/(?P<discrepancia_id>\d+)/(?P<accion>resolver|descartar|confirmar|reabrir)/$',
        verificacion_views.discrepancia_accion,
        name='auditoria_discrepancia_accion',
    ),
]

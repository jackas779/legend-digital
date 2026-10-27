from django.urls import path

from . import log_views

urlpatterns = [
    path('', log_views.lista, name='auditoria_lista'),
]

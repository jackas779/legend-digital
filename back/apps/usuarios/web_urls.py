from django.urls import path

from . import web_views

urlpatterns = [
    path('registro/', web_views.registro, name='registro'),
    path('cuenta/password/', web_views.cambiar_password, name='cambiar_password'),
]

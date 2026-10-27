from django.urls import path

from . import web_views

urlpatterns = [
    path('registro/', web_views.registro, name='registro'),
]

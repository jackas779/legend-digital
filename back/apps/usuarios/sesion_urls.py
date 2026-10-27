from django.contrib.auth import views as vistas_auth
from django.urls import path

from . import sesion_views

app_name = 'auth'

urlpatterns = [
    path('login/', sesion_views.acceder, name='login'),
    path('logout/', sesion_views.cerrar_sesion, name='logout'),
]

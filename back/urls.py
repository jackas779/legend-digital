"""
URL configuration for back project.

Vistas MVT en la raíz, API REST bajo /api/ y panel en /admin/.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación por sesión (login/logout) para el tarjetón MVT.
    # Se usa el namespace 'auth' para no chocar con el nombre 'login' de la API.
    path('accounts/', include(('django.contrib.auth.urls', 'auth'), namespace='auth')),

    # API REST
    path('api/usuarios/', include('back.apps.usuarios.urls')),
    path('api/elecciones/', include('back.apps.elecciones.urls')),
    path('api/votacion/', include('back.apps.votacion.urls')),
    path('api/auditoria/', include('back.apps.auditoria.urls')),

    # Vistas MVT: Edición → Categoría → Votación → Opción → Voto
    path('', include('back.apps.votacion.web_urls')),
]

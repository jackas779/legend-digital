"""
URL configuration for back project.

Vistas MVT en la raíz, API REST bajo /api/ y panel en /admin/.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación por sesión del sitio (login/logout del namespace 'auth').
    path('accounts/', include('back.apps.usuarios.sesion_urls')),

    # API REST
    path('api/usuarios/', include('back.apps.usuarios.urls')),
    path('api/elecciones/', include('back.apps.elecciones.urls')),
    path('api/votacion/', include('back.apps.votacion.urls')),
    path('api/auditoria/', include('back.apps.auditoria.urls')),

    # Vistas MVT: autenticación y registro de cuentas.
    path('', include('back.apps.usuarios.web_urls')),

    # Vistas MVT: Edición → Categoría → Votación → Opción → Voto
    path('', include('back.apps.votacion.web_urls')),

    # Gestión MVT: ediciones y categorías (ED1-ED4, CA1-CA3).
    path('gestion/', include('back.apps.elecciones.gestion_urls')),
]

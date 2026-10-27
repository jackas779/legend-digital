"""Contexto de navegación por rol: el menú del encabezado se adapta a quien
ingresa (igual que en el prototipo del front).

El votante ve su flujo de votación, el organizador la gestión electoral,
el auditor los resultados y la auditoría, y el administrador además el
panel de Django. Las etiquetas usan lenguaje claro, sin tecnicismos.
"""

from django.urls import NoReverseMatch, reverse

SECCIONES_POR_ROL = {
    'Votante': [
        ('inicio', 'Inicio'),
        ('resultados_indice', 'Resultados'),
        ('mis_votos', 'Mis votos'),
        ('cambiar_password', 'Mi cuenta'),
    ],
    'Organizador': [
        ('gestion:ediciones', 'Ediciones'),
        ('gestion:categorias', 'Categorías'),
        ('gestion:votaciones', 'Votaciones'),
        ('resultados_indice', 'Resultados'),
        ('cambiar_password', 'Mi cuenta'),
    ],
    'Auditor': [
        ('resultados_indice', 'Resultados'),
        ('auditoria_lista', 'Auditoría'),
        ('cambiar_password', 'Mi cuenta'),
    ],
    'Administrador': [
        ('admin:index', 'Panel admin'),
        ('gestion:ediciones', 'Ediciones'),
        ('gestion:categorias', 'Categorías'),
        ('gestion:votaciones', 'Votaciones'),
        ('resultados_indice', 'Resultados'),
        ('auditoria_lista', 'Auditoría'),
        ('cambiar_password', 'Mi cuenta'),
    ],
}


def navegacion(request):
    """Devuelve {rol_actual, menu_navegacion} para el encabezado."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    perfil = getattr(user, 'perfil_usuario', None)
    rol = getattr(getattr(perfil, 'rol', None), 'nombre', None)
    if user.is_superuser:
        rol = 'Administrador'

    items = []
    for nombre_url, etiqueta in SECCIONES_POR_ROL.get(rol, []):
        try:
            url = reverse(nombre_url)
        except NoReverseMatch:
            continue
        activo = request.path == url or (
            url != '/' and request.path.startswith(url.rstrip('/') + '/')
        )
        items.append({'url': url, 'etiqueta': etiqueta, 'activo': activo})

    return {'rol_actual': rol, 'menu_navegacion': items}

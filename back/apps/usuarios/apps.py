from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sincronizar_permisos(sender, **kwargs):
    """Tras cada migrate, los permisos nuevos del código llegan a los roles.

    Sin esto, un permiso agregado en una versión nueva (por ejemplo
    ``inscripciones.gestionar``) no lo tendría el organizador hasta correr
    ``cargar_permisos`` a mano, y vería 403 en la pantalla nueva.
    """
    from back.apps.usuarios.permisos import sincronizar_catalogo

    sincronizar_catalogo(crear_roles=False)


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'back.apps.usuarios'
    label = 'usuarios'

    def ready(self):
        post_migrate.connect(_sincronizar_permisos, sender=self)

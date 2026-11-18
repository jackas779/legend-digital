"""Aplica los cambios de estado por fecha antes de atender cada petición.

Así la apertura y el cierre automáticos se cumplen aunque no haya un cron
configurado: la primera petición después de la fecha los aplica. Además,
``Votacion.esta_abierta`` vuelve a comprobar fechas y estado de la edición,
de modo que ningún voto entra fuera de tiempo aunque esta sincronización
aún no haya corrido.
"""

import logging

from .ciclo import sincronizar

logger = logging.getLogger(__name__)


class SincronizarEstadosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            sincronizar()
        except Exception:
            # Nunca tumba la petición: el voto igual queda protegido por
            # Votacion.esta_abierta, que valida fechas y estado al votar.
            logger.exception('No se pudieron sincronizar los estados por fecha.')
        return self.get_response(request)

"""Escritura de eventos de auditoría (módulo de logs del prototipo).

Qué guarda cada evento:

- ``usuario``: quién hizo la acción (nulo si fue el sistema o anónimo).
- ``modulo`` + ``accion``: qué módulo y qué ocurrió (por ejemplo
  ``usuarios`` / ``login`` o ``votacion`` / ``voto_emitido``).
- ``detalles_json``: datos de contexto. Ojo: en el voto NUNCA se guarda
  la opción elegida, para no romper el secreto del voto; solo se deja
  constancia de que participó y en qué votación.
- ``ip_origen``: desde dónde se conectó.
- ``hash_trazabilidad``: SHA-256 que encadena cada evento con el
  anterior. Si alguien altera o borra filas de la tabla, la cadena deja
  de coincidir y la alteración queda en evidencia.

Los eventos se pueden ver en Django Admin (Auditoría → Eventos) y en la
pantalla web /auditoria/ (rol Auditor o Administrador).
"""

import hashlib
import logging

from .models import LogAuditoriaEvento

logger = logging.getLogger(__name__)

# Primer eslabón de la cadena cuando la tabla está vacía.
GENESIS = 'GENESIS'


def registrar_evento(request=None, modulo='', accion='', detalles=None):
    """Graba un evento de auditoría y devuelve la fila creada.

    Nunca lanza excepción: la auditoría no debe interrumpir el flujo del
    usuario; si la escritura falla, solo se deja constancia en el log.
    """
    try:
        user = getattr(request, 'user', None)
        autenticado = user is not None and user.is_authenticated

        anterior = LogAuditoriaEvento.objects.order_by('id').last()
        hash_previo = anterior.hash_trazabilidad if anterior else GENESIS

        evento = LogAuditoriaEvento.objects.create(
            usuario=user if autenticado else None,
            modulo=modulo,
            accion=accion,
            detalles_json=detalles,
            ip_origen=(
                request.META.get('REMOTE_ADDR')
                or request.META.get('HTTP_X_FORWARDED_FOR')
                or ''
            ) if request is not None else '',
            hash_trazabilidad='',
        )

        # El hash se calcula con los campos guardados, de modo que
        # cualquiera puede rehacer la cadena y verificar la tabla.
        contenido = '|'.join([
            hash_previo,
            evento.timestamp.isoformat(),
            evento.modulo,
            evento.accion,
            str(evento.usuario_id or ''),
        ])
        evento.hash_trazabilidad = hashlib.sha256(
            contenido.encode('utf-8')
        ).hexdigest()
        evento.save(update_fields=['hash_trazabilidad'])

        return evento
    except Exception:
        logger.warning('No se pudo registrar el evento de auditoría.', exc_info=True)
        return None

"""Inscripción de votantes a una edición y quién puede votar en cada votación.

- Votación LIBRE: vota cualquier votante con cuenta, aunque se registre ese día.
- Votación SOLO INSCRITOS: vota quien se inscribió a la edición **antes** de
  que esa votación abriera. Así la inscripción puede seguir abierta durante
  una preselección libre y cerrarse para la votación oficial al abrir.

Se inscribe el propio votante (botón "Inscribirme", con la edición
programada o activa) o el organizador por él, pegando una lista de
documentos (también en borrador). Solo se inscriben cuentas con rol
Votante: las autoridades del proceso no votan.
"""

import re

from django.db import IntegrityError, transaction

from back.apps.auditoria.servicio import registrar_evento
from back.apps.elecciones.models import Edicion, Votacion
from back.apps.usuarios.models import Usuario

from .models import InscripcionEdicion


class InscripcionNoPermitida(Exception):
    pass


def es_votante(user):
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None) == 'Votante'


def usa_inscripcion(edicion):
    """La edición tiene al menos una votación que exige inscripción."""
    return edicion.votaciones.filter(modo_participacion=Votacion.INSCRITOS).exists()


def esta_inscrito(user, edicion):
    return InscripcionEdicion.objects.filter(edicion=edicion, usuario=user).exists()


def es_elegible(user, votacion):
    """Puede votar en esta votación según su modo de participación."""
    if not votacion.solo_inscritos:
        return True
    return InscripcionEdicion.objects.filter(
        edicion_id=votacion.edicion_id,
        usuario=user,
        fecha_inscripcion__lt=votacion.fecha_apertura,
    ).exists()


def admite_inscripciones(edicion, por_organizador=False):
    estados = [Edicion.PROGRAMADA, Edicion.ACTIVA]
    if por_organizador:
        estados.append(Edicion.BORRADOR)
    return edicion.estado in estados


def inscribir(request, edicion, user, por_organizador=False):
    """Inscribe a ``user``; devuelve la inscripción (nueva o la existente)."""
    if not admite_inscripciones(edicion, por_organizador):
        raise InscripcionNoPermitida(
            f'La edición está {edicion.get_estado_display().lower()}: ya no admite inscripciones.'
        )
    if not es_votante(user):
        raise InscripcionNoPermitida('Solo se inscriben cuentas con rol Votante.')

    try:
        with transaction.atomic():
            inscripcion, creada = InscripcionEdicion.objects.get_or_create(
                edicion=edicion,
                usuario=user,
                defaults={
                    'origen': (
                        InscripcionEdicion.ORGANIZADOR if por_organizador else InscripcionEdicion.VOTANTE
                    ),
                    'inscrito_por': request.user if por_organizador else None,
                },
            )
    except IntegrityError:  # Doble clic o dos pestañas: ya quedó inscrito.
        return InscripcionEdicion.objects.get(edicion=edicion, usuario=user)

    if creada:
        registrar_evento(
            request,
            'inscripciones',
            'inscripcion_por_organizador' if por_organizador else 'inscripcion',
            {'edicion': edicion.pk, 'usuario': user.pk},
        )
    return inscripcion


def inscribir_por_documentos(request, edicion, texto):
    """Inscribe una lista de documentos (uno por línea, o separados por coma).

    Devuelve un informe: inscritos, ya_inscritos, sin_cuenta, no_votantes.
    """
    documentos = [d for d in re.split(r'[\s,;]+', texto or '') if d]
    informe = {'inscritos': [], 'ya_inscritos': [], 'sin_cuenta': [], 'no_votantes': []}
    vistos = set()
    for documento in documentos:
        if documento in vistos:
            continue
        vistos.add(documento)
        perfil = Usuario.objects.select_related('user', 'rol').filter(documento=documento).first()
        if perfil is None:
            informe['sin_cuenta'].append(documento)
            continue
        if not es_votante(perfil.user):
            informe['no_votantes'].append(documento)
            continue
        if esta_inscrito(perfil.user, edicion):
            informe['ya_inscritos'].append(documento)
            continue
        inscribir(request, edicion, perfil.user, por_organizador=True)
        informe['inscritos'].append(documento)
    return informe


def desinscribir(request, edicion, inscripcion):
    """Solo antes de que la edición se active: después la lista es historia."""
    if edicion.estado not in (Edicion.BORRADOR, Edicion.PROGRAMADA):
        raise InscripcionNoPermitida('Con la edición activa la lista de inscritos ya no cambia.')
    usuario_id = inscripcion.usuario_id
    inscripcion.delete()
    registrar_evento(
        request, 'inscripciones', 'inscripcion_retirada',
        {'edicion': edicion.pk, 'usuario': usuario_id},
    )

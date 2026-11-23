"""Flujo de discrepancias: el auditor verifica, otro resuelve.

- El auditor (``discrepancias.reportar``) registra la discrepancia, y
  después confirma la resolución o la reabre. Nunca la resuelve él.
- La resuelve el organizador si su rol tiene ``discrepancias.resolver``;
  si no lo tiene, la discrepancia pasa al administrador.
- Resolver exige una explicación: RESUELTA (se corrigió) o DESCARTADA
  (era un falso positivo).
- Una discrepancia abierta no bloquea el cierre de la edición.

Todo queda en el registro de auditoría.
"""

from django.utils import timezone

from back.apps.usuarios.models import RolPermiso
from back.apps.usuarios.permisos import tiene_permiso

from .models import ConfirmacionAuditoria, Discrepancia
from .servicio import registrar_evento


class AccionNoPermitida(Exception):
    pass


def _rol(user):
    if user.is_superuser:
        return 'Administrador'
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None)


def responsable_actual():
    """Quién resuelve hoy: el organizador si su rol tiene el permiso; si no, el administrador."""
    organizador_puede = RolPermiso.objects.filter(
        rol__nombre='Organizador', permiso__codigo='discrepancias.resolver'
    ).exists()
    return 'Organizador' if organizador_puede else 'Administrador'


def puede_resolver(user):
    """Quien resuelve nunca es el auditor, aunque alguien le asigne el permiso."""
    if not user.is_authenticated or _rol(user) == 'Auditor':
        return False
    if _rol(user) == 'Administrador':
        return True  # El administrador siempre es la instancia de respaldo.
    return tiene_permiso(user, 'discrepancias.resolver')


def puede_verificar(user):
    return tiene_permiso(user, 'discrepancias.reportar')


def reportar(request, edicion, tipo, descripcion, votacion=None, evidencia=None):
    if not puede_verificar(request.user):
        raise AccionNoPermitida('Solo el auditor registra discrepancias.')
    descripcion = (descripcion or '').strip()
    if not descripcion:
        raise AccionNoPermitida('La discrepancia necesita una descripción.')
    if tipo not in dict(Discrepancia.TIPOS):
        raise AccionNoPermitida('Tipo de discrepancia desconocido.')

    discrepancia = Discrepancia.objects.create(
        edicion=edicion,
        votacion=votacion,
        tipo=tipo,
        descripcion=descripcion,
        evidencia=evidencia,
        reportada_por=request.user,
    )
    registrar_evento(
        request,
        'auditoria',
        'discrepancia_reportada',
        {
            'id': discrepancia.pk,
            'edicion': edicion.pk,
            'votacion': getattr(votacion, 'pk', None),
            'tipo': tipo,
            'responsable': responsable_actual(),
        },
    )
    return discrepancia


def resolver(request, discrepancia, resolucion, descartar=False):
    if not puede_resolver(request.user):
        raise AccionNoPermitida('No tienes permiso para resolver discrepancias.')
    if not discrepancia.esta_abierta:
        raise AccionNoPermitida('La discrepancia ya no está abierta.')
    resolucion = (resolucion or '').strip()
    if len(resolucion) < 10:
        raise AccionNoPermitida('Explica la resolución con al menos 10 caracteres.')

    discrepancia.estado = Discrepancia.DESCARTADA if descartar else Discrepancia.RESUELTA
    discrepancia.resolucion = resolucion
    discrepancia.resuelta_por = request.user
    discrepancia.fecha_resolucion = timezone.now()
    discrepancia.confirmada_por = None
    discrepancia.fecha_confirmacion = None
    discrepancia.save()
    registrar_evento(
        request,
        'auditoria',
        'discrepancia_descartada' if descartar else 'discrepancia_resuelta',
        {'id': discrepancia.pk, 'edicion': discrepancia.edicion_id},
    )
    return discrepancia


def confirmar_resolucion(request, discrepancia):
    if not puede_verificar(request.user):
        raise AccionNoPermitida('Solo el auditor confirma resoluciones.')
    if discrepancia.esta_abierta:
        raise AccionNoPermitida('La discrepancia todavía no se ha resuelto.')
    discrepancia.confirmada_por = request.user
    discrepancia.fecha_confirmacion = timezone.now()
    discrepancia.save(update_fields=['confirmada_por', 'fecha_confirmacion'])
    registrar_evento(
        request, 'auditoria', 'discrepancia_confirmada', {'id': discrepancia.pk}
    )
    return discrepancia


def reabrir(request, discrepancia, motivo):
    if not puede_verificar(request.user):
        raise AccionNoPermitida('Solo el auditor reabre discrepancias.')
    if discrepancia.esta_abierta:
        raise AccionNoPermitida('La discrepancia ya está abierta.')
    motivo = (motivo or '').strip()
    if not motivo:
        raise AccionNoPermitida('Indica por qué se reabre.')
    discrepancia.estado = Discrepancia.ABIERTA
    discrepancia.confirmada_por = None
    discrepancia.fecha_confirmacion = None
    discrepancia.veces_reabierta += 1
    discrepancia.resolucion = (
        f'{discrepancia.resolucion}\n\n[Reabierta por el auditor: {motivo}]'.strip()
    )
    discrepancia.save()
    registrar_evento(
        request,
        'auditoria',
        'discrepancia_reabierta',
        {'id': discrepancia.pk, 'motivo': motivo},
    )
    return discrepancia


def confirmar_en_orden(request, edicion, observacion='', votacion=None):
    """Constancia del auditor de que la edición (o una votación) está en orden."""
    if not puede_verificar(request.user):
        raise AccionNoPermitida('Solo el auditor confirma que todo está en orden.')
    confirmacion = ConfirmacionAuditoria.objects.create(
        edicion=edicion,
        votacion=votacion,
        auditor=request.user,
        estado_edicion=edicion.estado,
        observacion=(observacion or '').strip(),
    )
    registrar_evento(
        request,
        'auditoria',
        'edicion_confirmada_en_orden',
        {'edicion': edicion.pk, 'votacion': getattr(votacion, 'pk', None), 'estado': edicion.estado},
    )
    return confirmacion

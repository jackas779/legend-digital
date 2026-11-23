"""Verificaciones automáticas que apoyan al auditor.

No cambian nada ni deciden nada: devuelven hallazgos para que el auditor
los revise y, si corresponde, los registre como discrepancia.

Cada hallazgo es un dict con ``tipo`` (de ``Discrepancia.TIPOS``),
``votacion`` (o None), ``descripcion`` y ``evidencia`` (JSON serializable).
"""

from datetime import timedelta

from django.db.models import Count, Q

from back.apps.elecciones.ciclo import sello_de_urna
from back.apps.elecciones.models import Edicion, Votacion
from back.apps.votacion.models import (
    ActaEscrutinio,
    InscripcionEdicion,
    PadronVotante,
    Voto,
    truncar_a_hora,
)

# Margen para no marcar como "fuera de horario" un voto que entró en el
# mismo segundo del cierre (los relojes de BD y aplicación pueden diferir).
TOLERANCIA = timedelta(seconds=5)


def verificar_edicion(edicion):
    """Corre todas las verificaciones sobre la edición y sus votaciones."""
    hallazgos = []
    votaciones = list(
        edicion.votaciones.exclude(estado=Votacion.BORRADOR).select_related('categoria')
    )
    actas = {
        acta.votacion_id: acta
        for acta in ActaEscrutinio.objects.filter(votacion__edicion=edicion)
    }

    for votacion in votaciones:
        hallazgos += _padron_contra_urna(votacion)
        hallazgos += _firmas(votacion)
        hallazgos += _votos_fuera_de_horario(edicion, votacion)
        hallazgos += _no_inscritos(votacion)
        acta = actas.get(votacion.pk)
        if acta is not None:
            hallazgos += _acta_contra_urna(votacion, acta)

    if edicion.estado in (Edicion.CERRANDO, Edicion.FINALIZADA):
        for votacion in votaciones:
            if votacion.estado == Votacion.ABIERTA:
                hallazgos.append({
                    'tipo': 'ABIERTA_CON_EDICION_CERRADA',
                    'votacion': votacion,
                    'descripcion': (
                        f'«{votacion.nombre}» sigue ABIERTA aunque la edición está '
                        f'{edicion.get_estado_display().upper()}.'
                    ),
                    'evidencia': {'votacion': votacion.pk, 'estado_edicion': edicion.estado},
                })
    return hallazgos


def _padron_contra_urna(votacion):
    participantes = PadronVotante.objects.filter(votacion=votacion, ha_votado=True).count()
    en_urna = Voto.objects.filter(opcion__votacion=votacion).count()
    if participantes == en_urna:
        return []
    return [{
        'tipo': 'PADRON_URNA',
        'votacion': votacion,
        'descripcion': (
            f'«{votacion.nombre}»: {en_urna} voto(s) en la urna y '
            f'{participantes} participante(s) marcados en el padrón.'
        ),
        'evidencia': {
            'votacion': votacion.pk,
            'votos_urna': en_urna,
            'participantes_padron': participantes,
        },
    }]


def _firmas(votacion):
    invalidos = [
        str(voto.pk)
        for voto in Voto.objects.filter(opcion__votacion=votacion)
        if voto.firma_criptografica != voto.calcular_firma()
    ]
    if not invalidos:
        return []
    return [{
        'tipo': 'FIRMA_INVALIDA',
        'votacion': votacion,
        'descripcion': (
            f'«{votacion.nombre}»: {len(invalidos)} voto(s) cuya firma no coincide '
            'con su contenido (posible alteración).'
        ),
        'evidencia': {'votacion': votacion.pk, 'votos': invalidos[:50]},
    }]


def _votos_fuera_de_horario(edicion, votacion):
    """Votos antes de la apertura o después del cierre (de la votación o de la edición)."""
    fin = votacion.fecha_cierre
    if edicion.fecha_fin and edicion.fecha_fin < fin:
        fin = edicion.fecha_fin
    if edicion.fecha_cierre_real and edicion.fecha_cierre_real < fin:
        fin = edicion.fecha_cierre_real
    inicio = votacion.fecha_apertura
    if edicion.fecha_inicio and edicion.fecha_inicio > inicio:
        inicio = edicion.fecha_inicio
    # Los votos se guardan redondeados a la hora (secreto del voto): un voto
    # de las 10:45 queda a las 10:00 aunque la votación abrió a las 10:30.
    inicio = truncar_a_hora(inicio)

    fuera = Voto.objects.filter(opcion__votacion=votacion).filter(
        Q(fecha_registro__lt=inicio - TOLERANCIA) | Q(fecha_registro__gt=fin + TOLERANCIA)
    )
    total = fuera.count()
    if not total:
        return []
    return [{
        'tipo': 'VOTO_FUERA_DE_HORARIO',
        'votacion': votacion,
        'descripcion': (
            f'«{votacion.nombre}»: {total} voto(s) registrados fuera de la ventana '
            'permitida.'
        ),
        'evidencia': {
            'votacion': votacion.pk,
            'votos': [str(pk) for pk in fuera.values_list('pk', flat=True)[:50]],
            'ventana': [inicio.isoformat(), fin.isoformat()],
        },
    }]


def _no_inscritos(votacion):
    """En "solo inscritos": nadie marcado en el padrón sin inscripción previa."""
    if not votacion.solo_inscritos:
        return []
    a_tiempo = InscripcionEdicion.objects.filter(
        edicion_id=votacion.edicion_id,
        fecha_inscripcion__lt=votacion.fecha_apertura,
    ).values('usuario_id')
    intrusos = (
        PadronVotante.objects.filter(votacion=votacion, ha_votado=True)
        .exclude(usuario_id__in=a_tiempo)
        .count()
    )
    if not intrusos:
        return []
    return [{
        'tipo': 'NO_INSCRITO',
        'votacion': votacion,
        'descripcion': (
            f'«{votacion.nombre}» es solo para inscritos y {intrusos} participante(s) no '
            'estaban inscritos antes de la apertura.'
        ),
        # Solo la cifra: el auditor no necesita saber quiénes son.
        'evidencia': {'votacion': votacion.pk, 'participantes_no_inscritos': intrusos},
    }]


def _acta_contra_urna(votacion, acta):
    en_urna = Voto.objects.filter(opcion__votacion=votacion).count()
    sello = sello_de_urna(votacion)
    if acta.total_votos_urna == en_urna and acta.hash_sello_bd == sello:
        return []
    return [{
        'tipo': 'ACTA_DESCUADRADA',
        'votacion': votacion,
        'descripcion': (
            f'«{votacion.nombre}»: el acta registra {acta.total_votos_urna} voto(s) y '
            f'la urna tiene {en_urna}, o su sello ya no coincide con el contenido.'
        ),
        'evidencia': {
            'votacion': votacion.pk,
            'acta': acta.pk,
            'votos_acta': acta.total_votos_urna,
            'votos_urna': en_urna,
            'sello_coincide': acta.hash_sello_bd == sello,
        },
    }]


def resumen_votaciones(edicion):
    """Cifras por votación para el panel del auditor."""
    return (
        edicion.votaciones.select_related('categoria')
        .annotate(
            votos=Count('opciones__votos', distinct=True),
            participantes=Count(
                'padron', filter=Q(padron__ha_votado=True), distinct=True
            ),
            habilitados=Count('padron', distinct=True),
        )
        .order_by('categoria__nombre', 'nombre')
    )

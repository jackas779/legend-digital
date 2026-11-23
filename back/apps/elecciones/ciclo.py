"""Ciclo de vida de la edición y sus votaciones: única puerta de cambios de estado.

Ninguna vista, serializer ni comando cambia ``estado`` a mano: todos pasan
por aquí, para que las reglas valgan igual en la web, la API y la demo.

Edición
-------
BORRADOR ──programar──▶ PROGRAMADA ──(fecha_inicio)──▶ ACTIVA
    ▲                       │                             │
    └────desprogramar───────┘        (fecha_fin) o cierre anticipado
                                                          ▼
            FINALIZADA ◀──(todo escrutado o cancelado)── CERRANDO

- Desde ACTIVA no se vuelve atrás.
- Solo se activa sola una edición PROGRAMADA; si llega su fecha de inicio
  y sigue en BORRADOR queda "no lista".

Votación (siempre subordinada a su edición)
-------------------------------------------
BORRADOR ──(programar la edición)──▶ LISTA ──(fecha_apertura, edición ACTIVA)──▶ ABIERTA
ABIERTA ──(fecha_cierre, cierre manual o cierre de la edición)──▶ CERRADA ──escrutar──▶ ESCRUTADA
BORRADOR/LISTA ──(cierre de la edición)──▶ CANCELADA

Rondas
------
Una votación con mayoría absoluta, clasificatoria o "repetir si gana el
blanco" tiene configurada su ronda siguiente (misma categoría, ronda N+1),
que espera en BORRADOR sin candidatos. Al escrutar la anterior:

- GANADOR → la siguiente se CANCELA (no hace falta).
- SEGUNDA_RONDA / CLASIFICADOS → recibe a los que pasan (con su foto) y
  queda LISTA para abrirse en su fecha.
- REPETIR → espera candidatos nuevos del organizador (``preparar_ronda``).
- EMPATE → espera la decisión del organizador (``resolver_empate``).

Una votación que alimenta otra ronda se escruta sola al cerrarse.

Reglas en cascada
-----------------
R1. Una votación solo está ABIERTA si su edición está ACTIVA.
R2. Las fechas de cada votación caen dentro del periodo de su edición.
R3. Al pasar la edición a CERRANDO: ABIERTA → CERRADA y BORRADOR/LISTA → CANCELADA.
R4. La edición pasa a FINALIZADA cuando cada votación está ESCRUTADA o CANCELADA.
R5. Con la edición FINALIZADA todo queda en solo lectura.

Las transiciones usan UPDATE condicionales (``filter(estado=X).update``):
si dos procesos intentan el mismo cambio a la vez, solo uno lo aplica.
"""

import hashlib

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from back.apps.auditoria.servicio import registrar_evento

from .models import Edicion, Opcion, Votacion


class TransicionInvalida(Exception):
    """El cambio de estado pedido no está permitido por las reglas."""

    def __init__(self, mensaje, errores=None):
        super().__init__(mensaje)
        self.errores = errores or []


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------

def errores_de_fechas_votacion(edicion, apertura, cierre):
    """R2: la apertura y el cierre de una votación dentro del periodo de la edición."""
    errores = []
    if apertura and cierre and apertura >= cierre:
        errores.append('El cierre debe ser posterior a la apertura.')
    if edicion is None:
        return errores
    if edicion.fecha_inicio and apertura and apertura < edicion.fecha_inicio:
        errores.append(
            'La apertura no puede ser anterior al inicio de la edición '
            f'({timezone.localtime(edicion.fecha_inicio):%d/%m/%Y %H:%M}).'
        )
    if edicion.fecha_fin and cierre and cierre > edicion.fecha_fin:
        errores.append(
            'El cierre no puede ser posterior al fin de la edición '
            f'({timezone.localtime(edicion.fecha_fin):%d/%m/%Y %H:%M}).'
        )
    return errores


def errores_para_programar(edicion):
    """Lo que le falta a una edición para pasar a PROGRAMADA (lista vacía = válida)."""
    errores = []
    ahora = timezone.now()

    if not edicion.fecha_inicio or not edicion.fecha_fin:
        errores.append('La edición necesita fecha de inicio y fecha de fin.')
    elif edicion.fecha_inicio >= edicion.fecha_fin:
        errores.append('La fecha de fin debe ser posterior a la de inicio.')
    elif edicion.fecha_fin <= ahora:
        errores.append('La fecha de fin ya pasó: ajusta el periodo de la edición.')

    votaciones = list(
        edicion.votaciones.select_related('categoria').annotate(
            validas=Count('opciones', filter=Q(opciones__es_voto_blanco=False))
        )
    )
    if not votaciones:
        errores.append('La edición necesita al menos una categoría con su votación.')

    con_siguiente = {v.ronda_anterior_id for v in votaciones if v.ronda_anterior_id}
    por_id = {v.pk: v for v in votaciones}
    for votacion in votaciones:
        # Una ronda derivada recibe sus candidatos al escrutar la anterior.
        if not votacion.es_ronda_derivada and votacion.validas < 2:
            errores.append(
                f'«{votacion.nombre}» ({votacion.categoria}) necesita al menos 2 '
                f'opciones válidas sin contar el voto en blanco; tiene {votacion.validas}.'
            )
        if votacion.regla_resultado == Votacion.CLASIFICAN_N and votacion.clasifican < 2:
            errores.append(f'«{votacion.nombre}»: deben clasificar al menos 2.')
        if (
            votacion.regla_resultado == Votacion.CLASIFICAN_N
            and not votacion.es_ronda_derivada
            and votacion.validas <= votacion.clasifican
        ):
            errores.append(
                f'«{votacion.nombre}»: clasifican {votacion.clasifican} y solo hay '
                f'{votacion.validas} opciones; no habría a quién descartar.'
            )
        if votacion.necesita_ronda_siguiente and votacion.pk not in con_siguiente:
            errores.append(
                f'«{votacion.nombre}» puede requerir otra ronda (segunda vuelta, '
                'clasificados o repetición): configura su ronda siguiente.'
            )
        anterior = por_id.get(votacion.ronda_anterior_id)
        if anterior is not None and votacion.fecha_apertura < anterior.fecha_cierre:
            errores.append(
                f'«{votacion.nombre}» debe abrir después del cierre de «{anterior.nombre}».'
            )
        for error in errores_de_fechas_votacion(
            edicion, votacion.fecha_apertura, votacion.fecha_cierre
        ):
            errores.append(f'«{votacion.nombre}»: {error}')
    return errores


def _exigir(edicion, *estados):
    if edicion.estado not in estados:
        nombres = ' o '.join(dict(Edicion.ESTADOS)[e] for e in estados)
        raise TransicionInvalida(
            f'La edición está {edicion.get_estado_display().upper()}; '
            f'esta acción solo aplica en estado {nombres.upper()}.'
        )


def _cambiar_estado(modelo, objeto, desde, hacia, **extra):
    """UPDATE condicional: aplica el cambio solo si sigue en ``desde``."""
    if isinstance(desde, str):
        desde = (desde,)
    cambiados = modelo.objects.filter(pk=objeto.pk, estado__in=desde).update(
        estado=hacia, **extra
    )
    if cambiados:
        objeto.estado = hacia
        for campo, valor in extra.items():
            setattr(objeto, campo, valor)
    return bool(cambiados)


# ---------------------------------------------------------------------------
# Transiciones de la edición
# ---------------------------------------------------------------------------

@transaction.atomic
def programar(edicion, request=None):
    """BORRADOR → PROGRAMADA, si pasa la validación. Sus votaciones quedan LISTA."""
    _exigir(edicion, Edicion.BORRADOR)
    errores = errores_para_programar(edicion)
    if errores:
        raise TransicionInvalida('La edición todavía no está lista para programarse.', errores)

    if not _cambiar_estado(Edicion, edicion, Edicion.BORRADOR, Edicion.PROGRAMADA):
        raise TransicionInvalida('La edición cambió de estado mientras se programaba.')
    # Las rondas derivadas siguen en BORRADOR hasta recibir sus candidatos.
    edicion.votaciones.filter(
        estado=Votacion.BORRADOR, ronda_anterior__isnull=True
    ).update(estado=Votacion.LISTA)
    registrar_evento(request, 'ediciones', 'edicion_programada', {'id': edicion.pk})

    # Si su fecha de inicio ya llegó, se activa de inmediato.
    sincronizar_edicion(edicion)
    return edicion


@transaction.atomic
def desprogramar(edicion, request=None):
    """PROGRAMADA → BORRADOR para corregir: todavía no hay votos."""
    _exigir(edicion, Edicion.PROGRAMADA)
    if not _cambiar_estado(Edicion, edicion, Edicion.PROGRAMADA, Edicion.BORRADOR):
        raise TransicionInvalida('La edición cambió de estado mientras se devolvía a borrador.')
    edicion.votaciones.filter(estado=Votacion.LISTA).update(estado=Votacion.BORRADOR)
    registrar_evento(request, 'ediciones', 'edicion_devuelta_a_borrador', {'id': edicion.pk})
    return edicion


@transaction.atomic
def activar(edicion, request=None):
    """PROGRAMADA → ACTIVA (automático al llegar fecha_inicio)."""
    if not _cambiar_estado(Edicion, edicion, Edicion.PROGRAMADA, Edicion.ACTIVA):
        return False
    registrar_evento(request, 'ediciones', 'edicion_activada', {'id': edicion.pk, 'automatico': True})
    abrir_votaciones_pendientes(edicion)
    return True


@transaction.atomic
def cerrar(edicion, request=None, motivo='', anticipado=False):
    """ACTIVA → CERRANDO, con el cierre en cascada (R3).

    Por fecha (automático) o anticipado por el organizador; el cierre
    anticipado exige un motivo, que queda en la edición y en la auditoría.
    """
    _exigir(edicion, Edicion.ACTIVA)
    motivo = (motivo or '').strip()
    if anticipado and not motivo:
        raise TransicionInvalida('El cierre anticipado exige un motivo.')

    ahora = timezone.now()
    if not _cambiar_estado(
        Edicion,
        edicion,
        Edicion.ACTIVA,
        Edicion.CERRANDO,
        cierre_anticipado=anticipado,
        motivo_cierre=motivo,
        fecha_cierre_real=ahora,
    ):
        return False

    cerradas = list(
        edicion.votaciones.filter(estado=Votacion.ABIERTA).values_list('pk', flat=True)
    )
    Votacion.objects.filter(pk__in=cerradas).update(estado=Votacion.CERRADA)
    canceladas = list(
        edicion.votaciones.filter(
            estado__in=(Votacion.BORRADOR, Votacion.LISTA)
        ).values_list('pk', flat=True)
    )
    Votacion.objects.filter(pk__in=canceladas).update(estado=Votacion.CANCELADA)

    registrar_evento(
        request,
        'ediciones',
        'edicion_cerrada_anticipadamente' if anticipado else 'edicion_cerrada',
        {
            'id': edicion.pk,
            'motivo': motivo or None,
            'automatico': not anticipado,
            'votaciones_cerradas': cerradas,
            'votaciones_canceladas': canceladas,
        },
    )
    intentar_finalizar(edicion, request)
    return True


def intentar_finalizar(edicion, request=None):
    """R4: CERRANDO → FINALIZADA cuando no queda nada por escrutar."""
    if edicion.estado != Edicion.CERRANDO:
        return False
    pendientes = edicion.votaciones.exclude(
        estado__in=(Votacion.ESCRUTADA, Votacion.CANCELADA)
    ).exists()
    if pendientes:
        return False
    if not _cambiar_estado(Edicion, edicion, Edicion.CERRANDO, Edicion.FINALIZADA):
        return False
    registrar_evento(
        request,
        'ediciones',
        'edicion_finalizada',
        {
            'id': edicion.pk,
            'automatico': True,
            'discrepancias_pendientes': edicion.num_discrepancias_pendientes,
        },
    )
    return True


# ---------------------------------------------------------------------------
# Transiciones de la votación
# ---------------------------------------------------------------------------

def abrir_votacion(votacion, request=None):
    """LISTA → ABIERTA antes de su fecha, por el organizador (R1)."""
    edicion = votacion.edicion
    if votacion.estado != Votacion.LISTA:
        raise TransicionInvalida(
            f'Solo se abre una votación LISTA; esta está {votacion.get_estado_display().upper()}.'
        )
    if not edicion.recibe_votos:
        raise TransicionInvalida(
            'La votación solo puede abrirse con la edición ACTIVA y dentro de su periodo.'
        )
    ahora = timezone.now()
    if votacion.fecha_cierre <= ahora:
        raise TransicionInvalida('Su fecha de cierre ya pasó; no puede abrirse.')

    extra = {}
    if votacion.fecha_apertura > ahora:
        # Apertura adelantada: la ventana empieza ahora.
        extra['fecha_apertura'] = ahora
    if not _cambiar_estado(Votacion, votacion, Votacion.LISTA, Votacion.ABIERTA, **extra):
        raise TransicionInvalida('La votación cambió de estado mientras se abría.')
    registrar_evento(request, 'votaciones', 'votacion_abierta', {'id': votacion.pk})
    return votacion


def cerrar_votacion(votacion, request=None, automatico=False):
    """ABIERTA → CERRADA. No borra votos; no se reabre."""
    if votacion.estado != Votacion.ABIERTA:
        raise TransicionInvalida(
            f'Solo se cierra una votación ABIERTA; esta está {votacion.get_estado_display().upper()}.'
        )
    if not _cambiar_estado(Votacion, votacion, Votacion.ABIERTA, Votacion.CERRADA):
        return False
    registrar_evento(
        request, 'votaciones', 'votacion_cerrada', {'id': votacion.pk, 'automatico': automatico}
    )
    # Si alimenta otra ronda se escruta de inmediato: la siguiente necesita
    # sus candidatos antes de su fecha de apertura.
    if Votacion.objects.filter(ronda_anterior=votacion).exists():
        escrutar(votacion, request)
    return True


def sello_de_urna(votacion):
    """Hash del contenido de la urna: firmas ordenadas + total de votos."""
    from back.apps.votacion.models import Voto

    firmas = sorted(
        Voto.objects.filter(opcion__votacion=votacion).values_list('firma_criptografica', flat=True)
    )
    contenido = f'{votacion.pk}|{len(firmas)}|' + '|'.join(firmas)
    return hashlib.sha256(contenido.encode('utf-8')).hexdigest()


@transaction.atomic
def escrutar(votacion, request=None):
    """CERRADA → ESCRUTADA generando su acta; luego intenta finalizar (R4)."""
    from back.apps.votacion.models import ActaEscrutinio, PadronVotante, Voto

    if votacion.estado != Votacion.CERRADA:
        raise TransicionInvalida(
            f'Solo se escruta una votación CERRADA; esta está {votacion.get_estado_display().upper()}.'
        )

    padron = PadronVotante.objects.filter(votacion=votacion)
    acta, _ = ActaEscrutinio.objects.update_or_create(
        votacion=votacion,
        defaults={
            'total_padron_habilitado': padron.count(),
            'total_participantes': padron.filter(ha_votado=True).count(),
            'total_votos_urna': Voto.objects.filter(opcion__votacion=votacion).count(),
            'hash_sello_bd': sello_de_urna(votacion),
        },
    )
    if not _cambiar_estado(Votacion, votacion, Votacion.CERRADA, Votacion.ESCRUTADA):
        raise TransicionInvalida('La votación cambió de estado mientras se escrutaba.')
    registrar_evento(
        request,
        'votaciones',
        'votacion_escrutada',
        {'id': votacion.pk, 'acta': acta.pk, 'votos': acta.total_votos_urna},
    )

    aplicar_resultado(votacion, calcular_resultado(votacion), request)

    edicion = Edicion.objects.get(pk=votacion.edicion_id)
    intentar_finalizar(edicion, request)
    return acta


# ---------------------------------------------------------------------------
# Resultados y rondas
# ---------------------------------------------------------------------------

def conteo(votacion):
    """Opciones con su total de votos, de mayor a menor (desempata la casilla)."""
    return list(
        votacion.opciones.annotate(total=Count('votos')).order_by('-total', 'orden')
    )


def calcular_resultado(votacion):
    """Aplica la regla de la votación al conteo. No guarda nada.

    El voto en blanco cuenta como voto válido (para el 50 % + 1 también),
    pero nunca gana ni clasifica. Si está activada la regla de repetición y
    el blanco saca más del 50 %, la votación se repite con otros candidatos.
    Un empate en el punto de corte no lo decide el sistema: queda EMPATE
    para que lo resuelva el organizador.
    """
    opciones = conteo(votacion)
    total = sum(o.total for o in opciones)
    candidatas = [o for o in opciones if not o.es_voto_blanco]
    blanco = sum(o.total for o in opciones if o.es_voto_blanco)

    def resultado(tipo, pasan=(), detalle=''):
        return {
            'resultado': tipo,
            'pasan': list(pasan),
            'ganadora': pasan[0] if tipo == Votacion.GANADOR and pasan else None,
            'total': total,
            'detalle': detalle,
        }

    if not total or not candidatas:
        return resultado(Votacion.EMPATE, detalle='No hubo votos por ningún candidato.')

    if votacion.repetir_si_gana_blanco and blanco * 2 > total:
        return resultado(
            Votacion.REPETIR,
            detalle=f'El voto en blanco obtuvo {blanco} de {total} votos (más del 50 %).',
        )

    def corte(n):
        """Los n primeros, o None si hay empate justo en el corte."""
        if len(candidatas) <= n:
            return candidatas
        if candidatas[n - 1].total == candidatas[n].total:
            return None
        return candidatas[:n]

    primera = candidatas[0]
    if votacion.regla_resultado == Votacion.MAYORIA_SIMPLE:
        ganadora = corte(1)
        if ganadora is None:
            return resultado(Votacion.EMPATE, detalle='Empate en el primer lugar.')
        return resultado(Votacion.GANADOR, ganadora)

    if votacion.regla_resultado == Votacion.MAYORIA_ABSOLUTA:
        if primera.total * 2 > total:
            return resultado(
                Votacion.GANADOR,
                [primera],
                f'{primera.nombre} obtuvo {primera.total} de {total} votos (más del 50 %).',
            )
        finalistas = corte(2)
        if finalistas is None:
            return resultado(Votacion.EMPATE, detalle='Empate en el segundo lugar: no se sabe quién pasa.')
        return resultado(
            Votacion.SEGUNDA_RONDA,
            finalistas,
            f'Nadie superó el 50 % ({primera.nombre}: {primera.total} de {total}).',
        )

    # Clasificatoria.
    clasificados = corte(votacion.clasifican)
    if clasificados is None:
        return resultado(
            Votacion.EMPATE,
            detalle=f'Empate en el puesto {votacion.clasifican}: no se sabe quién clasifica.',
        )
    return resultado(Votacion.CLASIFICADOS, clasificados)


def cuantos_pasan(votacion):
    """Cuántas opciones decide el organizador al resolver un empate."""
    if votacion.regla_resultado == Votacion.MAYORIA_SIMPLE:
        return 1
    if votacion.regla_resultado == Votacion.MAYORIA_ABSOLUTA:
        return 2
    return votacion.clasifican


def _ronda_siguiente(votacion):
    return Votacion.objects.filter(ronda_anterior=votacion).first()


def aplicar_resultado(votacion, calculado, request=None):
    """Guarda el resultado y prepara (o cancela) la ronda siguiente."""
    tipo = calculado['resultado']
    Votacion.objects.filter(pk=votacion.pk).update(
        resultado=tipo, opcion_ganadora=calculado['ganadora']
    )
    votacion.resultado = tipo
    votacion.opcion_ganadora = calculado['ganadora']
    registrar_evento(
        request,
        'votaciones',
        'resultado_aplicado',
        {
            'id': votacion.pk,
            'resultado': tipo,
            'pasan': [o.pk for o in calculado['pasan']],
            'detalle': calculado['detalle'],
        },
    )

    siguiente = _ronda_siguiente(votacion)
    if siguiente is None or siguiente.estado not in (Votacion.BORRADOR, Votacion.LISTA):
        return

    if tipo == Votacion.GANADOR:
        # La segunda vuelta o la final ya no hacen falta.
        _cambiar_estado(
            Votacion, siguiente, (Votacion.BORRADOR, Votacion.LISTA), Votacion.CANCELADA
        )
        registrar_evento(
            request, 'votaciones', 'ronda_cancelada',
            {'id': siguiente.pk, 'motivo': 'La ronda anterior tuvo ganador.'},
        )
    elif tipo in (Votacion.SEGUNDA_RONDA, Votacion.CLASIFICADOS):
        _llenar_ronda(siguiente, calculado['pasan'])
        try:
            preparar_ronda(siguiente, request)
        except TransicionInvalida as error:
            # Los candidatos quedan cargados; el organizador corrige (por
            # ejemplo, las fechas) y la prepara desde su panel.
            registrar_evento(
                request, 'votaciones', 'ronda_no_preparada',
                {'id': siguiente.pk, 'motivo': str(error), 'errores': error.errores},
            )
    # REPETIR: la ronda siguiente espera candidatos nuevos del organizador.
    # EMPATE: espera la decisión del organizador (resolver_empate).


def _llenar_ronda(siguiente, pasan):
    """Copia los candidatos que pasan (con su foto) más el voto en blanco."""
    siguiente.opciones.all().delete()
    for orden, origen in enumerate(pasan, start=1):
        Opcion.objects.create(
            votacion=siguiente,
            nombre=origen.nombre,
            subtitulo=origen.subtitulo,
            descripcion=origen.descripcion,
            foto=origen.foto.name if origen.foto else '',
            orden=orden,
            opcion_origen=origen,
        )
    Opcion.objects.create(
        votacion=siguiente,
        nombre='Voto en blanco',
        subtitulo='No favorece a ninguna candidatura.',
        orden=99,
        es_voto_blanco=True,
    )


def preparar_ronda(votacion, request=None):
    """Ronda derivada BORRADOR → LISTA cuando ya tiene candidatos.

    La llama el escrutinio de la ronda anterior (clasificados o segunda
    vuelta) o el organizador, tras cargar candidatos nuevos en una
    repetición. Si la edición está activa y su fecha llegó, abre.
    """
    if not votacion.es_ronda_derivada or votacion.estado != Votacion.BORRADOR:
        raise TransicionInvalida('Solo se prepara una ronda derivada en BORRADOR.')
    edicion = votacion.edicion
    if edicion.estado not in (Edicion.PROGRAMADA, Edicion.ACTIVA):
        raise TransicionInvalida('La edición ya no admite rondas nuevas.')
    validas = votacion.opciones.filter(es_voto_blanco=False).count()
    if validas < 2:
        raise TransicionInvalida('La ronda necesita al menos 2 candidatos.')
    errores = errores_de_fechas_votacion(edicion, votacion.fecha_apertura, votacion.fecha_cierre)
    if votacion.fecha_cierre <= timezone.now():
        errores.append('Su fecha de cierre ya pasó: ajústala antes de prepararla.')
    if errores:
        raise TransicionInvalida('La ronda no está lista.', errores)

    if not _cambiar_estado(Votacion, votacion, Votacion.BORRADOR, Votacion.LISTA):
        raise TransicionInvalida('La ronda cambió de estado mientras se preparaba.')
    registrar_evento(request, 'votaciones', 'ronda_preparada', {'id': votacion.pk})
    abrir_votaciones_pendientes(Edicion.objects.get(pk=edicion.pk))
    return votacion


@transaction.atomic
def resolver_empate(votacion, opciones, motivo, request=None):
    """El organizador decide un empate eligiendo quién gana o quiénes pasan."""
    if votacion.resultado != Votacion.EMPATE:
        raise TransicionInvalida('La votación no tiene un empate por resolver.')
    motivo = (motivo or '').strip()
    if len(motivo) < 10:
        raise TransicionInvalida('Explica la decisión con al menos 10 caracteres.')
    necesarias = cuantos_pasan(votacion)
    elegidas = [o for o in opciones if o.votacion_id == votacion.pk and not o.es_voto_blanco]
    if len(elegidas) != necesarias or len({o.pk for o in elegidas}) != necesarias:
        raise TransicionInvalida(f'Debes elegir exactamente {necesarias} opción(es).')

    if votacion.regla_resultado == Votacion.MAYORIA_SIMPLE:
        tipo = Votacion.GANADOR
    elif votacion.regla_resultado == Votacion.MAYORIA_ABSOLUTA:
        tipo = Votacion.SEGUNDA_RONDA
    else:
        tipo = Votacion.CLASIFICADOS
    Votacion.objects.filter(pk=votacion.pk).update(decision_empate=motivo)
    votacion.decision_empate = motivo
    aplicar_resultado(
        votacion,
        {
            'resultado': tipo,
            'pasan': elegidas,
            'ganadora': elegidas[0] if tipo == Votacion.GANADOR else None,
            'total': None,
            'detalle': f'Empate resuelto por el organizador: {motivo}',
        },
        request,
    )
    return votacion


def escrutar_edicion(edicion, request=None):
    """Escruta todas las votaciones CERRADAS de la edición. Devuelve cuántas."""
    escrutadas = 0
    for votacion in edicion.votaciones.filter(estado=Votacion.CERRADA):
        escrutar(votacion, request)
        escrutadas += 1
    edicion.refresh_from_db(fields=['estado'])
    return escrutadas


# ---------------------------------------------------------------------------
# Cambios automáticos por fecha
# ---------------------------------------------------------------------------

def abrir_votaciones_pendientes(edicion, ahora=None):
    """Abre las votaciones LISTA cuya ventana ya empezó (solo con la edición ACTIVA)."""
    ahora = ahora or timezone.now()
    if edicion.estado != Edicion.ACTIVA:
        return 0
    ids = list(
        edicion.votaciones.filter(
            estado=Votacion.LISTA, fecha_apertura__lte=ahora, fecha_cierre__gt=ahora
        ).values_list('pk', flat=True)
    )
    if ids:
        Votacion.objects.filter(pk__in=ids, estado=Votacion.LISTA).update(estado=Votacion.ABIERTA)
        for pk in ids:
            registrar_evento(None, 'votaciones', 'votacion_abierta', {'id': pk, 'automatico': True})
    return len(ids)


def sincronizar_edicion(edicion, ahora=None):
    """Aplica a una edición los cambios que tocan por fecha."""
    ahora = ahora or timezone.now()
    if (
        edicion.estado == Edicion.PROGRAMADA
        and edicion.fecha_inicio
        and edicion.fecha_inicio <= ahora
    ):
        activar(edicion)
    if edicion.estado == Edicion.ACTIVA and edicion.fecha_fin and edicion.fecha_fin <= ahora:
        cerrar(edicion)
    if edicion.estado == Edicion.ACTIVA:
        abrir_votaciones_pendientes(edicion, ahora)
        for votacion in edicion.votaciones.filter(
            estado=Votacion.ABIERTA, fecha_cierre__lte=ahora
        ):
            cerrar_votacion(votacion, automatico=True)


def sincronizar(ahora=None):
    """Recorre lo que tiene una fecha vencida y aplica sus cambios de estado.

    Lo llama el middleware en cada petición y el comando
    ``sincronizar_estados`` (para un cron). Cuando no hay nada pendiente
    son unas pocas consultas indexadas y ninguna escritura.
    """
    ahora = ahora or timezone.now()
    pendientes = Edicion.objects.filter(
        Q(estado=Edicion.PROGRAMADA, fecha_inicio__lte=ahora)
        | Q(estado=Edicion.ACTIVA, fecha_fin__lte=ahora)
        | Q(
            estado=Edicion.ACTIVA,
            votaciones__estado=Votacion.LISTA,
            votaciones__fecha_apertura__lte=ahora,
            votaciones__fecha_cierre__gt=ahora,
        )
        | Q(
            estado=Edicion.ACTIVA,
            votaciones__estado=Votacion.ABIERTA,
            votaciones__fecha_cierre__lte=ahora,
        )
    ).distinct()

    procesadas = 0
    for edicion in pendientes:
        sincronizar_edicion(edicion, ahora)
        procesadas += 1
    return procesadas

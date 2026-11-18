from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from back.apps.auditoria.servicio import registrar_evento
from back.apps.elecciones.models import Edicion, Opcion, Votacion
from back.apps.usuarios.permisos import tiene_permiso

from .inscripciones import (
    InscripcionNoPermitida,
    es_elegible,
    es_votante,
    esta_inscrito,
    inscribir,
    usa_inscripcion,
)
from .models import PadronVotante, Voto, nuevo_comprobante


def rol_del_usuario(user):
    """Nombre del rol del perfil del usuario (o None si no tiene perfil)."""
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None)


def inicio(request):
    """Listado de ediciones disponibles (Leyenda Vallenata, Festival...).

    Calcula por edición: fechas del proceso, votaciones abiertas ahora y el
    progreso personal (categorías en las que ya votó el usuario), para que
    la pantalla de inicio muestre todo de un vistazo y con una edición
    destacada que invite a entrar a votar.
    """
    ediciones = list(
        Edicion.objects
        .prefetch_related('votaciones__categoria')
        .order_by('-anio', 'nombre')
    )

    # Progreso del votante: (categoría, ronda) en las que ya consumió su
    # voto, agrupadas por edición.
    votos_por_edicion = {}
    if request.user.is_authenticated:
        filas = PadronVotante.objects.filter(
            usuario=request.user,
            ha_votado=True,
        ).values_list('edicion_id', 'categoria_id', 'ronda')
        for edicion_id, categoria_id, ronda in filas:
            votos_por_edicion.setdefault(edicion_id, set()).add((categoria_id, ronda))

    for edicion in ediciones:
        votaciones = [v for v in edicion.votaciones.all() if v.estado != Votacion.CANCELADA]
        aperturas = [v.fecha_apertura for v in votaciones]
        edicion.num_votaciones = len(votaciones)
        edicion.num_abiertas = sum(1 for v in votaciones if v.esta_abierta)
        # El periodo es el de la propia edición (fecha_inicio/fecha_fin).
        edicion.ultima_apertura = max(aperturas) if aperturas else None

        nombres = sorted({v.categoria.nombre for v in votaciones})
        edicion.num_categorias = len({(v.categoria_id, v.numero_ronda) for v in votaciones})
        edicion.nombres_categorias = nombres

        votadas = votos_por_edicion.get(edicion.pk, set())
        edicion.categorias_votadas = len(votadas)

    # Destacamos la edición cuya votación abierta se lanzó más recientemente,
    # así el proceso en curso encabeza la pantalla aunque existan ediciones
    # de años futuros o antiguas en paralelo.
    candidatas = [e for e in ediciones if e.estado == 'ACTIVA' and e.num_abiertas]
    destacada = (
        max(candidatas, key=lambda e: e.ultima_apertura)
        if candidatas
        else next((e for e in ediciones if e.estado == 'ACTIVA'), None)
    )

    # El resto se agrupa por momento del proceso. Los borradores no se
    # muestran al público: aún se están armando en gestión.
    resto = [e for e in ediciones if e is not destacada and e.estado != 'BORRADOR']
    en_curso = [e for e in resto if e.estado in ('ACTIVA', 'CERRANDO')]
    proximas = [e for e in resto if e.estado == 'PROGRAMADA']
    anteriores = [e for e in resto if e.estado == 'FINALIZADA']

    # Cifras en vivo (quién va primero, votos emitidos) solo para quien
    # tiene resultados.ver: al público no se le muestran para no influir
    # en quien todavía no vota.
    en_vivo = destacada is not None and tiene_permiso(request.user, 'resultados.ver')
    return render(
        request,
        'votacion/inicio.html',
        {
            'destacada': destacada,
            'lideres': _lideres_en_vivo(destacada) if en_vivo else [],
            'votos_destacada': (
                Voto.objects.filter(opcion__votacion__edicion=destacada).count()
                if en_vivo else 0
            ),
            'en_curso': en_curso,
            'proximas': proximas,
            'anteriores': anteriores,
            'hay_ediciones': bool(ediciones),
        },
    )


def _lideres_en_vivo(edicion):
    """Quién va primero en cada votación abierta (solo para resultados.ver).

    Solo se nombra un líder cuando la ventaja es clara (sin empate en el
    primer lugar) y nunca el voto en blanco.
    """
    lideres = []
    votaciones = (
        edicion.votaciones
        .filter(estado=Votacion.ABIERTA)
        .select_related('categoria')
        .order_by('categoria__nombre')
    )
    for votacion in votaciones:
        opciones = list(
            votacion.opciones.annotate(total=Count('votos')).order_by('-total', 'orden')
        )
        total = sum(o.total for o in opciones)
        candidatas = [o for o in opciones if not o.es_voto_blanco]
        if not total or not candidatas:
            continue
        primera = candidatas[0]
        if len(candidatas) > 1 and candidatas[1].total == primera.total:
            continue
        lideres.append({
            'votacion': votacion,
            'opcion': primera,
            'porcentaje': round(primera.total * 100 / total),
        })
    return lideres


def edicion_detalle(request, pk):
    """Categorías y votaciones de una edición, agrupadas por categoría.

    Para votantes autenticados marca qué votaciones (y qué categorías de
    la edición) ya consumieron su voto, guarda el hash de su comprobante
    y calcula fechas y votaciones abiertas, para que cada tarjeta muestre
    una llamada a la acción clara: votar, ver su voto o ver resultados.
    """
    edicion = get_object_or_404(Edicion, pk=pk)
    votaciones = list(
        edicion.votaciones
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    )

    ids_votaciones_votadas = set()
    turnos_votados = set()  # (categoría, ronda) donde ya usó su voto
    comprobantes = {}
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        filas = PadronVotante.objects.filter(
            usuario=usuario,
            edicion=edicion,
            ha_votado=True,
        ).values_list('votacion_id', 'categoria_id', 'ronda', 'hash_comprobante')
        ids_votaciones_votadas = {fila[0] for fila in filas}
        turnos_votados = {(fila[1], fila[2]) for fila in filas}
        comprobantes = {fila[0]: fila[3] for fila in filas if fila[3]}

    # Datos de contexto para el encabezado y las tarjetas. Las votaciones
    # canceladas se muestran (son historia) pero no cuentan como pendientes.
    edicion.num_abiertas = sum(1 for v in votaciones if v.esta_abierta)
    turnos = {(v.categoria_id, v.numero_ronda) for v in votaciones if v.estado != Votacion.CANCELADA}
    edicion.num_categorias = len(turnos)
    for votacion in votaciones:
        votacion.mi_comprobante = comprobantes.get(votacion.pk)
        # Ya votó en otra votación paralela de la misma categoría y ronda.
        votacion.bloqueada = (
            votacion.pk not in ids_votaciones_votadas
            and (votacion.categoria_id, votacion.numero_ronda) in turnos_votados
        )
        votacion.elegible = es_elegible(usuario, votacion) if usuario else True

    es_votante_actual = usuario is not None and es_votante(usuario)
    inscripcion = {
        'aplica': usa_inscripcion(edicion),
        'inscrito': es_votante_actual and esta_inscrito(usuario, edicion),
        'puede': (
            es_votante_actual
            and edicion.estado in (Edicion.PROGRAMADA, Edicion.ACTIVA)
        ),
    }

    return render(
        request,
        'votacion/edicion.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'ids_votaciones_votadas': ids_votaciones_votadas,
            'num_turnos_votados': len(turnos_votados & turnos),
            'inscripcion': inscripcion,
        },
    )


@login_required
@require_POST
def inscribirse(request, pk):
    """El votante se inscribe a la edición (para las votaciones solo inscritos)."""
    edicion = get_object_or_404(Edicion, pk=pk)
    try:
        inscribir(request, edicion, request.user)
    except InscripcionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            'Quedaste inscrito. Podrás votar en las votaciones "solo inscritos" '
            'que abran desde ahora.',
        )
    return redirect('edicion-detalle', pk=pk)


def tarjeton(request, pk):
    """Tarjetón: opciones de una votación y formulario de voto."""
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria'),
        pk=pk,
    )
    # El voto en blanco siempre al final del tarjetón.
    opciones = votacion.opciones.order_by('es_voto_blanco', 'orden', 'nombre')

    ya_voto = False
    elegible = True
    if request.user.is_authenticated:
        ya_voto = PadronVotante.objects.filter(
            usuario=request.user,
            votacion=votacion,
            ha_votado=True,
        ).exists()
        elegible = es_elegible(request.user, votacion)

    return render(
        request,
        'votacion/tarjeton.html',
        {
            'votacion': votacion,
            'opciones': opciones,
            'ya_voto': ya_voto,
            'elegible': elegible,
            'participacion': votacion.participacion(),
            'normativas': votacion.normativas.order_by('fecha_publicacion'),
            'resultados_visibles': _resultados_visibles(request.user, votacion),
            # Solo el rol Votante ve el formulario; las autoridades del
            # proceso (auditor, organizador, administrador) no emiten voto.
            'rol_votante': rol_del_usuario(request.user) == 'Votante',
        },
    )


def _resultados_visibles(user, votacion):
    """R2: el conteo por opción es público solo al cerrar la votación.

    Antes del cierre lo ven únicamente quienes tienen ``resultados.ver``
    (organizador, auditor, administrador): verlo podría influir en quien
    todavía no vota.
    """
    return votacion.tiene_resultado_final or tiene_permiso(user, 'resultados.ver')


@login_required
@require_POST
def votar(request, pk):
    """Registra el voto de forma atómica y marca el padrón."""
    votacion = get_object_or_404(Votacion, pk=pk)

    if not votacion.esta_abierta:
        messages.error(request, 'Esta votación no está abierta.')
        return redirect('tarjeton', pk=pk)

    # Regla electoral: solo el rol Votante emite voto. Las autoridades del
    # proceso (auditor, organizador, administrador) conservan la consulta.
    rol = rol_del_usuario(request.user)
    if rol != 'Votante':
        messages.warning(
            request,
            f'El rol «{rol or "sin rol"}» no emite voto; puedes consultar los '
            'resultados cuando la votación los muestre.',
        )
        return redirect('resultados', pk=pk)

    # Modo de participación: en una votación "solo inscritos" vota quien
    # se inscribió a la edición antes de que la votación abriera.
    if not es_elegible(request.user, votacion):
        messages.error(
            request,
            'Esta votación es solo para inscritos y no te inscribiste a la edición '
            'antes de que abriera.',
        )
        return redirect('tarjeton', pk=pk)

    opcion_id = request.POST.get('opcion')
    if not opcion_id:
        messages.error(request, 'Debes seleccionar una opción.')
        return redirect('tarjeton', pk=pk)

    opcion = get_object_or_404(Opcion, pk=opcion_id, votacion=votacion)

    # Regla de unicidad (CP-02): un voto por usuario, categoría y ronda en
    # cada edición, aunque la categoría tenga varias votaciones paralelas
    # (subeventos). El chequeo amistoso da el mensaje claro antes de la BD.
    votados = PadronVotante.objects.filter(
        usuario=request.user,
        edicion=votacion.edicion,
        categoria=votacion.categoria,
        ronda=votacion.numero_ronda,
        ha_votado=True,
    )
    if votados.exists():
        if votados.filter(votacion=votacion).exists():
            messages.warning(request, 'Ya registraste tu voto en esta votación.')
        else:
            messages.warning(
                request,
                'Ya registraste tu voto en esta categoría; solo se emite un '
                'voto por categoría dentro de la edición.',
            )
        return redirect('tarjeton', pk=pk)

    try:
        with transaction.atomic():
            padron, _ = PadronVotante.objects.get_or_create(
                usuario=request.user,
                votacion=votacion,
                defaults={
                    'edicion': votacion.edicion,
                    'categoria': votacion.categoria,
                },
            )

            # Sincroniza la copia desnormalizada (filas precargadas) para que
            # la constraint la contemple: save() la toma de la votación.
            if (
                padron.edicion_id != votacion.edicion_id
                or padron.categoria_id != votacion.categoria_id
                or padron.ronda != votacion.numero_ronda
            ):
                padron.save(update_fields=['edicion', 'categoria', 'ronda'])

            # Integridad frente a concurrencia: la reserva del voto se hace con
            # un UPDATE condicional atómico. Si dos requests simultáneas pasan
            # por aquí, solo una logra convertir ha_votado=False → True; la otra
            # recibe 0 filas y es rechazada. Sin esta condición, dos lecturas
            # concurrentes del flag podrían crear dos votos (la urna es anónima,
            # así que no hay llave que lo impida en MySQL). La creación del voto
            # queda dentro de la transacción: si falla, el rollback revierte la
            # reserva y el votante puede reintentar sin problema.
            reservados = PadronVotante.objects.filter(
                pk=padron.pk,
                ha_votado=False,
            ).update(ha_votado=True)

            if not reservados:
                messages.warning(request, 'Ya registraste tu voto en esta votación.')
                return redirect('tarjeton', pk=pk)

            # Secreto del voto: el voto no sabe de quién es, y el
            # comprobante es un código propio, no la firma del voto.
            Voto.objects.create(opcion=opcion)
            padron.hash_comprobante = nuevo_comprobante()
            padron.save(update_fields=['hash_comprobante'])
    except IntegrityError:
        # CP-09 y CP-02 estricto: si dos requests simultáneas compitieron por
        # la misma categoría (en esta u otra votación de la edición), la
        # constraint de BD rechaza la segunda; queda el primer voto.
        messages.warning(
            request,
            'Ya registraste tu voto en esta categoría; solo se emite un voto '
            'por categoría dentro de la edición.',
        )
        return redirect('tarjeton', pk=pk)

    messages.success(request, 'Tu voto quedó registrado correctamente.')
    # Auditoría: constancia de que entró un voto en la votación, sin quién
    # ni desde dónde (request=None): ni la opción ni la identidad.
    registrar_evento(
        None,
        modulo='votacion',
        accion='voto_emitido',
        detalles={'votacion': votacion.pk, 'votacion_nombre': votacion.nombre},
    )
    return redirect('comprobante', hash_comprobante=padron.hash_comprobante)


def resultados(request, pk):
    """Resultados por opción, con conteo y porcentaje.

    R2 (regla de visibilidad): el conteo es público cuando la votación cierra.
    Antes, solo con ``resultados.ver``; el público ve únicamente la
    participación en porcentaje (en el tarjetón).
    """
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria', 'opcion_ganadora'),
        pk=pk,
    )

    if not _resultados_visibles(request.user, votacion):
        messages.info(request, 'Los resultados se publicarán al cierre de la votación.')
        return redirect('tarjeton', pk=pk)

    opciones = list(
        votacion.opciones.annotate(total=Count('votos')).order_by('-total', 'orden')
    )
    total = sum(opcion.total for opcion in opciones)

    for opcion in opciones:
        opcion.porcentaje = round(opcion.total * 100 / total, 1) if total else 0

    # Primer lugar sin empate (el voto en blanco no "gana").
    candidatas = [o for o in opciones if not o.es_voto_blanco]
    lider = None
    if total and candidatas and (
        len(candidatas) == 1 or candidatas[0].total > candidatas[1].total
    ):
        lider = candidatas[0]

    # Con el resultado aplicado: quiénes pasan a la siguiente ronda.
    siguiente = Votacion.objects.filter(ronda_anterior=votacion).first()
    pasan = []
    if siguiente is not None and votacion.resultado in (Votacion.SEGUNDA_RONDA, Votacion.CLASIFICADOS):
        pasan = list(
            siguiente.opciones.filter(es_voto_blanco=False).values_list('opcion_origen_id', flat=True)
        )
    for opcion in opciones:
        opcion.pasa = opcion.pk in pasan

    return render(
        request,
        'votacion/resultados.html',
        {
            'votacion': votacion,
            'opciones': opciones,
            'total': total,
            'lider': lider,
            'siguiente': siguiente,
            'participacion': votacion.participacion(),
        },
    )


@login_required
def comprobante(request, hash_comprobante):
    """V4: comprobante de voto; solo lo ve su dueño y nunca revela la opción."""
    padron = get_object_or_404(
        PadronVotante.objects.select_related(
            'votacion__edicion', 'votacion__categoria'
        ),
        hash_comprobante=hash_comprobante,
    )

    if padron.usuario_id != request.user.id:
        raise PermissionDenied('Este comprobante solo lo puede ver su dueño.')

    return render(
        request,
        'votacion/comprobante.html',
        {'padron': padron, 'votacion': padron.votacion},
    )


@login_required
def mis_votos(request):
    """V5: votaciones en las que el usuario ya votó, con su comprobante."""
    padrones = (
        PadronVotante.objects.filter(usuario=request.user, ha_votado=True)
        .select_related('votacion__edicion', 'votacion__categoria')
        .order_by('-fecha_emision')
    )
    return render(request, 'votacion/mis_votos.html', {'padrones': padrones})


@login_required
def resultados_indice(request):
    """R3: ediciones visibles para elegir el consolidado."""
    return render(
        request,
        'votacion/resultados_indice.html',
        {'ediciones': Edicion.objects.exclude(estado=Edicion.BORRADOR).order_by('-anio', 'nombre')},
    )


@login_required
def resultados_consolidado(request, edicion_id):
    """R3: votaciones de una edición con su conteo.

    El conteo de una votación aún abierta solo lo ve quien tiene
    ``resultados.ver``; el resto ve "se publica al cierre".
    """
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    en_vivo = tiene_permiso(request.user, 'resultados.ver')
    votaciones = list(
        Votacion.objects.filter(edicion=edicion)
        .select_related('categoria', 'opcion_ganadora')
        .annotate(total=Count('opciones__votos'))
        .order_by('categoria__nombre', 'numero_ronda', 'nombre')
    )
    for votacion in votaciones:
        votacion.visible = en_vivo or votacion.tiene_resultado_final
    total_edicion = sum(v.total for v in votaciones if v.visible)

    return render(
        request,
        'votacion/resultados_consolidado.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'total_edicion': total_edicion,
        },
    )

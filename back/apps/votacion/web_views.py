from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from back.apps.auditoria.servicio import registrar_evento
from back.apps.elecciones.models import Edicion, Opcion, Votacion
from back.apps.usuarios.permisos import requiere_permiso, tiene_permiso

from .models import PadronVotante, Voto


def rol_del_usuario(user):
    """Nombre del rol del perfil del usuario (o None si no tiene perfil)."""
    perfil = getattr(user, 'perfil_usuario', None)
    return getattr(getattr(perfil, 'rol', None), 'nombre', None)


def inicio(request):
    """Listado de ediciones disponibles (Festival 2027, ...).

    Cada tarjeta resume cuántas categorías agrupa la edición y sus nombres,
    para que se vea de un vistazo que una edición puede tener varias.
    """
    ediciones = list(
        Edicion.objects
        .prefetch_related('votaciones__categoria')
        .order_by('-anio', 'nombre')
    )
    for edicion in ediciones:
        nombres = sorted({v.categoria.nombre for v in edicion.votaciones.all()})
        edicion.num_categorias = len(nombres)
        edicion.nombres_categorias = nombres
    return render(request, 'votacion/inicio.html', {'ediciones': ediciones})


def edicion_detalle(request, pk):
    """Categorías y votaciones de una edición, agrupadas por categoría.

    Para votantes autenticados marca qué votaciones (y qué categorías de
    la edición) ya consumieron su voto, para que la regla
    usuario → categoría → edición quede visible en la pantalla.
    """
    edicion = get_object_or_404(Edicion, pk=pk)
    votaciones = (
        edicion.votaciones
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    )

    ids_votaciones_votadas = set()
    ids_categorias_votadas = set()
    if request.user.is_authenticated:
        filas = PadronVotante.objects.filter(
            usuario=request.user,
            votacion__edicion=edicion,
            ha_votado=True,
        ).values_list('votacion_id', 'categoria_id')
        ids_votaciones_votadas = {fila[0] for fila in filas}
        ids_categorias_votadas = {fila[1] for fila in filas}

    return render(
        request,
        'votacion/edicion.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'ids_votaciones_votadas': ids_votaciones_votadas,
            'ids_categorias_votadas': ids_categorias_votadas,
        },
    )


def tarjeton(request, pk):
    """Tarjetón: opciones de una votación y formulario de voto."""
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria'),
        pk=pk,
    )
    opciones = votacion.opciones.order_by('orden', 'nombre')

    ya_voto = False
    if request.user.is_authenticated:
        ya_voto = PadronVotante.objects.filter(
            usuario=request.user,
            votacion=votacion,
            ha_votado=True,
        ).exists()

    return render(
        request,
        'votacion/tarjeton.html',
        {
            'votacion': votacion,
            'opciones': opciones,
            'ya_voto': ya_voto,
            # Solo el rol Votante ve el formulario; las autoridades del
            # proceso (auditor, organizador, administrador) no emiten voto.
            'rol_votante': rol_del_usuario(request.user) == 'Votante',
        },
    )


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

    opcion_id = request.POST.get('opcion')
    if not opcion_id:
        messages.error(request, 'Debes seleccionar una opción.')
        return redirect('tarjeton', pk=pk)

    opcion = get_object_or_404(Opcion, pk=opcion_id, votacion=votacion)

    # Regla de unicidad (CP-02): un voto por usuario, categoría y edición,
    # aunque la categoría tenga varias votaciones (subeventos). El chequeo
    # amistoso da el mensaje claro antes de tocar la BD.
    votados = PadronVotante.objects.filter(
        usuario=request.user,
        edicion=votacion.edicion,
        categoria=votacion.categoria,
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
        return redirect('resultados', pk=pk)

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

            # Sincroniza la copia desnormalizada (filas legadas o precargadas
            # sin la jerarquía) para que la constraint la contemple.
            if padron.edicion_id != votacion.edicion_id or padron.categoria_id != votacion.categoria_id:
                padron.edicion = votacion.edicion
                padron.categoria = votacion.categoria
                padron.save(update_fields=['edicion', 'categoria'])

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
                return redirect('resultados', pk=pk)

            voto = Voto.objects.create(opcion=opcion)
            padron.hash_comprobante = voto.firma_criptografica
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
        return redirect('resultados', pk=pk)

    messages.success(request, 'Tu voto quedó registrado correctamente.')
    # Auditoría: se deja constancia de la participación, NUNCA de la
    # opción elegida, para conservar el secreto del voto.
    registrar_evento(
        request,
        modulo='votacion',
        accion='voto_emitido',
        detalles={'votacion': votacion.pk, 'votacion_nombre': votacion.nombre},
    )
    return redirect('resultados', pk=pk)


def resultados(request, pk):
    """Resultados por opción, con conteo y porcentaje.

    R2 (regla de visibilidad): se ven si la votación los muestra en vivo,
    si ya está FINALIZADA o si se tiene el permiso ``resultados.ver``.
    """
    votacion = get_object_or_404(
        Votacion.objects.select_related('edicion', 'categoria'),
        pk=pk,
    )

    visible = (
        votacion.mostrar_resultados_en_vivo
        or votacion.estado == 'FINALIZADA'
        or tiene_permiso(request.user, 'resultados.ver')
    )

    if not visible:
        messages.info(request, 'Los resultados se publicarán al cierre de la votación.')
        return redirect('tarjeton', pk=pk)

    opciones = list(
        votacion.opciones.annotate(total=Count('votos')).order_by('-total', 'orden')
    )
    total = sum(opcion.total for opcion in opciones)

    for opcion in opciones:
        opcion.porcentaje = round(opcion.total * 100 / total, 1) if total else 0

    return render(
        request,
        'votacion/resultados.html',
        {'votacion': votacion, 'opciones': opciones, 'total': total},
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


@requiere_permiso('resultados.ver')
def resultados_indice(request):
    """R3: ediciones con resultados para elegir el consolidado."""
    return render(
        request,
        'votacion/resultados_indice.html',
        {'ediciones': Edicion.objects.order_by('-anio', 'nombre')},
    )


@requiere_permiso('resultados.ver')
def resultados_consolidado(request, edicion_id):
    """R3: todas las votaciones de una edición con su conteo."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    votaciones = (
        Votacion.objects.filter(edicion=edicion)
        .annotate(total=Count('opciones__votos'))
        .order_by('categoria__nombre', 'nombre')
    )
    total_edicion = sum(v.total for v in votaciones)

    return render(
        request,
        'votacion/resultados_consolidado.html',
        {
            'edicion': edicion,
            'votaciones': votaciones,
            'total_edicion': total_edicion,
        },
    )

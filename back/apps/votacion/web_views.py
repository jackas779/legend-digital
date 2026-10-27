from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from back.apps.elecciones.models import Edicion, Opcion, Votacion
from back.apps.usuarios.permisos import requiere_permiso, tiene_permiso

from .models import PadronVotante, Voto


def inicio(request):
    """Listado de ediciones disponibles (Festival 2027, ...)."""
    ediciones = (
        Edicion.objects
        .prefetch_related('votaciones__categoria')
        .order_by('-anio', 'nombre')
    )
    return render(request, 'votacion/inicio.html', {'ediciones': ediciones})


def edicion_detalle(request, pk):
    """Categorías y votaciones de una edición."""
    edicion = get_object_or_404(Edicion, pk=pk)
    votaciones = (
        edicion.votaciones
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    )
    return render(
        request,
        'votacion/edicion.html',
        {'edicion': edicion, 'votaciones': votaciones},
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

    opcion_id = request.POST.get('opcion')
    if not opcion_id:
        messages.error(request, 'Debes seleccionar una opción.')
        return redirect('tarjeton', pk=pk)

    opcion = get_object_or_404(Opcion, pk=opcion_id, votacion=votacion)

    with transaction.atomic():
        padron, _ = PadronVotante.objects.get_or_create(
            usuario=request.user,
            votacion=votacion,
        )

        if padron.ha_votado:
            messages.warning(request, 'Ya registraste tu voto en esta votación.')
            return redirect('resultados', pk=pk)

        voto = Voto.objects.create(opcion=opcion)
        padron.ha_votado = True
        padron.hash_comprobante = voto.firma_criptografica
        padron.save(update_fields=['ha_votado', 'hash_comprobante'])

    messages.success(request, 'Tu voto quedó registrado correctamente.')
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
